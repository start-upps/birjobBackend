#!/usr/bin/env python3
"""
Add last_activity column to device_users table
"""
import asyncio
import logging
from app.core.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migration():
    try:
        logger.info("Adding last_activity column to device_users table...")
        
        # Read migration SQL
        with open('add_last_activity.sql', 'r') as f:
            migration_sql = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            logger.info(f"Executing statement {i+1}/{len(statements)}")
            logger.info(f"SQL: {statement}")
            
            try:
                await db_manager.execute_command(statement)
                logger.info(f"✅ Statement {i+1} executed successfully")
            except Exception as e:
                if "already exists" in str(e).lower() or "column already exists" in str(e).lower():
                    logger.info(f"⚠️  Statement {i+1} skipped (already exists): {e}")
                else:
                    logger.error(f"❌ Failed on statement {i+1}: {statement}")
                    raise e
        
        logger.info("✅ last_activity migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    exit(0 if success else 1)