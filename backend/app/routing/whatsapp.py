"""
MP MITRA — WhatsApp Webhook Router
====================================
Handles:
1. Twilio Sandbox webhook (POST /api/whatsapp/webhook/twilio)
2. Meta Cloud API webhook (GET/POST /api/whatsapp/webhook/meta)
3. Simulator polling for frontend demo (GET/POST /api/whatsapp/simulator/*)
"""
from fastapi import APIRouter, Request, Response, Form, Query, BackgroundTasks
from typing import Optional, Dict, Any
import json
from app.agents.conversation import handle_message
from app.routing.whatsapp_send import get_simulator_messages

router = APIRouter()

def run_buffered_task(target_phone_number: str, func, *args, **kwargs):
    from app.routing.whatsapp_send import start_buffering, flush_buffering
    start_buffering(target_phone_number)
    try:
        return func(*args, **kwargs)
    finally:
        flush_buffering()

# ═══════════════════════════════════════════════════════════════════════════════
# 1. TWILIO WEBHOOK
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/webhook/twilio")
async def twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    NumMedia: int = Form(0),
    Latitude: Optional[float] = Form(None),
    Longitude: Optional[float] = Form(None)
):
    # Parse sender phone: "whatsapp:+919876543210" -> "+919876543210"
    phone = From.replace("whatsapp:", "").strip()
    
    # Extract media if present
    media_url = None
    msg_type = "text"
    
    if NumMedia > 0:
        form_data = await request.form()
        media_url = form_data.get("MediaUrl0")
        content_type = form_data.get("MediaContentType0", "")
        if "audio" in content_type:
            msg_type = "audio"
        elif "image" in content_type:
            msg_type = "image"
        elif "video" in content_type:
            msg_type = "video"
        else:
            msg_type = "document"

    if Latitude is not None and Longitude is not None:
        msg_type = "location"

    content = Body if msg_type == "text" else ""
    
    # Process message in background to respond immediately to Twilio (avoid timeouts)
    background_tasks.add_task(
        run_buffered_task,
        phone,
        handle_message,
        phone=phone,
        msg_type=msg_type,
        content=content,
        media_url=media_url,
        latitude=Latitude,
        longitude=Longitude
    )
    
    # Return empty response to Twilio
    return Response(content="<Response></Response>", media_type="application/xml")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. META CLOUD API WEBHOOK
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/webhook/meta")
def meta_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    import os
    expected_token = os.getenv("META_VERIFY_TOKEN", "mp_mitra_verify_2024")
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Verification failed", status_code=403)


@router.post("/webhook/meta")
async def meta_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        message = value.get("messages", [{}])[0]
        
        if message:
            phone = message.get("from")  # e.g. "919876543210"
            if not phone.startswith("+"):
                phone = f"+{phone}"
                
            msg_type = message.get("type", "text")
            content = ""
            media_url = None
            lat = None
            lon = None
            
            if msg_type == "text":
                content = message.get("text", {}).get("body", "")
            elif msg_type == "interactive":
                interactive = message.get("interactive", {})
                int_type = interactive.get("type")
                if int_type == "button_reply":
                    content = interactive.get("button_reply", {}).get("id", "")
                elif int_type == "list_reply":
                    content = interactive.get("list_reply", {}).get("id", "")
            elif msg_type == "location":
                loc = message.get("location", {})
                lat = loc.get("latitude")
                lon = loc.get("longitude")
            elif msg_type in ("image", "audio", "video", "document"):
                # Meta Cloud API media requires fetching the URL first using the Media ID
                media_id = message.get(msg_type, {}).get("id")
                # For demo simplicity, store ID as media_url or fetch via background helper
                media_url = f"https://graph.facebook.com/v19.0/{media_id}"
                
            background_tasks.add_task(
                run_buffered_task,
                phone,
                handle_message,
                phone=phone,
                msg_type=msg_type,
                content=content,
                media_url=media_url,
                latitude=lat,
                longitude=lon
            )
    except Exception as e:
        print(f"[Meta Webhook Error] {e}")
        
    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. WEB SIMULATOR (FOR DEV / DEMO)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/simulator/messages")
