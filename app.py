from flask import (
    Flask, render_template, request, jsonify, redirect, url_for, session
)
from werkzeug.utils import secure_filename
from datetime import datetime
from collections import deque
import os
import uuid

from model_loader import predict  # IMPORTAÇÃO CORRETA DA IA
from firebase_init import init_firebase, upload_to_firebase

# ======================================================
# CONFIGURAÇÃO PRINCIPAL
# ======================================================
app = Flask(__name__)
app.secret_key = "super-secret-key"

# Inicializar Firebase
init_firebase()

# Pasta local temporária
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Extensões permitidas
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# Histórico (últimas 10 análises)
recent_predictions = deque(maxlen=10)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ======================================================
# ROTAS PRINCIPAIS
# ======================================================
@app.route("/")
def index():
    if "logged" not in session:
        return redirect("/login")
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if "logged" not in session:
        return redirect("/login")
    return render_template("dashboard.html")


# ======================================================
# LOGIN
# ======================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")

        if user == "admin" and password == "123":
            session["logged"] = True
            return redirect("/")
        else:
            return render_template("login.html", error="Credenciais inválidas")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged", None)
    return redirect("/login")


# ======================================================
# UPLOAD + IA + FIREBASE + GPS
# ======================================================
@app.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Arquivo inválido"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Formato não suportado"}), 400

    # Nome único
    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    local_path = os.path.join(UPLOAD_FOLDER, new_filename)

    # Salvar temporariamente
    file.save(local_path)

    # IA — Modelo TFLite
    try:
        predicted_class, confidence, class_idx = predict(local_path)
    except Exception as e:
        print("Erro no modelo:", e)
        os.remove(local_path)
        return jsonify({"error": "Erro ao processar imagem com IA"}), 500

    # Firebase
    try:
        firebase_url = upload_to_firebase(local_path, new_filename)
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

    # GPS opcional
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    gps_link = None
    if lat and lon:
        gps_link = f"https://www.google.com/maps?q={lat},{lon}"

    # Resultado final
    result = {
        "file": new_filename,
        "url": firebase_url,
        "prediction": predicted_class,
        "confidence": confidence,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "gps_link": gps_link,
        "class_idx": class_idx,
    }

    recent_predictions.appendleft(result)

    return jsonify(result)


# ======================================================
# HISTÓRICO - PÁGINA
# ======================================================
@app.route("/recent")
def recent_page():
    if "logged" not in session:
        return redirect("/login")
    return render_template("recent.html")


# ======================================================
# HISTÓRICO (API)
# ======================================================
@app.route("/api/recent")
def api_recent():
    return jsonify(list(recent_predictions))


# ======================================================
# EXECUÇÃO LOCAL
# ======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)















