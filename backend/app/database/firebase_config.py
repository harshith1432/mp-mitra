import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage, messaging, auth

db = None
bucket = None

def initialize_firebase():
    global db, bucket
    # Check if Firebase is already initialized to avoid duplicate app errors
    if not firebase_admin._apps:
        from app.config_manager import config_manager
        
        # 1. Try loading credentials from a service account JSON string in config/env
        service_account_env = config_manager.get_secret("FIREBASE_SERVICE_ACCOUNT_JSON")
        bucket_name = config_manager.get("FIREBASE_STORAGE_BUCKET") or os.getenv("FIREBASE_STORAGE_BUCKET")

        if service_account_env:
            try:
                cred_dict = json.loads(service_account_env)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': bucket_name
                })
                print("Firebase Admin SDK successfully initialized via service account JSON.")
            except Exception as e:
                print(f"Error parsing FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
                # Fallback to default
                firebase_admin.initialize_app(options={'storageBucket': bucket_name})
        else:
            # 2. Try loading from a path to a service account JSON file
            cred_path = config_manager.get("FIREBASE_SERVICE_ACCOUNT_PATH") or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': bucket_name
                })
                print(f"Firebase Admin SDK successfully initialized via certificate file: {cred_path}")
            else:
                # 3. Fallback to Application Default Credentials (ADC) or default initialization
                try:
                    firebase_admin.initialize_app(options={'storageBucket': bucket_name})
                    print("Firebase Admin SDK initialized using default application credentials.")
                except Exception as e:
                    print(f"Warning: Firebase Admin SDK initialized with fallback empty config. Error: {e}")
                    firebase_admin.initialize_app()

    # Get services
    db = firestore.client(database_id='default')
    try:
        bucket = storage.bucket()
    except Exception as e:
        print(f"Warning: Failed to retrieve default storage bucket: {e}")
        bucket = None

# Initialize on module import
initialize_firebase()

def get_firestore_client():
    global db
    return db

def get_storage_bucket():
    global bucket
    return bucket
