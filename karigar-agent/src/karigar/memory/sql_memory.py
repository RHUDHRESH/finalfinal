"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from karigar.schemas.models import Base
import os

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./karigar.db")

# Create engine
# check_same_thread=False is needed for SQLite to work with FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=True  # Set to False in production to reduce logs
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database - create all tables.
    Run this once at startup.
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def get_session():
    """
    Get a database session.
    Use this in your code to interact with database.
    
    Usage:
        session = get_session()
        try:
            # Do database operations
            artisan = session.query(Artisan).filter_by(phone="1234567890").first()
        finally:
            session.close()
    """
    return SessionLocal()


def seed_sample_data():
    """
    Insert sample data for testing.
    Run this after init_db() for the first time.
    """
    from karigar.schemas.models import Artisan, Supplier
    
    session = get_session()
    
    try:
        # Check if data already exists
        if session.query(Artisan).count() > 0:
            print("Sample data already exists, skipping...")
            return
        
        # Create sample artisan
        artisan = Artisan(
            name="Ravi Kumar",
            phone="9876543210",
            email="ravi@example.com",
            location="Nehru Nagar, Delhi",
            city="Delhi",
            state="Delhi"
        )
        session.add(artisan)
        
        # Create sample suppliers
        suppliers = [
            Supplier(
                name="BuildMart Delhi",
                phone="9123456780",
                address="Sector 15, Noida",
                city="Noida",
                state="Uttar Pradesh",
                latitude=28.5355,
                longitude=77.3910,
                materials=["cement", "sand", "steel"],
                rating=4.5,
                total_reviews=120,
                delivery_radius_km=30
            ),
            Supplier(
                name="Quick Supply Co",
                phone="9123456781",
                address="Rohini, Delhi",
                city="Delhi",
                state="Delhi",
                latitude=28.7041,
                longitude=77.1025,
                materials=["bricks", "cement", "tiles"],
                rating=4.2,
                total_reviews=85,
                delivery_radius_km=50
            ),
            Supplier(
                name="Metro Builders Supply",
                phone="9123456782",
                address="Dwarka, Delhi",
                city="Delhi",
                state="Delhi",
                latitude=28.5921,
                longitude=77.0460,
                materials=["cement", "steel", "paint"],
                rating=4.7,
                total_reviews=200,
                delivery_radius_km=40
            )
        ]
        
        for supplier in suppliers:
            session.add(supplier)
        
        # Commit to database
        session.commit()
        print("Sample data inserted successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding data: {e}")
    finally:
        session.close()
