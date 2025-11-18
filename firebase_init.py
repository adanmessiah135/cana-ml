import firebase_admin
from firebase_admin import credentials, storage
import os


def init_firebase():

    if firebase_admin._apps:
        return

    KEY_PATH = "/etc/secrets/firebase_key.json"

    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(
            f"Arquivo de credenciais não encontrado: {KEY_PATH}\n"
            "→ Verifique se você adicionou o Secret File no Render."
        )

    cred = credentials.Certificate(KEY_PATH)

    # 🔥 Bucket REAL conforme mostrado no console do Firebase
    firebase_admin.initialize_app(cred, {
        "storageBucket": "cana-ml.firebasestorage.app"
    })

    print("🔥 Firebase inicializado com sucesso!")


def upload_to_firebase(local_path, filename):

    bucket = storage.bucket()
    blob = bucket.blob(f"uploads/{filename}")

    blob.upload_from_filename(local_path)
    blob.make_public()

    print(f"📤 Upload concluído: {blob.public_url}")

    return blob.public_url





