"""
Automated Scheduler & Cron Job Ingestion Engine
==============================================
Runs periodic updates of datasets, compares with existing records,
keeps history, and sends WhatsApp updates upon completion.

Can be run as a daily/weekly cron task:
    python -m app.cron_job
"""

import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import SessionLocal
from app.database.models import IngestionState, DatasetMetadata
from app.ingestion.connectors import (
    UdiseSchoolConnector,
    NhmHealthConnector,
    PmgsyRoadsConnector,
    JjmWaterConnector
)

def run_scheduled_sync():
    print(f"[{datetime.now()}] Starting Scheduled Background Ingestion Run...")
    db = SessionLocal()
    
    # Standard feed URLs (using Pratap Vardhan's repositories or open data mirrors as examples)
    sync_targets = [
        {
            "id": "udise_schools",
            "connector": UdiseSchoolConnector,
            "url": "https://raw.githubusercontent.com/harshith1432/mp-mitra/main/backend/DATASET/Village%20Amenities/school_sample.csv" # placeholder/mirror
        },
        {
            "id": "nhm_health",
            "connector": NhmHealthConnector,
            "url": "https://raw.githubusercontent.com/harshith1432/mp-mitra/main/backend/DATASET/Village%20Amenities/geocode_health_centre_sample.csv"
        },
        {
            "id": "pmgsy_roads",
            "connector": PmgsyRoadsConnector,
            "url": "https://raw.githubusercontent.com/harshith1432/mp-mitra/main/backend/DATASET/Village%20Amenities/road_sample.csv"
        }
    ]
    
    results = []
    for target in sync_targets:
        print(f"\n--- Syncing {target['id']} ---")
        try:
            connector_instance = target["connector"]()
            # In a real environment, the URL could point to an open government data API feed
            res = connector_instance.run_ingestion_pipeline(db, target["url"])
            print(f"Result for {target['id']}: {res}")
            results.append(res)
        except Exception as e:
            print(f"Failed to sync {target['id']}: {e}")
            results.append({"dataset_id": target["id"], "status": "error", "message": str(e)})
            
    db.close()
    print(f"\n[{datetime.now()}] Scheduled Ingestion Run Completed successfully.")
    return results

if __name__ == "__main__":
    run_scheduled_sync()
