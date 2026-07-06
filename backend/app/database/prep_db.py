import os
import csv
import sys
from sqlalchemy import select
from app.database.connection import engine, SessionLocal, Base
from app.database.models import IngestionState, Pincode, School, Road, HealthCentre, Habitation, WaterQuality

# Ensure database module is resolvable
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.database.dataset_manager import dataset_manager

# Attempt to scan and import datasets from the local workspace (Village Amenities)
here = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(here, "..", "..", ".."))
dataset_manager.import_local_datasets_from_workspace(root_dir)

DATASET_DIR = dataset_manager.get_dataset_dir()

def check_ingestion_completed():
    db = SessionLocal()
    try:
        state = db.query(IngestionState).filter(IngestionState.key == "global_ingestion").first()
        if state and state.value == "completed":
            return True
    except Exception as e:
        print(f"Error checking ingestion state: {e}")
    finally:
        db.close()
    return False

def mark_ingestion_completed():
    db = SessionLocal()
    try:
        state = db.query(IngestionState).filter(IngestionState.key == "global_ingestion").first()
        if not state:
            state = IngestionState(key="global_ingestion", value="completed")
            db.add(state)
        else:
            state.value = "completed"
        db.commit()
        print("Successfully marked ingestion as completed.")
    except Exception as e:
        print(f"Error marking ingestion state: {e}")
        db.rollback()
    finally:
        db.close()

def import_pincodes():
    filepath = os.path.join(DATASET_DIR, "pincode.csv")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print("Importing Pincodes...")
    db = SessionLocal()
    try:
        db.query(Pincode).delete()
        db.commit()

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            pincodes = []
            count = 0
            for row in reader:
                if len(row) < 11:
                    continue
                try:
                    p = Pincode(
                        circlename=row[0],
                        regionname=row[1],
                        divisionname=row[2],
                        officename=row[3],
                        pincode=row[4],
                        officetype=row[5],
                        delivery=row[6],
                        district=row[7].strip().upper(),
                        statename=row[8].strip().upper(),
                        latitude=float(row[9]) if row[9] else 0.0,
                        longitude=float(row[10]) if row[10] else 0.0
                    )
                    pincodes.append(p)
                    count += 1
                except ValueError:
                    continue

                if len(pincodes) >= 5000:
                    db.bulk_save_objects(pincodes)
                    db.commit()
                    pincodes = []
                    print(f"  Inserted {count} pincodes...")

            if pincodes:
                db.bulk_save_objects(pincodes)
                db.commit()
            print(f"Finished Pincodes: Total {count} imported.")
    except Exception as e:
        print(f"Error importing pincodes: {e}")
        db.rollback()
    finally:
        db.close()

def import_health_centres():
    filepath = os.path.join(DATASET_DIR, "geocode_health_centre.csv")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print("Importing Health Centres...")
    db = SessionLocal()
    try:
        db.query(HealthCentre).delete()
        db.commit()

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            centres = []
            count = 0
            for row in reader:
                if len(row) < 13:
                    continue
                try:
                    hc = HealthCentre(
                        state_name=row[0].strip().upper(),
                        district_name=row[1].strip().upper(),
                        subdistrict_name=row[2].strip().upper(),
                        facility_type=row[3],
                        facility_name=row[4],
                        facility_address=row[5] if len(row) > 5 else "",
                        latitude=float(row[6]) if row[6] and row[6].lower() != 'nan' else 0.0,
                        longitude=float(row[7]) if row[7] and row[7].lower() != 'nan' else 0.0,
                        active_flag=row[8],
                        location_type=row[10],
                        type_of_facility=row[11]
                    )
                    centres.append(hc)
                    count += 1
                except ValueError:
                    continue

                if len(centres) >= 5000:
                    db.bulk_save_objects(centres)
                    db.commit()
                    centres = []
                    print(f"  Inserted {count} health centres...")

            if centres:
                db.bulk_save_objects(centres)
                db.commit()
            print(f"Finished Health Centres: Total {count} imported.")
    except Exception as e:
        print(f"Error importing health centres: {e}")
        db.rollback()
    finally:
        db.close()

def import_roads():
    filepath = os.path.join(DATASET_DIR, "road.csv")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print("Importing Roads...")
    db = SessionLocal()
    try:
        db.query(Road).delete()
        db.commit()

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            roads = []
            count = 0
            for row in reader:
                if len(row) < 31:
                    continue
                try:
                    r = Road(
                        road_name=row[9],
                        state_name=row[2].strip().upper(),
                        district_name=row[4].strip().upper(),
                        block_name=row[6],
                        habitation_name=row[8],
                        upgrade_or_new=row[11],
                        surface_type=row[12],
                        physical_status=row[13],
                        length=float(row[20]) if row[20] else 0.0,
                        total_cost=float(row[30]) if row[30] else 0.0,
                        population=int(float(row[31])) if row[31] and row[31].lower() != 'none' else 0
                    )
                    roads.append(r)
                    count += 1
                except ValueError:
                    continue

                if len(roads) >= 5000:
                    db.bulk_save_objects(roads)
                    db.commit()
                    roads = []
                    print(f"  Inserted {count} roads...")

            if roads:
                db.bulk_save_objects(roads)
                db.commit()
            print(f"Finished Roads: Total {count} imported.")
    except Exception as e:
        print(f"Error importing roads: {e}")
        db.rollback()
    finally:
        db.close()

