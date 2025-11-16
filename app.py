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

# Inicializar Firebase Storage
init_firebase()

# Pastas locais (somente temporárias)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Extensões aceitas
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# Histórico em memória (últimas 10 análises)
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
# UPLOAD DE IMAGEM + FIREBASE + GPS
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
    local_path = os.path.join(UPLOAD_FOLDER, new_filename)

    # 1) Salva localmente
    file.save(local_path)

    # 2) Roda o modelo TFLite
    try:
        predicted_class, confidence, class_idx = predict_image(local_path)
    except Exception as e:
        # Se der erro na IA, loga e retorna erro amigável
        print("Erro ao rodar modelo TFLite:", e)
        os.remove(local_path)
        return jsonify({"error": "Erro ao processar a imagem com o modelo."}), 500

    # 3) Envia imagem para Firebase Storage
    try:
        firebase_url = upload_to_firebase(local_path, new_filename)
    finally:
        # 4) Remove arquivo local (independente de sucesso no upload)
        if os.path.exists(local_path):
            os.remove(local_path)

    # 5) Monta link de GPS (se veio do front)
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    gps_link = None
    if lat and lon:
        gps_link = f"https://www.google.com/maps?q={lat},{lon}"

    # 6) Monta resultado
    result = {
        "file": new_filename,
        "url": firebase_url,           # URL pública no Firebase
        "prediction": predicted_class, # classe real
        "confidence": confidence,      # 0.0 a 1.0
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "gps_link": gps_link,
        "class_idx": class_idx,
    }

    # 7) Guarda no histórico em memória
    recent_predictions.appendleft(result)

    # 8) Retorna para o front-end
    return jsonify(result)



# ===========================================
# TELA DO HISTÓRICO (HTML)
# ===========================================
@app.route("/recent")
def recent_page():
    if "logged" not in session:
        return redirect("/login")
    return render_template("recent.html")


# ===========================================
# API DO HISTÓRICO (JSON)
# ===========================================
@app.route("/api/recent")
def api_recent():
    # Gera uma cópia simples dos itens (pra não modificar o deque original)
    data = []

    for item in recent_predictions:
        data.append({
            "file": item["file"],
            "url": item["url"],                  # URL do Firebase
            "prediction": item["prediction"],
            "confidence": item["confidence"],
            "timestamp": item["timestamp"],
            "gps_link": item.get("gps_link"),
            "class_idx": item.get("class_idx"),
        })

    return jsonify(data)



# ===========================================
# EXECUTAR APP LOCALMENTE
# ===========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)











