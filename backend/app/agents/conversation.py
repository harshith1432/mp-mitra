"""
MP MITRA — Conversation Engine (State Machine)
================================================
Handles the full citizen journey across all 22 Indian languages.
States: LANG_SELECT → LOCATION → MAIN_MENU → SUBMIT/TRACK/SCHEME/PROJECTS/AI_CHAT
"""
import os
from typing import Dict, Tuple, Optional
from app.database.citizen_session import (
    SessionState, get_session, save_session, get_citizen_profile,
    save_citizen_profile, update_profile_field, update_session_temp,
    reset_session_to_menu, get_submissions, is_registered, get_language
)
from app.routing.whatsapp_send import send_text, send_buttons, send_list

# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGE REGISTRY — All 22 Scheduled Indian Languages
# ═══════════════════════════════════════════════════════════════════════════════

LANGUAGES = [
    {"id": "lang_hi", "code": "hi", "title": "हिन्दी",      "english": "Hindi",      "native": "हिन्दी (Hindi)"},
    {"id": "lang_kn", "code": "kn", "title": "ಕನ್ನಡ",         "english": "Kannada",    "native": "ಕನ್ನಡ (Kannada)"},
    {"id": "lang_ta", "code": "ta", "title": "தமிழ்",         "english": "Tamil",      "native": "தமிழ் (Tamil)"},
    {"id": "lang_te", "code": "te", "title": "తెలుగు",         "english": "Telugu",     "native": "తెలుగు (Telugu)"},
    {"id": "lang_ml", "code": "ml", "title": "മലയാളം",        "english": "Malayalam",  "native": "മലയാളം (Malayalam)"},
    {"id": "lang_bn", "code": "bn", "title": "বাংলা",          "english": "Bengali",    "native": "বাংলা (Bengali)"},
    {"id": "lang_mr", "code": "mr", "title": "मराठी",          "english": "Marathi",    "native": "मराठी (Marathi)"},
    {"id": "lang_gu", "code": "gu", "title": "ગુજરાતી",        "english": "Gujarati",   "native": "ગુજરાતી (Gujarati)"},
    {"id": "lang_pa", "code": "pa", "title": "ਪੰਜਾਬੀ",          "english": "Punjabi",    "native": "ਪੰਜਾਬੀ (Punjabi)"},
    {"id": "lang_or", "code": "or", "title": "ଓଡ଼ିଆ",           "english": "Odia",       "native": "ଓଡ଼ିଆ (Odia)"},
    {"id": "lang_as", "code": "as", "title": "অসমীয়া",         "english": "Assamese",   "native": "অসমীয়া (Assamese)"},
    {"id": "lang_ur", "code": "ur", "title": "اردو",            "english": "Urdu",       "native": "اردو (Urdu)"},
    {"id": "lang_en", "code": "en", "title": "English",         "english": "English",    "native": "English"},
    {"id": "lang_mai","code": "mai","title": "मैथिली",          "english": "Maithili",   "native": "मैथिली (Maithili)"},
    {"id": "lang_sat","code": "sat","title": "ᱥᱟᱱᱛᱟᱲᱤ",       "english": "Santali",    "native": "ᱥᱟᱱᱛᱟᱲᱤ (Santali)"},
    {"id": "lang_ks", "code": "ks", "title": "کٲشُر",           "english": "Kashmiri",   "native": "کٲشُر (Kashmiri)"},
    {"id": "lang_ne", "code": "ne", "title": "नेपाली",          "english": "Nepali",     "native": "नेपाली (Nepali)"},
    {"id": "lang_sd", "code": "sd", "title": "سنڌي",            "english": "Sindhi",     "native": "سنڌي (Sindhi)"},
    {"id": "lang_kok","code": "kok","title": "कोंकणी",          "english": "Konkani",    "native": "कोंकणी (Konkani)"},
    {"id": "lang_doi","code": "doi","title": "डोगरी",            "english": "Dogri",      "native": "डोगरी (Dogri)"},
    {"id": "lang_mni","code": "mni","title": "মৈতৈলোন্",         "english": "Manipuri",   "native": "মৈতৈলোন্ (Manipuri)"},
    {"id": "lang_bo", "code": "bo", "title": "बड़ो",             "english": "Bodo",       "native": "बड़ो (Bodo)"},
]

LANG_BY_ID   = {l["id"]: l for l in LANGUAGES}
LANG_BY_CODE = {l["code"]: l for l in LANGUAGES}

# ── Multilingual UI Strings ────────────────────────────────────────────────────
# Format: {lang_code: string}
# Default (en) used as fallback for less common languages

