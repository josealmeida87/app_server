import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
load_dotenv()


def init_firebase():
    cred_path = os.getenv("FIREBASE_CREDENTIALS")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()
