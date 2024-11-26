# Import SQLAlchemy components
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Create database engine using connection URL from settings
engine = create_engine(settings.DATABASE_URL)

# Create session factory with specified configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Dependency function to manage database sessions
def get_db():
    # Create new database session
    db = SessionLocal()
    try:
        # Yield session to caller
        yield db
    finally:
        # Ensure session is closed after use
        db.close() 