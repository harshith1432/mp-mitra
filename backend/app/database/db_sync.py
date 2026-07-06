import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.connection import Base
from app.database.models import (
    Pincode, School, Road, HealthCentre, Habitation, WaterQuality,
    VillageAmenities, CrawledScheme, CrawledNews, CrawledTender,
    CrawlerLog, VisitedUrl, IngestionState
)

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REMOTE_DATABASE_URL = os.getenv("REMOTE_DATABASE_URL")

def get_session(url, name="Database"):
    if not url:
        print(f"Error: {name} URL is not set.")
        return None
    try:
        if url.startswith("sqlite"):
            engine = create_engine(url, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(url, pool_pre_ping=True)
        
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return Session()
    except Exception as e:
        print(f"Error connecting to {name}: {e}")
        return None

def sync_table(local_db, remote_db, model_class, pk_attr="id", batch_size=1000):
    table_name = model_class.__tablename__
    print(f"\nSyncing table '{table_name}'...")
    
    # 1. Fetch PKs from both databases
    local_pks = set(x[0] for x in local_db.query(getattr(model_class, pk_attr)).all())
    remote_pks = set(x[0] for x in remote_db.query(getattr(model_class, pk_attr)).all())
    
    # 2. Identify missing records
    to_remote_pks = local_pks - remote_pks
    to_local_pks = remote_pks - local_pks
    
    print(f"  Local records: {len(local_pks)} | Remote records: {len(remote_pks)}")
    print(f"  -> Uploading to remote: {len(to_remote_pks)} records")
    print(f"  -> Downloading to local: {len(to_local_pks)} records")
    
    # 3. Upload to Remote
    if to_remote_pks:
        pks_list = list(to_remote_pks)
        for i in range(0, len(pks_list), batch_size):
            batch_pks = pks_list[i:i+batch_size]
            records = local_db.query(model_class).filter(getattr(model_class, pk_attr).in_(batch_pks)).all()
            
            # Recreate objects for remote session
            new_objects = []
            for record in records:
                # Extract values into dict
                data = {col.name: getattr(record, col.name) for col in model_class.__table__.columns}
                new_objects.append(model_class(**data))
                
            remote_db.bulk_save_objects(new_objects)
            remote_db.commit()
            print(f"    Uploaded batch {i // batch_size + 1}: {len(new_objects)} records.")
            
    # 4. Download to Local
    if to_local_pks:
        pks_list = list(to_local_pks)
        for i in range(0, len(pks_list), batch_size):
            batch_pks = pks_list[i:i+batch_size]
            records = remote_db.query(model_class).filter(getattr(model_class, pk_attr).in_(batch_pks)).all()
            
            new_objects = []
            for record in records:
                data = {col.name: getattr(record, col.name) for col in model_class.__table__.columns}
                new_objects.append(model_class(**data))
                
            local_db.bulk_save_objects(new_objects)
            local_db.commit()
            print(f"    Downloaded batch {i // batch_size + 1}: {len(new_objects)} records.")

def main():
    if not REMOTE_DATABASE_URL:
        print("REMOTE_DATABASE_URL environment variable is not defined.")
        print("Please configure REMOTE_DATABASE_URL in backend/.env to connect to your Firebase/Neon cloud database.")
        sys.exit(1)
        
    print(f"Local Database:  {DATABASE_URL}")
    print(f"Remote Database: {REMOTE_DATABASE_URL}")
    
    local_db = get_session(DATABASE_URL, "Local Database")
    remote_db = get_session(REMOTE_DATABASE_URL, "Remote Database")
    
    if not local_db or not remote_db:
        print("Database connection failed. Exiting.")
        sys.exit(1)
        
    try:
        # Sync relational models
        # Static geographical data
        sync_table(local_db, remote_db, Pincode, pk_attr="id")
        sync_table(local_db, remote_db, School, pk_attr="udise_school_code")
        sync_table(local_db, remote_db, Road, pk_attr="id")
        sync_table(local_db, remote_db, HealthCentre, pk_attr="id")
        sync_table(local_db, remote_db, Habitation, pk_attr="id")
        sync_table(local_db, remote_db, WaterQuality, pk_attr="id")
        sync_table(local_db, remote_db, VillageAmenities, pk_attr="id")
        
        # Dynamic web scraper data
        sync_table(local_db, remote_db, CrawledScheme, pk_attr="id")
        sync_table(local_db, remote_db, CrawledNews, pk_attr="id")
        sync_table(local_db, remote_db, CrawledTender, pk_attr="id")
        sync_table(local_db, remote_db, VisitedUrl, pk_attr="url")
        sync_table(local_db, remote_db, CrawlerLog, pk_attr="id")
        sync_table(local_db, remote_db, IngestionState, pk_attr="key")
        
        print("\nDatabase synchronization completed successfully!")
        
    except Exception as e:
        print(f"Error during synchronization: {e}")
    finally:
        if local_db:
            local_db.close()
        if remote_db:
            remote_db.close()

if __name__ == "__main__":
    main()
