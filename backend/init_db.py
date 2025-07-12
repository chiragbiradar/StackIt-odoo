"""
Initialize the database with tables and sample data.
"""
from database.database import engine
from database.models.base import Base

def init_database():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()
