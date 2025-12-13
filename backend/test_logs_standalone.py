#!/usr/bin/env python3
"""
Standalone test script for Supabase logs integration
This script tests the logs functionality independently of the main backend
"""

import asyncio
import sys
import os
import sqlite3
import json
from typing import Dict, Any

# Add backend path to imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import our utilities
from open_webui.utils.postgres_connection import postgres_manager
import asyncpg

async def test_database_connections():
    """Test database connections for all groups with database configuration"""
    
    print("🔍 Testing Supabase Database Connections")
    print("=" * 50)
    
    # Connect to SQLite database to get groups
    db_path = os.path.join(os.path.dirname(__file__), "data", "webui.db")
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    print(f"📂 Using database: {db_path}")
    
    try:
        # Connect to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all groups  
        cursor.execute('SELECT id, name, data FROM "group"')
        groups = cursor.fetchall()
        
        print(f"🔍 Found {len(groups)} groups in database")
        
        groups_with_db = []
        
        for group_id, group_name, group_data_json in groups:
            print(f"\n📋 Processing Group: {group_name} (ID: {group_id})")
            
            if not group_data_json:
                print("  ⚠️  No group data found")
                continue
            
            try:
                group_data = json.loads(group_data_json)
            except json.JSONDecodeError as e:
                print(f"  ❌ Invalid JSON in group data: {e}")
                continue
            
            # Check for database configuration
            if "database" not in group_data:
                print("  ⚠️  No database configuration")
                continue
            
            db_config = group_data["database"]
            if not db_config.get("enabled", False):
                print("  ⚠️  Database not enabled")
                continue
            
            if "connection" not in db_config:
                print("  ❌ No connection configuration")
                continue
            
            connection_config = db_config["connection"]
            print(f"  ✅ Database configured - Host: {connection_config.get('host', 'unknown')}")
            
            groups_with_db.append({
                "id": group_id,
                "name": group_name,
                "config": connection_config
            })
            
            # Test the actual connection
            try:
                print("  🔌 Testing database connection...")
                
                # Create connection parameters for asyncpg
                conn_params = {
                    "host": connection_config["host"],
                    "port": connection_config["port"],
                    "database": connection_config["database"],
                    "user": connection_config["user"],
                    "password": postgres_manager.decrypt_password(connection_config["password"]),
                    "ssl": "require"
                }
                
                # Test connection
                pg_conn = await asyncpg.connect(**conn_params)
                
                # Test basic query
                result = await pg_conn.fetchval("SELECT COUNT(*) FROM logs WHERE activation_status != 'deleted'")
                print(f"  ✅ Connection successful! Found {result} logs in database")
                
                # Test logs table structure
                schema_query = """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'logs' 
                ORDER BY ordinal_position
                """
                columns = await pg_conn.fetch(schema_query)
                print(f"  📊 Logs table has {len(columns)} columns:")
                for col in columns[:5]:  # Show first 5 columns
                    print(f"    - {col['column_name']}: {col['data_type']}")
                if len(columns) > 5:
                    print(f"    ... and {len(columns) - 5} more")
                
                # Test categories
                cat_result = await pg_conn.fetch("SELECT DISTINCT problem_category FROM logs WHERE problem_category IS NOT NULL LIMIT 5")
                if cat_result:
                    print(f"  🏷️  Sample categories: {[row['problem_category'] for row in cat_result]}")
                
                await pg_conn.close()
                
            except Exception as e:
                print(f"  ❌ Connection failed: {str(e)[:100]}...")
                continue
        
        conn.close()
        
        print(f"\n📊 Summary:")
        print(f"  Total groups: {len(groups)}")
        print(f"  Groups with database: {len(groups_with_db)}")
        
        if groups_with_db:
            print(f"\n🎉 Groups with working database connections:")
            for group in groups_with_db:
                print(f"  - {group['name']} (ID: {group['id']})")
        else:
            print(f"\n⚠️  No groups found with working database connections")
        
        return groups_with_db
        
    except Exception as e:
        print(f"❌ Error testing database connections: {e}")
        return []