def simulator_messages(phone: str = Query(...)):
    """Poll this endpoint to retrieve bot responses for the simulator UI."""
    return {"messages": get_simulator_messages(phone)}


class SimulatorMsgRequest(Dict[str, Any]):
    pass

@router.post("/simulator/message")
async def simulator_receive(request: Request, background_tasks: BackgroundTasks):
    """Simulate a citizen sending a message to the bot."""
    body = await request.json()
    phone = body.get("phone", "").strip()
    msg_type = body.get("msg_type", "text")
    content = body.get("content", "")
    media_url = body.get("media_url")
    lat = body.get("lat")
    lon = body.get("lon")
    
    if not phone:
        return {"error": "phone is required"}
        
    # Process message in background
    background_tasks.add_task(
        run_buffered_task,
        phone,
        handle_message,
        phone=phone,
        msg_type=msg_type,
        content=content,
        media_url=media_url,
        latitude=lat,
        longitude=lon
    )
    
    return {"status": "processing"}


# ═══════════════════════════════════════════════════════════════════════════════
# 4. WEB SELECTOR FOR TWILIO WEBHOOKS (MOCK INTERACTIVE MENUS)
# ═══════════════════════════════════════════════════════════════════════════════
from fastapi.responses import HTMLResponse
from app.routing.whatsapp_send import _pending_options
from pydantic import BaseModel

from pydantic import BaseModel

class SelectSubmitRequest(BaseModel):
    phone: str
    selected_id: str
    state: Optional[str] = None
    district: Optional[str] = None
    block: Optional[str] = None
    village: Optional[str] = None

