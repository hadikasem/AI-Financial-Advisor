#!/usr/bin/env python3
"""
Migration script to add last_mock_date column to users table (PostgreSQL)
"""

import os
import sys
import psycopg2
from datetime import datetime

def migrate_database():
    """Add last_mock_date column to users table"""
    
    # Database connection parameters
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://risk_agent_user:risk_agent_password@localhost/risk_agent_db')
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='last_mock_date'
        """)
        
        if cursor.fetchone():
            print("Column 'last_mock_date' already exists in users table")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN last_mock_date DATE
            """)
            print("Successfully added 'last_mock_date' column to users table")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_database()
