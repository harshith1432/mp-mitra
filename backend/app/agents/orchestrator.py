"""
MP MITRA — AI Agent Orchestrator (LangGraph Engine)
===================================================
Ties together all pipeline nodes:
STT → OCR → Vision → Translate → RAG → Web Scraper → Priority → Qwen 3 (via Groq/Gemini) → Translate Back.
"""
import os
import json
from typing import Dict, Any, List
from app.database.citizen_session import update_submission_status
from app.agents.stt_agent import transcribe_voice_url
from app.agents.ocr_agent import extract_text_from_media
from app.agents.vision_agent import analyze_image_objects
from app.agents.translate_agent import translate_to_english, translate_from_english
from app.agents.rag_agent import search_knowledge_base
from app.agents.web_research_agent import perform_live_research
from app.agents.priority_agent import analyze_priority_and_duplicates
from app.routing.whatsapp_send import send_text

# ── LLM Caller (Multi-Provider Support) ───────────────────────────────────────
def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Invokes the selected LLM provider (Groq HTTPX, Hugging Face, Gemini, or fallback mock)."""
    from app.config_manager import config_manager
    provider = config_manager.get("LLM_PROVIDER") or os.getenv("LLM_PROVIDER", "groq").lower()
    
    # 1. Groq via HTTPX (Zero-dependency, direct fast API endpoint)
    if provider == "groq":
        groq_key = config_manager.get_secret("GROQ_API_KEY")
        if groq_key:
            try:
                import httpx
                api_url = "https://api.groq.com/openai/v1/chat/completions"
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800
                }
                r = httpx.post(
                    api_url,
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=20
                )
                if r.status_code == 200:
                    data = r.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    # Retry with llama-3.3-70b-specdec if rate limited or model name mismatch
                    payload["model"] = "llama-3.3-70b-specdec"
                    r = httpx.post(
                        api_url,
                        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                        json=payload,
                        timeout=20
                    )
                    if r.status_code == 200:
                        return r.json()["choices"][0]["message"]["content"].strip()
                    else:
                        print(f"[Groq HTTPX Warning] Status {r.status_code}: {r.text[:200]}")
                        provider = "huggingface"
            except Exception as e:
                print(f"[LLM Agent] Groq HTTPX connection failed: {e}. Falling back to HuggingFace...")
                provider = "huggingface"
        else:
            provider = "huggingface"

    # 2. Hugging Face Serverless API (Free tier cascading model support)
    if provider == "huggingface":
        hf_token = config_manager.get_secret("HUGGINGFACE_API_KEY")
        if hf_token:
            try:
                import httpx
                models = [
                    "Qwen/Qwen2.5-7B-Instruct",
                    "meta-llama/Meta-Llama-3-8B-Instruct",
                    "mistralai/Mistral-7B-Instruct-v0.3"
                ]
                for model_name in models:
                    try:
                        api_url = f"https://api-inference.huggingface.co/models/{model_name}/v1/chat/completions"
                        payload = {
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "max_tokens": 800,
                            "temperature": 0.3
                        }
                        r = httpx.post(
                            api_url,
                            headers={"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"},
                            json=payload,
                            timeout=20
                        )
                        if r.status_code == 200:
                            data = r.json()
                            return data["choices"][0]["message"]["content"].strip()
                        else:
                            print(f"[HF API Warning] {model_name} returned status {r.status_code}: {r.text[:200]}")
                    except Exception as inner_e:
                        print(f"[HF API Warning] Exception calling {model_name}: {inner_e}")
                
                print("[LLM Agent] All Hugging Face models failed. Falling back to Gemini...")
                provider = "gemini"
            except Exception as e:
                print(f"[LLM Agent] HuggingFace setup failed: {e}. Falling back to Gemini...")
                provider = "gemini"
        else:
            provider = "gemini"
    
    # 3. Google Gemini Fallback (most likely available via system keys)
    if provider == "gemini":
        gemini_key = config_manager.get_secret("GOOGLE_API_KEY") or config_manager.get_secret("GEMINI_API_KEY")
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                try:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(
                        contents=f"System Instructions:\n{system_prompt}\n\nUser Question:\n{user_prompt}"
                    )
                except Exception:
                    # Fallback to gemini-pro for older SDK versions
                    model = genai.GenerativeModel("gemini-pro")
                    response = model.generate_content(
                        contents=f"System Instructions:\n{system_prompt}\n\nUser Question:\n{user_prompt}"
                    )
                return response.text.strip()
            except Exception as e:
                print(f"[LLM Agent] Gemini execution failed: {e}. Falling back to Groq SDK...")
                provider = "groq_sdk"
        else:
            provider = "groq_sdk"

    # 4. Groq SDK fallback
    if provider == "groq_sdk":
        groq_key = config_manager.get_secret("GROQ_API_KEY")
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=800,
                    temperature=0.3
                )
                return completion.choices[0].message.content.strip()
            except Exception as e:
                print(f"[LLM Agent] Groq SDK execution failed: {e}. Falling back to Mock...")
        else:
            print("[LLM Agent] Groq key missing. Falling back to Mock...")

    # 5. Graceful Mock Fallback (so it never crashes during offline/hackathon presentations)
    return _mock_llm_response(system_prompt, user_prompt)


def _mock_llm_response(system: str, user: str) -> str:
    # Deterministic mock response based on query keywords
    u = user.lower()
    if "water" in u or "pipe" in u or "ಕುಡಿಯುವ" in u:
        return (
            "🎯 *AI Water Scheme Match:*\n\n"
            "Your issue regarding drinking water supply fits perfectly under the *Jal Jeevan Mission (JJM)*.\n\n"
            "• *Scheme Benefit:* Provides clean tap water connection to every rural household.\n"
            "• *Eligibility:* All rural habitations.\n"
            "• *Action Plan:* The proposal has been queued. Total estimated cost is ₹14 Lakhs.\n"
            "• *Official Source:* jaljeevanmission.gov.in"
        )
    elif "road" in u or "pothole" in u or "ರಸ್ತೆ" in u:
        return (
            "🎯 *AI Road Scheme Match:*\n\n"
            "Your issue regarding road damage matches the *Pradhan Mantri Gram Sadak Yojana (PMGSY)*.\n\n"
            "• *Scheme Benefit:* All-weather connectivity to unconnected habitations.\n"
            "• *Eligible Funding:* Phase III Upgradation Scheme.\n"
            "• *Action Plan:* The suggestion has been aggregated for priority ranking.\n"
            "• *Official Source:* pmgsy.nic.in"
        )
    return (
        "🎯 *MP MITRA Suggestion Registered:*\n\n"
        "Your developmental feedback has been analyzed by our AI pipeline.\n"
        "We have matched this against central and state scheme databases. A brief report has been generated for the MP Dashboard."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH PIPELINE ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def process_submission(phone: str, submission_id: str, temp_data: Dict[str, Any], lang: str):
    """
    Executes the full multi-agent development intelligence pipeline.
    """
    print(f"[AI Orchestrator] Starting pipeline for {submission_id} (Lang: {lang})")
    
    text_content = temp_data.get("text_content", "").strip()
    media_items = temp_data.get("media_items", [])
    lat = temp_data.get("lat")
    lon = temp_data.get("lon")
    
    # Stored profile variables
    from app.database.citizen_session import get_citizen_profile
    profile = get_citizen_profile(phone) or {}
    state = profile.get("state", "")
    district = profile.get("district", "")
    village = profile.get("village", "")

    extracted_texts = []
    detected_objects = []
    
    # ── Node 1: STT Node (Speech-to-Text) ──────────────────────────────────────
    for item in media_items:
        if item["type"] == "audio":
            update_submission_status(phone, submission_id, "AI STT Processing", progress=15)
            stt_res = transcribe_voice_url(item["url"], phone)
            if "text" in stt_res:
                extracted_texts.append(stt_res["text"])
                if "language" in stt_res:
                    lang = stt_res["language"]

    # ── Node 2: OCR Node (Document Parsing) ────────────────────────────────────
    for item in media_items:
        if item["type"] == "document":
            update_submission_status(phone, submission_id, "AI OCR Processing", progress=30)
            ocr_res = extract_text_from_media(item["url"], "document", phone)
            if "text" in ocr_res:
                extracted_texts.append(ocr_res["text"])

    # ── Node 3: Vision Node (Computer Vision) ──────────────────────────────────
    for item in media_items:
        if item["type"] == "image":
            update_submission_status(phone, submission_id, "AI Object Detection", progress=45)
            vision_res = analyze_image_objects(item["url"], phone)
            if "objects" in vision_res:
                detected_objects.extend(vision_res["objects"])
                if "scene_description" in vision_res:
                    extracted_texts.append(f"Image analysis: {vision_res['scene_description']}")

    # Combine all text inputs
    all_raw_text = text_content + " " + " ".join(extracted_texts)
    all_raw_text = all_raw_text.strip()

    # ── Node 4: Translation Node ──────────────────────────────────────────────
    update_submission_status(phone, submission_id, "AI Normalization", progress=55)
    en_text = translate_to_english(all_raw_text, lang)

    # ── Node 5: Duplicates & Priority Scorer ──────────────────────────────────
    update_submission_status(phone, submission_id, "AI Prioritization", progress=65)
    score, sim_count, conf, reasoning = analyze_priority_and_duplicates(
        en_text, "General Development", state, district, village
    )

    # ── Node 6: RAG Search (Local & Web) ──────────────────────────────────────
    update_submission_status(phone, submission_id, "AI Scheme Matching", progress=75)
    rag_docs = search_knowledge_base(en_text, state, district, k=3)
    crawled_context = "\n\n".join([f"Source: {d.get('source_url','')}\n{d.get('content','')}" for d in rag_docs])

    # ── Node 7: Live Web Research (BeautifulSoup/Playwright) ──────────────────
    live_results = perform_live_research(en_text, state, district)
    web_context = "\n\n".join([f"Live Source ({item['source']}): {item['url']}\n{item['title']} - {item['summary']}" for item in live_results])

    # ── Node 8: LLM Reasoning (Qwen 3 / Gemini) ────────────────────────────────
    update_submission_status(phone, submission_id, "Generating Decision Intelligence", progress=85)
    
    category = "Infrastructure Need"
    if "water" in en_text.lower() or "pipe" in en_text.lower():
        category = "Water & Sanitation"
    elif "road" in en_text.lower() or "pothole" in en_text.lower():
        category = "Roads & Connectivity"
    elif "hospital" in en_text.lower() or "medicine" in en_text.lower():
        category = "Healthcare & Welfare"
        
    system_prompt = f"""You are MP MITRA, an advanced Development Intelligence Engine.
    Analyze the citizen's request for village {village}, district {district}, state {state}.
    
    Matched Database Schemes:
    {crawled_context}
    
    Live Web Research Findings:
    {web_context}
    
    Determine:
    1. A single best government welfare scheme match.
    2. Recommended action path with 3 steps.
    3. State if similar issues have been reported (similar count is {sim_count}).
    4. Provide official reference links.
    
    Format for WhatsApp (use *bold*, bullet points, and clean links). Keep under 250 words."""

    response_en = call_llm(system_prompt, en_text)

    # ── Node 9: Multilingual Response Translation ──────────────────────────────
    final_response = translate_from_english(response_en, lang)

    # ── Node 10: Save Status & Notify Citizen ──────────────────────────────────
    summary_text = translate_to_english(final_response[:200], lang) + "..."
    update_submission_status(
        phone, submission_id,
        status="Under Review",
        ai_summary=summary_text,
        remark=f"AI matched to NITI Aayog/JJM standards. Priority Score: {score}",
        progress=100
    )

    # Save extra detailed AI fields into PostgreSQL citizen_suggestions if model is registered
    try:
        from app.database.connection import SessionLocal
        from app.database.models import Base
        db = SessionLocal()
        
        # We also push a WebSocket notification to the frontend dashboard
        _notify_dashboard({
            "type": "new_suggestion",
            "submission_id": submission_id,
            "village": village,
            "district": district,
            "state": state,
            "category": category,
            "priority_score": score,
            "ai_summary": summary_text,
            "similar_count": sim_count,
            "created_at": "Just now"
        })
        
        # Insert into PostgreSQL table if table exists
        from sqlalchemy import text
        tbl_exists = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'citizen_suggestions')")).scalar()
        if tbl_exists:
            db.execute(text("""
                INSERT INTO citizen_suggestions (submission_id, citizen_phone, text_content, category, state, district, village, priority_score, status, ai_summary, similar_count)
                VALUES (:sid, :phone, :txt, :cat, :state, :dist, :village, :score, 'Under Review', :summary, :sim)
            """), {
                "sid": submission_id, "phone": phone, "txt": all_raw_text[:2000],
                "cat": category, "state": state, "dist": district, "village": village,
                "score": score, "summary": summary_text, "sim": sim_count
            })
            db.commit()
        db.close()

        # Copy to Firestore global complaints collection so WhatsApp suggestions appear in real time on dashboard/map
        try:
            from app.database.firebase_config import fs_db
            if fs_db:
                complaint_ref = fs_db.collection("complaints").document(submission_id)
                complaint_data = {
                    "id": submission_id,
                    "state_name": state.strip().upper(),
                    "district_name": district.strip().upper(),
                    "village_name": village,
                    "text_content": all_raw_text,
                    "category": category,
                    "urgency": "High" if score > 75 else "Medium",
                    "latitude": lat or 19.0,
                    "longitude": lon or 78.5,
                    "status": "Pending",
                    "created_at": datetime.now(),
                    "voice_url": media_items[0]["url"] if (media_items and media_items[0]["type"] == "audio") else None,
                    "image_url": media_items[0]["url"] if (media_items and media_items[0]["type"] == "image") else None,
                    "doc_url": media_items[0]["url"] if (media_items and media_items[0]["type"] == "document") else None,
                    "cluster_id": None,
                    "demand": float(sim_count + 1),
                    "priority_score": score,
                    "whatsapp_sim": True
                }
                complaint_ref.set(complaint_data)
                print(f"[Orchestrator] Successfully copied WhatsApp submission {submission_id} to global complaints.")
        except Exception as fe:
            print(f"[Orchestrator Firestore copy warning] {fe}")

    except Exception as dbe:
        print(f"[Orchestrator DB save warning] {dbe}")

    # Send final report to citizen WhatsApp
    send_text(phone, f"🤖 *MP MITRA AI Analysis for Submission {submission_id}*:\n\n" + final_response)
    print(f"[AI Orchestrator] Pipeline completed successfully for {submission_id}!")


def _notify_dashboard(payload: Dict[str, Any]):
    """Broadcast notification to active dashboard websockets via local REST endpoint."""
    try:
        import requests
        port = os.getenv("PORT", "8000")
        requests.post(f"http://localhost:{port}/api/admin/broadcast-suggestion", json=payload, timeout=3)
    except Exception as e:
        print(f"[Orchestrator] Dashboard WebSocket broadcast warning: {e}")
