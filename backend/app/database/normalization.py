"""
Spelling Normalization Utility for India Districts and States
============================================================
Resolves names between federal sources (UDISE, PMGSY, JJM), Election Commission
constituency maps, and local UI dropdowns.
"""

def normalize_district_name(name: str) -> str:
    if not name:
        return ""
    name = name.strip().upper()
    
    # Map all variants to the ECI Lok Sabha constituency / UI dropdown canonical names
    synonyms = {
        # Karnataka
        "BAGALKOTE": "BAGALKOT",
        "BAGALKOT": "BAGALKOT",
        "BANGALORE URBAN": "BENGALURU URBAN",
        "BANGALORE RURAL": "BENGALURU RURAL",
        "MYSORE": "MYSURU",
        "MYSOOR": "MYSURU",
        "TUMKUR": "TUMAKURU",
        "BELGAUM": "BELAGAVI",
        "GULBARGA": "KALABURAGI",
        "BELLARY": "BALLARI",
        "BIJAPUR": "VIJAYAPURA",
        "CHIKMAGALUR": "CHIKKAMAGALURU",
        "SHIMOGA": "SHIVAMOGGA",
        "VIJAYANAGAR": "VIJAYANAGARA",
        "VIJAYNAGAR": "VIJAYANAGARA",
        "CHAMARAJANAGAR": "CHAMARAJANAGARA",
        "CHIKKABALLAPUR": "CHIKKABALLAPURA",
        
        # Telangana
        "MAHABUBNAGAR": "MAHABUBNAGAR",
        "MAHBUBNAGAR": "MAHABUBNAGAR",
        "JOGULAMBA GADWAL": "JOGULAMBA GADWAL",
        "GADWAL": "JOGULAMBA GADWAL",
        "KOMARAM BHEEM ASIFABAD": "KOMARAM BHEEM",
        "ASIFABAD": "KOMARAM BHEEM",
        "WARANGAL RURAL": "WARANGAL",
        "WARANGAL URBAN": "HANUMAKONDA",
    }
    
    # Strip common suffixes/prefixes if not in synonyms
    if name not in synonyms:
        # E.g. "BAGALKOTE DISTRICT" -> "BAGALKOT"
        clean = name.replace("DISTRICT", "").replace("RURAL", "").replace("URBAN", "").strip()
        if clean in synonyms:
            return synonyms[clean]
            
    return synonyms.get(name, name)

def normalize_state_name(name: str) -> str:
    if not name:
        return ""
    name = name.strip().upper()
    
    # Normalise spelling variations
    synonyms = {
        "ORISSA": "ODISHA",
        "PONDICHERRY": "PUDUCHERRY",
        "UTTARANCHAL": "UTTARAKHAND",
    }
    return synonyms.get(name, name)
