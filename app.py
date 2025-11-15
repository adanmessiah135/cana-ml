import os
from datetime import datetime
from collections import deque
import logging
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for,
    session, send_from_directory
)
from werkzeug.utils import secure_filename
import numpy as np
import tensorflow as tf
from PIL import Image, ExifTags

# =====================================================
# CONFIGURAÇÕES GERAIS
# =====================================================
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "cana-ml-2025"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = "ml/cana_model_v5_TF210_COMPAT.tflite"
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

IMG_SIZE = (224, 224)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
recent_predictions = deque(maxlen=10)

# =====================================================
# FUNÇÃO DE CARREGAMENTO DO MODELO
# =====================================================
def load_model():
    """Carrega o modelo TFLite (SEM TRY/EXCEPT PARA FORÇAR O ERRO)"""
    print(f"⌛ Tentando carregar o modelo de: {MODEL_PATH}")
    
    # [MUDANÇA 1] Removido o try/except daqui
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    print(f"✅ Modelo TFLite carregado com sucesso: {MODEL_PATH}")
    return interpreter, input_details, output_details

# Vamos inicializar como None. O erro vai acontecer no predict.
interpreter, input_details, output_details = None, None, None
try:
    # Ainda tentamos carregar no início
    interpreter, input_details, output_details = load_model()
except Exception:
    print("❌ Erro INICIAL ao carregar modelo. O erro real aparecerá no /predict.")


# =====================================================
# MAPEAMENTO DE CLASSES (Sem mudanças)
# =====================================================
MODEL_CLASSES = [
    "EyeSpot", "Healthy", "Mosaic", "RedLeafSpot", "RedRot", "RingSpot",
    "Rust", "Yellow", "Broca", "Ferrugem", "Sadia"
]
DISPLAY_MAP = {
    "EyeSpot": "Mancha Ocular", "Healthy": "Sadia", "RedLeafSpot": "Mancha Vermelha",
    "RedRot": "Podridão Vermelha", "RingSpot": "Mancha Anelar", "Mosaic": "Mosaico",
    "Rust": "Ferrugem", "Yellow": "Amarelão", "Broca": "Broca",
    "Ferrugem": "Ferrugem", "Sadia": "Sadia"
}
EXPLAIN_MAP = {
    "Mancha Ocular": "Lesões ovais e amareladas com centro escuro, parecendo um olho.",
    "Sadia": "Folha com coloração verde uniforme e saudável.",
    "Mancha Vermelha": "Estrias ou manchas avermelhadas nas folhas.",
    "Podridão Vermelha": "Descoloração avermelhada interna do colmo.",
    "Mancha Anelar": "Manchas circulares com bordas escuras e centro claro.",
    "Mosaico": "Padrão irregular de manchas amarelas e verdes.",
    "Ferrugem": "Pústulas laranja ou marrom-avermelhadas nas folhas.",
    "Amarelão": "Amarelecimento progressivo das folhas.",
    "Broca": "Perfurações causadas pela lagarta da broca-da-cana."
}

# =====================================================
# FUNÇÕES DE VALIDAÇÃO E EXTRAÇÃO (Sem mudanças)
# =====================================================
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_gps(file_path):
    try:
        img = Image.open(file_path)
        exif = img._getexif()
        if not exif: return None
        gps_info = {}
        for tag, value in exif.items():
            tag_name = ExifTags.TAGS.get(tag)
            if tag_name == "GPSInfo":
                for key in value.keys():
                    gps_tag = ExifTags.GPSTAGS.get(key)
                    gps_info[gps_tag] = value[key]
        if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
            def convert_to_degrees(value):
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            lat = convert_to_degrees(gps_info["GPSLatitude"])
            lon = convert_to_degrees(gps_info["GPSLongitude"])
            if gps_info.get("GPSLatitudeRef") == "S": lat = -lat
            if gps_info.get("GPSLongitudeRef") == "W": lon = -lon
            return {"lat": lat, "lon": lon}
        return None
    except Exception:
        return None

# =====================================================
# LOGIN (Sem mudanças)
# =====================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")
        if user == "admin" and password == "1234":
            session["user"] = user
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Usuário ou senha inválidos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.before_request
def require_login():
    allowed = ["login", "static", "uploads"]
    if "user" not in session and request.endpoint not in allowed:
        return redirect(url_for("login"))

# =====================================================
# ROTAS PRINCIPAIS
# =====================================================
@app.route("/")
@app.route("/dashboard")
def dashboard():
    return render_template("index.html", user=session.get("user", "admin"))

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOADS_DIR, filename)

def preprocess_image(file_path):
    with Image.open(file_path) as img:
        img = img.resize(IMG_SIZE)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    return img_array.astype(np.float32)


@app.route("/predict", methods=["POST"])
def predict():
    global interpreter, input_details, output_details

    # [MUDANÇA 2] Removido o try/except daqui
    # O código vai quebrar aqui se o modelo não carregou
    if interpreter is None:
        interpreter, input_details, output_details = load_model()
        if interpreter is None:
             # Isso não deve acontecer, pois o load_model() vai quebrar antes
             return jsonify({"error": "Falha no carregamento."}), 500

    file = request.files.get("image")
    if not file:
        return jsonify({"error": "Nenhuma imagem enviada."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de arquivo não permitido (use .jpg, .jpeg, .png)"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOADS_DIR, filename)
    file.save(filepath)

    # O código vai quebrar aqui se a predição falhar
    gps = extract_gps(filepath)
    img_array = preprocess_image(filepath)
    interpreter.set_tensor(input_details[0]["index"], img_array)
    interpreter.invoke()
    preds = interpreter.get_tensor(output_details[0]["index"])[0]

    class_idx = np.argmax(preds)
    confidence = float(np.max(preds))
    class_name = MODEL_CLASSES[class_idx]
    display_name = DISPLAY_MAP.get(class_name, class_name)
    explanation = EXPLAIN_MAP.get(display_name, "Análise concluída.")

    alert = None
    if display_name == "Sadia" and confidence < 0.6:
        alert = "⚠️ Atenção: baixa confiança na classificação como 'Sadia'. Pode haver anomalias sutis."

    result = {
        "file": filename,
        "file_url": f"/uploads/{filename}",
        "class": display_name,
        "confidence": round(confidence * 100, 1),
        "explain": explanation,
        "alert": alert,
        "gps": gps,
        "gps_link": f"http://googleusercontent.com/maps/google.com/0{gps['lat']},{gps['lon']}" if gps else None,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:M:%S"),
    }
    recent_predictions.appendleft(result)
    return jsonify(result)

# =====================================================
# HISTÓRICO (Sem mudanças)
# =====================================================
@app.route("/recent")
def recent():
    return jsonify(list(recent_predictions))

@app.route("/recent_page")
def recent_page():
    return render_template("recent.html", user=session.get("user", "admin"))

# =====================================================
# EXECUÇÃO (Sem mudanças)
# =====================================================
if __name__ == "__main__":
    print("🌿 Iniciando Cana-ML em modo desenvolvimento (debug=True)")
    app.run(host="0.0.0.0", port=5000, debug=True)





