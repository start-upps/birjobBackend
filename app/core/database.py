import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import DisconnectionError, OperationalError
from typing import AsyncGenerator
import logging
import asyncio
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine - handle both asyncpg and psycopg2 URLs
database_url = settings.DATABASE_URL
original_url = database_url

if database_url and not database_url.startswith('postgresql+asyncpg://'):
    # Convert postgres:// to postgresql+asyncpg://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

# Remove sslmode from URL and configure SSL through connect_args
if database_url and 'sslmode=' in database_url:
    database_url = database_url.split('?sslmode=')[0]

# Configure SSL for cloud databases
connect_args = {}
if original_url and 'sslmode=require' in original_url:
    connect_args = {"ssl": "require"}

engine = create_async_engine(
    database_url,
    echo=False,
    pool_size=3,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,  # 30 minutes for Neon
    pool_timeout=30,
    connect_args=connect_args,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def init_db():
    """Initialize database connection and create tables if needed"""
    try:
        # Test connection
        async with engine.begin() as conn:
            logger.info("Database connection established")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise e

async def check_db_health():
    """Check database health and connection status"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            await result.fetchone()
            return {"status": "healthy", "message": "Database connection is working"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with retry logic"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                try:
                    yield session
                    break
                except (DisconnectionError, OperationalError) as e:
                    logger.warning(f"Database connection error on attempt {attempt + 1}: {e}")
                    await session.rollback()
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(retry_delay * (attempt + 1))
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        except (DisconnectionError, OperationalError) as e:
            logger.warning(f"Session creation failed on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(retry_delay * (attempt + 1))

class DatabaseManager:
    """Direct database operations using asyncpg for complex queries"""
    
    def __init__(self):
        self.pool = None
        self._pool_lock = asyncio.Lock()
    
    async def init_pool(self):
        """Initialize connection pool with retry logic"""
        async with self._pool_lock:
            if not self.pool:
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Remove asyncpg from URL for direct asyncpg connection
                        db_url = settings.DATABASE_URL.replace("+asyncpg", "")
                        self.pool = await asyncpg.create_pool(
                            db_url,
                            min_size=2,
                            max_size=8,
                            command_timeout=60,
                            server_settings={
                                'application_name': 'birjob_ios_backend',
                            }
                        )
                        logger.info("AsyncPG connection pool created successfully")
                        break
                    except Exception as e:
                        logger.error(f"Failed to create connection pool (attempt {attempt + 1}): {e}")
                        if attempt == max_retries - 1:
                            raise
                        await asyncio.sleep(2 ** attempt)
    
    async def execute_query(self, query: str, *args):
        """Execute a query and return results with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.pool:
                    await self.init_pool()
                
                async with self.pool.acquire() as conn:
                    return await conn.fetch(query, *args)
            except (asyncpg.ConnectionDoesNotExistError, asyncpg.InterfaceError) as e:
                logger.warning(f"Database connection error on query attempt {attempt + 1}: {e}")
                self.pool = None  # Reset pool on connection error
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))
    
    async def execute_command(self, command: str, *args):
        """Execute a command (INSERT, UPDATE, DELETE) with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.pool:
                    await self.init_pool()
                
                async with self.pool.acquire() as conn:
                    return await conn.execute(command, *args)
            except (asyncpg.ConnectionDoesNotExistError, asyncpg.InterfaceError) as e:
                logger.warning(f"Database connection error on command attempt {attempt + 1}: {e}")
                self.pool = None  # Reset pool on connection error
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))
    
    async def transaction(self):
        """Get a transaction context"""
        if not self.pool:
            await self.init_pool()
        
        return self.pool.acquire()

# Global database manager instance
db_manager = DatabaseManager()