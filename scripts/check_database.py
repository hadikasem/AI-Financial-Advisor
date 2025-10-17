#!/usr/bin/env python3
"""
Script to verify database schema and test the mock progress functionality
"""

import os
import sys
import sqlite3

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def check_database_schema():
    """Check if the database schema is correct"""
    
    # SQLite database path
    db_path = os.path.join(os.path.dirname(__file__), 'backend', 'instance', 'risk_agent.db')
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check users table schema
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("Users table schema:")
        for column in columns:
            print(f"  {column[1]} {column[2]} {'NOT NULL' if column[3] else 'NULL'} {'DEFAULT ' + str(column[4]) if column[4] else ''}")
        
        # Check if last_mock_date exists
        column_names = [column[1] for column in columns]
        if 'last_mock_date' in column_names:
            print("\n✅ last_mock_date column exists")
        else:
            print("\n❌ last_mock_date column missing")
        
        # Check if there are any users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\nTotal users in database: {user_count}")
        
        if user_count > 0:
            # Show sample user data
            cursor.execute("SELECT id, email, full_name, last_mock_date FROM users LIMIT 1")
            user = cursor.fetchone()
            print(f"Sample user: {user}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database check failed: {e}")
        return False

if __name__ == "__main__":
    check_database_schema()
