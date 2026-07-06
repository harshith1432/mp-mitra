"""
MP MITRA — WhatsApp Message Sender
====================================
Dual-mode: Twilio Sandbox (dev) + Meta Cloud API (prod) + Simulator (demo).
Set WHATSAPP_MODE in .env: "twilio" | "meta" | "simulator"
"""
import os, json, httpx, urllib.parse
from typing import List, Dict, Optional

from app.config_manager import config_manager

WHATSAPP_MODE = config_manager.get("WHATSAPP_MODE") or os.getenv("WHATSAPP_MODE", "simulator")
TWILIO_ACCOUNT_SID = config_manager.get_secret("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = config_manager.get_secret("TWILIO_AUTH_TOKEN")
TWILIO_FROM        = config_manager.get("TWILIO_WHATSAPP_FROM") or os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
META_TOKEN         = config_manager.get_secret("META_WHATSAPP_TOKEN")
META_PHONE_ID      = config_manager.get("META_PHONE_NUMBER_ID") or os.getenv("META_PHONE_NUMBER_ID", "")
META_API_URL       = f"https://graph.facebook.com/v19.0/{META_PHONE_ID}/messages" if META_PHONE_ID else ""
PUBLIC_BACKEND_URL = config_manager.get("PUBLIC_BACKEND_URL") or os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000").rstrip("/")

# Temporary store for web dropdown selections
_pending_options: Dict[str, Dict] = {}

# In-simulator mode, accumulate outgoing messages in memory for the frontend to poll
_simulator_outbox: Dict[str, List[Dict]] = {}


def _simulator_send(to: str, payload: Dict):
    """Store message for simulator frontend polling."""
    if to not in _simulator_outbox:
        _simulator_outbox[to] = []
    _simulator_outbox[to].append(payload)
    print(f"[Simulator → {to}] {json.dumps(payload, ensure_ascii=False)[:200]}")


def get_simulator_messages(phone: str) -> List[Dict]:
    """Frontend polls this to get pending bot messages."""
    msgs = _simulator_outbox.pop(phone, [])
    return msgs


# ── Twilio ────────────────────────────────────────────────────────────────────
def _twilio_send_text(to: str, body: str):
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(from_=TWILIO_FROM, to=f"whatsapp:{to}", body=body)
    except Exception as e:
        print(f"[Twilio Error] {e}")


# ── Meta Cloud API ─────────────────────────────────────────────────────────────
def _meta_post(payload: Dict):
    try:
        r = httpx.post(
            META_API_URL,
            headers={"Authorization": f"Bearer {META_TOKEN}", "Content-Type": "application/json"},
            json=payload, timeout=10
        )
        if r.status_code >= 400:
            print(f"[Meta API Error] {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[Meta API Error] {e}")


# ═══════════════════════════════════════════════════════════════════════════════
import contextvars

_msg_buffer = contextvars.ContextVar("msg_buffer", default=None)

def start_buffering(to: str):
    """Enable context-local outbound message buffering for the given phone number."""
    _msg_buffer.set({
        "to": to,
        "texts": [],
        "interactive": None
    })

def flush_buffering():
    """Consolidate and flush all buffered outbound messages into a single WhatsApp payload."""
    buf = _msg_buffer.get()
    _msg_buffer.set(None) # Disable buffering
    
    if not buf:
        return
        
    to = buf["to"]
    texts = buf["texts"]
    inter = buf["interactive"]
    
    # Merge all plain texts
    combined_text = "\n\n".join(t.strip() for t in texts if t.strip())
    
    if inter:
        itype = inter["type"]
        args = inter["args"]
        
        if itype == "list":
            header = args[1]
            body = args[2]
            button_text = args[3]
            sections = args[4]
            
            if combined_text:
                body = f"{combined_text}\n\n──────────────────\n\n{body}"
                
            _send_list_direct(to, header, body, button_text, sections)
            
        elif itype == "buttons":
            body = args[1]
            buttons = args[2]
            
            if combined_text:
                body = f"{combined_text}\n\n──────────────────\n\n{body}"
                
            _send_buttons_direct(to, body, buttons)
    else:
        if combined_text:
            _send_text_direct(to, combined_text)


def _send_text_direct(to: str, body: str):
    # Send via Twilio if phone looks real and SID/Token are set, or if twilio mode is active
    if (to.startswith("+") and len(to) > 8 and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN) or WHATSAPP_MODE == "twilio":
        _twilio_send_text(to, body)
    
    # Send via Meta Cloud API if token is set, or if meta mode is active
    if (to.startswith("+") and len(to) > 8 and META_TOKEN and META_PHONE_ID) or WHATSAPP_MODE == "meta":
        _meta_post({"messaging_product": "whatsapp", "to": to,
                    "type": "text", "text": {"body": body}})
                    
    # Log in simulator outbox if mode is simulator or it looks like a simulated number
    if WHATSAPP_MODE == "simulator" or " " in to or len(to) < 9:
        _simulator_send(to, {"type": "text", "body": body})


def send_text(to: str, body: str):
    """Send plain text message (buffered if context-buffering is active)."""
    buf = _msg_buffer.get()
    if buf is not None and buf["to"] == to:
        buf["texts"].append(body)
    else:
        _send_text_direct(to, body)


def _send_buttons_direct(to: str, body: str, buttons: List[Dict]):
    wa_buttons = [{"type": "reply", "reply": {"id": b["id"], "title": b["title"][:20]}}
                  for b in buttons[:3]]
                  
    # Store options for web select
    rows = [{"id": b["id"], "title": b["title"]} for b in buttons]
    _pending_options[to] = {
        "title": "Choose Option",
        "body": body,
        "options": rows
    }
                  
    if (to.startswith("+") and len(to) > 8 and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN) or WHATSAPP_MODE == "twilio":
        link = f"{PUBLIC_BACKEND_URL}/api/whatsapp/select?phone={urllib.parse.quote(to)}"
        _twilio_send_text(to, f"{body}\n\n👇 *Click to make your selection:* 👇\n{link}")
        
    if (to.startswith("+") and len(to) > 8 and META_TOKEN and META_PHONE_ID) or WHATSAPP_MODE == "meta":
        link = f"{PUBLIC_BACKEND_URL}/api/whatsapp/select?phone={urllib.parse.quote(to)}"
        _meta_post({
            "messaging_product": "whatsapp", "to": to, "type": "interactive",
            "interactive": {
                "type": "cta_url",
                "body": {"text": body},
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": "Choose Option",
                        "url": link
                    }
                }
            }
        })
        
    if WHATSAPP_MODE == "simulator" or " " in to or len(to) < 9:
        _simulator_send(to, {"type": "buttons", "body": body, "buttons": buttons[:3]})


