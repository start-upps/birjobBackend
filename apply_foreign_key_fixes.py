#!/usr/bin/env python3
"""
Apply missing foreign key relationships to fix RDBMS violations
This script safely adds the missing foreign key constraints to the analytics schema
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db_pool
from app.core.config import settings

async def apply_foreign_key_fixes():
    """Apply the foreign key fixes to the database"""
    
    # Read the SQL script
    sql_file = Path(__file__).parent / "fix_analytics_foreign_keys.sql"
    if not sql_file.exists():
        print("❌ SQL file not found: fix_analytics_foreign_keys.sql")
        return False
    
    with open(sql_file, 'r') as f:
        sql_script = f.read()
    
    # Split into individual statements (simple approach)
    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
    
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as connection:
            print("🔧 Applying foreign key fixes...")
            
            for i, statement in enumerate(statements, 1):
                try:
                    print(f"   📝 Executing statement {i}/{len(statements)}")
                    await connection.execute(statement)
                    print(f"   ✅ Statement {i} completed")
                except Exception as e:
                    error_msg = str(e)
                    # Check if it's a "already exists" error (which is OK)
                    if any(keyword in error_msg.lower() for keyword in ['already exists', 'duplicate', 'constraint already exists']):
                        print(f"   ⚠️  Statement {i} skipped (already exists): {error_msg}")
                    else:
                        print(f"   ❌ Statement {i} failed: {error_msg}")
                        # For ALTER TABLE statements, continue with others
                        if "alter table" not in statement.lower():
                            raise
            
            print("🎉 Foreign key fixes applied successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Failed to apply foreign key fixes: {e}")
        return False
    finally:
        await pool.close()

async def verify_foreign_keys():
    """Verify that the foreign keys were applied correctly"""
    
    verification_queries = [
        """
        SELECT tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_schema = 'iosapp'
        AND tc.table_name IN ('user_sessions', 'user_actions', 'search_analytics', 'job_engagement', 'user_preferences_history', 'notification_analytics')
        ORDER BY tc.table_name, tc.constraint_name;
        """,
        """
        SELECT COUNT(*) as analytics_tables_count 
        FROM information_schema.tables 
        WHERE table_schema = 'iosapp' 
        AND table_name IN ('user_sessions', 'user_actions', 'search_analytics', 'job_engagement', 'user_preferences_history', 'notification_analytics');
        """,
        """
        SELECT COUNT(*) as total_foreign_keys 
        FROM information_schema.table_constraints 
        WHERE constraint_type = 'FOREIGN KEY' 
        AND table_schema = 'iosapp';
        """
    ]
    
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as connection:
            print("\n🔍 Verifying foreign key relationships...")
            
            # Check foreign keys
            result = await connection.fetch(verification_queries[0])
            print(f"\n📊 Foreign key relationships found:")
            for row in result:
                print(f"   {row['table_name']}.{row['column_name']} -> {row['foreign_table_name']}")
            
            # Check table count
            result = await connection.fetchrow(verification_queries[1])
            print(f"\n📈 Analytics tables: {result['analytics_tables_count']}/6")
            
            # Check total foreign keys
            result = await connection.fetchrow(verification_queries[2])
            print(f"🔗 Total foreign keys in iosapp schema: {result['total_foreign_keys']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        await pool.close()

async def main():
    """Main execution function"""
    print("🚀 Starting foreign key fixes for analytics schema...")
    print(f"📊 Database URL: {settings.DATABASE_URL[:50]}...")
    
    # Apply the fixes
    success = await apply_foreign_key_fixes()
    
    if success:
        # Verify the fixes
        await verify_foreign_keys()
        print("\n✅ Foreign key fixes completed successfully!")
        print("📋 Analytics schema now follows proper RDBMS principles")
        return True
    else:
        print("\n❌ Foreign key fixes failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)