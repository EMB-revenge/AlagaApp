import firebase_admin
from firebase_admin import credentials
import os
from fastapi import FastAPI
from firebase_admin import firestore
from .db import db # Import db from the new db.py file

cred = credentials.Certificate(r'C:\Tests\Alaga\alaga_new_structure\backend\alaga-ac939-firebase-adminsdk-fbsvc-d06459947d.json')
firebase_admin.initialize_app(cred)
# Initialize Firebase Admin SDK
# Ensure GOOGLE_APPLICATION_CREDENTIALS environment variable is set
# to the path of your Firebase service account key file.
if not firebase_admin._apps:
    try:
        # Attempt to initialize with default credentials (picks up GOOGLE_APPLICATION_CREDENTIALS)
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully using Application Default Credentials.")
        db = firestore.client()
        print("Firestore client initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Firebase Admin SDK: {e}")
        print("Ensure GOOGLE_APPLICATION_CREDENTIALS is set correctly and points to a valid service account key file.")
        # Optionally, re-raise the exception or exit if Firebase is critical for startup.
        raise

# Routers
from .routers import appointments, users, calendar, health_records, medications, subscriptions, care_profiles, reminders, vitals # Add other routers as needed

# Initialize FastAPI
app = FastAPI(title="AlagaApp API")

# Include your API routers
app.include_router(appointments.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(health_records.router, prefix="/api")
app.include_router(medications.router, prefix="/api")
app.include_router(subscriptions.router, prefix="/api")
app.include_router(care_profiles.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")
app.include_router(vitals.router, prefix="/api")

@app.get("/api")
async def root():
    return {"message": "Welcome to the AlagaApp API!"}

# To run the app using Uvicorn:
# uvicorn backend.main:app --reload (from the alaga_app directory)
if __name__ == "__main__":
    import uvicorn
    # Note: Running with __main__ might have issues with relative imports if 'backend' is not in PYTHONPATH.
    # It's generally better to run with 'uvicorn backend.main:app --reload' from the project root.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, app_dir=r'C:\Tests\Alaga\alaga_new_structure\backend')