STRINGS = {
    "welcome": {
        "hi": "🙏 *नमस्ते! MP MITRA में आपका स्वागत है*\n\nमैं आपका AI-संचालित विकास सहायक हूँ। मैं आपको सरकारी योजनाओं की खोज, विकास सुझाव दर्ज करने और आपके क्षेत्र की प्रगति जानने में मदद करूँगा।",
        "kn": "🙏 *ನಮಸ್ಕಾರ! MP MITRA ಗೆ ಸ್ವಾಗತ*\n\nನಾನು ನಿಮ್ಮ AI-ಚಾಲಿತ ಅಭಿವೃದ್ಧಿ ಸಹಾಯಕ. ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು, ಅಭಿವೃದ್ಧಿ ಸಲಹೆಗಳನ್ನು ಸಲ್ಲಿಸಲು ಮತ್ತು ನಿಮ್ಮ ಪ್ರದೇಶದ ಪ್ರಗತಿಯನ್ನು ತಿಳಿಯಲು ನಾನು ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.",
        "ta": "🙏 *வணக்கம்! MP MITRA-க்கு வரவேற்கிறோம்*\n\nநான் உங்கள் AI-இயங்கும் வளர்ச்சி உதவியாளர். அரசு திட்டங்களைக் கண்டறிய, வளர்ச்சி ஆலோசனைகளை சமர்ப்பிக்க மற்றும் உங்கள் பகுதியின் முன்னேற்றத்தை அறிய உதவுவேன்.",
        "te": "🙏 *నమస్కారం! MP MITRA కి స్వాగతం*\n\nనేను మీ AI-ఆధారిత అభివృద్ధి సహాయకుడిని. ప్రభుత్వ పథకాలను కనుగొనడానికి, అభివృద్ధి సూచనలు సమర్పించడానికి మరియు మీ ప్రాంత పురోగతిని తెలుసుకోవడానికి సహాయం చేస్తాను.",
        "ml": "🙏 *നമസ്കാരം! MP MITRA-ലേക്ക് സ്വാഗതം*\n\nഞാൻ നിങ്ങളുടെ AI-പ്രവർത്തിത വികസന സഹായിയാണ്. സർക്കാർ പദ്ധതികൾ കണ്ടെത്താനും, വികസന നിർദ്ദേശങ്ങൾ സമർപ്പിക്കാനും, നിങ്ങളുടെ പ്രദേശത്തിന്റെ പ്രഗതി അറിയാനും ഞാൻ സഹായിക്കുന്നു.",
        "bn": "🙏 *নমস্কার! MP MITRA-তে স্বাগতম*\n\nআমি আপনার AI-চালিত উন্নয়ন সহায়ক। সরকারি প্রকল্প খুঁজে পেতে, উন্নয়ন পরামর্শ জমা দিতে এবং আপনার এলাকার অগ্রগতি জানতে আমি সাহায্য করব।",
        "mr": "🙏 *नमस्कार! MP MITRA मध्ये आपले स्वागत आहे*\n\nमी आपला AI-चालित विकास सहाय्यक आहे. सरकारी योजना शोधण्यासाठी, विकास सूचना सादर करण्यासाठी आणि आपल्या क्षेत्राची प्रगती जाणून घेण्यासाठी मी मदत करेन.",
        "gu": "🙏 *નમસ્તે! MP MITRA માં આપનું સ્વાગત છે*\n\nહું તમારો AI-સંચાલિત વિકાસ સહાયક છું. સરકારી યોજનાઓ શોધવા, વિકાસ સૂચનો રજૂ કરવા અને તમારા વિસ્તારની પ્રગતિ જાણવા માટે હું મદદ કરીશ.",
        "pa": "🙏 *ਸਤ ਸ੍ਰੀ ਅਕਾਲ! MP MITRA ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ*\n\nਮੈਂ ਤੁਹਾਡਾ AI-ਸੰਚਾਲਿਤ ਵਿਕਾਸ ਸਹਾਇਕ ਹਾਂ। ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਲੱਭਣ, ਵਿਕਾਸ ਸੁਝਾਅ ਦੇਣ ਅਤੇ ਤੁਹਾਡੇ ਖੇਤਰ ਦੀ ਤਰੱਕੀ ਜਾਣਨ ਵਿੱਚ ਮਦਦ ਕਰਾਂਗਾ।",
        "en": "🙏 *Welcome to MP MITRA!*\n\nI am your AI-powered Development Intelligence Assistant. I can help you discover government schemes, submit development suggestions, track your requests, and stay informed about upcoming projects in your area.",
    },
    "lang_prompt": {
        "en": "Please select your preferred language for our conversation:",
        "hi": "कृपया अपनी पसंदीदा भाषा चुनें:",
        "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಭಾಷೆ ಆಯ್ಕೆ ಮಾಡಿ:",
    },
    "location_prompt": {
        "en": "To personalize your experience, I need your location. Please select your *State* first:",
        "hi": "आपका अनुभव व्यक्तिगत बनाने के लिए, मुझे आपका स्थान चाहिए। पहले अपना *राज्य* चुनें:",
        "kn": "ನಿಮ್ಮ ಅನುಭವವನ್ನು ವ್ಯಕ್ತಿಗತಗೊಳಿಸಲು, ನಿಮ್ಮ ಸ್ಥಳ ಬೇಕಾಗಿದೆ. ಮೊದಲು ನಿಮ್ಮ *ರಾಜ್ಯ* ಆಯ್ಕೆ ಮಾಡಿ:",
        "ta": "உங்கள் அனுபவத்தை தனிப்பயனாக்க, உங்கள் இடம் தேவை. முதலில் உங்கள் *மாநிலம்* தேர்ந்தெடுக்கவும்:",
        "te": "మీ అనుభవాన్ని వ్యక్తిగతీకరించడానికి, మీ స్థానం అవసరం. మొదట మీ *రాష్ట్రం* ఎంచుకోండి:",
    },
    "main_menu": {
        "en": "🏠 *Main Menu*\n\nHow can I help you today?",
        "hi": "🏠 *मुख्य मेनू*\n\nआज मैं आपकी कैसे मदद कर सकता हूँ?",
        "kn": "🏠 *ಮುಖ್ಯ ಮೆನು*\n\nಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
        "ta": "🏠 *முதன்மை மெனு*\n\nஇன்று நான் உங்களுக்கு எப்படி உதவலாம்?",
        "te": "🏠 *ప్రధాన మెను*\n\nఈ రోజు నేను మీకు ఎలా సహాయం చేయగలను?",
        "ml": "🏠 *പ്രധാന മെനു*\n\nഇന്ന് ഞാൻ നിങ്ങൾക്ക് എങ്ങനെ സഹായിക്കാം?",
        "bn": "🏠 *প্রধান মেনু*\n\nআজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
        "mr": "🏠 *मुख्य मेनू*\n\nआज मी आपली कशी मदत करू शकतो?",
        "gu": "🏠 *મુખ્ય મેનૂ*\n\nઆજ હું તમારી કેવી રીતે મદદ કરી શકું?",
        "pa": "🏠 *ਮੁੱਖ ਮੀਨੂ*\n\nਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
    },
    "submit_prompt": {
        "en": "📝 *Submit a Development Suggestion*\n\nPlease describe the issue or development need in your area.\n\nYou can send:\n• Text message\n• Voice note 🎤\n• Photo or Video 📷\n• Document or PDF 📄\n• Share your location 📍\n\nSend as many messages as needed. Type *DONE* when finished.",
        "hi": "📝 *विकास सुझाव दर्ज करें*\n\nकृपया अपने क्षेत्र में समस्या या विकास की जरूरत बताएं।\n\nआप भेज सकते हैं:\n• पाठ संदेश\n• वॉइस नोट 🎤\n• फोटो या वीडियो 📷\n• दस्तावेज़ या PDF 📄\n• अपना स्थान साझा करें 📍\n\nजितनी जरूरत हो उतने संदेश भेजें। समाप्त होने पर *DONE* टाइप करें।",
        "kn": "📝 *ಅಭಿವೃದ್ಧಿ ಸಲಹೆ ಸಲ್ಲಿಸಿ*\n\nನಿಮ್ಮ ಪ್ರದೇಶದ ಸಮಸ್ಯೆ ಅಥವಾ ಅಭಿವೃದ್ಧಿ ಅಗತ್ಯವನ್ನು ವಿವರಿಸಿ.\n\nನೀವು ಕಳುಹಿಸಬಹುದು:\n• ಪಠ್ಯ ಸಂದೇಶ\n• ಧ್ವನಿ ಟಿಪ್ಪಣಿ 🎤\n• ಫೋಟೋ ಅಥವಾ ವೀಡಿಯೊ 📷\n• ದಾಖಲೆ ಅಥವಾ PDF 📄\n• ನಿಮ್ಮ ಸ್ಥಳ ಹಂಚಿಕೊಳ್ಳಿ 📍\n\nಮುಗಿದಾಗ *DONE* ಟೈಪ್ ಮಾಡಿ.",
    },
    "processing": {
        "en": "⏳ *Processing your submission...*\n\nOur AI is analyzing your message, searching government databases, and matching relevant schemes. This takes 15–30 seconds.",
        "hi": "⏳ *आपका सुझाव प्रोसेस हो रहा है...*\n\nहमारा AI आपके संदेश का विश्लेषण कर रहा है और संबंधित सरकारी योजनाएं खोज रहा है। 15-30 सेकंड लगेंगे।",
        "kn": "⏳ *ನಿಮ್ಮ ಸಲಹೆಯನ್ನು ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗುತ್ತಿದೆ...*\n\nನಮ್ಮ AI ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ವಿಶ್ಲೇಷಿಸುತ್ತಿದೆ. 15-30 ಸೆಕೆಂಡ್ ತೆಗೆದುಕೊಳ್ಳುತ್ತದೆ.",
    },
    "no_submissions": {
        "en": "📭 You haven't submitted any suggestions yet.\n\nType *1* or say *Submit* to share your first development suggestion!",
        "hi": "📭 आपने अभी तक कोई सुझाव नहीं दिया है।\n\nअपना पहला सुझाव देने के लिए *1* टाइप करें।",
        "kn": "📭 ನೀವು ಇನ್ನೂ ಯಾವುದೇ ಸಲಹೆ ಸಲ್ಲಿಸಿಲ್ಲ.\n\nನಿಮ್ಮ ಮೊದಲ ಸಲಹೆ ಸಲ್ಲಿಸಲು *1* ಟೈಪ್ ಮಾಡಿ.",
    },
}

