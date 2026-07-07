"""
Base Data Ingestion Connector
=============================
Defines the standard interface for external government dataset connectors.
Connectors pull from national portals (UDISE+, PMGSY, NHM, JJM, LGD, ECI)
and normalize them into MP Mitra's database tables.
"""

from abc import ABC, abstractmethod
import urllib.request
import csv
import io
import os
from sqlalchemy.orm import Session
from datetime import datetime

class BaseConnector(ABC):
    def __init__(self, dataset_id: str, name: str, source: str, table_name: str):
        self.dataset_id = dataset_id
        self.name = name
        self.source = source
        self.table_name = table_name

    @abstractmethod
    def fetch_data(self, url: str) -> list:
        """Downloads/fetches raw rows from source URL."""
        pass

    @abstractmethod
    def normalize_row(self, row: dict) -> dict:
        """Transforms source column keys to standardize schema keys."""
        pass

    @abstractmethod
    def save_batch(self, db: Session, batch: list) -> int:
        """Performs bulk save/upsert logic on standard tables."""
        pass

    def run_ingestion_pipeline(self, db: Session, url: str) -> dict:
        """Runs full download-normalize-load pipeline, logging metadata."""
        start_time = datetime.now()
        print(f"[Ingestion Pipeline] Launching connector '{self.name}' from source: {url}")
        
        try:
            # 1. Fetch
            raw_rows = self.fetch_data(url)
            print(f"[Ingestion Pipeline] Fetched {len(raw_rows)} raw records.")
            
            if not raw_rows:
                return {
                    "status": "warning",
                    "message": "No records fetched or file was empty.",
                    "records_processed": 0
                }
                
            # 2. Normalize & Batch
            normalized_batch = []
            missing_count = 0
            for r in raw_rows:
                norm = self.normalize_row(r)
                if norm:
                    normalized_batch.append(norm)
                    # Simple check for missing/null values
                    missing_count += sum(1 for v in norm.values() if v is None or v == "")
            
            # 3. Save
            saved_count = self.save_batch(db, normalized_batch)
            print(f"[Ingestion Pipeline] Saved {saved_count} records to DB table '{self.table_name}'.")
            
            # 4. Trigger Quality Score & Audit
            from app.database.quality_checker import run_quality_audit
            audit_res = run_quality_audit(db, self.table_name)
            
            # Update ingestion state
            from app.database.models import IngestionState
            state = db.query(IngestionState).filter_by(key=f"last_ingested_{self.dataset_id}").first()
            if not state:
                state = IngestionState(key=f"last_ingested_{self.dataset_id}", value=datetime.now().isoformat())
                db.add(state)
            else:
                state.value = datetime.now().isoformat()
            db.commit()
            
            return {
                "status": "success",
                "dataset_id": self.dataset_id,
                "dataset_name": self.name,
                "records_processed": len(raw_rows),
                "records_saved": saved_count,
                "missing_values": missing_count,
                "quality_score": audit_res.get("quality_score", 100.0),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            import traceback
            err_msg = f"Failed ingestion for {self.name}: {e}\n{traceback.format_exc()}"
            print(f"[Ingestion Pipeline Error] {err_msg}")
            return {
                "status": "error",
                "message": str(e)
            }
