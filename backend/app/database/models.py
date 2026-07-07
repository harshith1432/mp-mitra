from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database.connection import Base

class IngestionState(Base):
    __tablename__ = "ingestion_state"
    key = Column(String(50), primary_key=True)
    value = Column(String(255))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Pincode(Base):
    __tablename__ = "pincodes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    circlename = Column(String(100))
    regionname = Column(String(100))
    divisionname = Column(String(100))
    officename = Column(String(100))
    pincode = Column(String(20), index=True)
    officetype = Column(String(20))
    delivery = Column(String(20))
    district = Column(String(100), index=True)
    statename = Column(String(100), index=True)
    latitude = Column(Float)
    longitude = Column(Float)

class School(Base):
    __tablename__ = "schools"
    udise_school_code = Column(String(50), primary_key=True)
    school_name = Column(String(255))
    state_name = Column(String(100), index=True)
    district_name = Column(String(100), index=True)
    sub_district_name = Column(String(100))
    village_name = Column(String(255))
    pincode = Column(String(20))
    school_category = Column(String(100))
    school_type = Column(String(100))
    total_teachers = Column(Integer, default=0)
    total_students = Column(Integer, default=0)
    latitude = Column(Float)
    longitude = Column(Float)

class Road(Base):
    __tablename__ = "roads"
    id = Column(Integer, primary_key=True, autoincrement=True)
    road_name = Column(String(255))
    state_name = Column(String(100), index=True)
    district_name = Column(String(100), index=True)
    block_name = Column(String(100))
    habitation_name = Column(String(255))
    upgrade_or_new = Column(String(100))
    surface_type = Column(String(100))
    physical_status = Column(String(100))
    length = Column(Float)
    total_cost = Column(Float)
    population = Column(Integer, default=0)

class HealthCentre(Base):
    __tablename__ = "health_centres"
    id = Column(Integer, primary_key=True, autoincrement=True)
    facility_name = Column(String(255))
    state_name = Column(String(100), index=True)
    district_name = Column(String(100), index=True)
    subdistrict_name = Column(String(100))
    facility_type = Column(String(100)) # CHC, PHC, Subcentre
    facility_address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    active_flag = Column(String(10))
    location_type = Column(String(50)) # Rural / Urban
    type_of_facility = Column(String(50)) # Public / Private

class Habitation(Base):
    __tablename__ = "habitations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    state_name = Column(String(100), index=True)
    district_name = Column(String(100), index=True)
    block_name = Column(String(100))
    panchayat_name = Column(String(100))
    village_name = Column(String(255))
    habitation_name = Column(String(255))
    sc_population = Column(Integer, default=0)
    st_population = Column(Integer, default=0)
    general_population = Column(Integer, default=0)
    status = Column(String(50)) # Fully Covered, Not Covered, etc.
    year = Column(String(20))

class WaterQuality(Base):
    __tablename__ = "water_quality_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    state_name = Column(String(100), index=True)
    district_name = Column(String(100), index=True)
    block_name = Column(String(100))
    panchayat_name = Column(String(100))
    village_name = Column(String(255))
    habitation_name = Column(String(255))
    quality_parameter = Column(String(100)) # Fluoride, Iron, Salinity
    year = Column(String(20))

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, autoincrement=True)
    citizen_name = Column(String(100), default="Anonymous")
    state_name = Column(String(100), index=True)
    district_name = Column(String(100), index=True)
    village_name = Column(String(255))
    text_content = Column(Text)
    category = Column(String(100))
    urgency = Column(String(50))
    affected_population = Column(Integer, default=0)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(String(50), default="Pending") # Pending, Cluster, Verified, In Progress, Completed
    cluster_id = Column(Integer, default=-1) # ID of DBSCAN cluster it belongs to
    created_at = Column(DateTime, default=func.now())

class ProjectRecommendation(Base):
    __tablename__ = "project_recommendations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(255))
    state_name = Column(String(100), index=True)
    district_name = Column(String(100), index=True)
    village_name = Column(String(255))
    description = Column(Text)
    estimated_cost = Column(Float)
    priority_score = Column(Float)
    scheme_matched = Column(String(255))
    beneficiaries = Column(Integer, default=0)
    status = Column(String(50), default="Proposed") # Proposed, Approved, Rejected
    rationale = Column(Text) # Explainable AI SHAP breakdown text
    created_at = Column(DateTime, default=func.now())

class VillageAmenities(Base):
    __tablename__ = "village_amenities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String(150), index=True)
    district = Column(String(150), index=True)
    sub_district = Column(String(150))
    village_name = Column(String(255), index=True)
    year = Column(String(100))
    pre_primary_school = Column(String(100))
    primary_school = Column(String(100))
    middle_school = Column(String(100))
    secondary_school = Column(String(100))
    senior_secondary_school = Column(String(100))
    chc_distance = Column(String(100))
    phc_distance = Column(String(100))
    maternity_centre_distance = Column(String(100))
    allopathic_hospital_distance = Column(String(100))
    veterinary_hospital_distance = Column(String(100))
    mobile_health_clinic_distance = Column(String(100))
    filtered_tap_water = Column(String(100))
    closed_drainage = Column(String(100))
    open_drainage = Column(String(100))
    post_office = Column(String(100))
    telephone_landlines = Column(String(100))
    mobile_phone_coverage = Column(String(100))
    internet_cafe_csc = Column(String(100))
    commercial_bank = Column(String(100))
    cooperative_bank = Column(String(100))
    power_domestic_supply = Column(String(100))
    power_domestic_hours_summer = Column(String(100))
    power_domestic_hours_winter = Column(String(100))
    all_weather_road = Column(String(100))
    population = Column(Integer, default=0)
    sc_population = Column(Integer, default=0)
    st_population = Column(Integer, default=0)

