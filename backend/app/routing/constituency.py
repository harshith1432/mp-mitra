import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.database.connection import get_db
from app.database.models import School, HealthCentre, Road, Habitation, WaterQuality, Pincode, VillageAmenities
from firebase_admin import firestore
from app.database.firebase_config import db as fs_db

router = APIRouter()

@router.get("/states")
def get_states(db: Session = Depends(get_db)):
    try:
        # Get unique states from pincodes or schools
        states = db.query(Pincode.statename).distinct().order_by(Pincode.statename).all()
        # Clean up results
        state_list = [s[0].strip() for s in states if s[0]]
        if not state_list:
            # Fallback to schools if pincodes table is empty
            states = db.query(School.state_name).distinct().order_by(School.state_name).all()
            state_list = [s[0].strip() for s in states if s[0]]
        return {"states": state_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/districts")
def get_districts(state: str, db: Session = Depends(get_db)):
    try:
        districts = db.query(Pincode.district).filter(
            func.upper(Pincode.statename) == state.strip().upper()
        ).distinct().order_by(Pincode.district).all()
        
        district_list = [d[0].strip() for d in districts if d[0]]
        if not district_list:
            # Fallback to schools
            districts = db.query(School.district_name).filter(
                func.upper(School.state_name) == state.strip().upper()
            ).distinct().order_by(School.district_name).all()
            district_list = [d[0].strip() for d in districts if d[0]]
        return {"districts": district_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data")
def get_constituency_data(state: str, district: str, db: Session = Depends(get_db)):
    from app.database.normalization import normalize_district_name, normalize_state_name
    state_upper = normalize_state_name(state)
    dist_upper = normalize_district_name(district)
    
    try:
        # 1. Fetch schools data
        schools = db.query(School).filter(
            func.upper(School.state_name) == state_upper,
            func.upper(School.district_name) == dist_upper
        ).all()
        
        total_schools = len(schools)
        total_teachers = sum([s.total_teachers for s in schools])
        total_students = sum([s.total_students for s in schools])
        avg_ptr = total_students / total_teachers if total_teachers > 0 else 0
        
        school_locations = [
            {
                "code": s.udise_school_code,
                "name": s.school_name,
                "category": s.school_category,
                "type": s.school_type,
                "teachers": s.total_teachers,
                "students": s.total_students,
                "lat": s.latitude,
                "lng": s.longitude
            } for s in schools if s.latitude and s.longitude
        ]

        # 2. Fetch health centres
        clinics = db.query(HealthCentre).filter(
            func.upper(HealthCentre.state_name) == state_upper,
            func.upper(HealthCentre.district_name) == dist_upper
        ).all()
        
        total_clinics = len(clinics)
        chc_count = sum([1 for c in clinics if c.facility_type.lower() == 'chc'])
        phc_count = sum([1 for c in clinics if c.facility_type.lower() == 'phc'])
        sub_count = sum([1 for c in clinics if 'sub' in c.facility_type.lower()])
        
        clinic_locations = [
            {
                "id": c.id,
                "name": c.facility_name,
                "type": c.facility_type,
                "lat": c.latitude,
                "lng": c.longitude,
                "location_type": c.location_type
            } for c in clinics if c.latitude and c.longitude
        ]

        # 3. Fetch road statistics
        roads = db.query(Road).filter(
            func.upper(Road.state_name) == state_upper,
            func.upper(Road.district_name) == dist_upper
        ).all()
        
        total_roads = len(roads)
        completed_roads = sum([1 for r in roads if r.physical_status.lower() == 'completed'])
        total_road_cost = sum([r.total_cost for r in roads])
        total_road_length = sum([r.length for r in roads])
        avg_road_cost_per_km = total_road_cost / total_road_length if total_road_length > 0 else 0
        
        # 4. Fetch habitation demographics using state-normalised lists & district substring LIKE matching
        states_list = normalize_state_filter(state)
        habitations = db.query(Habitation).filter(
            func.upper(Habitation.state_name).in_([s.upper() for s in states_list]),
            func.upper(Habitation.district_name).like(f"{dist_upper}%")
        ).all()
        
        total_habitations = len(habitations)
        sc_pop = sum([h.sc_population for h in habitations])
        st_pop = sum([h.st_population for h in habitations])
        gen_pop = sum([h.general_population for h in habitations])
        total_pop = sc_pop + st_pop + gen_pop
        
        fully_covered_habs = sum([1 for h in habitations if 'fully' in h.status.lower()])
        water_coverage_ratio = fully_covered_habs / total_habitations if total_habitations > 0 else 0

        # 5. Fetch water quality issues using state-normalised lists & district substring LIKE matching
        water_issues = db.query(WaterQuality).filter(
            func.upper(WaterQuality.state_name).in_([s.upper() for s in states_list]),
            func.upper(WaterQuality.district_name).like(f"{dist_upper}%")
        ).all()
        
        total_water_issues = len(water_issues)
        contaminants = {}
        for w in water_issues:
            contaminants[w.quality_parameter] = contaminants.get(w.quality_parameter, 0) + 1

        # 6. Fetch dynamic complaints from Firestore
        active_complaints = []
        try:
            complaints_ref = fs_db.collection("complaints")
            query_ref = complaints_ref.where(filter=firestore.FieldFilter("state_name", "==", state_upper))\
                                      .where(filter=firestore.FieldFilter("district_name", "==", dist_upper))
            docs = query_ref.stream()
            raw_complaints = []
            for doc in docs:
                data = doc.to_dict()
                raw_complaints.append({
                    "id": doc.id,
                    "text": data.get("text_content", ""),
                    "category": data.get("category", ""),
                    "urgency": data.get("urgency", ""),
                    "lat": data.get("latitude", 0.0),
                    "lng": data.get("longitude", 0.0),
                    "status": data.get("status", ""),
                    "date": data.get("created_at"),
                    "village": data.get("village_name", "")
                })
            
            # Sort by date in memory (newest first)
            def get_timestamp(x):
                ts = x["date"]
                if ts and hasattr(ts, "timestamp"):
                    return ts.timestamp()
                return 0
            raw_complaints.sort(key=get_timestamp, reverse=True)
            
            for c in raw_complaints:
                ts = c["date"]
                date_str = ts.strftime("%Y-%m-%d") if ts and hasattr(ts, "strftime") else datetime.now().strftime("%Y-%m-%d")
                active_complaints.append({
                    "id": c["id"],
                    "text": c["text"],
                    "category": c["category"],
                    "urgency": c["urgency"],
                    "lat": c["lat"],
                    "lng": c["lng"],
                    "status": c["status"],
                    "date": date_str,
                    "village": c["village"]
                })
        except Exception as e:
            print(f"Error fetching complaints from Firestore: {e}")

        # Group habitations by village name (case-insensitive)
        village_habs = {}
        for h in habitations:
            if not h.village_name:
                continue
            v_key = h.village_name.strip().upper()
            if v_key not in village_habs:
                village_habs[v_key] = []
            village_habs[v_key].append(h)

        # Group schools by village name
        village_schools = {}
        for s in schools:
            if not s.school_name:
                continue
            v_key = s.village_name.strip().upper() if s.village_name else "UNKNOWN"
            if v_key not in village_schools:
                village_schools[v_key] = []
            village_schools[v_key].append(s)

        # Group water quality records by village name
        village_wq = {}
        for w in water_issues:
            if not w.village_name:
                continue
            v_key = w.village_name.strip().upper()
            if v_key not in village_wq:
                village_wq[v_key] = []
            village_wq[v_key].append(w)

        # Build detailed unique villages list
        unique_villages = sorted(list(set([h.village_name.strip().title() for h in habitations if h.village_name])))
        villages_list = []
        for v_name in unique_villages:
            v_key = v_name.strip().upper()
            v_habs = village_habs.get(v_key, [])
            v_schs = village_schools.get(v_key, [])
            v_wq = village_wq.get(v_key, [])
            
            v_pop = sum([h.sc_population + h.st_population + h.general_population for h in v_habs])
            v_sc = sum([h.sc_population for h in v_habs])
            v_st = sum([h.st_population for h in v_habs])
            v_gen = sum([h.general_population for h in v_habs])
            
            statuses = [h.status for h in v_habs if h.status]
            if not statuses:
                jjm_status = "Unknown"
            elif all("fully" in s.lower() for s in statuses):
                jjm_status = "Fully Covered"
            elif any("fully" in s.lower() for s in statuses):
                jjm_status = "Partially Covered"
            else:
                jjm_status = "Not Covered"
                
            contams = sorted(list(set([w.quality_parameter for w in v_wq if w.quality_parameter])))
            
            habs_details = [
                {
                    "name": h.habitation_name.strip().title() if h.habitation_name else "Unknown Habitation",
                    "population": h.sc_population + h.st_population + h.general_population,
                    "status": h.status
                } for h in v_habs
            ]
            
            schs_details = [
                {
                    "code": s.udise_school_code,
                    "name": s.school_name,
                    "category": s.school_category,
                    "type": s.school_type,
                    "teachers": s.total_teachers,
                    "students": s.total_students,
                    "ptr": round(s.total_students / s.total_teachers, 1) if s.total_teachers > 0 else 0
                } for s in v_schs
            ]

            villages_list.append({
                "name": v_name,
                "population": v_pop,
                "sc_population": v_sc,
                "st_population": v_st,
                "general_population": v_gen,
                "habitation_count": len(v_habs),
                "school_count": len(v_schs),
                "water_status": jjm_status,
                "contaminants": contams,
                "habitations": habs_details,
                "schools": schs_details
            })

        # Group habitations by Gram Panchayat name (case-insensitive)
        panchayat_habs = {}
        for h in habitations:
            if not h.panchayat_name:
                continue
            p_key = h.panchayat_name.strip().upper()
            if p_key not in panchayat_habs:
                panchayat_habs[p_key] = []
            panchayat_habs[p_key].append(h)

        # Build detailed unique Gram Panchayats list
        unique_panchayats = sorted(list(set([h.panchayat_name.strip().title() for h in habitations if h.panchayat_name])))
        panchayats_list = []
        for p_name in unique_panchayats:
            p_key = p_name.strip().upper()
            p_habs = panchayat_habs.get(p_key, [])
            
            p_pop = sum([h.sc_population + h.st_population + h.general_population for h in p_habs])
            p_sc = sum([h.sc_population for h in p_habs])
            p_st = sum([h.st_population for h in p_habs])
            p_gen = sum([h.general_population for h in p_habs])
            
            statuses = [h.status for h in p_habs if h.status]
            if not statuses:
                jjm_status = "Unknown"
            elif all("fully" in s.lower() for s in statuses):
                jjm_status = "Fully Covered"
            elif any("fully" in s.lower() for s in statuses):
                jjm_status = "Partially Covered"
            else:
                jjm_status = "Not Covered"
                
            gp_villages = sorted(list(set([h.village_name.strip().title() for h in p_habs if h.village_name])))
            
            panchayats_list.append({
                "name": p_name,
                "population": p_pop,
                "sc_population": p_sc,
                "st_population": p_st,
                "general_population": p_gen,
                "habitation_count": len(p_habs),
                "village_count": len(gp_villages),
                "villages": gp_villages,
                "water_status": jjm_status
            })

        # Build roads list
        roads_list = [
            {
                "name": r.road_name,
                "block": r.block_name,
                "habitation": r.habitation_name,
                "upgrade_or_new": r.upgrade_or_new,
                "surface": r.surface_type,
                "status": r.physical_status,
                "length_km": r.length,
                "cost_lakh": r.total_cost,
                "population": r.population
            } for r in roads
        ]

        # Build water quality list
        water_quality_list = [
            {
                "block": w.block_name,
                "panchayat": w.panchayat_name,
                "village": w.village_name,
                "habitation": w.habitation_name,
                "parameter": w.quality_parameter,
                "year": w.year
            } for w in water_issues
        ]

        # 7. Compute Real-Time Constituency Health Score (0-100)
        # Ind 1: School Pupil-Teacher Ratio (PTR) -> target < 30. Max points: 25
        ptr_score = max(0, min(25, 25 * (1 - (avg_ptr - 20) / 40))) if avg_ptr > 20 else 25
        
        # Ind 2: Clinic Coverage per 10,000 population -> target > 2. Max points: 25
        clinics_per_10k = (total_clinics / (total_pop / 10000)) if total_pop > 0 else 0
        clinic_score = min(25, 25 * (clinics_per_10k / 2.5)) if clinics_per_10k > 0 else 15
        
        # Ind 3: Water Coverage (Fully Covered Habitations Ratio) -> Max points: 25
        water_score = 25 * water_coverage_ratio
        
        # Ind 4: Road Completion rate -> Max points: 25
        road_completion_ratio = completed_roads / total_roads if total_roads > 0 else 0.8
        road_score = 25 * road_completion_ratio
        
        composite_health_score = int(ptr_score + clinic_score + water_score + road_score)

        # Fetch crawled news, tenders, and schemes to merge real-time scraper data
        from app.database.models import CrawledNews, CrawledTender, CrawledScheme
        crawled_news_db = db.query(CrawledNews).filter(
            func.upper(CrawledNews.district_name) == dist_upper
        ).order_by(CrawledNews.severity_score.desc()).limit(3).all()
        
        crawled_news_alerts = [
            {
                "title": n.title,
                "source": n.source,
                "severity": "High" if n.severity_score >= 80 else "Medium",
                "village": n.district_name.title()
            } for n in crawled_news_db
        ]

        crawled_tenders_count = db.query(CrawledTender).filter(
            func.upper(CrawledTender.district_name) == dist_upper
        ).count()

        crawled_schemes_count = db.query(CrawledScheme).count()

        if crawled_news_db:
            composite_health_score = max(40, composite_health_score - len(crawled_news_db) * 2)

        return {
            "constituency": f"{district}, {state}",
            "health_score": composite_health_score,
            "metrics": {
                "population": total_pop,
                "crawled_news_alerts": crawled_news_alerts,
                "crawled_tenders_count": crawled_tenders_count,
                "crawled_schemes_count": crawled_schemes_count,
                "sc_st_percentage": round((sc_pop + st_pop) / total_pop * 100, 2) if total_pop > 0 else 0,
                "total_villages": len(unique_villages),
                "total_panchayats": len(unique_panchayats),
                "villages_list": villages_list,
                "panchayats_list": panchayats_list,
                "roads_list": roads_list,
                "water_quality_list": water_quality_list,
                "schools": {
                    "count": total_schools,
                    "students": total_students,
                    "teachers": total_teachers,
                    "avg_ptr": round(avg_ptr, 1)
                },
                "healthcare": {
                    "count": total_clinics,
                    "chc": chc_count,
                    "phc": phc_count,
                    "subcentre": sub_count
                },
                "roads": {
                    "count": total_roads,
                    "completed": completed_roads,
                    "total_cost_cr": round(total_road_cost / 10000000, 2), # In Crores
                    "avg_cost_per_km_lakh": round(avg_road_cost_per_km / 100000, 2) # In Lakhs
                },
                "water": {
                    "total_habitations": total_habitations,
                    "fully_covered": fully_covered_habs,
                    "quality_records": total_water_issues,
                    "contaminants": contaminants
                }
            },
            "map_points": {
                "schools": school_locations,
                "clinics": clinic_locations,
                "complaints": active_complaints
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blocks")
def get_blocks(state: str, district: str, db: Session = Depends(get_db)):
    from app.database.normalization import normalize_district_name, normalize_state_name
    try:
        state_upper = normalize_state_name(state)
        dist_upper = normalize_district_name(district)
        
        results = db.query(Habitation.block_name).filter(
            func.upper(Habitation.state_name) == state_upper,
            func.upper(Habitation.district_name) == dist_upper
        ).distinct().order_by(Habitation.block_name).all()
        
        blocks = [r[0].title() for r in results if r[0]]
        if not blocks:
            blocks = ["Block A", "Block B", "Block C"]
        return {"blocks": blocks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/villages")
def get_villages(state: str, district: str, db: Session = Depends(get_db)):
    from app.database.normalization import normalize_district_name, normalize_state_name
    try:
        state_upper = normalize_state_name(state)
        dist_upper = normalize_district_name(district)
        
        # Query unique village names from Habitation database table
        results = db.query(Habitation.village_name).filter(
            func.upper(Habitation.state_name) == state_upper,
            func.upper(Habitation.district_name) == dist_upper
        ).distinct().order_by(Habitation.village_name).all()
        
        villages = [r[0].title() for r in results if r[0]]
        # Fallback if empty
        if not villages:
            villages = ["Village X", "Village Y", "Village Z"]
        return {"villages": villages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-projects")
def search_projects(
    state: str = None,
    district: str = None,
    block: str = None,
    panchayat: str = None,
    village: str = None,
    habitation: str = None,
    quality_parameter: str = None,
    year: str = None,
    db: Session = Depends(get_db)
):
    try:
        # Query Water Quality Records
        wq_query = db.query(WaterQuality)
        if state:
            wq_query = wq_query.filter(func.upper(WaterQuality.state_name) == state.strip().upper())
        if district:
            wq_query = wq_query.filter(func.upper(WaterQuality.district_name) == district.strip().upper())
        if block:
            wq_query = wq_query.filter(func.upper(WaterQuality.block_name) == block.strip().upper())
        if panchayat:
            wq_query = wq_query.filter(func.upper(WaterQuality.panchayat_name) == panchayat.strip().upper())
        if village:
            wq_query = wq_query.filter(func.upper(WaterQuality.village_name) == village.strip().upper())
        if habitation:
            wq_query = wq_query.filter(func.upper(WaterQuality.habitation_name) == habitation.strip().upper())
        if quality_parameter:
            wq_query = wq_query.filter(func.upper(WaterQuality.quality_parameter) == quality_parameter.strip().upper())
        if year:
            wq_query = wq_query.filter(func.upper(WaterQuality.year) == year.strip().upper())
            
        wq_results = wq_query.limit(50).all()
        
        # Query Habitation Census records
        hab_query = db.query(Habitation)
        if state:
            hab_query = hab_query.filter(func.upper(Habitation.state_name) == state.strip().upper())
        if district:
            hab_query = hab_query.filter(func.upper(Habitation.district_name) == district.strip().upper())
        if block:
            hab_query = hab_query.filter(func.upper(Habitation.block_name) == block.strip().upper())
        if panchayat:
            hab_query = hab_query.filter(func.upper(Habitation.panchayat_name) == panchayat.strip().upper())
        if village:
            hab_query = hab_query.filter(func.upper(Habitation.village_name) == village.strip().upper())
        if habitation:
            hab_query = hab_query.filter(func.upper(Habitation.habitation_name) == habitation.strip().upper())
        if year:
            # Habitation year format is '01_04_2012' so we search by suffix or match
            hab_query = hab_query.filter(Habitation.year.like(f"%{year}%"))
            
        hab_results = hab_query.limit(50).all()
        
        projects = []
        for r in wq_results:
            projects.append({
                "type": "Water Quality Contamination",
                "state_name": r.state_name,
                "district_name": r.district_name,
                "block_name": r.block_name,
                "panchayat_name": r.panchayat_name,
                "village_name": r.village_name,
                "habitation_name": r.habitation_name,
                "parameter": r.quality_parameter,
                "year": r.year,
                "status": "Contaminated"
            })
            
        for r in hab_results:
            projects.append({
                "type": "Habitation Coverage Status",
                "state_name": r.state_name,
                "district_name": r.district_name,
                "block_name": r.block_name,
                "panchayat_name": r.panchayat_name,
                "village_name": r.village_name,
                "habitation_name": r.habitation_name,
                "parameter": f"SC Pop: {r.sc_population} | ST Pop: {r.st_population} | Gen Pop: {r.general_population}",
                "year": r.year,
                "status": r.status
            })

        # Query Village Amenities from Census 2011 table
        amenities_query = db.query(VillageAmenities)
        if state:
            states_list = normalize_state_filter(state)
            conditions = []
            for s in states_list:
                conditions.append(func.upper(VillageAmenities.state).like(f"{s}%"))
            amenities_query = amenities_query.filter(or_(*conditions))
        if district:
            amenities_query = amenities_query.filter(func.upper(VillageAmenities.district).like(f"{district.strip().upper()}%"))
        if village:
            amenities_query = amenities_query.filter(func.upper(VillageAmenities.village_name) == village.strip().upper())
            
        amenities = amenities_query.limit(50).all()
        for r in amenities:
            projects.append({
                "type": "Village Census Amenities",
                "state_name": r.state,
                "district_name": r.district,
                "block_name": r.sub_district,
                "panchayat_name": "N/A",
                "village_name": r.village_name,
                "habitation_name": "All Habitations",
                "parameter": f"Tap Water: {r.filtered_tap_water} | Drainage: Closed={r.closed_drainage}/Open={r.open_drainage} | CHC Dist: {r.chc_distance} | PHC Dist: {r.phc_distance} | Road: {r.all_weather_road}",
                "year": r.year,
                "status": f"Pop: {r.population} (SC:{r.sc_population}/ST:{r.st_population})"
            })
            
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def normalize_state_filter(state_val: str):
    state_val = state_val.strip().upper()
    if state_val == 'TELANGANA':
        return ['TELANGANA', 'ANDHRA PRADESH']
    if state_val == 'UTTARAKHAND':
        return ['UTTARAKHAND', 'UTTARANCHAL']
    if state_val == 'ODISHA':
        return ['ODISHA', 'ORISSA']
    if state_val == 'PUDUCHERRY':
        return ['PUDUCHERRY', 'PONDICHERRY']
    return [state_val]

@router.get("/filter-options")
def get_filter_options(
    state: str = None,
    district: str = None,
    block: str = None,
    panchayat: str = None,
    village: str = None,
    db: Session = Depends(get_db)
):
    try:
        # Base query for Habitations
        query = db.query(Habitation)
        
        # In the 2012 Census dataset, states/districts/blocks might be different. 
        # We use LIKE match to be robust to trailing code suffixes like (19) or (03).
        if state:
            states_list = normalize_state_filter(state)
            conditions = []
            for s in states_list:
                conditions.append(func.upper(Habitation.state_name).like(f"{s}%"))
            query = query.filter(or_(*conditions))
            
        if district:
            query = query.filter(func.upper(Habitation.district_name).like(f"{district.strip().upper()}%"))
            
        if not block:
            # Return distinct blocks
            results = query.with_entities(Habitation.block_name).distinct().order_by(Habitation.block_name).all()
            blocks = [r[0].strip() for r in results if r[0]]
            return {"blocks": blocks}
            
        # If block is provided, filter by block
        query = query.filter(func.upper(Habitation.block_name) == block.strip().upper())
        
        if not panchayat:
            # Return distinct panchayats
            results = query.with_entities(Habitation.panchayat_name).distinct().order_by(Habitation.panchayat_name).all()
            panchayats = [r[0].strip() for r in results if r[0]]
            return {"panchayats": panchayats}
            
        # If panchayat is provided, filter by panchayat
        query = query.filter(func.upper(Habitation.panchayat_name) == panchayat.strip().upper())
        
        if not village:
            # Return distinct villages
            results = query.with_entities(Habitation.village_name).distinct().order_by(Habitation.village_name).all()
            villages = [r[0].strip() for r in results if r[0]]
            return {"villages": villages}
            
        # If village is provided, filter by village
        query = query.filter(func.upper(Habitation.village_name) == village.strip().upper())
        
        # Return distinct habitations
        results = query.with_entities(Habitation.habitation_name).distinct().order_by(Habitation.habitation_name).all()
        habitations = [r[0].strip() for r in results if r[0]]
        return {"habitations": habitations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/water-quality-list")
def get_water_quality_list(state: str, district: str, db: Session = Depends(get_db)):
    from app.database.normalization import normalize_district_name, normalize_state_name
    try:
        state_upper = normalize_state_name(state)
        district_upper = normalize_district_name(district)
        records = db.query(WaterQuality).filter(
            func.upper(WaterQuality.state_name) == state_upper,
            func.upper(WaterQuality.district_name) == district_upper
        ).limit(100).all()
        return {
            "records": [
                {
                    "id": r.id,
                    "block": r.block_name,
                    "panchayat": r.panchayat_name,
                    "village": r.village_name,
                    "habitation": r.habitation_name,
                    "parameter": r.quality_parameter,
                    "year": r.year
                } for r in records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/habitation-list")
def get_habitation_list(state: str, district: str, status: str = None, db: Session = Depends(get_db)):
    from app.database.normalization import normalize_district_name, normalize_state_name
    try:
        state_upper = normalize_state_name(state)
        district_upper = normalize_district_name(district)
        query = db.query(Habitation).filter(
            func.upper(Habitation.state_name) == state_upper,
            func.upper(Habitation.district_name) == district_upper
        )
        if status:
            if status == "fully_covered":
                query = query.filter(func.lower(Habitation.status).like("%fully%"))
            elif status == "partially_covered":
                query = query.filter(func.lower(Habitation.status).like("%partial%"))
        records = query.limit(100).all()
        return {
            "records": [
                {
                    "id": r.id,
                    "block": r.block_name,
                    "panchayat": r.panchayat_name,
                    "village": r.village_name,
                    "habitation": r.habitation_name,
                    "sc_pop": r.sc_population,
                    "st_pop": r.st_population,
                    "gen_pop": r.general_population,
                    "status": r.status
                } for r in records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/road-list")
def get_road_list(state: str, district: str, status: str = None, db: Session = Depends(get_db)):
    from app.database.normalization import normalize_district_name, normalize_state_name
    try:
        state_upper = normalize_state_name(state)
        district_upper = normalize_district_name(district)
        query = db.query(Road).filter(
            func.upper(Road.state_name) == state_upper,
            func.upper(Road.district_name) == district_upper
        )
        if status:
            if status == "completed":
                query = query.filter(func.lower(Road.physical_status) == "completed")
            elif status == "pending":
                query = query.filter(func.lower(Road.physical_status) != "completed")
        records = query.limit(100).all()
        return {
            "records": [
                {
                    "id": r.id,
                    "road_name": r.road_name,
                    "length": r.length,
                    "total_cost": r.total_cost,
                    "physical_status": r.physical_status,
                    "stage_complete": r.stage_complete
                } for r in records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/school-list")
def get_school_list(state: str, district: str, status: str = None, db: Session = Depends(get_db)):
    from app.database.normalization import normalize_district_name, normalize_state_name
    try:
        state_upper = normalize_state_name(state)
        district_upper = normalize_district_name(district)
        query = db.query(School).filter(
            func.upper(School.state_name) == state_upper,
            func.upper(School.district_name) == district_upper
        )
        if status == "ptr_deficit":
            query = query.filter(School.total_teachers > 0, (School.total_students / School.total_teachers) > 30)
            
        records = query.limit(100).all()
        return {
            "records": [
                {
                    "id": s.udise_school_code,
                    "name": s.school_name,
                    "category": s.school_category,
                    "type": s.school_type,
                    "students": s.total_students,
                    "teachers": s.total_teachers
                } for s in records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clinic-list")
def get_clinic_list(state: str, district: str, type: str = None, db: Session = Depends(get_db)):
    from app.database.normalization import normalize_district_name, normalize_state_name
    try:
        state_upper = normalize_state_name(state)
        district_upper = normalize_district_name(district)
        query = db.query(HealthCentre).filter(
            func.upper(HealthCentre.state_name) == state_upper,
            func.upper(HealthCentre.district_name) == district_upper
        )
        if type == "chc_phc":
            query = query.filter(func.lower(HealthCentre.facility_type).in_(["chc", "phc"]))
        elif type == "subcentre":
            query = query.filter(func.lower(HealthCentre.facility_type).like("%sub%"))
            
        records = query.limit(100).all()
        return {
            "records": [
                {
                    "id": c.id,
                    "name": c.facility_name,
                    "type": c.facility_type,
                    "location_type": c.location_type,
                    "lat": c.latitude or 0.0,
                    "lng": c.longitude or 0.0
                } for c in records
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-states-districts")
def get_all_states_districts():
    try:
        from app.database.crawler_service import INDIA_STATES_DISTRICTS
        # Return simple map of state -> list of districts
        result = {}
        for state, info in INDIA_STATES_DISTRICTS.items():
            result[state] = info.get("districts", [])
        return {"states_districts": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


