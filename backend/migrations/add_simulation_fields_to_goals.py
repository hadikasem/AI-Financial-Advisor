#!/usr/bin/env python3
"""
Migration script to add last_simulation_date and completed_at columns to goals table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Goal
from sqlalchemy import text

def migrate():
    """Add last_simulation_date and completed_at columns to goals table"""
    with app.app_context():
        try:
            # Add the columns
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE goals 
                    ADD COLUMN last_simulation_date DATE
                """))
                conn.execute(text("""
                    ALTER TABLE goals 
                    ADD COLUMN completed_at TIMESTAMP
                """))
                conn.commit()
            print("Successfully added last_simulation_date and completed_at columns to goals table")
            print("Migration completed successfully")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    migrate()