class CrawledScheme(Base):
    __tablename__ = "crawled_schemes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    ministry = Column(String(255))
    category = Column(String(100))
    description = Column(Text)
    eligibility_income = Column(Float, nullable=True)
    eligibility_age_min = Column(Integer, default=0)
    eligibility_age_max = Column(Integer, default=150)
    eligibility_gender = Column(String(50), default="ALL")
    eligibility_occupation = Column(String(255), default="ALL")
    eligibility_state = Column(String(100), default="ALL")
    link = Column(String(255))
    status = Column(String(50), default="Active")
    crawled_at = Column(DateTime, default=func.now())

class CrawledNews(Base):
    __tablename__ = "crawled_news"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    source = Column(String(100))
    summary = Column(Text)
    category = Column(String(100))
    state_name = Column(String(100), index=True)
    district_name = Column(String(100), index=True)
    link = Column(String(255))
    severity_score = Column(Float, default=1.0)
    crawled_at = Column(DateTime, default=func.now())

class CrawledTender(Base):
    __tablename__ = "crawled_tenders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    authority = Column(String(255))
    cost = Column(String(100))
    deadline = Column(String(100))
    category = Column(String(100))
    state_name = Column(String(100), index=True)
    district_name = Column(String(100), index=True)
    link = Column(String(255))
    crawled_at = Column(DateTime, default=func.now())

class CrawlerLog(Base):
    __tablename__ = "crawler_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    status = Column(String(50))
    items_crawled = Column(Integer, default=0)
    message = Column(Text)




class VisitedUrl(Base):
    __tablename__ = "visited_urls"
    url = Column(String(500), primary_key=True)
    topic = Column(String(200))
    crawled_at = Column(DateTime, default=func.now())


# ─── Phase 1: Parliamentary Constituency Mapping ──────────────────────────────

class ParliamentaryConstituency(Base):
    """
    543 Parliamentary Constituencies of India (Lok Sabha seats).
    Source: Election Commission of India (ECI).
    pc_code follows the ECI official numbering scheme.
    """
    __tablename__ = "parliamentary_constituencies"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    pc_code      = Column(String(10), unique=True, index=True)   # ECI code e.g. "S14001"
    pc_name      = Column(String(255), index=True)               # e.g. "MYSURU"
    state_name   = Column(String(100), index=True)
    total_voters = Column(Integer, default=0)
    mp_name      = Column(String(255), nullable=True)
    mp_party     = Column(String(100), nullable=True)
    mp_since     = Column(String(20), nullable=True)             # year elected
    area_sq_km   = Column(Float, nullable=True)
    created_at   = Column(DateTime, default=func.now())
    updated_at   = Column(DateTime, default=func.now(), onupdate=func.now())


class AssemblyConstituency(Base):
    """
    ~4,120 Assembly Constituencies (Vidhan Sabha seats).
    Each AC belongs to exactly one Parliamentary Constituency.
    """
    __tablename__ = "assembly_constituencies"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    ac_code    = Column(String(10), unique=True, index=True)     # ECI AC code
    ac_name    = Column(String(255), index=True)
    pc_code    = Column(String(10), ForeignKey("parliamentary_constituencies.pc_code"), index=True)
    state_name = Column(String(100), index=True)
    mla_name   = Column(String(255), nullable=True)
    mla_party  = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now())


class ConstituencyVillageMap(Base):
    """
    Master join table: Village → Panchayat → Taluk → District → AC → PC.
    This is the backbone of the national hierarchy — every village entry
    in MP Mitra can be resolved to its Parliamentary Constituency through this table.
    Source: LGD (Local Government Directory) + ECI delimitation data.
    """
    __tablename__ = "constituency_village_map"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    state_name     = Column(String(100), index=True)
    district_name  = Column(String(100), index=True)
    taluk_name     = Column(String(100), index=True)
    panchayat_name = Column(String(255))
    village_name   = Column(String(255), index=True)
    village_code   = Column(String(20), nullable=True)           # LGD village code
    ac_code        = Column(String(10), ForeignKey("assembly_constituencies.ac_code"), nullable=True, index=True)
    pc_code        = Column(String(10), ForeignKey("parliamentary_constituencies.pc_code"), nullable=True, index=True)
    latitude       = Column(Float, nullable=True)
    longitude      = Column(Float, nullable=True)
    population     = Column(Integer, default=0)
    created_at     = Column(DateTime, default=func.now())


class ConstituencyBudgetAllocation(Base):
    """
    Budget allocations and MPLADS fund utilization per Parliamentary Constituency.
    MPs get ₹5 crore/year under MPLADS. This tracks how it is spent.
    """
    __tablename__ = "constituency_budget"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    pc_code      = Column(String(10), ForeignKey("parliamentary_constituencies.pc_code"), index=True)
    scheme_name  = Column(String(255))
    project_name = Column(String(255), nullable=True)
    amount_cr    = Column(Float, default=0.0)
    year         = Column(String(10))                            # e.g. "2024-25"
    status       = Column(String(50), default="Proposed")       # Released / Pending / Utilized / Completed
    district     = Column(String(100), nullable=True)
    village      = Column(String(255), nullable=True)
    created_at   = Column(DateTime, default=func.now())
