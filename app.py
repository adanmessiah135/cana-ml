import os
import uuid
import shutil
from datetime import datetime
from collections import deque
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for,
    session, send_from_directory
)
from werkzeug.utils import secure_filename

# ===========================================
# CONFIGURAÇÃO PRINCIPAL
# ===========================================
app = Flask(__name__)
app.secret_key = "super-secret-key"

UPLOAD_FOLDER = "uploads"
RECENT_FOLDER = os.path.join("static", "recent")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RECENT_FOLDER, exist_ok=True)

# Histórico em memória (últimas 10 análises)
recent_predictions = deque(maxlen=10)

# ===========================================
# FUNÇÕES AUXILIARES
# ===========================================
def allowed_file(filename):
    """Verifica se extensão é permitida"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ===========================================
# ROTAS PRINCIPAIS
# ===========================================

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


# ===========================================
# LOGIN / LOGOUT
# ===========================================
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


# ===========================================
# ENVIO + PROCESSAMENTO DE IMAGENS
# ===========================================
@app.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Arquivo inválido"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Formato não suportado"}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    new_filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, new_filename)

    file.save(filepath)

    # ============================
    # Recebe a geolocalização
    # ============================
    lat = request.form.get("lat")
    lon = request.form.get("lon")

    gps_link = None
    if lat and lon:
        gps_link = f"https://www.google.com/maps?q={lat},{lon}"

    # Resultado da análise (simulado por enquanto)
    result = {
        "file": new_filename,
        "prediction": "broca",  # temporário
        "confidence": 0.92,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "gps_link": gps_link,
        "lat": lat,
        "lon": lon
    }

    # Salvar no histórico
    recent_predictions.appendleft(result)

    return jsonify(result)



# ===========================================
# PÁGINA DE HISTÓRICO
# ===========================================
@app.route("/recent")
def recent_page():
    if "logged" not in session:
        return redirect("/login")
    return render_template("recent.html")


# ===========================================
# API JSON PARA O FRONT-END (histórico)
# ===========================================
@app.route("/api/recent")
def api_recent():
    data = list(recent_predictions)

    # preparar urls completas
    for item in data:
        item["file_url"] = f"/static/recent/{item['file']}"
        item["file_url"] = f"/static/recent/{item['file']}"
        item["gps_link"] = item.get("gps_link")

    return jsonify(data)


# ===========================================
# SERVIR ARQUIVOS ESTÁTICOS
# ===========================================
@app.route("/uploads/<path:filename>")
def uploaded_files(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/static/recent/<path:filename>")
def recent_files(filename):
    return send_from_directory(RECENT_FOLDER, filename)


# ===========================================
# EXECUTAR LOCALMENTE
# ===========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)









