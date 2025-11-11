"""
Database Configuration and Session Management
File: backend/config/database.py
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create logger
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Maximum overflow connections
    echo=False,          # Set True to see SQL queries
    connect_args={
        "options": "-c timezone=utc"  # Set timezone to UTC
    }
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for models
Base = declarative_base()

# Event listener for connection
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Event listener for new database connections"""
    logger.info("New database connection established")

# Event listener for connection checkout
@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Event listener for connection checkout from pool"""
    logger.debug("Connection checked out from pool")


def get_db():
    """
    Dependency function for FastAPI endpoints.
    Yields a database session and ensures it's closed after use.
    
    Usage in FastAPI:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed")


@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    Automatically handles commit/rollback and cleanup.
    
    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
            user.name = "Updated Name"
            # Commits automatically on success
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
        logger.debug("Database transaction committed")
    except Exception as e:
        db.rollback()
        logger.error(f"Database transaction rolled back: {str(e)}")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


def init_db():
    """
    Initialize database - create all tables.
    Call this function to create tables if they don't exist.
    
    Usage:
        from backend.config.database import init_db
        init_db()
    """
    from backend.models.database import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_db_connection():
    """
    Check if database connection is working.
    Returns True if connection successful, False otherwise.
    """
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False