#!/usr/bin/env python3
import os
import sys
import sqlite3
from pathlib import Path

def initialize_database():
    """Initialize the database with proper permissions and path setup"""
    
    # Set the working directory to backend
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Ensure data directory exists
    data_dir = backend_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Database file path
    db_file = data_dir / "webui.db"
    
    # Set the DATABASE_URL environment variable
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
    
    print(f"Data directory: {data_dir}")
    print(f"Database file: {db_file}")
    print(f"DATABASE_URL: {os.environ['DATABASE_URL']}")
    
    # Create an empty database file if it doesn't exist
    if not db_file.exists():
        print("Creating new database file...")
        # Create empty database
        conn = sqlite3.connect(str(db_file))
        conn.close()
        print(f"Database file created: {db_file}")
    
    # Test database connection
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        print("Database connection test successful!")
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    success = initialize_database()
    sys.exit(0 if success else 1)