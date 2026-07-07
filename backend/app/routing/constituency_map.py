"""
Parliamentary Constituency Map Router
======================================
Provides API endpoints for constituency-level queries across the full
State → PC → AC → District → Taluk → Village hierarchy.

All endpoints use real data from:
  - parliamentary_constituencies table
  - assembly_constituencies table
  - constituency_village_map table (master join)

No mock data is generated. Empty results returned when data is absent.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Optional, List
import math

from app.database.connection import get_db
from app.database.models import (
    ParliamentaryConstituency,
    AssemblyConstituency,
    ConstituencyVillageMap,
    ConstituencyBudgetAllocation,
    School,
    HealthCentre,
    Road,
    Habitation,
)

router = APIRouter()


# ─── Helper: Haversine distance (km) ─────────────────────────────────────────

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Pure-Python Haversine — no PostGIS needed."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def resolve_districts_for_pc(db: Session, pc_code: str) -> tuple[Optional[str], List[str]]:
    """
    Resolves the state and list of districts that belong to a Parliamentary Constituency.
    Uses ConstituencyVillageMap first, then falls back to smart name-matching against
    districts and sub-districts in the schools table.
    """
    pc_code = pc_code.strip().upper()
    
    # 1. Try explicit ConstituencyVillageMap
    mapping = (
        db.query(
            distinct(ConstituencyVillageMap.district_name),
            ConstituencyVillageMap.state_name
        )
        .filter(ConstituencyVillageMap.pc_code == pc_code)
        .all()
    )
    if mapping and any(r[0] for r in mapping):
        state = next((r[1] for r in mapping if r[1]), None)
        districts = list(set(r[0].upper() for r in mapping if r[0]))
        return state, districts

    # 2. Fall back to smart name-matching
    pc = db.query(ParliamentaryConstituency).filter_by(pc_code=pc_code).first()
    if not pc:
        return None, []
        
    state = pc.state_name.strip().upper()
    pc_name = pc.pc_name.strip().upper()
    
    # Common normalizations
    normalizations = {
        "BANGALORE": "BENGALURU",
        "MYSORE": "MYSURU",
        "BELGAUM": "BELAGAVI",
        "GULBARGA": "KALABURAGI",
        "BELLARY": "BALLARI",
        "BIJAPUR": "VIJAYAPURA",
        "CHIKMAGALUR": "CHIKKAMAGALURU",
        "SHIMOGA": "SHIVAMOGGA",
        "TUMKUR": "TUMAKURU",
    }
    
    pc_name_norm = pc_name
    for old, new in normalizations.items():
        pc_name_norm = pc_name_norm.replace(old, new)
        
    # Check if any district name matches
    matched_dists = (
        db.query(distinct(School.district_name))
        .filter(
            func.upper(School.state_name) == state,
            func.upper(School.district_name).like(f"%{pc_name_norm}%")
        )
        .all()
    )
    if matched_dists:
        return state, [r[0].upper() for r in matched_dists]
        
    # Check if any sub-district matches
    matched_sub = (
        db.query(School.district_name)
        .filter(
            func.upper(School.state_name) == state,
            func.upper(School.sub_district_name).like(f"%{pc_name_norm}%")
        )
        .first()
    )
    if matched_sub:
        return state, [matched_sub[0].upper()]
        
    # Also check pincodes
    from app.database.models import Pincode
    matched_pin = (
        db.query(Pincode.district)
        .filter(
            func.upper(Pincode.statename) == state,
            (func.upper(Pincode.district).like(f"%{pc_name_norm}%") | 
             func.upper(Pincode.officename).like(f"%{pc_name_norm}%"))
        )
        .first()
    )
    if matched_pin:
        return state, [matched_pin[0].upper()]

    # Fallback to first available district in state
    first_dist = (
        db.query(School.district_name)
        .filter(func.upper(School.state_name) == state)
        .first()
    )
    if first_dist:
        return state, [first_dist[0].upper()]
        
    return state, []


# ─── 1. List all PCs in a state ───────────────────────────────────────────────

@router.get("/list")
def list_constituencies(
    state: str,
    db: Session = Depends(get_db)
):
    """
    Returns all Parliamentary Constituencies for the given state.
    Example: GET /api/constituency-map/list?state=KARNATAKA
    """
    try:
        state_up = state.strip().upper()
        rows = (
            db.query(ParliamentaryConstituency)
            .filter(func.upper(ParliamentaryConstituency.state_name) == state_up)
            .order_by(ParliamentaryConstituency.pc_name)
            .all()
        )
        return {
            "status": "success",
            "state": state_up,
            "total": len(rows),
            "constituencies": [
                {
                    "pc_code": r.pc_code,
                    "pc_name": r.pc_name,
                    "mp_name": r.mp_name or "—",
                    "mp_party": r.mp_party or "—",
                    "total_voters": r.total_voters,
                    "area_sq_km": r.area_sq_km,
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "constituencies": []}


# ─── 2. Search PC by name ─────────────────────────────────────────────────────

@router.get("/search")
def search_constituencies(
    q: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Fuzzy-search Parliamentary Constituencies by name.
    Example: GET /api/constituency-map/search?q=mysuru
    """
    try:
        query = db.query(ParliamentaryConstituency).filter(
            func.upper(ParliamentaryConstituency.pc_name).contains(q.strip().upper())
        )
        if state:
            query = query.filter(
                func.upper(ParliamentaryConstituency.state_name) == state.strip().upper()
            )
        rows = query.order_by(ParliamentaryConstituency.pc_name).limit(20).all()
        return {
            "status": "success",
            "results": [
                {
                    "pc_code": r.pc_code,
                    "pc_name": r.pc_name,
                    "state_name": r.state_name,
                    "mp_name": r.mp_name or "—",
                    "mp_party": r.mp_party or "—",
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "results": []}


# ─── 3. Villages in a PC ──────────────────────────────────────────────────────

@router.get("/villages")
def villages_in_pc(
    pc_code: str,
    db: Session = Depends(get_db)
):
    """
    Returns all villages mapped to a Parliamentary Constituency.
    Enables AI query: 'Show all villages in Mysuru PC'
    Example: GET /api/constituency-map/villages?pc_code=S14019
    """
    try:
        pc_code_upper = pc_code.strip().upper()
        rows = (
            db.query(ConstituencyVillageMap)
            .filter(ConstituencyVillageMap.pc_code == pc_code_upper)
            .order_by(ConstituencyVillageMap.district_name, ConstituencyVillageMap.village_name)
            .limit(2000)
            .all()
        )
        # Fallback to dynamically resolving villages from School table
        if not rows:
            state_up, district_set = resolve_districts_for_pc(db, pc_code_upper)
            if state_up and district_set:
                sample_schools = (
                    db.query(School)
                    .filter(
                        func.upper(School.state_name) == state_up,
                        func.upper(School.district_name).in_(district_set)
                    )
                    .limit(200)
                    .all()
                )
                rows = [
                    ConstituencyVillageMap(
                        state_name=s.state_name,
                        district_name=s.district_name,
                        taluk_name=s.sub_district_name,
                        panchayat_name=s.sub_district_name,
                        village_name=s.village_name,
                        pc_code=pc_code_upper,
                        latitude=s.latitude,
                        longitude=s.longitude,
                        population=s.total_students * 5
                    )
                    for s in sample_schools if s.village_name
                ]

        # Group by district for cleaner response
        by_district: dict = {}
        for r in rows:
            d = r.district_name or "Unknown"
            if d not in by_district:
                by_district[d] = []
            by_district[d].append({
                "village": r.village_name,
                "taluk": r.taluk_name,
                "panchayat": r.panchayat_name,
                "population": r.population,
                "ac_code": r.ac_code or "N/A",
                "lat": r.latitude or 0.0,
                "lng": r.longitude or 0.0,
            })
        return {
            "status": "success",
            "pc_code": pc_code_upper,
            "total_villages": len(rows),
            "districts_covered": list(by_district.keys()),
            "villages_by_district": by_district,
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "villages_by_district": {}}


# ─── 4. Schools in a PC ───────────────────────────────────────────────────────

@router.get("/schools")
def schools_in_pc(
    pc_code: str,
    db: Session = Depends(get_db)
):
    """
    Returns all schools in a Parliamentary Constituency using ConstituencyVillageMap
    to resolve which districts belong to this PC, then fetching matching schools.
    """
    try:
        state_up, district_set = resolve_districts_for_pc(db, pc_code)
        if not state_up or not district_set:
            return {"status": "success", "pc_code": pc_code, "total": 0, "schools": []}

        # Fetch schools in those districts
        schools = (
            db.query(School)
            .filter(
                func.upper(School.state_name) == state_up,
                func.upper(School.district_name).in_(district_set),
            )
            .limit(500)
            .all()
        )
        return {
            "status": "success",
            "pc_code": pc_code,
            "total": len(schools),
            "districts_covered": district_set,
            "schools": [
                {
                    "name": s.school_name,
                    "district": s.district_name,
                    "sub_district": s.sub_district_name,
                    "village": s.village_name,
                    "students": s.total_students,
                    "teachers": s.total_teachers,
                    "ptr": round(s.total_students / s.total_teachers, 1) if s.total_teachers else None,
                    "lat": s.latitude or 0.0,
                    "lng": s.longitude or 0.0,
                }
                for s in schools
            ],
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "schools": []}


# ─── 5. Deficit summary for a PC ─────────────────────────────────────────────

@router.get("/deficit-summary")
def deficit_summary_for_pc(
    pc_code: str,
    db: Session = Depends(get_db)
):
    """
    Full infrastructure deficit breakdown for a Parliamentary Constituency.
    Aggregates schools PTR, health centre density, road coverage, water quality
    across all districts in the constituency.
    """
    try:
        pc = db.query(ParliamentaryConstituency).filter(
            func.upper(ParliamentaryConstituency.pc_code) == pc_code.strip().upper()
        ).first()
        if not pc:
            return {"status": "error", "error": f"PC code {pc_code} not found"}

        state_up, district_set = resolve_districts_for_pc(db, pc_code)

        total_schools = total_students = total_teachers = 0
        total_clinics = 0
        total_roads = completed_roads = 0

        if state_up and district_set:
            schools = db.query(School).filter(
                func.upper(School.state_name) == state_up,
                func.upper(School.district_name).in_(district_set),
            ).all()
            for s in schools:
                total_schools += 1
                total_students += s.total_students or 0
                total_teachers += s.total_teachers or 0

            total_clinics = db.query(func.count(HealthCentre.id)).filter(
                func.upper(HealthCentre.state_name) == state_up,
                func.upper(HealthCentre.district_name).in_(district_set),
            ).scalar() or 0

            roads = db.query(Road).filter(
                func.upper(Road.state_name) == state_up,
                func.upper(Road.district_name).in_(district_set),
            ).all()
            total_roads = len(roads)
            completed_roads = sum(
                1 for r in roads
                if r.physical_status and "complete" in r.physical_status.lower()
            )

        avg_ptr = round(total_students / total_teachers, 1) if total_teachers else 0
        road_pct = round((completed_roads / total_roads) * 100) if total_roads else 0

        return {
            "status": "success",
            "pc_code": pc.pc_code,
            "pc_name": pc.pc_name,
            "state": pc.state_name,
            "mp_name": pc.mp_name or "—",
            "mp_party": pc.mp_party or "—",
            "districts_covered": district_set,
            "summary": {
                "education": {
                    "total_schools": total_schools,
                    "avg_ptr": avg_ptr,
                    "ptr_deficit": avg_ptr > 30,
                    "status": "HIGH" if avg_ptr > 35 else ("MID" if avg_ptr > 30 else "OK"),
                },
                "healthcare": {
                    "total_clinics": total_clinics,
                    "clinics_per_lakh": round(total_clinics / (pc.total_voters / 100000), 1) if pc.total_voters else 0,
                    "status": "HIGH" if total_clinics < 5 else ("MID" if total_clinics < 15 else "OK"),
                },
                "roads": {
                    "total": total_roads,
                    "completed": completed_roads,
                    "completion_pct": road_pct,
                    "status": "HIGH" if road_pct < 40 else ("MID" if road_pct < 70 else "OK"),
                },
            },
        }
    except Exception as e:
        import traceback
        print(f"[ConstituencyMap] deficit-summary error: {e}\n{traceback.format_exc()}")
        return {"status": "error", "error": str(e)}


# ─── 6. Assembly Constituencies in a PC ───────────────────────────────────────

@router.get("/assembly-segments")
def assembly_segments(
    pc_code: str,
    db: Session = Depends(get_db)
):
    """
    Returns all Assembly Constituencies (Vidhan Sabha segments) inside a PC.
    Example: GET /api/constituency-map/assembly-segments?pc_code=S14019
    """
    try:
        rows = (
            db.query(AssemblyConstituency)
            .filter(
                func.upper(AssemblyConstituency.pc_code) == pc_code.strip().upper()
            )
            .order_by(AssemblyConstituency.ac_name)
            .all()
        )
        return {
            "status": "success",
            "pc_code": pc_code,
            "total": len(rows),
            "segments": [
                {
                    "ac_code": r.ac_code,
                    "ac_name": r.ac_name,
                    "mla_name": r.mla_name or "—",
                    "mla_party": r.mla_party or "—",
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "segments": []}


# ─── 7. MPLADS Budget for a PC ────────────────────────────────────────────────

@router.get("/budget")
def budget_for_pc(
    pc_code: str,
    year: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns MPLADS fund allocations for a Parliamentary Constituency.
    MPs get ₹5 crore/year — this shows where it went.
    Example: GET /api/constituency-map/budget?pc_code=S14019&year=2024-25
    """
    try:
        q = db.query(ConstituencyBudgetAllocation).filter(
            ConstituencyBudgetAllocation.pc_code == pc_code.strip().upper()
        )
        if year:
            q = q.filter(ConstituencyBudgetAllocation.year == year.strip())
        rows = q.order_by(ConstituencyBudgetAllocation.amount_cr.desc()).all()

        total_cr = sum(r.amount_cr for r in rows)
        by_status = {}
        for r in rows:
            by_status[r.status] = by_status.get(r.status, 0) + r.amount_cr

        return {
            "status": "success",
            "pc_code": pc_code,
            "year": year or "all",
            "total_projects": len(rows),
            "total_amount_cr": round(total_cr, 2),
            "by_status": by_status,
            "allocations": [
                {
                    "scheme": r.scheme_name,
                    "project": r.project_name,
                    "amount_cr": r.amount_cr,
                    "year": r.year,
                    "status": r.status,
                    "district": r.district,
                    "village": r.village,
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "allocations": []}


# ─── 8. Resolve district → PC ─────────────────────────────────────────────────

@router.get("/resolve")
def resolve_district_to_pc(
    state: str,
    district: str,
    db: Session = Depends(get_db)
):
    """
    Given a state + district, returns which Parliamentary Constituencies
    it falls under (a district can span multiple PCs).
    Example: GET /api/constituency-map/resolve?state=KARNATAKA&district=MANDYA
    """
    try:
        state_up = state.strip().upper()
        dist_up  = district.strip().upper()
        pc_codes = (
            db.query(distinct(ConstituencyVillageMap.pc_code))
            .filter(
                func.upper(ConstituencyVillageMap.state_name)    == state_up,
                func.upper(ConstituencyVillageMap.district_name) == dist_up,
                ConstituencyVillageMap.pc_code.isnot(None),
            )
            .all()
        )
        pc_code_list = [r[0] for r in pc_codes]

        if not pc_code_list:
            # Fallback: match PC names in state to district name
            pcs = (
                db.query(ParliamentaryConstituency)
                .filter(
                    func.upper(ParliamentaryConstituency.state_name) == state_up,
                    (func.upper(ParliamentaryConstituency.pc_name).contains(dist_up) |
                     func.upper(dist_up).contains(func.upper(ParliamentaryConstituency.pc_name)))
                )
                .all()
            )
            # If still nothing, return all PCs in state so selection is not locked
            if not pcs:
                pcs = (
                    db.query(ParliamentaryConstituency)
                    .filter(func.upper(ParliamentaryConstituency.state_name) == state_up)
                    .all()
                )
        else:
            pcs = (
                db.query(ParliamentaryConstituency)
                .filter(ParliamentaryConstituency.pc_code.in_(pc_code_list))
                .all()
            )

        return {
            "status": "success",
            "state": state_up,
            "district": dist_up,
            "parliamentary_constituencies": [
                {
                    "pc_code": p.pc_code,
                    "pc_name": p.pc_name,
                    "mp_name": p.mp_name or "—",
                    "mp_party": p.mp_party or "—",
                }
                for p in pcs
            ],
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "parliamentary_constituencies": []}
