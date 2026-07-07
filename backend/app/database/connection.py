import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config_manager import config_manager

# Load environment variables from .env for local development fallback
load_dotenv()

# First attempt to read from config_manager, then fallback to environment
DATABASE_URL = config_manager.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[Database Connection] WARNING: DATABASE_URL not set. Falling back to local SQLite.")
    DATABASE_URL = "sqlite:///./mpmitra_fallback.db"

# Create the engine with a robust connection test and fallback
try:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            DATABASE_URL, 
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
            pool_pre_ping=True
        )
    # Test the connection immediately
    with engine.connect() as conn:
        print("[Database Connection] Successfully verified database connection.")
except Exception as e:
    print(f"[Database Connection Error] Failed to connect to {DATABASE_URL}: {e}")
    print("[Database Connection Fallback] Falling back to local SQLite database: ./mpmitra_fallback.db")
    DATABASE_URL = "sqlite:///./mpmitra_fallback.db"
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
