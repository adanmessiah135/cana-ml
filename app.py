from model_loader import predict_image
from firebase_init import init_firebase, upload_to_firebase
import os
import uuid
from datetime import datetime
from collections import deque
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for,
    session
)
from werkzeug.utils import secure_filename

# ===========================================
# CONFIGURAÇÃO PRINCIPAL
# ===========================================
app = Flask(__name__)
app.secret_key = "super-secret-key"

# Inicializar Firebase
init_firebase()

# Pasta temporária
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Extensões válidas
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# Histórico em memória
recent_predictions = deque(maxlen=10)

# ===========================================
# FUNÇÕES AUXILIARES
# ===========================================
def allowed_file(filename):
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
# UPLOAD + IA + FIREBASE + GPS
# ===========================================
@app.route("/upload", methods=["POST"])
def upload_image():
    if "logged" not in session:
        return jsonify({"error": "Não autorizado"}), 401

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
    local_path = os.path.join(UPLOAD_FOLDER, new_filename)

    # 1) Salvar localmente
    file.save(local_path)

    # 2) Executar modelo
    try:
        predicted_class, confidence, class_idx = predict_image(local_path)
    except Exception as e:
        print("Erro na IA:", e)
        os.remove(local_path)
        return jsonify({"error": "Erro no modelo IA"}), 500

    # 3) Upload Firebase
    try:
        firebase_url = upload_to_firebase(local_path, new_filename)
    except Exception as e:
        print("Erro no Firebase:", e)
        firebase_url = None
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

    # 4) GPS
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    gps_link = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None

    # 5) Resultado final
    result = {
        "file": new_filename,
        "url": firebase_url,
        "prediction": predicted_class,
        "confidence": confidence,
        "class_idx": class_idx,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "gps_link": gps_link,
    }

    # 6) Salvar no histórico
    recent_predictions.appendleft(result)

    return jsonify(result)


# ===========================================
# HISTÓRICO (HTML)
# ===========================================
@app.route("/recent")
def recent_page():
    if "logged" not in session:
        return redirect("/login")
    return render_template("recent.html")


# ===========================================
# HISTÓRICO (JSON)
# ===========================================
@app.route("/api/recent")
def api_recent():
    return jsonify(list(recent_predictions))


# ===========================================
# EXECUTAR LOCAL
# ===========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)












