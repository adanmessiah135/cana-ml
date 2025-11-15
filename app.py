import os
import uuid
import json
from datetime import datetime
from collections import deque
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for, 
    session, send_from_directory
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super-secret-key"

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
RECENT_FOLDER = os.path.join("static", "recent")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RECENT_FOLDER, exist_ok=True)

recent_predictions = deque(maxlen=10)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    if "logged" not in session:
        return redirect("/login")
    return render_template("index.html")

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

    result = {
        "file": new_filename,
        "prediction": "broca",
        "confidence": 0.92,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

    recent_predictions.appendleft(result)

    recent_copy_path = os.path.join(RECENT_FOLDER, new_filename)
    file.save(recent_copy_path)

    return jsonify(result)

@app.route("/recent")
def recent_page():
    return render_template("recent.html", items=list(recent_predictions))

@app.route("/uploads/<path:filename>")
def uploaded_files(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/static/recent/<path:filename>")
def recent_files(filename):
    return send_from_directory(RECENT_FOLDER, filename)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)