def _t(key: str, lang: str, **kwargs) -> str:
    """Translate a UI string to the given language, falling back to English."""
    lang_strings = STRINGS.get(key, {})
    text = lang_strings.get(lang) or lang_strings.get("en", f"[{key}]")
    return text.format(**kwargs) if kwargs else text


# ── MAIN MENU BUTTONS ─────────────────────────────────────────────────────────
def _main_menu_buttons(lang: str) -> Tuple[str, list]:
    labels = {
        "en": ["📝 Submit Suggestion", "📋 Track My Submissions", "🔍 Scheme Finder",
               "🏗️ Projects Near Me", "🤖 AI Assistant", "📍 Update Location"],
        "hi": ["📝 सुझाव दर्ज करें", "📋 मेरे सुझाव ट्रैक करें", "🔍 योजना खोजें",
               "🏗️ मेरे पास परियोजनाएं", "🤖 AI सहायक", "📍 स्थान अपडेट करें"],
        "kn": ["📝 ಸಲಹೆ ಸಲ್ಲಿಸಿ", "📋 ನನ್ನ ಸಲಹೆ ಟ್ರ್ಯಾಕ್", "🔍 ಯೋಜನೆ ಹುಡುಕಿ",
               "🏗️ ಹತ್ತಿರದ ಯೋಜನೆಗಳು", "🤖 AI ಸಹಾಯಕ", "📍 ಸ್ಥಳ ಅಪ್ಡೇಟ್"],
        "ta": ["📝 ஆலோசனை சமர்ப்பிக்க", "📋 என் சமர்ப்பிப்புகள்", "🔍 திட்ட தேடல்",
               "🏗️ அருகில் திட்டங்கள்", "🤖 AI உதவியாளர்", "📍 இடம் புதுப்பி"],
        "te": ["📝 సూచన సమర్పించు", "📋 నా సూచనలు", "🔍 పథకం వెతకు",
               "🏗️ సమీప ప్రాజెక్టులు", "🤖 AI సహాయకుడు", "📍 స్థానం నవీకరించు"],
    }
    btn_labels = labels.get(lang, labels["en"])
    ids = ["menu_submit", "menu_track", "menu_scheme", "menu_projects", "menu_ai", "menu_location"]
    buttons = [{"id": ids[i], "title": btn_labels[i]} for i in range(len(ids))]
    return _t("main_menu", lang), buttons


