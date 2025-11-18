import numpy as np
import cv2
import os
from tflite_runtime.interpreter import Interpreter

# ================================================
# CARREGA O MODELO .TFLITE
# ================================================

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_best.tflite")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"❌ Modelo TFLite não encontrado: {MODEL_PATH}")

# Inicializa o interpretador
interpreter = Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Tamanho da imagem esperada
IMG_SIZE = (224, 224)

# Classes do modelo (mesma ordem do treinamento)
CLASSES = [
    "EyeSpot",
    "Healthy",
    "Mosaic",
    "RedLeafSpot",
    "RedRot",
    "RingSpot",
    "Rust",
    "Yellow"
]


# ================================================
# PRÉ-PROCESSAMENTO
# ================================================
def preprocess_image(image_path: str):
    """
    Abre a imagem, redimensiona e normaliza para o modelo TFLite.
    """
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError(f"Não foi possível carregar a imagem: {image_path}")

    img = cv2.resize(img, IMG_SIZE)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)

    return img


# ================================================
# PREDICT PRINCIPAL (USADO NO app.py)
# ================================================
def predict(image_path: str):
    """
    Faz a previsão de uma imagem usando o modelo TFLite.
    Retorna:
        - classe prevista (str)
        - confiança (float)
        - índice da classe (int)
    """

    # Pré-processa a imagem
    img = preprocess_image(image_path)

    # Insere a imagem no Tensor
    interpreter.set_tensor(input_details[0]['index'], img)

    # Executa o modelo
    interpreter.invoke()

    # Obtém o resultado
    output = interpreter.get_tensor(output_details[0]['index'])

    class_idx = int(np.argmax(output))
    confidence = float(np.max(output))
    predicted_class = CLASSES[class_idx]

    return predicted_class, confidence, class_idx