def import_schools():
    filepath = os.path.join(DATASET_DIR, "school.csv")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print("Importing Schools...")
    db = SessionLocal()
    try:
        db.query(School).delete()
        db.commit()

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            schools = []
            count = 0
            for row in reader:
                if len(row) < 31:
                    continue
                try:
                    # Calculate total students from various classes
                    total_stu = 0
                    # Students columns are index 31 to 43 (i_students, etc.)
                    for idx in range(31, 44):
                        if idx < len(row) and row[idx]:
                            try:
                                total_stu += int(float(row[idx]))
                            except ValueError:
                                pass

                    s = School(
                        udise_school_code=row[14],
                        school_name=row[13],
                        state_name=row[2].strip().upper(),
                        district_name=row[4].strip().upper(),
                        sub_district_name=row[6],
                        village_name=row[9],
                        pincode=row[11],
                        school_category=row[15],
                        school_type=row[16],
                        total_teachers=int(float(row[30])) if row[30] and row[30].lower() != 'none' else 0,
                        total_students=total_stu,
                        latitude=float(row[20]) if row[20] and row[20].lower() != 'none' else 0.0,
                        longitude=float(row[19]) if row[19] and row[19].lower() != 'none' else 0.0
                    )
                    schools.append(s)
                    count += 1
                except ValueError:
                    continue

                if len(schools) >= 5000:
                    db.bulk_save_objects(schools)
                    db.commit()
                    schools = []
                    print(f"  Inserted {count} schools...")

            if schools:
                db.bulk_save_objects(schools)
                db.commit()
            print(f"Finished Schools: Total {count} imported.")
    except Exception as e:
        print(f"Error importing schools: {e}")
        db.rollback()
    finally:
        db.close()

def import_habitations():
    filepath = os.path.join(DATASET_DIR, "Basic_habitation_info_2012_04_01.csv")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print("Importing Habitations...")
    db = SessionLocal()
    try:
        db.query(Habitation).delete()
        db.commit()

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            habitations = []
            count = 0
            for row in reader:
                if len(row) < 16:
                    continue
                try:
                    sc = int(row[6]) if row[6] else 0
                    st = int(row[7]) if row[7] else 0
                    gen = int(row[8]) if row[8] else 0
                    
                    h = Habitation(
                        state_name=row[0].strip().upper(),
                        district_name=row[1].strip().upper(),
                        block_name=row[2],
                        panchayat_name=row[3],
                        village_name=row[4],
                        habitation_name=row[5],
                        sc_population=sc,
                        st_population=st,
                        general_population=gen,
                        status=row[12],
                        year=row[15]
                    )
                    habitations.append(h)
                    count += 1
                except ValueError:
                    continue

                if len(habitations) >= 5000:
                    db.bulk_save_objects(habitations)
                    db.commit()
                    habitations = []
                    print(f"  Inserted {count} habitations...")

            if habitations:
                db.bulk_save_objects(habitations)
                db.commit()
            print(f"Finished Habitations: Total {count} imported.")
    except Exception as e:
        print(f"Error importing habitations: {e}")
        db.rollback()
    finally:
        db.close()

def import_water_quality():
    filepath = os.path.join(DATASET_DIR, "Water_quality_affected_habitation_2012_04_01.csv")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print("Importing Water Quality...")
    db = SessionLocal()
    try:
        db.query(WaterQuality).delete()
        db.commit()

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            records = []
            count = 0
            for row in reader:
                if len(row) < 8:
                    continue
                try:
                    wq = WaterQuality(
                        state_name=row[0].strip().upper(),
                        district_name=row[1].strip().upper(),
                        block_name=row[2],
                        panchayat_name=row[3],
                        village_name=row[4],
                        habitation_name=row[5],
                        quality_parameter=row[6],
                        year=row[7]
                    )
                    records.append(wq)
                    count += 1
                except ValueError:
                    continue

                if len(records) >= 5000:
                    db.bulk_save_objects(records)
                    db.commit()
                    records = []
                    print(f"  Inserted {count} water quality records...")

            if records:
                db.bulk_save_objects(records)
                db.commit()
            print(f"Finished Water Quality: Total {count} imported.")
    except Exception as e:
        print(f"Error importing water quality: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    print("Starting Database Ingestion Engine...")
    
    # 1. Create tables
    print("Creating tables if not exists...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Check if already ingested
    if check_ingestion_completed():
        print("Ingestion already completed. Skipping and running speed startup!")
        return

    # 3. Perform ingestion
    import_pincodes()
    import_health_centres()
    import_roads()
    import_schools()
    import_habitations()
    import_water_quality()
    
    # 4. Mark ingestion completed
    mark_ingestion_completed()
    print("Database preparation and pipeline ingestion successfully completed.")

if __name__ == "__main__":
    main()
