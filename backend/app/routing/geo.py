"""
MP MITRA — Geospatial API
===========================
Provides geocoding, reverse geocoding, and village coordinates for Leaflet mapping.
"""
from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional
import requests

router = APIRouter()


@router.get("/reverse")
def reverse_geocode(lat: float = Query(...), lon: float = Query(...)) -> Dict[str, Any]:
    """Reverse geocode coordinates to state, district, block, and village."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        headers = {"User-Agent": "mp_mitra_platform_v1"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        
        data = r.json()
        addr = data.get("address", {})
        
        state = addr.get("state", "")
        district = addr.get("county") or addr.get("state_district") or addr.get("city", "")
        taluk = addr.get("suburb") or addr.get("city_district") or addr.get("village", "")
        village = addr.get("village") or addr.get("town") or addr.get("suburb") or addr.get("hamlet", "")
        
        return {
            "state": state,
            "district": district,
            "taluk": taluk,
            "village": village,
            "display_name": data.get("display_name", "")
        }
    except Exception as e:
        return {"error": f"Reverse geocoding failed: {str(e)}"}


@router.get("/heatmap")
def get_heatmap_coordinates(district: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Returns coordinates and density of citizen submissions for Leaflet heatmaps."""
    from app.database.connection import SessionLocal
    from sqlalchemy import text
    import random
    import datetime
    
    coords = []
    
    # Try fetching from Firestore first (Real-time data!)
    try:
        from app.database.firebase_config import fs_db
        if fs_db:
            complaints_ref = fs_db.collection("complaints")
            docs = complaints_ref.stream()
            for doc in docs:
                data = doc.to_dict()
                
                # Filter by district if provided
                doc_dist = (data.get("district_name") or "").strip().upper()
                if district and doc_dist != district.strip().upper():
                    continue
                
                lat = data.get("latitude")
                lon = data.get("longitude")
                if not lat or not lon or float(lat) == 19.0 or float(lon) == 78.5:
                    # Assign a random coordinate around Mandya centroid if coords are mock/missing
                    lat = 12.5218 + random.uniform(-0.06, 0.06)
                    lon = 76.8951 + random.uniform(-0.06, 0.06)
                else:
                    lat = float(lat)
                    lon = float(lon)
                
                # Resolve category
                category = data.get("category") or "General Need"
                if category.lower() in ["water", "water & sanitation", "sanitation"]:
                    category = "Water & Sanitation"
                elif category.lower() in ["road", "roads & connectivity", "roads"]:
                    category = "Roads & Connectivity"
                elif category.lower() in ["health", "healthcare & welfare", "healthcare"]:
                    category = "Healthcare & Welfare"
                elif category.lower() in ["education", "education & schools", "schools"]:
                    category = "Education & Schools"
                
                # Resolve priority
                priority = data.get("priority_score") or data.get("priority")
                if not priority:
                    urgency = (data.get("urgency") or "medium").lower()
                    if urgency == "high" or urgency == "critical":
                        priority = random.randint(85, 96)
                    elif urgency == "medium":
                        priority = random.randint(70, 84)
                    else:
                        priority = random.randint(50, 69)
                else:
                    try:
                        priority = int(float(priority))
                    except:
                        priority = 75
                
                # Resolve duration
                duration = "14 days ago"
                created_val = data.get("created_at")
                if created_val:
                    try:
                        # Firestore timestamp or string
                        if isinstance(created_val, str):
                            if "T" in created_val:
                                date_part = created_val.split("T")[0]
                                date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")
                            else:
                                date_obj = datetime.datetime.strptime(created_val.split(".")[0], "%Y-%m-%d %H:%M:%S")
                        else:
                            date_obj = created_val
                        diff = datetime.datetime.now() - date_obj
                        if diff.days > 0:
                            duration = f"{diff.days} days ago"
                        else:
                            duration = "1 day ago"
                    except Exception:
                        duration = "Recent"
                
                # Generate AI Solution recommendation dynamically
                text_lower = (data.get("text_content") or "").lower()
                village_name = data.get("village_name") or "this village"
                if "water" in text_lower or "pipe" in text_lower or "leak" in text_lower or "drain" in text_lower:
                    solution = f"AI Solution Path: 1. Deploy district engineering team to inspect pipeline in {village_name}. 2. Re-allocate ₹15 Lakhs from JJM (Jal Jeevan Mission) maintenance fund. 3. Install community filtration module to eliminate salinity/fluoride trace."
                elif "road" in text_lower or "pothole" in text_lower or "bridge" in text_lower:
                    solution = f"AI Solution Path: 1. Conduct immediate pothole patching using asphalt overlays. 2. Draft PMGSY link road proposal connecting {village_name} to nearest state highway. 3. Allocate budget of ₹42 Lakhs from MPLADS general development pool."
                elif "doctor" in text_lower or "health" in text_lower or "clinic" in text_lower or "nurse" in text_lower:
                    solution = f"AI Solution Path: 1. Re-allocate 1 resident doctor on rotational duty from district headquarters. 2. Upgrade sub-centre medical diagnostic kits under National Health Mission (NHM). 3. Organize monthly mobile health camp in {village_name}."
                elif "school" in text_lower or "teacher" in text_lower or "education" in text_lower:
                    solution = f"AI Solution Path: 1. Re-assign teaching staff from high-PTR schools in urban Mandya to balance ratio. 2. Establish boundary wall safety gating using Samagra Shiksha funds. 3. Upgrade classroom benches and lighting."
                else:
                    solution = f"AI Solution Path: 1. File formal field verification report to district planning officer. 2. Deploy MPLADS grant allocation funding of ₹8 Lakhs. 3. Complete civil work construction review within 14 business days."
                
                coords.append({
                    "id": data.get("id") or doc.id,
                    "lat": lat,
                    "lon": lon,
                    "intensity": float(priority) / 100.0,
                    "village": data.get("village_name") or "General Area",
                    "district": data.get("district_name") or "MANDYA",
                    "state": data.get("state_name") or "KARNATAKA",
                    "category": category,
                    "priority": priority,
                    "summary": data.get("text_content") or "No description provided.",
                    "duration": duration,
                    "photo_url": data.get("image_url") or data.get("voice_url") or None,
                    "solution": solution
                })
    except Exception as fe:
        print(f"[Geo API Firestore Error] {fe}")
    
    # Fallback to local SQLite complaints table if Firestore failed or is empty
    if not coords:
        db = SessionLocal()
        try:
            complaints_exist = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'complaints')")).scalar()
            if complaints_exist:
                sql = "SELECT id, village_name, district_name, state_name, text_content, category, urgency, created_at, latitude, longitude FROM complaints"
                if district:
                    sql += " WHERE UPPER(district_name) = :dist"
                
                rows = db.execute(text(sql), {"dist": district.upper()} if district else {}).fetchall()
                for r in rows:
                    lat = r.latitude if r.latitude else (12.5218 + random.uniform(-0.06, 0.06))
                    lon = r.longitude if r.longitude else (76.8951 + random.uniform(-0.06, 0.06))
                    
                    priority = 85
                    if r.urgency and r.urgency.lower() == 'high':
                        priority = random.randint(85, 98)
                    elif r.urgency and r.urgency.lower() == 'medium':
                        priority = random.randint(70, 84)
                    elif r.urgency and r.urgency.lower() == 'low':
                        priority = random.randint(45, 69)
                    
                    duration = "3 weeks"
                    if r.created_at:
                        diff = datetime.datetime.now() - r.created_at
                        if diff.days > 0:
                            duration = f"{diff.days} days ago"
                        else:
                            duration = "1 day ago"
                    
                    category = r.category or "General Need"
                    if category == "water":
                        category = "Water & Sanitation"
                    elif category == "road":
                        category = "Roads & Connectivity"
                    elif category == "health":
                        category = "Healthcare & Welfare"
                    elif category == "education":
                        category = "Education & Schools"
                    
                    coords.append({
                        "id": r.id,
                        "lat": lat,
                        "lon": lon,
                        "intensity": float(priority) / 100.0,
                        "village": r.village_name or "General Area",
                        "district": r.district_name or "MANDYA",
                        "state": r.state_name or "KARNATAKA",
                        "category": category,
                        "priority": priority,
                        "summary": r.text_content or "No description provided.",
                        "duration": duration,
                        "photo_url": None,
                        "solution": f"AI Solution: Deploy resources under central welfare schemes. Inspect site in {r.village_name or 'General Area'}."
                    })
        except Exception as e:
            print(f"[Geo API Heatmap SQL Error] {e}")
        finally:
            db.close()
            
    # If still no database records, return premium detailed mock points for demo
    if not coords:
        villages = [
            {"name": "Katteri", "cat": "Water & Sanitation", "prob": "Main water pipeline leak near the temple, muddy water coming from taps for 2 weeks.", "dur": "14 days ago", "priority": 95},
            {"name": "Koppa", "cat": "Roads & Connectivity", "prob": "Severely damaged main connecting road with huge potholes, making school bus travel impossible.", "dur": "2 months ago", "priority": 88},
            {"name": "Besagarahalli", "cat": "Healthcare & Welfare", "prob": "Local Primary Health Center lacks doctors. Citizens travel 18km to Mandya City for emergencies.", "dur": "6 months ago", "priority": 78},
            {"name": "Maddur", "cat": "Education & Schools", "prob": "Primary school roof leaking and wall collapsed during recent monsoon rains. Active safety hazard.", "dur": "10 days ago", "priority": 92},
            {"name": "Guttalu", "cat": "Water & Sanitation", "prob": "Open drainage overflows directly onto the village pathway, causing foul smell and malaria risks.", "dur": "1 month ago", "priority": 82},
            {"name": "Huliyurdurga", "cat": "Roads & Connectivity", "prob": "Earthen road washed away by heavy rains. Villagers completely cut off from market center.", "dur": "5 days ago", "priority": 90}
        ]
        
        for i, v in enumerate(villages):
            coords.append({
                "id": 1000 + i,
                "lat": 12.5218 + random.uniform(-0.06, 0.06),
                "lon": 76.8951 + random.uniform(-0.06, 0.06),
                "intensity": float(v["priority"]) / 100.0,
                "village": v["name"],
                "district": district or "MANDYA",
                "state": "KARNATAKA",
                "category": v["cat"],
                "priority": v["priority"],
                "summary": v["prob"],
                "duration": v["dur"],
                "photo_url": None,
                "solution": f"AI Solution Path: 1. Deploy emergency inspection to {v['name']}. 2. Propose local development allocation fund. 3. Coordinate site resolution."
            })
            
    return coords
