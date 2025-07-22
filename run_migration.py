#!/usr/bin/env python3
"""
Database migration script for v4.0.0 Job Match Session System
Runs automatically during deployment to create missing tables
"""
import asyncio
import logging
from app.core.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migration():
    """Run the database migration"""
    try:
        logger.info("Starting v4.0.0 database migration...")
        
        # Read migration SQL
        with open('migrate_v4_tables.sql', 'r') as f:
            migration_sql = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        # Filter out comments and empty statements
        sql_statements = []
        for stmt in statements:
            clean_stmt = stmt.strip()
            if clean_stmt and not clean_stmt.startswith('--'):
                sql_statements.append(clean_stmt)
        
        logger.info(f"Found {len(sql_statements)} SQL statements to execute")
        
        for i, statement in enumerate(sql_statements):
            logger.info(f"Executing statement {i+1}/{len(sql_statements)}")
            logger.info(f"SQL: {statement[:200]}...")
            
            try:
                await db_manager.execute_query(statement)
                logger.info(f"✅ Statement {i+1} executed successfully")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"⚠️  Statement {i+1} skipped (already exists): {e}")
                else:
                    logger.error(f"❌ Failed on statement {i+1}: {statement}")
                    raise e
        
        logger.info("✅ v4.0.0 database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    exit(0 if success else 1)