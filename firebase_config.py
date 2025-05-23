import firebase_admin
from firebase_admin import credentials, firestore
import os

def init_firebase():
    cred_path = os.getenv("FAREBASE_CREDENTIALS.json")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()
