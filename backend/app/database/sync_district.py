import os
import sys
import argparse
from dotenv import load_dotenv
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add project root and backend to path
sys.path.append(r"d:\projects softwares\hackthon pm")
sys.path.append(r"d:\projects softwares\hackthon pm\backend")

from backend.app.database.connection import Base
from backend.app.database.models import (
    Pincode, School, Road, HealthCentre, Habitation, WaterQuality,
    VillageAmenities
)

# Load environment variables
load_dotenv(dotenv_path=r"d:\projects softwares\hackthon pm\backend\.env")

LOCAL_DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///d:\\projects softwares\\hackthon pm\\backend\\mpmitra_fallback.db"
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
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return Session()
    except Exception as e:
        print(f"Error connecting to {name}: {e}")
        return None

def sync_table_for_district(local_db, remote_db, model_class, state, district, pk_attr="id"):
    table_name = model_class.__tablename__
    state_upper = state.strip().upper()
    district_upper = district.strip().upper()
    
    print(f"\nSyncing table '{table_name}' for {district_upper}, {state_upper}...")
    
    # Query records locally matching state and district
    local_query = local_db.query(model_class)
    
    # Filter dynamically based on available columns
    if hasattr(model_class, 'state_name') and hasattr(model_class, 'district_name'):
        local_records = local_query.filter(
            func.upper(model_class.state_name) == state_upper,
            func.upper(model_class.district_name) == district_upper
        ).all()
    elif hasattr(model_class, 'statename') and hasattr(model_class, 'district'):
        local_records = local_query.filter(
            func.upper(model_class.statename) == state_upper,
            func.upper(model_class.district) == district_upper
        ).all()
    elif hasattr(model_class, 'state_name') and hasattr(model_class, 'district'):
        local_records = local_query.filter(
            func.upper(model_class.state_name) == state_upper,
            func.upper(model_class.district) == district_upper
        ).all()
    elif hasattr(model_class, 'district_name'):
        local_records = local_query.filter(
            func.upper(model_class.district_name) == district_upper
        ).all()
    elif hasattr(model_class, 'district'):
        local_records = local_query.filter(
            func.upper(model_class.district) == district_upper
        ).all()
    else:
        print(f"  Skipping '{table_name}': Table schema has no state/district columns to filter.")
        return

    print(f"  Found {len(local_records)} local records.")
    if not local_records:
        return

    # Fetch existing PKs in remote database to avoid duplicates (coerced to string for safe comparison)
    try:
        remote_pks = set(str(x[0]) for x in remote_db.query(getattr(model_class, pk_attr)).all())
    except Exception as e:
        print(f"  Could not read remote PKs for {table_name}: {e}. Initializing with empty set.")
        remote_pks = set()
    
    to_upload = []
    for record in local_records:
        pk_val = str(getattr(record, pk_attr))
        if pk_val not in remote_pks:
            to_upload.append(record)
            
    print(f"  -> Uploading {len(to_upload)} new records to remote database...")
    
    if to_upload:
        uploaded_count = 0
        for idx, record in enumerate(to_upload):
            try:
                # Re-bind object values to new instance for remote DB
                data = {col.name: getattr(record, col.name) for col in model_class.__table__.columns}
                remote_db.add(model_class(**data))
                uploaded_count += 1
                
                # Commit in batches
                if uploaded_count % 100 == 0:
                    remote_db.commit()
            except Exception as e:
                remote_db.rollback()
                print(f"    Failed to upload record {idx} (PK: {getattr(record, pk_attr)}): {e}")
        
        # Final commit
        try:
            remote_db.commit()
        except Exception as e:
            remote_db.rollback()
            print(f"    Final commit failed: {e}")
            
        print(f"  Uploaded {uploaded_count} records successfully.")
            
    print(f"  Sync for '{table_name}' complete.")

def main():
    parser = argparse.ArgumentParser(description="Synchronize a specific district dataset to Neon PostgreSQL.")
    parser.add_argument("state", help="Name of the Indian State (e.g. KARNATAKA)")
    parser.add_argument("district", help="Name of the District (e.g. MANDYA)")
    args = parser.parse_args()

    print(f"--- MP MITRA District Sync: {args.district.upper()}, {args.state.upper()} ---")
    print(f"Local Database:  {LOCAL_DATABASE_URL}")
    print(f"Remote Database: {REMOTE_DATABASE_URL}")

    local_db = get_session(LOCAL_DATABASE_URL, "Local Database")
    remote_db = get_session(REMOTE_DATABASE_URL, "Remote Database")

    if not local_db or not remote_db:
        print("Failed to initialize database sessions.")
        return

    try:
        # Sync tables sequentially
        sync_table_for_district(local_db, remote_db, Pincode, args.state, args.district, pk_attr="pincode")
        sync_table_for_district(local_db, remote_db, School, args.state, args.district, pk_attr="udise_school_code")
        sync_table_for_district(local_db, remote_db, Road, args.state, args.district, pk_attr="id")
        sync_table_for_district(local_db, remote_db, HealthCentre, args.state, args.district, pk_attr="id")
        sync_table_for_district(local_db, remote_db, Habitation, args.state, args.district, pk_attr="id")
        sync_table_for_district(local_db, remote_db, WaterQuality, args.state, args.district, pk_attr="id")
        sync_table_for_district(local_db, remote_db, VillageAmenities, args.state, args.district, pk_attr="id")
        
        print("\nSynchronization completed successfully!")
    finally:
        local_db.close()
        remote_db.close()

if __name__ == "__main__":
    main()
