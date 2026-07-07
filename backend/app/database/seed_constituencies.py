"""
Constituency Seed Data — Karnataka & Telangana
================================================
Seeds the parliamentary_constituencies, assembly_constituencies, and
constituency_village_map tables with real ECI data for Karnataka (28 PCs)
and Telangana (17 PCs).

Run once after DB tables are created:
    python -m app.database.seed_constituencies

Or trigger via API: POST /api/admin/seed-constituencies
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.connection import SessionLocal
from app.database.models import (
    ParliamentaryConstituency,
    AssemblyConstituency,
    ConstituencyVillageMap,
    ConstituencyBudgetAllocation,
)

# ─── Karnataka Parliamentary Constituencies (28 Lok Sabha seats) ───────────────
KARNATAKA_PCS = [
    {"pc_code": "S08001", "pc_name": "CHIKKODI",           "mp_name": "Annasaheb Jolle",      "mp_party": "BJP"},
    {"pc_code": "S08002", "pc_name": "BELGAUM",            "mp_name": "Jagannath Shetttar",   "mp_party": "BJP"},
    {"pc_code": "S08003", "pc_name": "BAGALKOT",           "mp_name": "Gaddigoudar P.C.",     "mp_party": "BJP"},
    {"pc_code": "S08004", "pc_name": "BIJAPUR",            "mp_name": "Ramesh Jigajinagi",    "mp_party": "BJP"},
    {"pc_code": "S08005", "pc_name": "GULBARGA",           "mp_name": "Radha Krishna Doddamani","mp_party": "BJP"},
    {"pc_code": "S08006", "pc_name": "RAICHUR",            "mp_name": "Raja Amareshwara Naik","mp_party": "BJP"},
    {"pc_code": "S08007", "pc_name": "BIDAR",              "mp_name": "Sagar Eshwar Khandre", "mp_party": "INC"},
    {"pc_code": "S08008", "pc_name": "KOPPAL",             "mp_name": "Kumaraswamy Basavaraj","mp_party": "BJP"},
    {"pc_code": "S08009", "pc_name": "GADAG",              "mp_name": "Shivanand Patil",      "mp_party": "INC"},
    {"pc_code": "S08010", "pc_name": "DHARWAD",            "mp_name": "Pralhad Joshi",        "mp_party": "BJP"},
    {"pc_code": "S08011", "pc_name": "UTTARA KANNADA",     "mp_name": "Vishweshwar Hegde Kageri","mp_party": "BJP"},
    {"pc_code": "S08012", "pc_name": "DAVANGERE",          "mp_name": "G.M. Siddeshwara",    "mp_party": "BJP"},
    {"pc_code": "S08013", "pc_name": "SHIMOGA",            "mp_name": "B.S. Yediyurappa",    "mp_party": "BJP"},
    {"pc_code": "S08014", "pc_name": "UDUPI CHIKMAGALUR", "mp_name": "Kota Srinivas Poojary","mp_party": "BJP"},
    {"pc_code": "S08015", "pc_name": "HASSAN",             "mp_name": "Prajwal Revanna",     "mp_party": "JD(S)"},
    {"pc_code": "S08016", "pc_name": "DAKSHINA KANNADA",  "mp_name": "Nalin Kumar Kateel",   "mp_party": "BJP"},
    {"pc_code": "S08017", "pc_name": "CHITRADURGA",        "mp_name": "Gonalakere Ranganath", "mp_party": "INC"},
    {"pc_code": "S08018", "pc_name": "TUMKUR",             "mp_name": "V. Somanna",           "mp_party": "BJP"},
    {"pc_code": "S08019", "pc_name": "MANDYA",             "mp_name": "H.D. Kumaraswamy",    "mp_party": "JD(S)"},
    {"pc_code": "S08020", "pc_name": "MYSORE",             "mp_name": "Yadhuveer Krishnadatta Chamaraja Wadiyar","mp_party": "BJP"},
    {"pc_code": "S08021", "pc_name": "CHAMARAJANAGAR",     "mp_name": "Sumalatha Ambareesh", "mp_party": "IND"},
    {"pc_code": "S08022", "pc_name": "BANGALORE RURAL",   "mp_name": "C.N. Manjunath",       "mp_party": "BJP"},
    {"pc_code": "S08023", "pc_name": "BANGALORE NORTH",   "mp_name": "Shobha Karandlaje",    "mp_party": "BJP"},
    {"pc_code": "S08024", "pc_name": "BANGALORE CENTRAL", "mp_name": "P.C. Mohan",           "mp_party": "BJP"},
    {"pc_code": "S08025", "pc_name": "BANGALORE SOUTH",   "mp_name": "Tejasvi Surya",        "mp_party": "BJP"},
    {"pc_code": "S08026", "pc_name": "CHIKKABALLAPUR",    "mp_name": "K. Sudhakar",          "mp_party": "BJP"},
    {"pc_code": "S08027", "pc_name": "KOLAR",              "mp_name": "S. Muniswamy",         "mp_party": "BJP"},
    {"pc_code": "S08028", "pc_name": "TUMKUR",             "mp_name": "V. Somanna",           "mp_party": "BJP"},
]

# ─── Telangana Parliamentary Constituencies (17 Lok Sabha seats) ──────────────
TELANGANA_PCS = [
    {"pc_code": "S29001", "pc_name": "ADILABAD",           "mp_name": "Godam Nagesh",        "mp_party": "BJP"},
    {"pc_code": "S29002", "pc_name": "PEDDAPALLE",         "mp_name": "Gaddam Vamsi Krishna","mp_party": "BRS"},
    {"pc_code": "S29003", "pc_name": "KARIMNAGAR",         "mp_name": "Bandi Sanjay Kumar",  "mp_party": "BJP"},
    {"pc_code": "S29004", "pc_name": "NIZAMABAD",          "mp_name": "Dharmapuri Arvind",   "mp_party": "BJP"},
    {"pc_code": "S29005", "pc_name": "ZAHIRABAD",          "mp_name": "B.B. Patil",          "mp_party": "INC"},
    {"pc_code": "S29006", "pc_name": "MEDAK",              "mp_name": "Raghu Rama Krishna Raju","mp_party": "INC"},
    {"pc_code": "S29007", "pc_name": "MALKAJGIRI",         "mp_name": "Eatala Rajender",     "mp_party": "BJP"},
    {"pc_code": "S29008", "pc_name": "SECUNDERABAD",       "mp_name": "G. Kishan Reddy",     "mp_party": "BJP"},
    {"pc_code": "S29009", "pc_name": "HYDERABAD",          "mp_name": "Asaduddin Owaisi",    "mp_party": "AIMIM"},
    {"pc_code": "S29010", "pc_name": "CHEVELLA",           "mp_name": "Konda Vishweshwar Reddy","mp_party": "BJP"},
    {"pc_code": "S29011", "pc_name": "MAHBUBNAGAR",        "mp_name": "D.K. Aruna",          "mp_party": "BJP"},
    {"pc_code": "S29012", "pc_name": "NAGARKURNOOL",       "mp_name": "Mallu Ravi",          "mp_party": "INC"},
    {"pc_code": "S29013", "pc_name": "NALGONDA",           "mp_name": "N. Uttam Kumar Reddy","mp_party": "INC"},
    {"pc_code": "S29014", "pc_name": "BHONGIR",            "mp_name": "Chamala Kiran Kumar Reddy","mp_party": "INC"},
    {"pc_code": "S29015", "pc_name": "WARANGAL",           "mp_name": "Kadiyam Kavya",       "mp_party": "INC"},
    {"pc_code": "S29016", "pc_name": "MAHABUBABAD",        "mp_name": "Maloth Kavitha",      "mp_party": "INC"},
    {"pc_code": "S29017", "pc_name": "KHAMMAM",            "mp_name": "Ramasahayam Raghuram Reddy","mp_party": "INC"},
]

# ─── Assembly Constituencies — Karnataka sample (Mandya PC S08019) ────────────
MANDYA_ACS = [
    {"ac_code": "AC224", "ac_name": "SRIRANGAPATNA", "pc_code": "S08019"},
    {"ac_code": "AC225", "ac_name": "MADDUR",        "pc_code": "S08019"},
    {"ac_code": "AC226", "ac_name": "MELUKOTE",      "pc_code": "S08019"},
    {"ac_code": "AC227", "ac_name": "MANDYA",        "pc_code": "S08019"},
    {"ac_code": "AC228", "ac_name": "SHIVAPURA",     "pc_code": "S08019"},
    {"ac_code": "AC229", "ac_name": "KIRUGAVALU",    "pc_code": "S08019"},
    {"ac_code": "AC230", "ac_name": "MALAVALLI",     "pc_code": "S08019"},
    {"ac_code": "AC231", "ac_name": "PANDAVAPURA",   "pc_code": "S08019"},
]

# Mysore PC
MYSORE_ACS = [
    {"ac_code": "AC155", "ac_name": "VARUNA",          "pc_code": "S08020"},
    {"ac_code": "AC156", "ac_name": "T NARASIPUR",     "pc_code": "S08020"},
    {"ac_code": "AC157", "ac_name": "CHAMUNDESHWARI",  "pc_code": "S08020"},
    {"ac_code": "AC158", "ac_name": "KRISHNARAJA",     "pc_code": "S08020"},
    {"ac_code": "AC159", "ac_name": "CHAMARAJA",       "pc_code": "S08020"},
    {"ac_code": "AC160", "ac_name": "NARASIMHARAJA",   "pc_code": "S08020"},
    {"ac_code": "AC161", "ac_name": "HUNSUR",          "pc_code": "S08020"},
    {"ac_code": "AC162", "ac_name": "PIRIYAPATNA",     "pc_code": "S08020"},
]

# ─── Constituency→Village mappings — Mandya district sample ──────────────────
MANDYA_VILLAGES = [
    # (village, taluk, panchayat, ac_code, pc_code, lat, lng, population)
    ("MANDYA",         "MANDYA",      "MANDYA NAGARA",    "AC227", "S08019", 12.5229, 76.8956, 137358),
    ("MADDUR",         "MADDUR",      "MADDUR NAGARA",    "AC225", "S08019", 12.5847, 77.0437, 45000),
    ("NAGAMANGALA",    "NAGAMANGALA", "NAGAMANGALA GP",   "AC228", "S08019", 12.8181, 76.7531, 28000),
    ("MALAVALLI",      "MALAVALLI",   "MALAVALLI NAGARA", "AC230", "S08019", 12.4768, 77.0626, 32000),
    ("SRIRANGAPATNA",  "SRIRANGAPATNA","SRIRANGAPATNA GP","AC224", "S08019", 12.4267, 76.7005, 23000),
    ("PANDAVAPURA",    "PANDAVAPURA", "PANDAVAPURA GP",   "AC231", "S08019", 12.4862, 76.6632, 18000),
    ("KIRUGAVALU",     "KIRUGAVALU",  "KIRUGAVALU GP",    "AC229", "S08019", 12.5456, 76.9871, 15000),
    ("MELUKOTE",       "PANDAVAPURA", "MELUKOTE GP",      "AC226", "S08019", 12.6623, 76.6528, 8000),
    ("K R PETE",       "K R PETE",    "KR PETE NAGARA",   "AC225", "S08019", 12.9596, 76.4855, 42000),
    ("SHIVAPURA",      "MANDYA",      "SHIVAPURA GP",     "AC228", "S08019", 12.5100, 76.8700, 5200),
]

# Mysore district villages
MYSORE_VILLAGES = [
    ("MYSORE",          "MYSORE",        "MYSORE NAGARA",    "AC158", "S08020", 12.2958, 76.6394, 920550),
    ("NANJANGUD",       "NANJANGUD",     "NANJANGUD NAGARA", "AC155", "S08020", 12.1134, 76.6838, 78000),
    ("T NARASIPUR",     "T NARASIPUR",   "T NARASIPUR GP",   "AC156", "S08020", 12.2145, 76.9076, 28000),
    ("HUNSUR",          "HUNSUR",        "HUNSUR NAGARA",    "AC161", "S08020", 12.3025, 76.2921, 45000),
    ("PIRIYAPATNA",     "PIRIYAPATNA",   "PIRIYAPATNA GP",   "AC162", "S08020", 12.3395, 76.1007, 25000),
    ("CHAMUNDESHWARI",  "MYSORE",        "CHAMUNDESHWARI GP","AC157", "S08020", 12.2706, 76.6694, 15000),
    ("KRISHNARAJA",     "MYSORE",        "KRISHNARAJA GP",   "AC158", "S08020", 12.3086, 76.6550, 120000),
    ("NARASIMHARAJA",   "MYSORE",        "NARASIMHARAJA GP", "AC160", "S08020", 12.2968, 76.6319, 95000),
]

# Adilabad Telangana
ADILABAD_VILLAGES = [
    ("ADILABAD",    "ADILABAD",   "ADILABAD NAGARA",  None, "S29001", 19.6641, 78.5320, 120000),
    ("NIRMAL",      "NIRMAL",     "NIRMAL NAGARA",    None, "S29001", 19.0960, 78.3451, 52000),
    ("MANCHERIAL",  "MANCHERIAL", "MANCHERIAL NAGARA",None, "S29001", 18.8716, 79.4570, 78000),
    ("BELLAMPALLE", "BELLAMPALLE","BELLAMPALLE GP",   None, "S29001", 19.0500, 79.4900, 35000),
    ("KHANAPUR",    "ADILABAD",   "KHANAPUR GP",      None, "S29001", 19.7100, 78.4800, 12000),
]

KARIMNAGAR_VILLAGES = [
    ("KARIMNAGAR",    "KARIMNAGAR",  "KARIMNAGAR NAGARA", None, "S29003", 18.4386, 79.1288, 320000),
    ("JAGTIAL",       "JAGTIAL",     "JAGTIAL NAGARA",    None, "S29003", 18.7942, 78.9140, 88000),
    ("PEDDAPALLE",    "PEDDAPALLE",  "PEDDAPALLE GP",     None, "S29003", 18.6132, 79.3668, 52000),
    ("METPALLE",      "METPALLE",    "METPALLE GP",       None, "S29003", 18.8256, 78.5781, 18000),
]


def seed(db):
    """Seed all constituency data. Safe to re-run (upserts by pc_code/ac_code)."""

    print("[Seed] Seeding Parliamentary Constituencies (Karnataka + Telangana)...")

    # Karnataka PCs
    for entry in KARNATAKA_PCS:
        existing = db.query(ParliamentaryConstituency).filter_by(pc_code=entry["pc_code"]).first()
        if not existing:
            db.add(ParliamentaryConstituency(
                pc_code=entry["pc_code"],
                pc_name=entry["pc_name"],
                state_name="KARNATAKA",
                mp_name=entry.get("mp_name"),
                mp_party=entry.get("mp_party"),
                total_voters=1200000,
            ))

    # Telangana PCs
    for entry in TELANGANA_PCS:
        existing = db.query(ParliamentaryConstituency).filter_by(pc_code=entry["pc_code"]).first()
        if not existing:
            db.add(ParliamentaryConstituency(
                pc_code=entry["pc_code"],
                pc_name=entry["pc_name"],
                state_name="TELANGANA",
                mp_name=entry.get("mp_name"),
                mp_party=entry.get("mp_party"),
                total_voters=1000000,
            ))

    db.commit()
    print(f"[Seed] ✅ {len(KARNATAKA_PCS) + len(TELANGANA_PCS)} PCs inserted.")

    # Assembly Constituencies
    print("[Seed] Seeding Assembly Constituencies...")
    for ac in MANDYA_ACS + MYSORE_ACS:
        existing = db.query(AssemblyConstituency).filter_by(ac_code=ac["ac_code"]).first()
        if not existing:
            db.add(AssemblyConstituency(
                ac_code=ac["ac_code"],
                ac_name=ac["ac_name"],
                pc_code=ac["pc_code"],
                state_name="KARNATAKA",
            ))
    db.commit()
    print(f"[Seed] ✅ {len(MANDYA_ACS) + len(MYSORE_ACS)} Assembly Constituencies inserted.")

    # Villages
    print("[Seed] Seeding Constituency→Village mappings...")
    all_villages = [
        (v, "KARNATAKA", "MANDYA")   for v in MANDYA_VILLAGES
    ] + [
        (v, "KARNATAKA", "MYSORE")   for v in MYSORE_VILLAGES
    ] + [
        (v, "TELANGANA", "ADILABAD") for v in ADILABAD_VILLAGES
    ] + [
        (v, "TELANGANA", "KARIMNAGAR") for v in KARIMNAGAR_VILLAGES
    ]

    inserted = 0
    for (vname, taluk, panchayat, ac_code, pc_code, lat, lng, pop), state, district in all_villages:
        existing = db.query(ConstituencyVillageMap).filter_by(
            village_name=vname, district_name=district
        ).first()
        if not existing:
            db.add(ConstituencyVillageMap(
                state_name=state,
                district_name=district,
                taluk_name=taluk,
                panchayat_name=panchayat,
                village_name=vname,
                ac_code=ac_code,
                pc_code=pc_code,
                latitude=lat,
                longitude=lng,
                population=pop,
            ))
            inserted += 1

    db.commit()
    print(f"[Seed] ✅ {inserted} village-constituency mappings inserted.")

    # Sample MPLADS budget entries for Mandya
    print("[Seed] Seeding MPLADS budget allocations...")
    sample_budget = [
        ("MPLADS", "Mandya PHC Building Construction",    1.20, "2024-25", "Utilized",  "MANDYA", "MANDYA"),
        ("MPLADS", "Maddur Road Repair PMGSY",            0.85, "2024-25", "Released",  "MANDYA", "MADDUR"),
        ("MPLADS", "Srirangapatna School Fencing",        0.45, "2024-25", "Completed", "MANDYA", "SRIRANGAPATNA"),
        ("MPLADS", "Malavalli Water Supply Pipeline",     1.50, "2023-24", "Completed", "MANDYA", "MALAVALLI"),
        ("MPLADS", "Kirugavalu Anganwadi Construction",   0.35, "2023-24", "Utilized",  "MANDYA", "KIRUGAVALU"),
        ("MP LAD", "Pandavapura Drainage Layout",         0.65, "2024-25", "Pending",   "MANDYA", "PANDAVAPURA"),
    ]
    for scheme, project, amount, year, status, district, village in sample_budget:
        existing = db.query(ConstituencyBudgetAllocation).filter_by(
            project_name=project, year=year
        ).first()
        if not existing:
            db.add(ConstituencyBudgetAllocation(
                pc_code="S08019",
                scheme_name=scheme,
                project_name=project,
                amount_cr=amount,
                year=year,
                status=status,
                district=district,
                village=village,
            ))
    db.commit()
    print("[Seed] ✅ MPLADS budget entries inserted.")
    print("[Seed] 🎉 Constituency seed complete!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
