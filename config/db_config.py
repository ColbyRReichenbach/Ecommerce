from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database Credentials
DB_CONFIG = {
    "user": "colbyreichenbach",
    "password": "817!30Cr20!?",
    "host": "localhost",
    "port": "5432",
    "database": "ecommerce"
}

# Construct the database URL
DB_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Create SQLAlchemy Engine
engine = create_engine(DB_URL, echo=True)  # Set echo=False to disable SQL logging

# Create a configured session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Returns a new SQLAlchemy session."""
    return SessionLocal()