# ── INDIA STATES LIST (for location flow) ─────────────────────────────────────
INDIA_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman & Nicobar", "Chandigarh", "Delhi", "Jammu & Kashmir", "Ladakh",
    "Lakshadweep", "Puducherry", "Dadra & Nagar Haveli"
]


def _states_sections() -> list:
    """Group states into WhatsApp list sections (max 10 rows per section)."""
    sections = []
    groups = [
        ("A–G States", INDIA_STATES[:10]),
        ("G–M States", INDIA_STATES[10:20]),
        ("N–W States", INDIA_STATES[20:28]),
        ("Union Territories", INDIA_STATES[28:]),
    ]
    for title, states in groups:
        rows = [{"id": f"state_{s.replace(' ', '_')}", "title": s[:24]} for s in states]
        sections.append({"title": title, "rows": rows})
    return sections


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER: handle_message()
# ═══════════════════════════════════════════════════════════════════════════════

def handle_message(phone: str, msg_type: str, content: str,
                   media_url: Optional[str] = None,
                   latitude: Optional[float] = None,
                   longitude: Optional[float] = None):
    """
    Main conversation router. Called from the WhatsApp webhook.
    phone: WhatsApp number (e.g. "+919876543210")
    msg_type: "text" | "audio" | "image" | "video" | "document" | "location" | "interactive"
    content: text body or interactive reply ID
    """
    session  = get_session(phone)
    state    = session.get("state", SessionState.START)
    step     = session.get("step", 0)
    temp     = session.get("temp_data", {})
    lang     = get_language(phone)
    profile  = get_citizen_profile(phone) or {}

    text = (content or "").strip()
    text_lower = text.lower()

    # ── Intercept Consolidated Location Selection ─────────────────────────────
    if text.startswith("Location Selection:"):
        parts = {}
        for item in text.replace("Location Selection:", "").split(","):
            if "=" in item:
                k, v = item.split("=", 1)
                parts[k.strip().lower()] = v.strip()
        
        state_val = parts.get("state", "").strip()
        district_val = parts.get("district", "").strip()
        village_val = parts.get("village", "").strip()
        
        update_profile_field(phone, "state", state_val)
        update_profile_field(phone, "district", district_val)
        update_profile_field(phone, "taluk", district_val)
        update_profile_field(phone, "village", village_val)
        
        profile = get_citizen_profile(phone) or {}
        profile.update({
            "state": state_val,
            "district": district_val,
            "taluk": district_val,
            "village": village_val,
            "setup_complete": True
        })
        save_citizen_profile(phone, profile)
        
        _send_registration_complete(phone, lang, profile)
        return

    # ── Global commands (work from any state) ─────────────────────────────────
    greetings = ("hi", "hii", "hy", "hello", "helo", "namaste", "start", "hey", "hola",
                 "नमस्ते", "ನಮಸ್ಕಾರ", "வணக்கம்", "నమస్కారం", "ഹലോ", "ನಮಸ್ಕಾರ", "ಹಲೋ")
    is_greeting = text_lower in greetings or any(text_lower.startswith(g + " ") for g in greetings)
    if is_greeting:
        # Always restart with welcome
        _send_welcome(phone)
        return

    if text_lower in ("menu", "home", "back", "cancel", "मेनू", "ಮೆನು"):
        reset_session_to_menu(phone)
        _send_main_menu(phone, lang, profile)
        return

    # ── State machine ─────────────────────────────────────────────────────────
    if state == SessionState.START or state == SessionState.LANG_SELECT:
        _handle_lang_select(phone, text, msg_type, content)

    elif state == SessionState.STATE_SELECT:
        _handle_state_select(phone, text, lang)

    elif state == SessionState.DISTRICT_SELECT:
        _handle_district_select(phone, text, lang, temp)

    elif state == SessionState.TALUK_SELECT:
        _handle_taluk_select(phone, text, lang, temp)

    elif state == SessionState.VILLAGE_SELECT:
        _handle_village_select(phone, text, lang, temp)

    elif state == SessionState.LOCATION_SHARE:
        if msg_type == "location" and latitude and longitude:
            _handle_location_shared(phone, latitude, longitude, lang)
        else:
            _handle_village_select(phone, text, lang, temp)

    elif state == SessionState.MAIN_MENU:
        _handle_main_menu_choice(phone, text, lang, profile)

    elif state == SessionState.SUBMIT_DESCRIBE:
        _handle_submit_describe(phone, msg_type, text, media_url, latitude, longitude, lang, temp)

    elif state == SessionState.TRACK:
        _send_track_results(phone, lang)

    elif state == SessionState.SCHEME:
        _handle_scheme_finder(phone, lang, profile, text)

    elif state == SessionState.PROJECTS:
        _handle_projects(phone, lang, profile)

    elif state == SessionState.AI_CHAT:
        _handle_ai_chat(phone, text, lang, profile)

    else:
        _send_main_menu(phone, lang, profile)


