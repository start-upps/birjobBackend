import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import logging

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
    pool_size=10,
    max_overflow=20,
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

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

class DatabaseManager:
    """Direct database operations using asyncpg for complex queries"""
    
    def __init__(self):
        self.pool = None
    
    async def init_pool(self):
        """Initialize connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL.replace("+asyncpg", ""),
                min_size=5,
                max_size=20
            )
    
    async def execute_query(self, query: str, *args):
        """Execute a query and return results"""
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_command(self, command: str, *args):
        """Execute a command (INSERT, UPDATE, DELETE)"""
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as conn:
            return await conn.execute(command, *args)
    
    async def transaction(self):
        """Get a transaction context"""
        if not self.pool:
            await self.init_pool()
        
        return self.pool.acquire()

# Global database manager instance
db_manager = DatabaseManager()