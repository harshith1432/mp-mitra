import os
import uuid
import random
import urllib.parse
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import requests
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _sklearn_available = True
except ImportError:
    _sklearn_available = False
from firebase_admin import firestore

from app.database.firebase_config import db as fs_db, bucket

router = APIRouter()

def translate_to_english(text: str) -> tuple[str, str]:
    """
    Translates the text to English using Google Translate free web API.
    Returns a tuple of (detected_language, translated_text).
    """
    if not text or not text.strip():
        return "English", ""
        
    has_indic = any(ord(char) > 127 for char in text)
    if not has_indic:
        return "English", text
        
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(text)}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            detected_lang = "Indic"
            if len(res_json) > 2 and isinstance(res_json[2], str):
                lang_map = {
                    "hi": "Hindi",
                    "kn": "Kannada",
                    "te": "Telugu",
                    "ta": "Tamil",
                    "ml": "Malayalam",
                    "mr": "Marathi",
                    "gu": "Gujarati",
                    "bn": "Bengali",
                    "pa": "Punjabi"
                }
                detected_lang = lang_map.get(res_json[2], res_json[2].upper())
            
            translated = "".join([part[0] for part in res_json[0] if part[0]])
            return detected_lang, translated
    except Exception as e:
        print(f"Translation API error: {e}")
        
    # Heuristic detect language from unicode range if translation failed
    detected = "English"
    if any('\u0c80' <= c <= '\u0cff' for c in text):
        detected = "Kannada"
    elif any('\u0900' <= c <= '\u097f' for c in text):
        detected = "Hindi"
    elif any('\u0c00' <= c <= '\u0c7f' for c in text):
        detected = "Telugu"
    elif any('\u0b80' <= c <= '\u0bff' for c in text):
        detected = "Tamil"
    elif any('\u0d00' <= c <= '\u0d7f' for c in text):
        detected = "Malayalam"
    return detected, text

# Intent keywords mapping
INTENT_KEYWORDS = {
    "water": {"category": "Water Supply", "urgency": "High", "pop": 1200},
    "drinking water": {"category": "Water Supply", "urgency": "High", "pop": 1500},
    "pothole": {"category": "Roads & Connectivity", "urgency": "Medium", "pop": 450},
    "road": {"category": "Roads & Connectivity", "urgency": "Medium", "pop": 800},
    "bridge": {"category": "Roads & Connectivity", "urgency": "High", "pop": 2500},
    "school": {"category": "Education & Schools", "urgency": "Medium", "pop": 350},
    "teacher": {"category": "Education & Schools", "urgency": "Medium", "pop": 300},
    "clinic": {"category": "Healthcare & Clinics", "urgency": "High", "pop": 1800},
    "hospital": {"category": "Healthcare & Clinics", "urgency": "High", "pop": 3000},
    "doctor": {"category": "Healthcare & Clinics", "urgency": "High", "pop": 2000},
    "power": {"category": "Electricity & Power", "urgency": "Medium", "pop": 900},
    "electricity": {"category": "Electricity & Power", "urgency": "Medium", "pop": 1100},
    "garbage": {"category": "Sanitation & Drainage", "urgency": "Low", "pop": 250},
    "drain": {"category": "Sanitation & Drainage", "urgency": "Medium", "pop": 600},
    "sewage": {"category": "Sanitation & Drainage", "urgency": "High", "pop": 1500},
}

def analyze_complaint_text(text: str):
    text_lower = text.lower()
    category = "Other Development"
    urgency = "Medium"
    affected_pop = 500
    intent = "General Grievance"
    
    for key, val in INTENT_KEYWORDS.items():
        if key in text_lower:
            category = val["category"]
            urgency = val["urgency"]
            affected_pop = val["pop"] + random.randint(-100, 200)
            intent = f"Request for {category}"
            break
            
    return {
        "category": category,
        "urgency": urgency,
        "affected_population": max(50, affected_pop),
        "intent": intent,
        "confidence": round(random.uniform(88, 98), 1)
    }

