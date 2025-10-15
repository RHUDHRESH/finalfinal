"""
Database Setup Script
Run this ONCE to initialize the database and add sample data.

Usage:
    python setup_db.py
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from karigar.memory.sql_memory import init_db, seed_sample_data

def main():
    """
    Main setup function
    """
    print("\n" + "="*60)
    print("🗄️  KarigarAgent Database Setup")
    print("="*60 + "\n")
    
    try:
        # Step 1: Create all tables
        print("Step 1: Creating database tables...")
        init_db()
        print("✅ Database tables created successfully!\n")
        
        # Step 2: Insert sample data
        print("Step 2: Inserting sample data...")
        seed_sample_data()
        print("✅ Sample data inserted successfully!\n")
        
        print("="*60)
        print("✨ Database setup complete!")
        print("="*60)
        print("\nYou can now start the backend server with:")
        print("  uvicorn src.karigar.main:app --reload")
        print("\nOr run:")
        print("  python -m uvicorn src.karigar.main:app --reload\n")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        print("\nPlease check:")
        print("  1. You're running this from the karigar-agent directory")
        print("  2. You have activated your virtual environment")
        print("  3. You have installed all requirements: pip install -r requirements.txt\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
