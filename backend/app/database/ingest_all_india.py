import os
import csv
import sys
import sqlite3
import time
from pathlib import Path

# Add project root and backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.dataset_manager import dataset_manager

# Scan and extract dataset zip from workspace
here = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(here, "..", "..", ".."))
dataset_manager.import_local_datasets_from_workspace(root_dir)

DATASET_DIR = dataset_manager.get_dataset_dir()
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mpmitra_fallback.db")

def init_db(conn):
    print("Creating tables in SQLite database...")
    cursor = conn.cursor()
    
    # 1. Pincodes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pincodes (
        pincode VARCHAR(20) PRIMARY KEY,
        circlename VARCHAR(150),
        regionname VARCHAR(150),
        divisionname VARCHAR(150),
        officename VARCHAR(200),
        officetype VARCHAR(50),
        delivery VARCHAR(50),
        district VARCHAR(150),
        statename VARCHAR(150),
        latitude REAL,
        longitude REAL
    )
    """)
    
    # 2. Health Centres
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS health_centres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_name VARCHAR(100),
        district_name VARCHAR(100),
        subdistrict_name VARCHAR(100),
        facility_type VARCHAR(100),
        facility_name VARCHAR(250),
        facility_address TEXT,
        latitude REAL,
        longitude REAL,
        active_flag VARCHAR(20),
        location_type VARCHAR(50),
        type_of_facility VARCHAR(100)
    )
    """)
    
    # 3. Roads
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        road_name VARCHAR(250),
        state_name VARCHAR(100),
        district_name VARCHAR(100),
        block_name VARCHAR(100),
        habitation_name VARCHAR(250),
        upgrade_or_new VARCHAR(50),
        surface_type VARCHAR(100),
        physical_status VARCHAR(100),
        length REAL,
        total_cost REAL,
        population INTEGER
    )
    """)
    
    # 4. Schools
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schools (
        udise_school_code VARCHAR(50) PRIMARY KEY,
        school_name VARCHAR(250),
        state_name VARCHAR(100),
        district_name VARCHAR(100),
        sub_district_name VARCHAR(100),
        village_name VARCHAR(150),
        pincode VARCHAR(20),
        school_category VARCHAR(150),
        school_type VARCHAR(50),
        total_teachers INTEGER,
        total_students INTEGER,
        latitude REAL,
        longitude REAL
    )
    """)
    
    # 5. Habitations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habitations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_name VARCHAR(100),
        district_name VARCHAR(100),
        block_name VARCHAR(100),
        panchayat_name VARCHAR(150),
        village_name VARCHAR(150),
        habitation_name VARCHAR(250),
        sc_population INTEGER,
        st_population INTEGER,
        general_population INTEGER,
        status VARCHAR(100),
        year VARCHAR(20)
    )
    """)
    
    # 6. Water Quality
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS water_quality_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_name VARCHAR(100),
        district_name VARCHAR(100),
        block_name VARCHAR(100),
        panchayat_name VARCHAR(150),
        village_name VARCHAR(150),
        habitation_name VARCHAR(250),
        quality_parameter VARCHAR(250),
        year VARCHAR(20)
    )
    """)
    
    # 7. Parliamentary Constituencies
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parliamentary_constituencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pc_code VARCHAR(10) UNIQUE,
        pc_name VARCHAR(255),
        state_name VARCHAR(100),
        total_voters INTEGER,
        mp_name VARCHAR(255),
        mp_party VARCHAR(100),
        mp_since VARCHAR(20),
        area_sq_km REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 8. Assembly Constituencies
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assembly_constituencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ac_code VARCHAR(10) UNIQUE,
        ac_name VARCHAR(255),
        pc_code VARCHAR(10),
        state_name VARCHAR(100),
        mla_name VARCHAR(255),
        mla_party VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 9. Constituency Village Map
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS constituency_village_map (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_name VARCHAR(100),
        district_name VARCHAR(100),
        taluk_name VARCHAR(100),
        panchayat_name VARCHAR(255),
        village_name VARCHAR(255),
        village_code VARCHAR(20),
        ac_code VARCHAR(10),
        pc_code VARCHAR(10),
        latitude REAL,
        longitude REAL,
        population INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 10. Constituency Budget
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS constituency_budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pc_code VARCHAR(10),
        scheme_name VARCHAR(255),
        project_name VARCHAR(255),
        amount_cr REAL,
        year VARCHAR(10),
        status VARCHAR(50),
        district VARCHAR(100),
        village VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()

def ingest_pincodes(conn):
    filepath = os.path.join(DATASET_DIR, "pincode.csv")
    if not os.path.exists(filepath):
        print(f"Pincode file not found: {filepath}")
        return
        
    print("Ingesting Pincodes...")
    start = time.time()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pincodes")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        next(reader) # skip header
        batch = []
        count = 0
        
        for row in reader:
            if len(row) < 11:
                continue
            try:
                batch.append((
                    row[4], row[0], row[1], row[2], row[3], row[5], row[6],
                    row[7].strip().upper(), row[8].strip().upper(),
                    float(row[9]) if row[9] else 0.0,
                    float(row[10]) if row[10] else 0.0
                ))
                count += 1
            except ValueError:
                continue
                
            if len(batch) >= 10000:
                cursor.executemany("""
                INSERT OR IGNORE INTO pincodes 
                (pincode, circlename, regionname, divisionname, officename, officetype, delivery, district, statename, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                conn.commit()
                batch = []
                print(f"  Processed {count} pincodes...")
                
        if batch:
            cursor.executemany("""
            INSERT OR IGNORE INTO pincodes 
            (pincode, circlename, regionname, divisionname, officename, officetype, delivery, district, statename, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            
    print(f"Finished Pincodes: {count} rows in {time.time() - start:.2f}s")

def ingest_health_centres(conn):
    filepath = os.path.join(DATASET_DIR, "geocode_health_centre.csv")
    if not os.path.exists(filepath):
        print(f"Health centre file not found: {filepath}")
        return
        
    print("Ingesting Health Centres...")
    start = time.time()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM health_centres")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        next(reader)
        batch = []
        count = 0
        
        for row in reader:
            if len(row) < 12:
                continue
            try:
                batch.append((
                    row[0].strip().upper(), row[1].strip().upper(), row[2].strip().upper(),
                    row[3], row[4], row[5] if len(row) > 5 else "",
                    float(row[6]) if row[6] and row[6].lower() != 'nan' else 0.0,
                    float(row[7]) if row[7] and row[7].lower() != 'nan' else 0.0,
                    row[8], row[10], row[11]
                ))
                count += 1
            except ValueError:
                continue
                
            if len(batch) >= 10000:
                cursor.executemany("""
                INSERT INTO health_centres 
                (state_name, district_name, subdistrict_name, facility_type, facility_name, facility_address, latitude, longitude, active_flag, location_type, type_of_facility)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                conn.commit()
                batch = []
                
        if batch:
            cursor.executemany("""
            INSERT INTO health_centres 
            (state_name, district_name, subdistrict_name, facility_type, facility_name, facility_address, latitude, longitude, active_flag, location_type, type_of_facility)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            
    print(f"Finished Health Centres: {count} rows in {time.time() - start:.2f}s")

def ingest_roads(conn):
    filepath = os.path.join(DATASET_DIR, "road.csv")
    if not os.path.exists(filepath):
        print(f"Road file not found: {filepath}")
        return
        
    print("Ingesting Roads...")
    start = time.time()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM roads")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        next(reader)
        batch = []
        count = 0
        
        for row in reader:
            if len(row) < 31:
                continue
            try:
                batch.append((
                    row[9], row[2].strip().upper(), row[4].strip().upper(), row[6], row[8], row[11], row[12], row[13],
                    float(row[20]) if row[20] else 0.0,
                    float(row[30]) if row[30] else 0.0,
                    int(float(row[31])) if row[31] and row[31].lower() != 'none' else 0
                ))
                count += 1
            except ValueError:
                continue
                
            if len(batch) >= 10000:
                cursor.executemany("""
                INSERT INTO roads 
                (road_name, state_name, district_name, block_name, habitation_name, upgrade_or_new, surface_type, physical_status, length, total_cost, population)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                conn.commit()
                batch = []
                print(f"  Processed {count} roads...")
                
        if batch:
            cursor.executemany("""
            INSERT INTO roads 
            (road_name, state_name, district_name, block_name, habitation_name, upgrade_or_new, surface_type, physical_status, length, total_cost, population)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            
    print(f"Finished Roads: {count} rows in {time.time() - start:.2f}s")

def ingest_schools(conn):
    filepath = os.path.join(DATASET_DIR, "school.csv")
    if not os.path.exists(filepath):
        print(f"School file not found: {filepath}")
        return
        
    print("Ingesting Schools...")
    start = time.time()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schools")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        next(reader)
        batch = []
        count = 0
        
        for row in reader:
            if len(row) < 31:
                continue
            try:
                total_stu = 0
                for idx in range(31, 44):
                    if idx < len(row) and row[idx]:
                        try:
                            total_stu += int(float(row[idx]))
                        except ValueError:
                            pass
                            
                batch.append((
                    row[14], row[13], row[2].strip().upper(), row[4].strip().upper(), row[6], row[9], row[11], row[15], row[16],
                    int(float(row[30])) if row[30] and row[30].lower() != 'none' else 0,
                    total_stu,
                    float(row[20]) if row[20] and row[20].lower() != 'none' else 0.0,
                    float(row[19]) if row[19] and row[19].lower() != 'none' else 0.0
                ))
                count += 1
            except ValueError:
                continue
                
            if len(batch) >= 10000:
                cursor.executemany("""
                INSERT OR IGNORE INTO schools 
                (udise_school_code, school_name, state_name, district_name, sub_district_name, village_name, pincode, school_category, school_type, total_teachers, total_students, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                conn.commit()
                batch = []
                print(f"  Processed {count} schools...")
                
        if batch:
            cursor.executemany("""
            INSERT OR IGNORE INTO schools 
            (udise_school_code, school_name, state_name, district_name, sub_district_name, village_name, pincode, school_category, school_type, total_teachers, total_students, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            
    print(f"Finished Schools: {count} rows in {time.time() - start:.2f}s")

def ingest_habitations(conn):
    filepath = os.path.join(DATASET_DIR, "Basic_habitation_info_2012_04_01.csv")
    if not os.path.exists(filepath):
        print(f"Habitation file not found: {filepath}")
        return
        
    print("Ingesting Habitations...")
    start = time.time()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habitations")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        next(reader)
        batch = []
        count = 0
        
        for row in reader:
            if len(row) < 13:
                continue
            try:
                batch.append((
                    row[0].strip().upper(), row[1].strip().upper(), row[2], row[3], row[4], row[5],
                    int(row[6]) if row[6] else 0,
                    int(row[7]) if row[7] else 0,
                    int(row[8]) if row[8] else 0,
                    row[12], row[15] if len(row) > 15 else ""
                ))
                count += 1
            except ValueError:
                continue
                
            if len(batch) >= 10000:
                cursor.executemany("""
                INSERT INTO habitations 
                (state_name, district_name, block_name, panchayat_name, village_name, habitation_name, sc_population, st_population, general_population, status, year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                conn.commit()
                batch = []
                print(f"  Processed {count} habitations...")
                
        if batch:
            cursor.executemany("""
            INSERT INTO habitations 
            (state_name, district_name, block_name, panchayat_name, village_name, habitation_name, sc_population, st_population, general_population, status, year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            
    print(f"Finished Habitations: {count} rows in {time.time() - start:.2f}s")

def ingest_water_quality(conn):
    filepath = os.path.join(DATASET_DIR, "Water_quality_affected_habitation_2012_04_01.csv")
    if not os.path.exists(filepath):
        print(f"Water quality file not found: {filepath}")
        return
        
    print("Ingesting Water Quality...")
    start = time.time()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM water_quality_records")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        next(reader)
        batch = []
        count = 0
        
        for row in reader:
            if len(row) < 8:
                continue
            try:
                batch.append((
                    row[0].strip().upper(), row[1].strip().upper(), row[2], row[3], row[4], row[5], row[6], row[7]
                ))
                count += 1
            except ValueError:
                continue
                
            if len(batch) >= 10000:
                cursor.executemany("""
                INSERT INTO water_quality_records 
                (state_name, district_name, block_name, panchayat_name, village_name, habitation_name, quality_parameter, year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                conn.commit()
                batch = []
                
        if batch:
            cursor.executemany("""
            INSERT INTO water_quality_records 
            (state_name, district_name, block_name, panchayat_name, village_name, habitation_name, quality_parameter, year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            
    print(f"Finished Water Quality: {count} rows in {time.time() - start:.2f}s")

def main():
    print(f"Master CSV Location: {DATASET_DIR}")
    print(f"Target Database File: {DB_PATH}")
    
    if os.path.exists(DB_PATH):
        print("Existing fallback database found. Overwriting...")
        try:
            os.remove(DB_PATH)
        except Exception as e:
            print(f"Could not remove database file (is the server running?): {e}")
            return
            
    conn = sqlite3.connect(DB_PATH)
    try:
        # Optimized SQLite write settings
        conn.execute("PRAGMA journal_mode = OFF")
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute("PRAGMA cache_size = 100000")
        
        init_db(conn)
        
        ingest_pincodes(conn)
        ingest_health_centres(conn)
        ingest_roads(conn)
        ingest_schools(conn)
        ingest_habitations(conn)
        ingest_water_quality(conn)
        
        # Seed ECI constituencies
        from app.database.seed_constituencies import seed_sqlite
        try:
            print("Seeding Parliamentary Constituencies from seed file...")
            seed_sqlite(conn)
        except Exception as err:
            print(f"Failed to seed constituencies in fallback SQLite db: {err}")
            
        print("\n=== SUCCESS: All-India fall-back SQLite Database generated successfully! ===")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