# ═══════════════════════════════════════════════════════════════════════════════
# WELCOME & LANGUAGE SELECTION
# ═══════════════════════════════════════════════════════════════════════════════

def _send_welcome(phone: str):
    """Send welcome in English + ask language in one single message to save WhatsApp API cost."""
    welcome_body = STRINGS["welcome"].get("en") + "\n\n──────────────────\n\n" + "Please select your preferred language / कृपया भाषा चुनें / ದಯವಿಟ್ಟು ಭಾಷೆ ಆಯ್ಕೆ ಮಾಡಿ:"
    # Send language list
    sections = [
        {
            "title": "Major Languages",
            "rows": [{"id": l["id"], "title": l["native"][:24]} for l in LANGUAGES[:10]]
        },
        {
            "title": "More Languages",
            "rows": [{"id": l["id"], "title": l["native"][:24]} for l in LANGUAGES[10:]]
        }
    ]
    send_list(phone,
              header="🌐 Language / भाषा / ಭಾಷೆ",
              body=welcome_body,
              button_text="Select Language",
              sections=sections)
    save_session(phone, SessionState.LANG_SELECT)


def _handle_lang_select(phone: str, text: str, msg_type: str, content: str):
    """Process language selection."""
    selected_lang = None

    # Match by list reply ID (e.g. "lang_kn")
    if content and content.startswith("lang_"):
        lang_data = LANG_BY_ID.get(content)
        if lang_data:
            selected_lang = lang_data["code"]

    # Match by number (1-22)
    if not selected_lang and text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(LANGUAGES):
            selected_lang = LANGUAGES[idx]["code"]

    # Match by language name
    if not selected_lang:
        for l in LANGUAGES:
            if text.lower() in [l["english"].lower(), l["title"].lower(), l["code"]]:
                selected_lang = l["code"]
                break

    if not selected_lang:
        selected_lang = "en"  # default

    # Save language
    update_profile_field(phone, "language", selected_lang)
    lang_data = LANG_BY_CODE.get(selected_lang, LANG_BY_CODE["en"])

    send_text(phone, f"✅ *{lang_data['native']}* selected!\n\n" + _t("welcome", selected_lang))

    # Check if already registered
    profile = get_citizen_profile(phone) or {}
    if profile.get("village"):
        # Already has location — go straight to menu
        save_session(phone, SessionState.MAIN_MENU)
        _send_main_menu(phone, selected_lang, profile)
    else:
        # Need location setup (send single message)
        send_list(phone,
                  header="📍 Select Your State",
                  body=_t("location_prompt", selected_lang),
                  button_text="Choose State",
                  sections=_states_sections())
        save_session(phone, SessionState.STATE_SELECT)


# ═══════════════════════════════════════════════════════════════════════════════
# LOCATION FLOW
# ═══════════════════════════════════════════════════════════════════════════════

def _handle_state_select(phone: str, text: str, lang: str):
    # Extract state from reply ID or text
    state_name = ""
    if text.startswith("state_"):
        state_name = text.replace("state_", "").replace("_", " ")
    else:
        # Try matching state name from typed text
        text_up = text.title()
        for s in INDIA_STATES:
            if text_up in s or s.lower().startswith(text.lower()[:4]):
                state_name = s
                break
        if not state_name and text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(INDIA_STATES):
                state_name = INDIA_STATES[idx]

    if not state_name:
        send_text(phone, f"Please select a valid state. Type the state name or number.")
        return

    update_profile_field(phone, "state", state_name)
    send_text(phone, f"✅ *{state_name}* selected.\n\nNow please enter your *District* name:")
    save_session(phone, SessionState.DISTRICT_SELECT, temp_data={"state": state_name})


def _handle_district_select(phone: str, text: str, lang: str, temp: dict):
    if len(text) < 2:
        send_text(phone, "Please enter your district name (e.g. Mandya, Pune, Patna):")
        return
    district = text.title()
    update_profile_field(phone, "district", district)
    send_text(phone, f"✅ *{district}* district selected.\n\nPlease enter your *Block / Taluk* name:")
    temp["district"] = district
    save_session(phone, SessionState.TALUK_SELECT, temp_data=temp)