@router.get("/select", response_class=HTMLResponse)
def select_page(phone: str = Query(...)):
    # HTML template with outfit/inter fonts, search box, location dropdowns, and mobile responsive card design
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MP MITRA - Selection</title>
    <meta property="og:title" content="🔗 Click to Select Options" />
    <meta property="og:description" content="Select language/location to continue your conversation on WhatsApp." />
    <meta property="og:type" content="website" />
    <meta property="og:image" content="https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Emblem_of_India.svg/200px-Emblem_of_India.svg.png" />
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background: #F5F7FA;
            color: #1a1a1a;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 90vh;
        }
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0, 59, 122, 0.08);
            border: 1px solid #DDE1E7;
            padding: 24px;
            width: 100%;
            max-width: 400px;
            text-align: center;
            box-sizing: border-box;
        }
        .logo {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            color: #003B7A;
            font-size: 22px;
            margin-bottom: 4px;
        }
        .subtitle {
            font-size: 10px;
            text-transform: uppercase;
            color: #FF6B1A;
            font-weight: 700;
            letter-spacing: 0.06em;
            margin-bottom: 24px;
        }
        h2 {
            font-size: 15px;
            color: #2D3748;
            margin-bottom: 20px;
            line-height: 1.5;
            font-weight: 600;
        }
        .search-box {
            width: 100%;
            padding: 12px 14px;
            margin-bottom: 16px;
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            border-radius: 10px;
            font-size: 13.5px;
            color: #1E293B;
            box-sizing: border-box;
            font-family: inherit;
            outline: none;
            transition: all 0.2s ease;
            text-align: left;
        }
        .search-box:focus {
            background: white;
            border-color: #003B7A;
            box-shadow: 0 0 0 3px rgba(0, 59, 122, 0.1);
        }
        .options-container {
            max-height: 320px;
            overflow-y: auto;
            padding-right: 4px;
        }
        .option-btn {
            display: block;
            width: 100%;
            padding: 14px;
            margin: 8px 0;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            font-size: 13.5px;
            font-weight: 600;
            color: #0F172A;
            cursor: pointer;
            text-align: left;
            transition: all 0.2s ease;
            box-sizing: border-box;
        }
        .option-btn:hover {
            background: #EEF3FA;
            border-color: #003B7A;
            color: #003B7A;
        }
        
        /* Dropdown selection styles */
        .dropdown-label {
            display: block;
            text-align: left;
            font-size: 12.5px;
            font-weight: 600;
            color: #475569;
            margin-top: 14px;
            margin-bottom: 6px;
        }
        .dropdown-select {
            width: 100%;
            padding: 12px 14px;
            background: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-radius: 10px;
            font-size: 13.5px;
            color: #0F172A;
            box-sizing: border-box;
            font-family: inherit;
            outline: none;
            cursor: pointer;
            transition: all 0.2s ease;
            appearance: none;
            background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right 14px center;
            background-size: 16px;
            padding-right: 40px;
        }
        .dropdown-select:focus {
            background-color: white;
            border-color: #003B7A;
            box-shadow: 0 0 0 3px rgba(0, 59, 122, 0.1);
        }
        .dropdown-select:disabled {
            background-color: #F1F5F9;
            border-color: #E2E8F0;
            color: #94A3B8;
            cursor: not-allowed;
        }
        .submit-btn {
            display: block;
            width: 100%;
            padding: 14px;
            margin-top: 24px;
            background: #003B7A;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 700;
            color: white;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .submit-btn:disabled {
            background: #E2E8F0;
            color: #94A3B8;
            cursor: not-allowed;
        }
        .submit-btn:not(:disabled):hover {
            background: #00254D;
        }
        
        .success-card {
            display: none;
            text-align: center;
        }
        .success-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        .success-title {
            font-size: 18px;
            font-weight: 700;
            color: #138808;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container" id="main-card">
        <div class="logo">MP MITRA</div>
        <div class="subtitle">AI Citizen Engagement</div>
        <h2 id="prompt-body">Loading choices...</h2>
        <input type="text" id="search-input" placeholder="🔍 Search..." class="search-box" style="display: none;" oninput="filterOptions()">
        <div class="options-container" id="options-list"></div>
    </div>
    
    <div class="container" id="geo-card" style="display: none;">
        <div class="logo">MP MITRA</div>
        <div class="subtitle">Location Setup</div>
        <h2 style="margin-bottom: 10px;">Select your location:</h2>
        <p style="font-size: 12px; color: #64748B; margin-top:0; margin-bottom: 20px;">Personalize your scheme discovery and amenities tracking.</p>
        
        <label class="dropdown-label">State</label>
        <select id="state-select" class="dropdown-select" onchange="onStateChange()">
            <option value="">-- Choose State --</option>
        </select>
        
        <label class="dropdown-label">District</label>
        <select id="district-select" class="dropdown-select" disabled onchange="onDistrictChange()">
            <option value="">-- Choose District --</option>
        </select>
        
        <label class="dropdown-label">Block / Taluk</label>
        <select id="block-select" class="dropdown-select" disabled onchange="onBlockChange()">
            <option value="">-- Choose Block --</option>
        </select>
        
        <label class="dropdown-label">Village / Town</label>
        <select id="village-select" class="dropdown-select" disabled>
            <option value="">-- Choose Village --</option>
        </select>
        
        <button id="submit-geo-btn" class="submit-btn" disabled onclick="submitGeo()">Submit Location</button>
    </div>
    
    <div class="container success-card" id="success-card">
        <div class="success-icon">✅</div>
        <div class="success-title">Location Setup Complete!</div>
        <p style="font-size:13px; color:#64748B; line-height:1.5;">You can now close this tab and return to WhatsApp. We have loaded your dashboard and menu options!</p>
    </div>

    <script>
        const phone = new URLSearchParams(window.location.search).get('phone');
        let allOptions = [];
        
        async function loadOptions() {
            try {
                const res = await fetch(`/api/whatsapp/select-options?phone=` + encodeURIComponent(phone));
                const data = await res.json();
                if (!data || (!data.options && !data.is_geo)) {
                    document.getElementById('prompt-body').innerText = "No pending choices found for this session.";
                    return;
                }
                
                if (data.is_geo) {
                    document.getElementById('main-card').style.display = 'none';
                    document.getElementById('geo-card').style.display = 'block';
                    
                    const stateSel = document.getElementById('state-select');
                    data.options.forEach(opt => {
                        const op = document.createElement('option');
                        op.value = opt.title;
                        op.innerText = opt.title;
                        stateSel.appendChild(op);
                    });
                } else {
                    document.getElementById('prompt-body').innerText = data.body || "Please select an option:";
                    allOptions = data.options || [];
                    
                    // Show search bar if options count is greater than 5
                    const searchInput = document.getElementById('search-input');
                    if (allOptions.length > 5) {
                        searchInput.style.display = 'block';
                        setTimeout(() => searchInput.focus(), 100);
                    } else {
                        searchInput.style.display = 'none';
                    }
                    
                    renderOptions(allOptions);
                }
            } catch (err) {
                document.getElementById('prompt-body').innerText = "Error loading choices. Please try again.";
            }
        }
        
        function renderOptions(options) {
            const list = document.getElementById('options-list');
            list.innerHTML = "";
            options.forEach(opt => {
                const btn = document.createElement('button');
                btn.className = "option-btn";
                btn.innerText = opt.title;
                btn.onclick = () => submitChoice(opt.id);
                list.appendChild(btn);
            });
        }
        
        function filterOptions() {
            const query = document.getElementById('search-input').value.toLowerCase();
            const filtered = allOptions.filter(opt => opt.title.toLowerCase().includes(query));
            renderOptions(filtered);
        }
        
        async function submitChoice(id) {
            try {
                const res = await fetch(`/api/whatsapp/select-submit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone, selected_id: id })
                });
                const data = await res.json();
                if (data.status === "ok") {
                    document.getElementById('main-card').style.display = 'none';
                    document.getElementById('success-card').style.display = 'block';
                } else {
                    alert("Submission failed. Please try again.");
                }
            } catch (err) {
                alert("Error submitting choice. Please check connection.");
            }
        }
        
        async function onStateChange() {
            const state = document.getElementById('state-select').value;
            const distSel = document.getElementById('district-select');
            const blockSel = document.getElementById('block-select');
            const villSel = document.getElementById('village-select');
            const btn = document.getElementById('submit-geo-btn');
            
            // Reset downstream
            distSel.innerHTML = '<option value="">-- Choose District --</option>';
            distSel.disabled = true;
            blockSel.innerHTML = '<option value="">-- Choose Block --</option>';
            blockSel.disabled = true;
            villSel.innerHTML = '<option value="">-- Choose Village --</option>';
            villSel.disabled = true;
            btn.disabled = true;
            
            if (!state) return;
            
            try {
                const res = await fetch(`/api/constituency/districts?state=` + encodeURIComponent(state));
                const data = await res.json();
                if (data.districts) {
                    data.districts.forEach(d => {
                        const op = document.createElement('option');
                        op.value = d;
                        op.innerText = d;
                        distSel.appendChild(op);
                    });
                    distSel.disabled = false;
                }
            } catch (e) {}
        }
        
        async function onDistrictChange() {
            const state = document.getElementById('state-select').value;
            const district = document.getElementById('district-select').value;
            const blockSel = document.getElementById('block-select');
            const villSel = document.getElementById('village-select');
            const btn = document.getElementById('submit-geo-btn');
            
            blockSel.innerHTML = '<option value="">-- Choose Block --</option>';
            blockSel.disabled = true;
            villSel.innerHTML = '<option value="">-- Choose Village --</option>';
            villSel.disabled = true;
            btn.disabled = true;
            
            if (!district) return;
            
            try {
                const res = await fetch(`/api/constituency/blocks?state=` + encodeURIComponent(state) + `&district=` + encodeURIComponent(district));
                const data = await res.json();
                if (data.blocks) {
                    data.blocks.forEach(b => {
                        const op = document.createElement('option');
                        op.value = b;
                        op.innerText = b;
                        blockSel.appendChild(op);
                    });
                    blockSel.disabled = false;
                }
            } catch (e) {}
        }
        
        async function onBlockChange() {
            const state = document.getElementById('state-select').value;
            const district = document.getElementById('district-select').value;
            const block = document.getElementById('block-select').value;
            const villSel = document.getElementById('village-select');
            const btn = document.getElementById('submit-geo-btn');
            
            villSel.innerHTML = '<option value="">-- Choose Village --</option>';
            villSel.disabled = true;
            btn.disabled = true;
            
            if (!block) return;
            
            try {
                const res = await fetch(`/api/constituency/villages?state=` + encodeURIComponent(state) + `&district=` + encodeURIComponent(district));
                const data = await res.json();
                if (data.villages) {
                    data.villages.forEach(v => {
                        const op = document.createElement('option');
                        op.value = v;
                        op.innerText = v;
                        villSel.appendChild(op);
                    });
                    villSel.disabled = false;
                    
                    villSel.onchange = () => {
                        btn.disabled = !villSel.value;
                    };
                }
            } catch (e) {}
        }
        
        async function submitGeo() {
            const state = document.getElementById('state-select').value;
            const district = document.getElementById('district-select').value;
            const block = document.getElementById('block-select').value;
            const village = document.getElementById('village-select').value;
            
            try {
                const res = await fetch(`/api/whatsapp/select-submit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        phone: phone,
                        selected_id: "geo_submit",
                        state: state,
                        district: district,
                        block: block,
                        village: village
                    })
                });
                const data = await res.json();
                if (data.status === "ok") {
                    document.getElementById('geo-card').style.display = 'none';
                    document.getElementById('success-card').style.display = 'block';
                } else {
                    alert("Submission failed. Please try again.");
                }
            } catch (err) {
                alert("Error submitting location. Please check connection.");
            }
        }
        
        if (phone) {
            loadOptions();
        } else {
            document.getElementById('prompt-body').innerText = "Missing phone number parameter.";
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@router.get("/select-options")
def get_select_options(phone: str = Query(...)):
    options_data = _pending_options.get(phone, {"title": "Select Option", "body": "Please select an option:", "options": []})
    return options_data

@router.post("/select-submit")
async def submit_select(body: SelectSubmitRequest, background_tasks: BackgroundTasks):
    phone = body.phone.strip()
    selected_id = body.selected_id.strip()
    
    # Remove from pending list
    _pending_options.pop(phone, None)
    
    if selected_id == "geo_submit" and body.state and body.district and body.village:
        from app.database.citizen_session import update_profile_field, get_citizen_profile, get_language
        from app.agents.conversation import _send_registration_complete
        
        state = body.state.strip()
        district = body.district.strip()
        block = (body.block or "").strip()
        village = body.village.strip()
        
        update_profile_field(phone, "state", state)
        update_profile_field(phone, "district", district)
        update_profile_field(phone, "taluk", block)
        update_profile_field(phone, "village", village)
        update_profile_field(phone, "setup_complete", True)
        
        profile = get_citizen_profile(phone) or {}
        lang = get_language(phone) or "en"
        
        background_tasks.add_task(
            run_buffered_task,
            phone,
            _send_registration_complete,
            phone=phone,
            lang=lang,
            profile=profile
        )
    else:
        # Process message in background to advance conversation
        background_tasks.add_task(
            run_buffered_task,
            phone,
            handle_message,
            phone=phone,
            msg_type="text",
            content=selected_id
        )
    return {"status": "ok"}
