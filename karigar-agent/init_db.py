"""
Run this file ONCE to set up the database.
Command: python init_db.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.karigar.memory.sql_memory import init_db, seed_sample_data

if __name__ == "__main__":
    print("Setting up database...")
    init_db()
    seed_sample_data()
    print("Database setup complete!")
