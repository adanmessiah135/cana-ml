from flask import (
    Flask, render_template, request, jsonify, redirect, url_for, session
)
from werkzeug.utils import secure_filename
from datetime import datetime
from collections import deque
import os
import uuid

from model_loader import predict_image as predict
from firebase_init import init_firebase, upload_to_firebase  # Firebase Storage

# ======================================================
# CONFIG PRINCIPAL
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

# Histórico (últimas 10 análises em memória)
recent_predictions = deque(maxlen=10)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def build_recommendation(prediction: str, confidence: float) -> dict:
    """
    Gera recomendação agronômica simples com base na classe e na confiança.
    """
    # Faixas de confiança
    if confidence < 0.6:
        return {
            "level": "baixa",
            "color": "orange",  # tratado no HTML como alert-orange
            "message": (
                "A confiança do modelo é baixa. "
                "Recomenda-se coletar uma nova amostra (outra folha, outro ângulo) "
                "e, se possível, solicitar avaliação de um engenheiro-agrônomo."
            ),
        }
    elif confidence < 0.8:
        return {
            "level": "moderada",
            "color": "warning",
            "message": (
                "O modelo identificou um possível quadro de "
                f"{prediction}. Sugere-se monitorar a área, repetir a análise "
                "em mais folhas e acompanhar possíveis avanços dos sintomas."
            ),
        }
    else:
        # Alta confiança
        if prediction.lower() == "healthy":
            return {
                "level": "alta",
                "color": "success",
                "message": (
                    "Folha considerada saudável com alta confiança. "
                    "Sugere-se manter o manejo atual, monitorando rotineiramente "
                    "para detecção precoce de qualquer alteração."
                ),
            }
        else:
            return {
                "level": "alta",
                "color": "danger",
                "message": (
                    f"Doença {prediction} detectada com alta confiança. "
                    "Recomenda-se avaliação presencial de um engenheiro-agrônomo, "
                    "vistorias em talhões vizinhos e planejamento de manejo específico "
                    "conforme recomendações técnicas."
                ),
            }


# ======================================================
# ROTAS PRINCIPAIS
# ======================================================
@app.route("/")
def index():
    if "logged" not in session:
        return redirect("/login")
    # Se você quiser que caia direto no dashboard:
    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    if "logged" not in session:
        return redirect("/login")

    # Converter deque -> list para usar no Jinja + tojson
    return render_template(
        "dashboard.html",
        recent_predictions=list(recent_predictions),
    )


# ======================================================
# LOGIN
# ======================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")

        # login simples (demo)
        if user == "admin" and password == "123":
            session["logged"] = True
            return redirect("/dashboard")
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
        if os.path.exists(local_path):
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

    # Recomendação agronômica
    recommendation = build_recommendation(predicted_class, confidence)

    # Resultado final
    result = {
        "file": new_filename,
        "url": firebase_url,
        "prediction": predicted_class,
        "confidence": confidence,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "gps_link": gps_link,
        "class_idx": class_idx,
        "recommendation": recommendation,
    }

    recent_predictions.appendleft(result)

    return jsonify(result)


# ======================================================
# HISTÓRICO - PÁGINA / API
# ======================================================
@app.route("/recent")
def recent_page():
    if "logged" not in session:
        return redirect("/login")
    return render_template("recent.html")  # se usar outra página, ajuste aqui


@app.route("/api/recent")
def api_recent():
    return jsonify(list(recent_predictions))


# ======================================================
# EXECUÇÃO LOCAL
# ======================================================
if __name__ == "__main__":
    # Para rodar local:
    app.run(host="0.0.0.0", port=5000, debug=True)
