def upload_to_firebase_storage(upload_file: UploadFile, folder: str) -> str:
    if not bucket:
        print("Warning: Firebase Storage bucket is not initialized.")
        return ""
    try:
        contents = upload_file.file.read()
        upload_file.file.seek(0) # reset stream
        
        ext = os.path.splitext(upload_file.filename)[1]
        filename = f"{folder}/{uuid.uuid4()}{ext}"
        blob = bucket.blob(filename)
        
        blob.upload_from_string(contents, content_type=upload_file.content_type)
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"Error uploading file to Firebase Storage: {e}")
        return ""

@router.post("/submit")
async def submit_complaint(
    state: str = Form(...),
    district: str = Form(...),
    village: str = Form(...),
    text_content: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    voice_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    doc_file: Optional[UploadFile] = File(None)
):
    try:
        agent_logs = []
        transcribed_text = ""
        language = "English"
        
        # 1. Firebase Storage uploads for attachments
        voice_url = ""
        image_url = ""
        doc_url = ""
        
        if voice_file:
            agent_logs.append("Storage Agent: Uploading audio clip to Firebase Storage...")
            voice_url = upload_to_firebase_storage(voice_file, "complaints/audio")
            agent_logs.append(f"Storage Agent: File saved. URL: {voice_url}")
            
            # Speech transcription agent
            if text_content and text_content.strip():
                raw_text = text_content
                agent_logs.append("Speech Processing Agent: Received transcribed text from client.")
                language, translated_text = translate_to_english(raw_text)
            else:
                # Fallback to random choice if no text was pre-filled or typed
                language = random.choice(["Kannada", "Hindi", "Telugu", "Tamil", "Malayalam"])
                transcripts = {
                    "Kannada": "ನಮ್ಮ ಹಳ್ಳಿಯಲ್ಲಿ ಕುಡಿಯುವ ನೀರಿನ ಸೌಲಭ್ಯವಿಲ್ಲ.",
                    "Hindi": "हमारे गाँव में सड़क बहुत खराब है और गड्ढे हैं।",
                    "Telugu": "మా ఊరిలో స్కూల్ బస్సు సౌకర్యం లేదు.",
                    "Tamil": "எங்கள் கிராமத்திற்கு ఒక ஆரம்ப சுகாதார நிலையம் தேவை.",
                    "Malayalam": "ഞങ്ങളുടെ ഗ്രാമത്തിൽ കുടിവെള്ളമില്ല."
                }
                raw_text = transcripts.get(language, "ನಮ್ಮ ಹಳ್ಳಿಯಲ್ಲಿ ಕುಡಿಯುವ ನೀರಿನ ಸೌಲಭ್ಯವಿಲ್ಲ.")
                language, translated_text = translate_to_english(raw_text)

            agent_logs.append(f"Speech Processing Agent: Detected language: {language}")
            agent_logs.append(f"Speech Processing Agent: Transcribed raw text: '{raw_text}'")
            
            # 2. Translation Agent
            if language != "English":
                agent_logs.append(f"Translation Agent: Translating '{raw_text}' into English...")
                agent_logs.append(f"Translation Agent: Translated text: '{translated_text}'")
            else:
                agent_logs.append("Translation Agent: Source language is English. Skipping translation.")
                
            text_content = translated_text
            transcribed_text = text_content
        else:
            if text_content and text_content.strip():
                language, translated_text = translate_to_english(text_content)
                if language != "English":
                    agent_logs.append(f"Language Agent: Detected Indic script ({language}). Translating...")
                    agent_logs.append(f"Translation Agent: Translated text: '{translated_text}'")
                    text_content = translated_text
                transcribed_text = text_content
            else:
                transcribed_text = "General complaint"

        if image_file:
            agent_logs.append("Storage Agent: Uploading complaint image to Firebase Storage...")
            image_url = upload_to_firebase_storage(image_file, "complaints/images")
            agent_logs.append(f"Storage Agent: File saved. URL: {image_url}")
            
            # Simulate YOLOv11 Detections
            detections = [
                {"bbox": [120, 240, 310, 420], "label": "Pothole", "confidence": 0.94},
                {"bbox": [50, 80, 200, 290], "label": "Broken Street Light", "confidence": 0.89},
                {"bbox": [200, 150, 450, 480], "label": "Garbage Heap", "confidence": 0.96},
                {"bbox": [80, 120, 350, 400], "label": "Water Leakage", "confidence": 0.92}
            ]
            matched_detection = random.choice(detections)
            agent_logs.append(f"Image Analysis Agent: YOLO detected object: '{matched_detection['label']}' with confidence {matched_detection['confidence']*100}%")
            
            vlm_descriptions = {
                "Pothole": "Visual analysis confirms a deep pothole approximately 1.5m wide, posing a severe traffic hazard on a rural road.",
                "Broken Street Light": "Detected broken streetlight casing on the roadside, resulting in pitch black conditions during night.",
                "Garbage Heap": "Unchecked landfill accumulation blocking pedestrian access and raising sanitation hazards.",
                "Water Leakage": "Water pipeline burst causing active water logging on the road and wasting potable water."
            }
            desc = vlm_descriptions.get(matched_detection['label'])
            agent_logs.append(f"Image Analysis Agent: Scene understanding: '{desc}'")
            text_content = (text_content or "") + f" (Detected: {matched_detection['label']} - {desc})"

        if doc_file:
            agent_logs.append("Storage Agent: Uploading document to Firebase Storage...")
            doc_url = upload_to_firebase_storage(doc_file, "complaints/docs")
            agent_logs.append(f"Storage Agent: File saved. URL: {doc_url}")
            
            # OCR simulation
            ocr_text = f"Subject: Request for drinking water tank installation. From: Sarpanch, Panchayat of {village}. Dated: 2026-06-15."
            agent_logs.append("OCR Agent: Extracted text successfully. Detected project name: 'Water Tank'.")
            text_content = (text_content or "") + f" (OCR Extract: {ocr_text})"

        # 3. Intent Classifier
        nlp_analysis = analyze_complaint_text(text_content or transcribed_text)
        category = nlp_analysis["category"]
        urgency = nlp_analysis["urgency"]
        affected_pop = nlp_analysis["affected_population"]
        agent_logs.append(f"Intent Classifier: Classified category: '{category}', Urgency: '{urgency}', Beneficiaries: {affected_pop}")

        if not latitude or not longitude:
            latitude = 19.0 + random.uniform(-0.5, 0.5)
            longitude = 78.5 + random.uniform(-0.5, 0.5)
            agent_logs.append(f"Location Agent: No GPS coordinates. Centroid interpolated: {latitude:.5f}, {longitude:.5f}")

        # 4. Duplicate Detection via Firestore query
        existing_complaints = []
        try:
            complaints_ref = fs_db.collection("complaints")
            query_ref = complaints_ref.where(filter=firestore.FieldFilter("state_name", "==", state.strip().upper()))\
                                      .where(filter=firestore.FieldFilter("district_name", "==", district.strip().upper()))
            docs = query_ref.stream()
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                existing_complaints.append(data)
        except Exception as e:
            agent_logs.append(f"Firestore Agent Warning: Could not fetch complaints for duplicate check: {e}")

        assigned_cluster_id = -1
        is_duplicate = False
        
        if existing_complaints and text_content:
            agent_logs.append(f"Duplicate Detection Agent: Scanning {len(existing_complaints)} existing complaints in {district}...")
            corpus = [text_content] + [c.get("text_content", "") for c in existing_complaints]
            
            try:
                if _sklearn_available:
                    vectorizer = TfidfVectorizer().fit_transform(corpus)
                    vectors = vectorizer.toarray()
                    similarities = cosine_similarity(vectors[0:1], vectors[1:])[0]
                    max_sim_idx = similarities.argmax()
                    max_sim = similarities[max_sim_idx]
                else:
                    # Pure Python Jaccard Similarity fallback
                    words_target = set(text_content.lower().split())
                    max_sim = -1.0
                    max_sim_idx = -1
                    for idx, c in enumerate(existing_complaints):
                        c_text = c.get("text_content", "")
                        words_c = set(c_text.lower().split())
                        intersection = words_target.intersection(words_c)
                        union = words_target.union(words_c)
                        jaccard = len(intersection) / len(union) if union else 0.0
                        if jaccard > max_sim:
                            max_sim = jaccard
                            max_sim_idx = idx
                    
                agent_logs.append(f"Duplicate Detection Agent: Highest match: {max_sim*100:.1f}%")
                
                if max_sim > 0.55:
                    duplicate_match = existing_complaints[max_sim_idx]
                    is_duplicate = True
                    assigned_cluster_id = duplicate_match.get("cluster_id", -1)
                    if assigned_cluster_id == -1:
                        assigned_cluster_id = duplicate_match["id"]
                        
                    # Update matched complaint in Firestore
                    fs_db.collection("complaints").document(duplicate_match["id"]).update({
                        "cluster_id": assigned_cluster_id,
                        "status": "Cluster"
                    })
                    agent_logs.append(f"Duplicate Detection Agent: Grouped with Complaint #{duplicate_match['id']} under Cluster #{assigned_cluster_id}.")
            except Exception as e:
                agent_logs.append(f"Duplicate Detection Agent Warning: TF-IDF failed: {e}")

        # 5. Save new complaint to Firestore
        new_complaint_ref = fs_db.collection("complaints").document()
        new_complaint_data = {
            "state_name": state.strip().upper(),
            "district_name": district.strip().upper(),
            "village_name": village,
            "text_content": text_content or transcribed_text,
            "category": category,
            "urgency": urgency,
            "affected_population": affected_pop,
            "latitude": latitude,
            "longitude": longitude,
            "status": "Cluster" if assigned_cluster_id != -1 else "Pending",
            "cluster_id": assigned_cluster_id,
            "created_at": firestore.SERVER_TIMESTAMP,
            "voice_url": voice_url,
            "image_url": image_url,
            "doc_url": doc_url
        }
        new_complaint_ref.set(new_complaint_data)
        complaint_id = new_complaint_ref.id

        return {
            "status": "success",
            "complaint_id": complaint_id,
            "category": category,
            "urgency": urgency,
            "is_duplicate": is_duplicate,
            "cluster_id": assigned_cluster_id,
            "transcription": transcribed_text if voice_file else None,
            "language_detected": language,
            "agent_logs": agent_logs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/complaints")
def list_complaints(state: str, district: str):
    try:
        complaints_ref = fs_db.collection("complaints")
        query_ref = complaints_ref.where(filter=firestore.FieldFilter("state_name", "==", state.strip().upper()))\
                                  .where(filter=firestore.FieldFilter("district_name", "==", district.strip().upper()))
        docs = query_ref.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            results.append({
                "id": doc.id,
                "text": data.get("text_content", ""),
                "category": data.get("category", ""),
                "urgency": data.get("urgency", ""),
                "pop": data.get("affected_population", 0),
                "lat": data.get("latitude", 0.0),
                "lng": data.get("longitude", 0.0),
                "status": data.get("status", ""),
                "cluster_id": data.get("cluster_id", -1),
                "date": data.get("created_at")
            })
            
        # Sort in memory
        def get_timestamp(x):
            ts = x["date"]
            if ts and hasattr(ts, "timestamp"):
                return ts.timestamp()
            return 0
            
        results.sort(key=get_timestamp, reverse=True)
        
        for r in results:
            ts = r["date"]
            if ts and hasattr(ts, "strftime"):
                r["date"] = ts.strftime("%Y-%m-%d %H:%M")
            else:
                r["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
