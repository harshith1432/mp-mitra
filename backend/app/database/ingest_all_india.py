import os
import csv
import sys
import time
from pathlib import Path

# Add project root and backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.connection import engine, Base
from app.database.dataset_manager import dataset_manager

# Scan and extract dataset zip from workspace
here = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(here, "..", "..", ".."))
dataset_manager.import_local_datasets_from_workspace(root_dir)

DATASET_DIR = dataset_manager.get_dataset_dir()
is_pg = "postgresql" in str(engine.url)

def bulk_insert(cursor, table, cols, batch):
    if is_pg:
        from psycopg2.extras import execute_values
        conflict_target = ""
        if table == "schools":
            conflict_target = "ON CONFLICT (udise_school_code) DO NOTHING"
        elif table == "parliamentary_constituencies":
            conflict_target = "ON CONFLICT (pc_code) DO NOTHING"
        elif table == "assembly_constituencies":
            conflict_target = "ON CONFLICT (ac_code) DO NOTHING"
            
        columns_str = ", ".join(cols)
        query = f"INSERT INTO {table} ({columns_str}) VALUES %s {conflict_target}"
        execute_values(cursor, query, batch)
    else:
        columns_str = ", ".join(cols)
        placeholders = ", ".join(["?"] * len(cols))
        query = f"INSERT OR IGNORE INTO {table} ({columns_str}) VALUES ({placeholders})"
        cursor.executemany(query, batch)

def clear_tables(conn):
    print("Clearing existing table records...")
    cursor = conn.cursor()
    tables = [
        "pincodes", "health_centres", "roads", "schools",
        "habitations", "water_quality_records", "parliamentary_constituencies",
        "assembly_constituencies", "constituency_village_map", "constituency_budget"
    ]
    for t in tables:
        try:
            if is_pg:
                cursor.execute(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE")
            else:
                cursor.execute(f"DELETE FROM {t}")
        except Exception as e:
            pass
    conn.commit()

def ingest_pincodes(conn):
    filepath = os.path.join(DATASET_DIR, "pincode.csv")
    if not os.path.exists(filepath):
        print(f"Pincode file not found: {filepath}")
        return
        
    print("Ingesting Pincodes...")
    start = time.time()
    cursor = conn.cursor()
    
    cols = [
        "pincode", "circlename", "regionname", "divisionname", "officename", 
        "officetype", "delivery", "district", "statename", "latitude", "longitude"
    ]
    
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
                bulk_insert(cursor, "pincodes", cols, batch)
                conn.commit()
                batch = []
                print(f"  Processed {count} pincodes...")
                
        if batch:
            bulk_insert(cursor, "pincodes", cols, batch)
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
    
    cols = [
        "state_name", "district_name", "subdistrict_name", "facility_type", "facility_name", 
        "facility_address", "latitude", "longitude", "active_flag", "location_type", "type_of_facility"
    ]
    
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
                bulk_insert(cursor, "health_centres", cols, batch)
                conn.commit()
                batch = []
                
        if batch:
            bulk_insert(cursor, "health_centres", cols, batch)
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
    
    cols = [
        "road_name", "state_name", "district_name", "block_name", "habitation_name", 
        "upgrade_or_new", "surface_type", "physical_status", "length", "total_cost", "population"
    ]
    
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
                bulk_insert(cursor, "roads", cols, batch)
                conn.commit()
                batch = []
                print(f"  Processed {count} roads...")
                
        if batch:
            bulk_insert(cursor, "roads", cols, batch)
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
    
    cols = [
        "udise_school_code", "school_name", "state_name", "district_name", "sub_district_name", 
        "village_name", "pincode", "school_category", "school_type", "total_teachers", "total_students", "latitude", "longitude"
    ]
    
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
                bulk_insert(cursor, "schools", cols, batch)
                conn.commit()
                batch = []
                print(f"  Processed {count} schools...")
                
        if batch:
            bulk_insert(cursor, "schools", cols, batch)
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
    
    cols = [
        "state_name", "district_name", "block_name", "panchayat_name", "village_name", 
        "habitation_name", "sc_population", "st_population", "general_population", "status", "year"
    ]
    
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
                bulk_insert(cursor, "habitations", cols, batch)
                conn.commit()
                batch = []
                print(f"  Processed {count} habitations...")
                
        if batch:
            bulk_insert(cursor, "habitations", cols, batch)
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
    
    cols = [
        "state_name", "district_name", "block_name", "panchayat_name", "village_name", "habitation_name", "quality_parameter", "year"
    ]
    
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
                bulk_insert(cursor, "water_quality_records", cols, batch)
                conn.commit()
                batch = []
                
        if batch:
            bulk_insert(cursor, "water_quality_records", cols, batch)
            conn.commit()
            
    print(f"Finished Water Quality: {count} rows in {time.time() - start:.2f}s")

def main():
    print(f"Master CSV Location: {DATASET_DIR}")
    print(f"Active DB Engine: {engine.url}")
    
    # 1. Create tables safe using SQLAlchemy
    print("Synchronizing DB schema tables...")
    from app.database import models
    Base.metadata.create_all(bind=engine)
    
    # 2. Get connection
    conn = engine.raw_connection()
    try:
        # SQLite optimization
        if not is_pg:
            conn.execute("PRAGMA journal_mode = OFF")
            conn.execute("PRAGMA synchronous = OFF")
            conn.execute("PRAGMA cache_size = 100000")
            
        clear_tables(conn)
        
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
            print(f"Failed to seed constituencies in DB: {err}")
            
        print("\n=== SUCCESS: All-India Local Ingestion completed successfully! ===")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
