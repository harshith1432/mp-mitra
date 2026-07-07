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

# Automatic Bootstrap Loader for local SQLite fallback
if DATABASE_URL.startswith("sqlite"):
    db_file = "mpmitra_fallback.db"
    if not os.path.exists(db_file) or os.path.getsize(db_file) < 1000000:
        import urllib.request
        import zipfile
        print("[Startup Bootstrap] All-India SQLite database file is missing or empty.")
        print("[Startup Bootstrap] Downloading pre-populated all-India database zip...")
        url = "https://github.com/harshith1432/mp-mitra/releases/download/datasets-v1/mpmitra_fallback.zip"
        zip_path = "mpmitra_fallback.zip"
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
                out_file.write(response.read())
            print("[Startup Bootstrap] Download completed. Extracting database...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove(zip_path)
            print("[Startup Bootstrap] Database extracted and initialized successfully!")
        except Exception as e:
            print(f"[Startup Bootstrap Error] Failed to auto-download database: {e}")

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
