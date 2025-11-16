import firebase_admin
from firebase_admin import credentials, storage

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase-key.json")
        firebase_admin.initialize_app(cred, {
            "storageBucket": "cana-ml.appspot.com"
        })

def upload_to_firebase(local_path, filename):
    bucket = storage.bucket()
    blob = bucket.blob(f"uploads/{filename}")
    blob.upload_from_filename(local_path)

    # deixar público
    blob.make_public()

    return blob.public_url
