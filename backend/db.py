import firebase_admin
from firebase_admin import credentials
import os
from firebase_admin import firestore

# Initialize Firebase Admin SDK using the service-key file
if not firebase_admin._apps:
    try:
        # Use the service-key file located in the backend directory
        cred = credentials.Certificate('backend/service-key')
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully using service-key file.")
    except FileNotFoundError:
         print("Service account key file not found at 'backend/service-key'. Please ensure it exists.")
         # Decide whether to raise or continue without Firebase based on app requirements
         raise
    except Exception as e:
         print(f"Failed to initialize Firebase Admin SDK with service-key file: {e}")
         # Decide whether to raise or continue without Firebase based on app requirements
         raise

# Use globally initialized Firestore client
db = firestore.client() 