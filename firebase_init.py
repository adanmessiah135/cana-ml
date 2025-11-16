import os
import firebase_admin
from firebase_admin import credentials, storage

def init_firebase():
    if not firebase_admin._apps:
        # Caminho correto para secret files no Render
        key_path = "/etc/secrets/firebase_key.json"

        # Inicializa Firebase Admin
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred, {
            "storageBucket": "cana-ml.appspot.com"
        })

def upload_to_firebase(local_path, filename):
    bucket = storage.bucket()
    blob = bucket.blob(f"uploads/{filename}")

    # Envia arquivo
    blob.upload_from_filename(local_path)

    # Deixa público
    blob.make_public()

    return blob.public_url