async def test_logs_api_simulation():
    """Simulate the logs API endpoints locally"""
    
    print("\n🧪 Testing Logs API Simulation")
    print("=" * 40)
    
    # Get groups with database
    groups_with_db = await test_database_connections()
    
    if not groups_with_db:
        print("❌ No database connections available for API testing")
        return
    
    # Test with first available group
    test_group = groups_with_db[0]
    print(f"\n🎯 Testing with group: {test_group['name']} (ID: {test_group['id']})")
    
    try:
        # Connect using our connection manager
        async with postgres_manager.get_connection(test_group['id'], test_group['config']) as conn:
            
            # Test GET logs endpoint simulation
            print("\n📖 Simulating GET /api/v1/logs")
            query = """
            SELECT id, insight_title, insight_content, user_name, created_at, 
                   problem_category, verified, activation_status
            FROM logs 
            WHERE activation_status != 'deleted'
            ORDER BY created_at DESC 
            LIMIT 5
            """
            
            logs = await conn.fetch(query)
            print(f"  ✅ Retrieved {len(logs)} logs")
            
            for log in logs[:2]:  # Show first 2 logs
                print(f"    📝 {log['insight_title'][:50]}... (by {log['user_name']})")
            
            # Test categories endpoint simulation
            print(f"\n📂 Simulating GET /api/v1/logs/categories")
            cat_query = """
            SELECT DISTINCT problem_category 
            FROM logs 
            WHERE problem_category IS NOT NULL 
            AND activation_status != 'deleted'
            ORDER BY problem_category
            """
            
            categories = await conn.fetch(cat_query)
            category_list = [row['problem_category'] for row in categories]
            print(f"  ✅ Found {len(category_list)} categories: {category_list[:5]}")
            
            # Test equipment groups endpoint simulation
            print(f"\n⚙️  Simulating GET /api/v1/logs/equipment-groups")
            eq_query = """
            SELECT id, conventional_name, model_numbers, aliases
            FROM equipment_groups 
            WHERE activation_status = 'active'
            ORDER BY conventional_name
            LIMIT 5
            """
            
            try:
                equipment = await conn.fetch(eq_query)
                eq_list = [row['conventional_name'] for row in equipment]
                print(f"  ✅ Found {len(eq_list)} equipment groups: {eq_list}")
            except Exception as e:
                print(f"  ⚠️  Equipment table may not exist: {str(e)[:50]}...")
            
            print(f"\n✅ API simulation completed successfully!")
            
    except Exception as e:
        print(f"❌ API simulation failed: {e}")

def test_groups_with_logs_simulation():
    """Simulate the groups endpoint that returns groups with database access"""
    
    print("\n👥 Simulating GET /api/v1/logs/groups-with-logs")
    print("=" * 50)
    
    # Connect to SQLite database to get groups
    db_path = os.path.join(os.path.dirname(__file__), "data", "webui.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get groups with database configuration
        cursor.execute('SELECT id, name, data FROM "group"')
        groups = cursor.fetchall()
        
        groups_with_logs = []
        
        for group_id, group_name, group_data_json in groups:
            if not group_data_json:
                continue
                
            try:
                group_data = json.loads(group_data_json)
            except json.JSONDecodeError:
                continue
            
            # Check for database configuration
            if ("database" in group_data and 
                group_data["database"].get("enabled", False) and
                "connection" in group_data["database"]):
                
                groups_with_logs.append({
                    "id": group_id,
                    "name": group_name
                })
        
        conn.close()
        
        print(f"✅ Found {len(groups_with_logs)} groups with database access:")
        for group in groups_with_logs:
            print(f"  - {group['name']} (ID: {group['id']})")
        
        return groups_with_logs
        
    except Exception as e:
        print(f"❌ Error simulating groups endpoint: {e}")
        return []

async def main():
    """Main test function"""
    
    print("🚀 Supabase Logs Integration Test")
    print("=" * 60)
    
    # Test 1: Database connections
    await test_database_connections()
    
    # Test 2: Groups with logs simulation
    test_groups_with_logs_simulation()
    
    # Test 3: API simulation
    await test_logs_api_simulation()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("\nNext steps:")
    print("1. If connections work, the logs router should work when properly imported")
    print("2. Check Python module path resolution for logs router import")
    print("3. Consider adding logs router endpoint to main.py without import issues")

if __name__ == "__main__":
    asyncio.run(main())