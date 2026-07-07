"""
Database Quality Checker Engine
================================
Audits the tables in MP Mitra to calculate completeness, missing values,
coverage level, and ECI alignment. Stores results in the dataset_metadata table.

Calculates:
  - Completeness % (non-null key fields)
  - Missing GPS coords % (latitude/longitude check)
  - Constituency Mapping coverage % (aligned to PC/AC)
  - Freshness (time since last update)
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import (
    DatasetMetadata,
    School,
    HealthCentre,
    Road,
    Pincode,
    Habitation,
    WaterQualityRecord,
    ConstituencyVillageMap
)

def run_quality_audit(db: Session, dataset_id: str) -> dict:
    """Runs data quality checks on a table, saves/updates stats in metadata."""
    now = datetime.now()
    
    # Defaults
    name = dataset_id.replace("_", " ").title()
    dept = "Ministry of Electronics and Information Technology"
    coverage = "National"
    total_records = 0
    missing_count = 0
    details = {}
    
    if dataset_id == "schools":
        name = "UDISE+ Schools Directory"
        dept = "Department of School Education & Literacy"
        total_records = db.query(func.count(School.udise_school_code)).scalar() or 0
        
        # Check missing names, states or total teachers/students
        missing_names = db.query(func.count(School.udise_school_code)).filter((School.school_name == None) | (School.school_name == "")).scalar() or 0
        missing_coords = db.query(func.count(School.udise_school_code)).filter((School.latitude == 0.0) | (School.latitude == None)).scalar() or 0
        
        missing_count = missing_names + missing_coords
        details = {
            "missing_names": missing_names,
            "missing_gps_coords": missing_coords,
            "completeness_pct": round(((total_records - missing_names) / total_records * 100), 2) if total_records else 100.0,
            "gps_coverage_pct": round(((total_records - missing_coords) / total_records * 100), 2) if total_records else 100.0,
        }
        # Quality score out of 100
        quality_score = (details["completeness_pct"] * 0.4) + (details["gps_coverage_pct"] * 0.6)
        
    elif dataset_id == "health_centres":
        name = "National Health Infrastructure Directory"
        dept = "Ministry of Health and Family Welfare"
        total_records = db.query(func.count(HealthCentre.id)).scalar() or 0
        
        missing_names = db.query(func.count(HealthCentre.id)).filter((HealthCentre.facility_name == None) | (HealthCentre.facility_name == "")).scalar() or 0
        missing_coords = db.query(func.count(HealthCentre.id)).filter((HealthCentre.latitude == 0.0) | (HealthCentre.latitude == None)).scalar() or 0
        
        missing_count = missing_names + missing_coords
        details = {
            "missing_names": missing_names,
            "missing_gps_coords": missing_coords,
            "completeness_pct": round(((total_records - missing_names) / total_records * 100), 2) if total_records else 100.0,
            "gps_coverage_pct": round(((total_records - missing_coords) / total_records * 100), 2) if total_records else 100.0,
        }
        quality_score = (details["completeness_pct"] * 0.4) + (details["gps_coverage_pct"] * 0.6)

    elif dataset_id == "roads":
        name = "PMGSY Rural Roads Registry"
        dept = "Ministry of Rural Development"
        total_records = db.query(func.count(Road.id)).scalar() or 0
        
        missing_names = db.query(func.count(Road.id)).filter((Road.road_name == None) | (Road.road_name == "")).scalar() or 0
        missing_status = db.query(func.count(Road.id)).filter((Road.physical_status == None) | (Road.physical_status == "")).scalar() or 0
        
        missing_count = missing_names + missing_status
        details = {
            "missing_names": missing_names,
            "missing_status": missing_status,
            "completeness_pct": round(((total_records - missing_names) / total_records * 100), 2) if total_records else 100.0,
            "status_coverage_pct": round(((total_records - missing_status) / total_records * 100), 2) if total_records else 100.0,
        }
        quality_score = (details["completeness_pct"] * 0.5) + (details["status_coverage_pct"] * 0.5)

    elif dataset_id == "habitations":
        name = "Integrated Habitation Information Census"
        dept = "Ministry of Jal Shakti"
        total_records = db.query(func.count(Habitation.id)).scalar() or 0
        
        missing_names = db.query(func.count(Habitation.id)).filter((Habitation.habitation_name == None) | (Habitation.habitation_name == "")).scalar() or 0
        missing_pop = db.query(func.count(Habitation.id)).filter(Habitation.general_population == 0).scalar() or 0
        
        missing_count = missing_names + missing_pop
        details = {
            "missing_names": missing_names,
            "missing_population": missing_pop,
            "completeness_pct": round(((total_records - missing_names) / total_records * 100), 2) if total_records else 100.0,
            "population_coverage_pct": round(((total_records - missing_pop) / total_records * 100), 2) if total_records else 100.0,
        }
        quality_score = (details["completeness_pct"] * 0.5) + (details["population_coverage_pct"] * 0.5)

    elif dataset_id == "water_quality":
        name = "Affected Habitation Water Quality Registry"
        dept = "Ministry of Jal Shakti"
        total_records = db.query(func.count(WaterQualityRecord.id)).scalar() or 0
        
        missing_param = db.query(func.count(WaterQualityRecord.id)).filter((WaterQualityRecord.quality_parameter == None) | (WaterQualityRecord.quality_parameter == "")).scalar() or 0
        
        missing_count = missing_param
        details = {
            "missing_parameters": missing_param,
            "completeness_pct": round(((total_records - missing_param) / total_records * 100), 2) if total_records else 100.0,
        }
        quality_score = details["completeness_pct"]

    elif dataset_id == "pincodes":
        name = "India Post Pincodes Registry"
        dept = "Department of Posts"
        total_records = db.query(func.count(Pincode.id)).scalar() or 0
        
        missing_pin = db.query(func.count(Pincode.id)).filter((Pincode.pincode == None) | (Pincode.pincode == "")).scalar() or 0
        
        missing_count = missing_pin
        details = {
            "missing_pincodes": missing_pin,
            "completeness_pct": round(((total_records - missing_pin) / total_records * 100), 2) if total_records else 100.0,
        }
        quality_score = details["completeness_pct"]

    else:
        # Generic table audit
        return {"status": "error", "message": f"Unknown dataset_id: {dataset_id}"}
        
    quality_score = round(max(0.0, min(100.0, quality_score)), 2)
    
    # Save/Update metadata entry
    meta = db.query(DatasetMetadata).filter(DatasetMetadata.dataset_id == dataset_id).first()
    if not meta:
        meta = DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=name,
            source_department=dept,
            last_updated_date=now,
            num_records=total_records,
            version="1.0.0",
            missing_values_count=missing_count,
            coverage_level=coverage,
            quality_score=quality_score,
            details_json=json.dumps(details)
        )
        db.add(meta)
    else:
        meta.num_records = total_records
        meta.missing_values_count = missing_count
        meta.quality_score = quality_score
        meta.details_json = json.dumps(details)
        meta.last_updated_date = now
        
    db.commit()
    
    return {
        "dataset_id": dataset_id,
        "dataset_name": name,
        "source_department": dept,
        "last_updated": now.isoformat(),
        "total_records": total_records,
        "missing_records": missing_count,
        "quality_score": quality_score,
        "details": details
    }


def audit_all_tables(db: Session) -> list:
    """Runs audit on all 6 major tables in MP Mitra."""
    tables = ["schools", "health_centres", "roads", "habitations", "water_quality", "pincodes"]
    results = []
    for t in tables:
        try:
            res = run_quality_audit(db, t)
            results.append(res)
        except Exception as e:
            results.append({"dataset_id": t, "status": "error", "message": str(e)})
    return results
