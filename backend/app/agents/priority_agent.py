"""
MP MITRA — Prioritization & Duplicate Detection Agent
======================================================
Computes a multi-factor priority score and checks for duplicate submissions
against the PostgreSQL database.
"""
from typing import Dict, Any, Tuple
from app.database.connection import SessionLocal
# CitizenSuggestion model does not exist in models.py; we query using raw SQL check

# Let's write a robust module that checks existing suggestions and ranks priority
def analyze_priority_and_duplicates(
    text_content: str,
    category: str,
    state: str,
    district: str,
    village: str
) -> Tuple[float, int, float, str]:
    """
    Computes priority_score, similar_count, confidence, and reasoning.
    """
    db = SessionLocal()
    
    similar_count = 0
    neglect_years = 1.0  # default
    urgency_level = 3    # medium
    affected_pop = 500   # default village population estimate
    infra_gap = 0.5      # medium
    healthcare_impact = 0.0
    education_impact = 0.0
    disaster_risk = 0.0

    try:
        # Check for similar submissions in PostgreSQL
        # We search matching category and village first
        # (Using safe SQL to avoid query failures on schema differences)
        from sqlalchemy import text
        tbl_exists = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'citizen_suggestions')")).scalar()
        
        if tbl_exists:
            dup_query = text("""
                SELECT COUNT(*) FROM citizen_suggestions 
                WHERE village = :village AND category = :category
            """)
            similar_count = db.execute(dup_query, {"village": village, "category": category}).scalar() or 0
    except Exception as e:
        print(f"[Priority Agent] Database query warning: {e}")
    finally:
        db.close()

    # Rule-based contextual adjustments from text keywords
    text_lower = text_content.lower()
    
    # Category detection and adjustments
    if any(k in text_lower for k in ("water", "drinking", "pipeline", "pipe", "borewell", "clean water", "पानी", "ನೀರು", "ತೊಂದರೆ")):
        category = "Water & Sanitation"
        infra_gap = 0.8
        healthcare_impact = 0.9  # high healthcare impact for lack of water
        urgency_level = 4
        
    elif any(k in text_lower for k in ("road", "bridge", "connectivity", "pothole", "highway", "ರಸ್ತೆ", "ಸೇತುವೆ", "रास्ता", "गड्ढा")):
        category = "Roads & Connectivity"
        infra_gap = 0.7
        urgency_level = 3
        
    elif any(k in text_lower for k in ("hospital", "phc", "clinic", "doctor", "medicine", "ಆಸ್ಪತ್ರೆ", "औषधि", "दवा")):
        category = "Healthcare & Welfare"
        infra_gap = 0.9
        healthcare_impact = 1.0
        urgency_level = 5  # Critical
        
    elif any(k in text_lower for k in ("school", "teacher", "classroom", "education", "ಶಾಲೆಯ", "स्कूल", "शिक्षक")):
        category = "Education & Schools"
        infra_gap = 0.6
        education_impact = 0.9
        
    elif any(k in text_lower for k in ("flood", "rain", "landslide", "storm", "disaster", "ಪ್ರವಾಹ", "ಬರಗಾಲ", "बाढ़")):
        disaster_risk = 1.0
        urgency_level = 5

    # Urgency analysis
    if any(k in text_lower for k in ("urgent", "immediately", "critical", "emergency", "danger", "ಶೀಘ್ರದಲ್ಲೇ", "तुरंत")):
        urgency_level = min(5, urgency_level + 1)
    if any(k in text_lower for k in ("years", "months", "long time", "since", "ವರ್ಷಗಳಿಂದ", "साल से")):
        neglect_years = 3.5  # historical neglect multiplier

    # Population estimate adjustments based on similar complaints (social signal)
    affected_pop = min(10000, 200 + (similar_count * 150))

    # Multi-factor Priority Scoring Formula
    score = (
        (min(similar_count, 20) / 20) * 25 +   # 25% similar count
        (min(affected_pop, 5000) / 5000) * 20 + # 20% affected population
        (urgency_level / 5) * 15 +              # 15% urgency level
        (min(neglect_years, 5) / 5) * 15 +      # 15% neglect years
        (healthcare_impact * 10) +              # 10% health & safety
        (infra_gap * 10) +                      # 10% infrastructure gap
        (disaster_risk * 5)                     # 5% disaster index
    )
    
    score = round(min(100.0, max(10.0, score)), 1)
    confidence = round(0.75 + (similar_count * 0.02), 2)
    confidence = min(0.99, confidence)

    # Detailed AI Reasoning explanation
    reasoning_parts = []
    if similar_count > 0:
        reasoning_parts.append(f"Supported by {similar_count} similar citizen suggestions in {village}.")
    reasoning_parts.append(f"Infrastructure gap classified as {category.upper()} with urgency level {urgency_level}/5.")
    if neglect_years > 1.0:
        reasoning_parts.append(f"Indicates prolonged issue with historical neglect.")
    if healthcare_impact > 0.5:
        reasoning_parts.append("Direct impact on public health and sanitation safety.")
        
    reasoning = " ".join(reasoning_parts) or "Analyzed against local village demographic indices."

    return score, similar_count, confidence, reasoning
