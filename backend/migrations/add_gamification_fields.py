import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Add gamification columns to users table
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN current_streak INTEGER DEFAULT 0
                """))
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN last_activity_date DATE
                """))
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN total_points INTEGER DEFAULT 0
                """))
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN level VARCHAR(20) DEFAULT 'Bronze'
                """))
                conn.commit()
            print("Successfully added gamification columns to users table")
            print("Migration completed successfully")
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    return True

if __name__ == "__main__":
    migrate()
