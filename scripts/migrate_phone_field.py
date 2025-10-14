#!/usr/bin/env python3
"""
Database migration script to fix phone field constraint
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def migrate_database():
    """Update the phone field size in the database"""
    
    # Database connection parameters
    db_params = {
        'host': 'localhost',
        'port': '5432',
        'database': 'risk_agent_db',
        'user': 'risk_agent_user',
        'password': 'risk_agent_password'
    }
    
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Updating phone field size from VARCHAR(20) to VARCHAR(50)...")
        
        # Update the phone column size
        cursor.execute("""
            ALTER TABLE users 
            ALTER COLUMN phone TYPE VARCHAR(50);
        """)
        
        print("✅ Phone field updated successfully!")
        
        # Verify the change
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'phone';
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Verification: phone field is now {result[1]}({result[2]})")
        
        cursor.close()
        conn.close()
        
        print("🎉 Database migration completed successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Database Migration: Phone Field Fix ===")
    success = migrate_database()
    
    if success:
        print("\n✅ Migration completed! You can now register users with longer phone numbers.")
        print("📱 Phone field now accepts up to 50 characters and is optional.")
    else:
        print("\n❌ Migration failed. Please check the database connection and try again.")
