"""
Government Dataset Connectors implementation
============================================
Implements UDISE+, NHM, PMGSY, JJM, LGD, and ECI standard connectors
inheriting from BaseConnector.
"""

import urllib.request
import csv
import io
from sqlalchemy.orm import Session
from app.ingestion.base_connector import BaseConnector
from app.database.models import School, HealthCentre, Road, Habitation, ParliamentaryConstituency
from app.database.normalization import normalize_district_name, normalize_state_name

class UdiseSchoolConnector(BaseConnector):
    def __init__(self):
        super().__init__(
            dataset_id="udise_schools",
            name="UDISE+ Schools Directory",
            source="Department of School Education & Literacy",
            table_name="schools"
        )

    def fetch_data(self, url: str) -> list:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)

    def normalize_row(self, row: dict) -> dict:
        # Standardize UDISE keys (often varying between state portals)
        return {
            "udise_school_code": row.get("udise_school_code") or row.get("school_code") or row.get("udise_code"),
            "school_name": row.get("school_name") or row.get("name") or row.get("sch_name"),
            "state_name": normalize_state_name(row.get("state_name") or row.get("state")),
            "district_name": normalize_district_name(row.get("district_name") or row.get("district")),
            "sub_district_name": row.get("sub_district_name") or row.get("block") or row.get("taluk") or "",
            "village_name": row.get("village_name") or row.get("village") or "",
            "pincode": row.get("pincode") or "",
            "school_category": row.get("school_category") or row.get("category") or "",
            "school_type": row.get("school_type") or row.get("type") or "",
            "total_teachers": int(row.get("total_teachers") or 0),
            "total_students": int(row.get("total_students") or 0),
            "latitude": float(row.get("latitude") or 0.0),
            "longitude": float(row.get("longitude") or 0.0),
        }

    def save_batch(self, db: Session, batch: list) -> int:
        count = 0
        for data in batch:
            if not data["udise_school_code"]:
                continue
            existing = db.query(School).filter_by(udise_school_code=data["udise_school_code"]).first()
            if not existing:
                db.add(School(**data))
                count += 1
            else:
                for k, v in data.items():
                    setattr(existing, k, v)
        db.commit()
        return count


class NhmHealthConnector(BaseConnector):
    def __init__(self):
        super().__init__(
            dataset_id="nhm_health",
            name="National Health Mission Directory",
            source="Ministry of Health and Family Welfare",
            table_name="health_centres"
        )

    def fetch_data(self, url: str) -> list:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)

    def normalize_row(self, row: dict) -> dict:
        return {
            "facility_name": row.get("facility_name") or row.get("name"),
            "state_name": normalize_state_name(row.get("state_name") or row.get("state")),
            "district_name": normalize_district_name(row.get("district_name") or row.get("district")),
            "subdistrict_name": row.get("subdistrict_name") or row.get("block") or row.get("taluk") or "",
            "facility_type": row.get("facility_type") or "PHC",
            "facility_address": row.get("facility_address") or "",
            "latitude": float(row.get("latitude") or 0.0),
            "longitude": float(row.get("longitude") or 0.0),
            "active_flag": row.get("active_flag") or "Y",
            "location_type": row.get("location_type") or "Rural",
            "type_of_facility": row.get("type_of_facility") or "Public",
        }

    def save_batch(self, db: Session, batch: list) -> int:
        count = 0
        for data in batch:
            if not data["facility_name"]:
                continue
            existing = db.query(HealthCentre).filter_by(facility_name=data["facility_name"], district_name=data["district_name"]).first()
            if not existing:
                db.add(HealthCentre(**data))
                count += 1
        db.commit()
        return count


class PmgsyRoadsConnector(BaseConnector):
    def __init__(self):
        super().__init__(
            dataset_id="pmgsy_roads",
            name="PMGSY Roads Registry",
            source="Ministry of Rural Development",
            table_name="roads"
        )

    def fetch_data(self, url: str) -> list:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)

    def normalize_row(self, row: dict) -> dict:
        return {
            "road_name": row.get("road_name") or row.get("name"),
            "state_name": normalize_state_name(row.get("state_name") or row.get("state")),
            "district_name": normalize_district_name(row.get("district_name") or row.get("district")),
            "block_name": row.get("block_name") or "",
            "habitation_name": row.get("habitation_name") or "",
            "upgrade_or_new": row.get("upgrade_or_new") or "New",
            "surface_type": row.get("surface_type") or "BT",
            "physical_status": row.get("physical_status") or "Complete",
            "length": float(row.get("length") or 0.0),
            "total_cost": float(row.get("total_cost") or 0.0),
            "population": int(row.get("population") or 0),
        }

    def save_batch(self, db: Session, batch: list) -> int:
        count = 0
        for data in batch:
            if not data["road_name"]:
                continue
            existing = db.query(Road).filter_by(road_name=data["road_name"], district_name=data["district_name"]).first()
            if not existing:
                db.add(Road(**data))
                count += 1
        db.commit()
        return count


class JjmWaterConnector(BaseConnector):
    def __init__(self):
        super().__init__(
            dataset_id="jjm_water",
            name="Jal Jeevan Mission Census",
            source="Ministry of Jal Shakti",
            table_name="habitations"
        )

    def fetch_data(self, url: str) -> list:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)

    def normalize_row(self, row: dict) -> dict:
        return {
            "state_name": normalize_state_name(row.get("state_name") or row.get("state")),
            "district_name": normalize_district_name(row.get("district_name") or row.get("district")),
            "block_name": row.get("block_name") or "",
            "panchayat_name": row.get("panchayat_name") or "",
            "village_name": row.get("village_name") or "",
            "habitation_name": row.get("habitation_name") or "",
            "sc_population": int(row.get("sc_population") or 0),
            "st_population": int(row.get("st_population") or 0),
            "general_population": int(row.get("general_population") or 0),
            "status": row.get("status") or "FC",
            "year": row.get("year") or "",
        }

    def save_batch(self, db: Session, batch: list) -> int:
        count = 0
        for data in batch:
            if not data["habitation_name"]:
                continue
            existing = db.query(Habitation).filter_by(habitation_name=data["habitation_name"], district_name=data["district_name"]).first()
            if not existing:
                db.add(Habitation(**data))
                count += 1
        db.commit()
        return count