def _handle_taluk_select(phone: str, text: str, lang: str, temp: dict):
    if len(text) < 2:
        send_text(phone, "Please enter your Block / Taluk name:")
        return
    taluk = text.title()
    update_profile_field(phone, "taluk", taluk)
    send_text(phone, f"✅ *{taluk}* Block selected.\n\nFinally, enter your *Village / Town* name:\n\n_(Or share your 📍 live location to auto-detect)_")
    temp["taluk"] = taluk
    save_session(phone, SessionState.VILLAGE_SELECT, temp_data=temp)


def _handle_village_select(phone: str, text: str, lang: str, temp: dict):
    if len(text) < 2:
        send_text(phone, "Please enter your village or town name:")
        return
    village = text.title()
    update_profile_field(phone, "village", village)

    # Build complete profile
    profile = get_citizen_profile(phone) or {}
    profile.update({"village": village, "setup_complete": True})
    save_citizen_profile(phone, profile)

    _send_registration_complete(phone, lang, profile)


def _handle_location_shared(phone: str, lat: float, lon: float, lang: str):
    """Reverse geocode shared location and save."""
    try:
        from geopy.geocoders import Nominatim
        geo = Nominatim(user_agent="mp_mitra")
        location = geo.reverse(f"{lat},{lon}", language="en")
        addr = location.raw.get("address", {})
        state   = addr.get("state", "")
        district= addr.get("county") or addr.get("state_district", "")
        village = addr.get("village") or addr.get("town") or addr.get("suburb", "")
        taluk   = addr.get("suburb") or addr.get("city_district", "")

        update_profile_field(phone, "state", state)
        update_profile_field(phone, "district", district)
        update_profile_field(phone, "taluk", taluk)
        update_profile_field(phone, "village", village)
        update_profile_field(phone, "lat", lat)
        update_profile_field(phone, "lon", lon)
        update_profile_field(phone, "setup_complete", True)

        profile = get_citizen_profile(phone) or {}
        send_text(phone, f"✅ Location detected!\n📍 *{village}, {district}, {state}*")
        _send_registration_complete(phone, lang, profile)
    except Exception as e:
        send_text(phone, f"Could not detect location automatically. Please type your village name:")
        save_session(phone, SessionState.VILLAGE_SELECT)


def _send_registration_complete(phone: str, lang: str, profile: dict):
    prefix = (
        f"🎉 *Registration Complete!*\n\n"
        f"📍 {profile.get('village','')}, {profile.get('district','')}, {profile.get('state','')}\n\n"
        f"Your location has been saved. You won't need to enter it again!"
    )
    save_session(phone, SessionState.MAIN_MENU)
    _send_main_menu(phone, lang, profile, prefix=prefix)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

def _send_main_menu(phone: str, lang: str, profile: dict, prefix: str = None):
    body, buttons = _main_menu_buttons(lang)
    loc_str = f"📍 {profile.get('village','')}, {profile.get('district','')}" if profile.get("village") else ""
    if loc_str:
        body = f"{body}\n\n{loc_str}"
    if prefix:
        body = f"{prefix}\n\n──────────────────\n\n{body}"
    send_list(phone,
              header="🏛️ MP MITRA",
              body=body,
              button_text="Select Option",
              sections=[{"title": "Services", "rows": [
                  {"id": "menu_submit",   "title": "📝 Submit Suggestion",   "description": "Report an issue or development need"},
                  {"id": "menu_track",    "title": "📋 Track Submissions",   "description": "Check status of your submissions"},
                  {"id": "menu_scheme",   "title": "🔍 Scheme Finder",       "description": "Discover eligible government schemes"},
                  {"id": "menu_projects", "title": "🏗️ Projects Near Me",    "description": "Upcoming development projects"},
                  {"id": "menu_ai",       "title": "🤖 AI Assistant",        "description": "Ask any question about governance"},
                  {"id": "menu_location", "title": "📍 Update Location",     "description": "Change your village/district"},
              ]}])