def send_buttons(to: str, body: str, buttons: List[Dict]):
    """Send reply buttons (buffered if context-buffering is active)."""
    buf = _msg_buffer.get()
    if buf is not None and buf["to"] == to:
        buf["interactive"] = {
            "type": "buttons",
            "args": (to, body, buttons),
            "kwargs": {}
        }
    else:
        _send_buttons_direct(to, body, buttons)


def _send_list_direct(to: str, header: str, body: str, button_text: str, sections: List[Dict]):
    # Store options for web select
    rows = []
    is_geo = False
    for sec in sections:
        for row in sec.get("rows", []):
            rows.append({"id": row["id"], "title": row["title"]})
            if row["id"].startswith("state_"):
                is_geo = True
            
    _pending_options[to] = {
        "title": header or button_text or "Select Option",
        "body": body,
        "options": rows,
        "is_geo": is_geo
    }
    
    if (to.startswith("+") and len(to) > 8 and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN) or WHATSAPP_MODE == "twilio":
        link = f"{PUBLIC_BACKEND_URL}/api/whatsapp/select?phone={urllib.parse.quote(to)}"
        _twilio_send_text(to, f"{body}\n\n👇 *Click to make your selection:* 👇\n{link}")
        
    if (to.startswith("+") and len(to) > 8 and META_TOKEN and META_PHONE_ID) or WHATSAPP_MODE == "meta":
        link = f"{PUBLIC_BACKEND_URL}/api/whatsapp/select?phone={urllib.parse.quote(to)}"
        _meta_post({
            "messaging_product": "whatsapp", "to": to, "type": "interactive",
            "interactive": {
                "type": "cta_url",
                "body": {"text": body},
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": button_text or "Select Option",
                        "url": link
                    }
                }
            }
        })
        
    if WHATSAPP_MODE == "simulator" or " " in to or len(to) < 9:
        _simulator_send(to, {"type": "list", "header": header, "body": body,
                              "button_text": button_text, "sections": sections})


def send_list(to: str, header: str, body: str, button_text: str, sections: List[Dict]):
    """Send list selection (buffered if context-buffering is active)."""
    buf = _msg_buffer.get()
    if buf is not None and buf["to"] == to:
        buf["interactive"] = {
            "type": "list",
            "args": (to, header, body, button_text, sections),
            "kwargs": {}
        }
    else:
        _send_list_direct(to, header, body, button_text, sections)


def send_media(to: str, media_url: str, caption: str = ""):
    """Send image or document."""
    if (to.startswith("+") and len(to) > 8 and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN) or WHATSAPP_MODE == "twilio":
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            client.messages.create(from_=TWILIO_FROM, to=f"whatsapp:{to}",
                                   body=caption, media_url=[media_url])
        except Exception as e:
            print(f"[Twilio Media Error] {e}")
    elif WHATSAPP_MODE == "meta":
        _meta_post({
            "messaging_product": "whatsapp", "to": to, "type": "image",
            "image": {"link": media_url, "caption": caption}
        })


def send_typing(to: str):
    """Send typing indicator (Meta only, simulator logs it)."""
    if WHATSAPP_MODE == "simulator":
        _simulator_send(to, {"type": "typing"})
    elif WHATSAPP_MODE == "meta":
        _meta_post({
            "messaging_product": "whatsapp", "to": to,
            "status": "read"  # Meta uses read receipts before responding
        })
