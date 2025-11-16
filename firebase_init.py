import firebase_admin
from firebase_admin import credentials, storage
import os


# ============================================================
#   INICIALIZA O FIREBASE USANDO O SECRET FILE DO RENDER
# ============================================================
def init_firebase():
    """
    Inicializa o Firebase apenas uma vez.
    No Render, o secret file é salvo em:
        /etc/secrets/firebase_key.json
    """

    if firebase_admin._apps:
        return  # já iniciado

    # Caminho do secret file no Render
    KEY_PATH = "/etc/secrets/firebase_key.json"

    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(
            f"Arquivo de credenciais não encontrado: {KEY_PATH}\n"
            "→ Verifique se você adicionou o Secret File no Render."
        )

    cred = credentials.Certificate(KEY_PATH)

    firebase_admin.initialize_app(cred, {
        "storageBucket": "cana-ml.appspot.com"
    })

    print("🔥 Firebase inicializado com sucesso!")


# ============================================================
#   UPLOAD DE ARQUIVOS AO FIREBASE STORAGE
# ============================================================
def upload_to_firebase(local_path, filename):
    """
    Faz upload do arquivo local para o Firebase Storage
    e retorna a URL pública.
    """

    bucket = storage.bucket()
    blob = bucket.blob(f"uploads/{filename}")

    # Upload
    blob.upload_from_filename(local_path)

    # Deixa o arquivo acessível publicamente
    blob.make_public()

    print(f"📤 Upload concluído: {blob.public_url}")

    return blob.public_url



