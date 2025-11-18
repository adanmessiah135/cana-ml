import firebase_admin
from firebase_admin import credentials, storage
import os
import json


def init_firebase():
    """
    Inicializa o Firebase apenas uma vez.
    No Render, o secret file fica em:
        /etc/secrets/firebase_key.json
    """

    if firebase_admin._apps:
        return  # Já inicializado

    KEY_PATH = "/etc/secrets/firebase_key.json"

    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(
            f"Arquivo de credenciais não encontrado: {KEY_PATH}\n"
            "→ Verifique se você adicionou o Secret File no Render."
        )

    # Lê o arquivo JSON para extrair o bucket automaticamente
    with open(KEY_PATH, "r") as f:
        data = json.load(f)

    if "storage_bucket" in data:
        bucket_name = data["storage_bucket"]
    else:
        # Fallback: tenta extrair a partir do project_id
        bucket_name = f"{data['project_id']}.appspot.com"

    cred = credentials.Certificate(KEY_PATH)

    firebase_admin.initialize_app(cred, {
        "storageBucket": bucket_name
    })

    print(f"🔥 Firebase inicializado!")
    print(f"📦 Bucket: {bucket_name}")


def upload_to_firebase(local_path, filename):
    """
    Faz upload de um arquivo para o Firebase Storage
    e retorna a URL pública.
    """

    bucket = storage.bucket()
    blob = bucket.blob(f"uploads/{filename}")

    # Upload
    blob.upload_from_filename(local_path)

    # Deixa público
    blob.make_public()

    print(f"📤 Upload concluído: {blob.public_url}")

    return blob.public_url




