#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')
from app.core.database import db_manager

async def check_tables():
    await db_manager.init_pool()
    result = await db_manager.execute_query("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'iosapp' 
        AND table_name IN ('search_analytics', 'job_engagement', 'user_actions', 'notification_analytics')
        ORDER BY table_name, column_name
    """)
    
    print('📊 Current analytics table columns:')
    current_table = None
    for row in result:
        if row['table_name'] != current_table:
            current_table = row['table_name']
            print(f'\n  {current_table}:')
        print(f'    - {row["column_name"]}')

asyncio.run(check_tables())