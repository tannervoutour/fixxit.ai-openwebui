#!/usr/bin/env python3
"""
Check Management Dashboard Configuration

This script checks the database to diagnose why the Management Dashboard button
might not be showing for managers.
"""

import sqlite3
import json
import sys
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "backend" / "data" / "webui.db"

def check_managers():
    """Check all users with manager role and their managed_groups"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("CHECKING MANAGER USERS")
    print("=" * 80)

    cursor.execute("""
        SELECT id, email, name, role, managed_groups
        FROM user
        WHERE role = 'manager'
    """)

    managers = cursor.fetchall()

    if not managers:
        print("\n⚠️  No users with role='manager' found!")
        print("   Make sure you have created manager users.\n")
        return []

    manager_group_map = {}

    for user_id, email, name, role, managed_groups_json in managers:
        print(f"\n✓ Manager Found: {name} ({email})")
        print(f"  User ID: {user_id}")
        print(f"  Role: {role}")

        if not managed_groups_json:
            print("  ⚠️  managed_groups: NULL or empty")
            print("     → Button will NOT show (no groups assigned)")
            continue

        try:
            managed_groups = json.loads(managed_groups_json)
            if not managed_groups or len(managed_groups) == 0:
                print(f"  ⚠️  managed_groups: [] (empty array)")
                print("     → Button will NOT show (no groups assigned)")
            else:
                print(f"  ✓ managed_groups: {managed_groups}")
                manager_group_map[user_id] = {
                    'email': email,
                    'name': name,
                    'groups': managed_groups
                }
        except json.JSONDecodeError:
            print(f"  ⚠️  managed_groups: Invalid JSON: {managed_groups_json}")
            print("     → Button will NOT show (invalid data)")

    conn.close()
    return manager_group_map

def check_groups(manager_group_map):
    """Check if groups have management_dashboard_url configured"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("CHECKING GROUP CONFIGURATIONS")
    print("=" * 80)

    for manager_id, manager_info in manager_group_map.items():
        print(f"\n\nManager: {manager_info['name']} ({manager_info['email']})")
        print("-" * 80)

        has_dashboard_groups = False

        for group_id in manager_info['groups']:
            cursor.execute("""
                SELECT id, name, data
                FROM "group"
                WHERE id = ?
            """, (group_id,))

            result = cursor.fetchone()

            if not result:
                print(f"\n  ⚠️  Group ID: {group_id}")
                print("     ERROR: Group not found in database!")
                continue

            db_id, name, data_json = result
            print(f"\n  Group: {name}")
            print(f"  ID: {db_id}")

            if not data_json:
                print("  ⚠️  data: NULL")
                print("     → No dashboard URL configured")
                print("     → Button will NOT show for this group")
                continue

            try:
                data = json.loads(data_json)
                dashboard_url = data.get('management_dashboard_url')

                if dashboard_url:
                    print(f"  ✓ Dashboard URL: {dashboard_url}")
                    print("     → Button WILL show for this group")
                    has_dashboard_groups = True
                else:
                    print("  ⚠️  management_dashboard_url: Not set")
                    print("     → Button will NOT show for this group")

                    # Show what other data exists
                    if data:
                        print(f"     Other data fields: {list(data.keys())}")
            except json.JSONDecodeError:
                print(f"  ⚠️  data: Invalid JSON: {data_json}")
                print("     → Button will NOT show for this group")

        print(f"\n  {'✓' if has_dashboard_groups else '⚠️'}  Overall: ", end='')
        if has_dashboard_groups:
            print(f"Button WILL show for {manager_info['name']}")
        else:
            print(f"Button will NOT show for {manager_info['name']}")
            print("     → None of their managed groups have dashboard URL configured")

    conn.close()

def show_fix_instructions():
    """Show how to fix common issues"""
    print("\n" + "=" * 80)
    print("HOW TO FIX")
    print("=" * 80)

    print("""
If the button is not showing, here's how to fix it:

1. ASSIGN GROUPS TO MANAGER:
   - Via UI: Admin Panel → Users → Edit User → Managed Groups
   - Via Database:
     UPDATE user
     SET managed_groups = '["group-id-1", "group-id-2"]'
     WHERE email = 'manager@example.com';

2. CONFIGURE DASHBOARD URL FOR GROUP:
   - Via UI: Admin Panel → Groups → Edit Group → Management Dashboard tab
   - Enter URL like: https://cooperativekny.fixxit.ai
   - Click Save

3. VERIFY IN BROWSER:
   - Open browser console (F12)
   - Look for logs starting with "[Management Dashboard]"
   - Run: JSON.parse(localStorage.getItem('user'))
   - Check that role='manager' and managed_groups=[...]

4. CLEAR CACHE:
   - Hard reload browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
   - Or clear localStorage: localStorage.clear(); location.reload();
""")

def main():
    print("\nManagement Dashboard Configuration Checker")
    print("Database:", DB_PATH)

    if not DB_PATH.exists():
        print(f"\n❌ ERROR: Database not found at {DB_PATH}")
        print("   Make sure you're running this from the project root directory.")
        sys.exit(1)

    # Check managers
    manager_group_map = check_managers()

    if not manager_group_map:
        print("\n⚠️  No managers with managed groups found.")
        show_fix_instructions()
        return

    # Check groups
    check_groups(manager_group_map)

    # Show fix instructions
    show_fix_instructions()

if __name__ == "__main__":
    main()