def _handle_main_menu_choice(phone: str, text: str, lang: str, profile: dict):
    # Match by ID, number, or keyword
    choice_map = {
        "menu_submit":   SessionState.SUBMIT_DESCRIBE,
        "menu_track":    SessionState.TRACK,
        "menu_scheme":   SessionState.SCHEME,
        "menu_projects": SessionState.PROJECTS,
        "menu_ai":       SessionState.AI_CHAT,
        "menu_location": SessionState.STATE_SELECT,
    }
    keyword_map = {
        "1": "menu_submit", "submit": "menu_submit", "suggestion": "menu_submit",
        "2": "menu_track",  "track": "menu_track",
        "3": "menu_scheme", "scheme": "menu_scheme", "yojana": "menu_scheme",
        "4": "menu_projects","project": "menu_projects",
        "5": "menu_ai",     "ai": "menu_ai", "help": "menu_ai",
        "6": "menu_location","location": "menu_location", "update": "menu_location",
    }
    text_lower = text.lower()
    choice_id = text if text in choice_map else keyword_map.get(text_lower, "")
    new_state = choice_map.get(choice_id)

    if new_state == SessionState.SUBMIT_DESCRIBE:
        send_text(phone, _t("submit_prompt", lang))
        save_session(phone, SessionState.SUBMIT_DESCRIBE, temp_data={"media_items": []})
    elif new_state == SessionState.TRACK:
        save_session(phone, SessionState.TRACK)
        _send_track_results(phone, lang)
    elif new_state == SessionState.SCHEME:
        save_session(phone, SessionState.SCHEME)
        _handle_scheme_finder(phone, lang, profile, "")
    elif new_state == SessionState.PROJECTS:
        save_session(phone, SessionState.PROJECTS)
        _handle_projects(phone, lang, profile)
    elif new_state == SessionState.AI_CHAT:
        save_session(phone, SessionState.AI_CHAT)
        prompt = {
            "en": "🤖 *AI Assistant active*\nAsk me anything about government schemes, infrastructure, development projects, or your submitted suggestions!\n\nType *menu* to go back.",
            "hi": "🤖 *AI सहायक सक्रिय*\nसरकारी योजनाओं, बुनियादी ढांचे, या विकास परियोजनाओं के बारे में कुछ भी पूछें!\n\nवापस जाने के लिए *menu* टाइप करें।",
            "kn": "🤖 *AI ಸಹಾಯಕ ಸಕ್ರಿಯ*\nಸರ್ಕಾರಿ ಯೋಜನೆಗಳು, ಮೂಲಸೌಕರ್ಯ ಅಥವಾ ಅಭಿವೃದ್ಧಿ ಯೋಜನೆಗಳ ಬಗ್ಗೆ ಏನಾದರೂ ಕೇಳಿ!\n\nಹಿಂತಿರುಗಲು *menu* ಟೈಪ್ ಮಾಡಿ.",
        }
        send_text(phone, prompt.get(lang, prompt["en"]))
    elif new_state == SessionState.STATE_SELECT:
        send_list(phone, header="📍 Update Location", body="Select your State:",
                  button_text="Choose State", sections=_states_sections())
        save_session(phone, SessionState.STATE_SELECT)
    else:
        send_text(phone, "Please select a valid option (1-6) or type *menu*.")
        _send_main_menu(phone, lang, profile)


# ═══════════════════════════════════════════════════════════════════════════════
# SUBMISSION FLOW
# ═══════════════════════════════════════════════════════════════════════════════

def _handle_submit_describe(phone: str, msg_type: str, text: str,
                             media_url: Optional[str], lat, lon,
                             lang: str, temp: dict):
    """Collect multimodal submission content."""
    from app.database.citizen_session import save_submission, update_submission_status

    if text.upper() in ("DONE", "SUBMIT", "SEND", "OK", "ಮುಗಿಯಿತು", "हो गया"):
        if not temp.get("media_items") and not temp.get("text_content"):
            send_text(phone, "Please describe the issue first, then type DONE.")
            return

        # Trigger async AI processing
        send_text(phone, _t("processing", lang))
        sub_id = save_submission(phone, {
            "text_content": temp.get("text_content", ""),
            "media_items":  temp.get("media_items", []),
            "location_lat": temp.get("lat"),
            "location_lon": temp.get("lon"),
            "state":    get_citizen_profile(phone).get("state", ""),
            "district": get_citizen_profile(phone).get("district", ""),
            "village":  get_citizen_profile(phone).get("village", ""),
            "category": "General Development",
            "status":   "AI Processing",
        })

        # Trigger AI pipeline in background thread
        import threading
        from app.agents.orchestrator import process_submission
        def _bg():
            process_submission(phone, sub_id, temp, lang)
        threading.Thread(target=_bg, daemon=True).start()

        save_session(phone, SessionState.MAIN_MENU)
        return

    # Accumulate content
    items = temp.get("media_items", [])
    if msg_type == "text" and text:
        temp["text_content"] = temp.get("text_content", "") + " " + text
        send_text(phone, f"✅ Message received. Send more (photo/voice/doc) or type *DONE* to submit.")
    elif msg_type in ("image", "video", "document", "audio") and media_url:
        items.append({"type": msg_type, "url": media_url})
        temp["media_items"] = items
        labels = {
            "image": "📷 Photo", "video": "🎥 Video",
            "document": "📄 Document", "audio": "🎤 Voice note"
        }
        send_text(phone, f"✅ {labels.get(msg_type,'File')} received. Send more or type *DONE* to submit.")
    elif msg_type == "location" and lat and lon:
        temp["lat"] = lat
        temp["lon"] = lon
        send_text(phone, f"📍 Location captured ({lat:.4f}, {lon:.4f}). Send more or type *DONE*.")

    update_session_temp(phone, "media_items", items)
    if "text_content" in temp:
        update_session_temp(phone, "text_content", temp["text_content"])
    if lat: update_session_temp(phone, "lat", lat)
    if lon: update_session_temp(phone, "lon", lon)


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK SUBMISSIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _send_track_results(phone: str, lang: str):
    submissions = get_submissions(phone)
    if not submissions:
        send_text(phone, _t("no_submissions", lang))
        reset_session_to_menu(phone)
        return

    status_emoji = {
        "Received": "📥", "AI Processing": "🤖", "Under Review": "👀",
        "In Progress": "🔄", "Completed": "✅", "Rejected": "❌"
    }
    msg_lines = ["📋 *Your Submissions:*\n"]
    for i, sub in enumerate(submissions[:5], 1):
        emoji = status_emoji.get(sub.get("status", ""), "📌")
        msg_lines.append(
            f"*{i}. {sub.get('submission_id','')}*\n"
            f"   📅 {sub.get('created_at','')[:10]}\n"
            f"   🏷️ {sub.get('category','')}\n"
            f"   {emoji} {sub.get('status','')}\n"
            f"   📝 {sub.get('ai_summary','Awaiting AI analysis')[:80]}\n"
        )

    body = "\n".join(msg_lines) + "\n\n──────────────────\n\nWhat would you like to do next?"
    send_buttons(phone, body,
                 [{"id": "menu_submit", "title": "Submit New"},
                  {"id": "main_menu",  "title": "Main Menu"}])
    reset_session_to_menu(phone)


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEME FINDER
# ═══════════════════════════════════════════════════════════════════════════════

