# Import SQLAlchemy components
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings


# Build the database URL
DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.POSTGRES_DB}"

# Create database engine using connection URL from settings
engine = create_engine(DATABASE_URL)

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
        db.commit()  # Auto-commit after request
    except Exception:
        db.rollback()  # Rollback on error
        raise
    finally:
        db.close()
