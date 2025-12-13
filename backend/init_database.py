#!/usr/bin/env python3
"""
Database initialization script for OpenWebUI
This ensures the database is properly configured and accessible.
"""

import os
import sqlite3
from pathlib import Path

def init_database():
    """Initialize the database with proper permissions and basic structure"""
    
    # Get the backend directory
    backend_dir = Path(__file__).parent.resolve()
    data_dir = backend_dir / "data"
    db_path = data_dir / "webui.db"
    
    print(f"Backend directory: {backend_dir}")
    print(f"Data directory: {data_dir}")
    print(f"Database path: {db_path}")
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Data directory created/verified: {data_dir}")
    
    # Test database connectivity
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Test basic operations
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            print(f"✓ Database connected successfully. Found {len(tables)} tables.")
            print(f"  Tables: {[t[0] for t in tables]}")
        else:
            print("✓ Database connected, but no tables found (this might be normal for first run)")
        
        # Set proper permissions
        conn.close()
        os.chmod(str(db_path), 0o666)
        print(f"✓ Database permissions set to 666")
        
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def set_environment():
    """Set proper environment variables for database access"""
    backend_dir = Path(__file__).parent.resolve()
    
    env_vars = {
        'DATA_DIR': str(backend_dir / "data"),
        'DATABASE_URL': f"sqlite:///{backend_dir}/data/webui.db",
        'WEBUI_SECRET_KEY': 'fixxit-development-secret-key'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✓ {key}={value}")

if __name__ == "__main__":
    print("OpenWebUI Database Initialization")
    print("=" * 40)
    
    set_environment()
    print()
    
    if init_database():
        print("\n✅ Database initialization completed successfully!")
        exit(0)
    else:
        print("\n❌ Database initialization failed!")
        exit(1)