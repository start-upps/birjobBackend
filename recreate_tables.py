#!/usr/bin/env python3
"""
Script to recreate minimal database tables
Run this to clean up and create only essential tables
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def recreate_tables():
    """Recreate minimal database tables"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return
    
    print("🔄 Connecting to database...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database")
        
        # Read SQL file
        sql_file = Path(__file__).parent / "recreate_minimal_tables.sql"
        if not sql_file.exists():
            print("❌ SQL file not found: recreate_minimal_tables.sql")
            return
            
        sql_content = sql_file.read_text()
        print("📝 Read SQL recreation script")
        
        # Execute SQL commands
        print("🗑️ Dropping and recreating tables...")
        await conn.execute(sql_content)
        print("✅ Tables recreated successfully!")
        
        # Verify tables were created
        tables_query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'iosapp'
            ORDER BY tablename;
        """
        
        tables = await conn.fetch(tables_query)
        print(f"📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   • {table['tablename']}")
        
        await conn.close()
        print("✅ Database recreation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error recreating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🏗️ Recreating Minimal Database Tables")
    print("=" * 50)
    asyncio.run(recreate_tables())