def _handle_scheme_finder(phone: str, lang: str, profile: dict, text: str):
    from app.database.connection import SessionLocal
    from app.database.models import CrawledScheme
    db = SessionLocal()
    state_name = profile.get("state", "").upper()
    try:
        schemes = db.query(CrawledScheme).filter(
            (CrawledScheme.eligibility_state == "ALL") |
            (CrawledScheme.eligibility_state == state_name)
        ).limit(8).all()

        if not schemes:
            send_text(phone, "No schemes found for your profile. Our AI is updating the database. Please try again in a few minutes.")
            reset_session_to_menu(phone)
            return

        msg_lines = [f"🔍 *Government Schemes for {profile.get('district','your area')}*\n"]
        for i, s in enumerate(schemes[:5], 1):
            msg_lines.append(
                f"*{i}. {s.title}*\n"
                f"   🏛️ {s.ministry}\n"
                f"   🏷️ {s.category}\n"
                f"   📝 {(s.description or '')[:100]}...\n"
                f"   🔗 {s.link}\n"
            )
        msg_lines.append("\n_Type the scheme number for more details, or type *menu* to go back._")
        send_text(phone, "\n".join(msg_lines))
    finally:
        db.close()
    reset_session_to_menu(phone)


# ═══════════════════════════════════════════════════════════════════════════════
# PROJECTS
# ═══════════════════════════════════════════════════════════════════════════════

def _handle_projects(phone: str, lang: str, profile: dict):
    from app.database.connection import SessionLocal
    from app.database.models import CrawledTender
    db = SessionLocal()
    district = profile.get("district", "").upper()
    try:
        tenders = db.query(CrawledTender).filter(
            CrawledTender.district_name == district
        ).limit(5).all()

        if not tenders:
            send_text(phone, f"🏗️ No active projects found for {profile.get('district','your district')} yet. Our AI crawler updates this daily.\n\nType *menu* to go back.")
            reset_session_to_menu(phone)
            return

        msg_lines = [f"🏗️ *Development Projects — {profile.get('district','')}*\n"]
        for i, t in enumerate(tenders, 1):
            msg_lines.append(
                f"*{i}. {t.title}*\n"
                f"   🏛️ {t.authority}\n"
                f"   💰 {t.cost}\n"
                f"   📅 Deadline: {t.deadline}\n"
                f"   🏷️ {t.category}\n"
            )
        send_text(phone, "\n".join(msg_lines))
    finally:
        db.close()
    reset_session_to_menu(phone)


# ═══════════════════════════════════════════════════════════════════════════════
# AI CHAT
# ═══════════════════════════════════════════════════════════════════════════════

def _handle_ai_chat(phone: str, text: str, lang: str, profile: dict):
    """Free-form AI Q&A using LLM + RAG."""
    if not text or len(text) < 3:
        send_text(phone, "Please ask your question.")
        return

    send_text(phone, "🤖 Searching government databases and official sources...")

    try:
        from app.agents.rag_agent import search_knowledge_base
        from app.agents.translate_agent import translate_to_english, translate_from_english
        from app.agents.orchestrator import call_llm

        # Translate question to English for processing
        en_question = translate_to_english(text, lang)

        # RAG search
        context_docs = search_knowledge_base(en_question, state=profile.get("state",""), k=4)
        context = "\n\n".join([f"Source: {d.get('source_url','')}\n{d.get('content','')}" for d in context_docs])

        # Build prompt
        system_prompt = f"""You are MP MITRA, an AI assistant helping Indian citizens understand government schemes, 
        infrastructure projects, and development programs. The citizen is from {profile.get('village','')}, 
        {profile.get('district','')}, {profile.get('state','')}.
        
        Use the following official government information to answer:
        {context}
        
        Always cite the official source URL when referencing information.
        Keep response under 300 words. Format for WhatsApp (use *bold*, bullet points)."""

        response_en = call_llm(system_prompt, en_question)
        response_local = translate_from_english(response_en, lang)
        send_text(phone, response_local)

    except Exception as e:
        print(f"[AI Chat Error] {e}")
        send_text(phone,
            "🤖 Based on our database:\n\n"
            f"For your query about *{text[:50]}*, please visit:\n"
            "• myscheme.gov.in — Government scheme portal\n"
            "• pmjay.gov.in — Health schemes\n"
            "• nrega.nic.in — Employment schemes\n"
            "• pmgsy.nic.in — Road connectivity\n\n"
            "Type *menu* to return to main menu."
        )

    save_session(phone, SessionState.AI_CHAT)
