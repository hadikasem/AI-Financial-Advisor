#!/usr/bin/env python3
"""
Migration script to add account_id column to goals table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Goal
from sqlalchemy import text

def migrate():
    """Add account_id column to goals table"""
    with app.app_context():
        try:
            # Add the account_id column
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE goals 
                    ADD COLUMN account_id VARCHAR(36) 
                    REFERENCES accounts(id)
                """))
                conn.commit()
            print("Successfully added account_id column to goals table")
            
            # Update existing goals to have NULL account_id (they will be created when needed)
            print("Migration completed successfully")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    migrate()
