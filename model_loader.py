import numpy as np
from PIL import Image
import os
from tflite_runtime.interpreter import Interpreter  # IMPORTANTE

# Caminho correto para o modelo
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_best.tflite")

# Carrega o modelo TFLite
interpreter = Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Tamanho esperado pelo modelo (ajuste se necessário)
IMG_SIZE = (224, 224)

# Classes do modelo
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

def preprocess_image(image_path):
    """Pré-processa a imagem usando Pillow (compatível com Render)."""
    img = Image.open(image_path).convert("RGB")
    img = img.resize(IMG_SIZE)

    # Converte para numpy e normaliza
    img = np.array(img, dtype=np.float32) / 255.0

    # Expande para o formato: (1, 224, 224, 3)
    img = np.expand_dims(img, axis=0)

    return img

def predict_image(image_path):
    """Executa a predição usando o modelo TFLite."""
    img = preprocess_image(image_path)

    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details[0]['index'])
    class_idx = int(np.argmax(output))
    confidence = float(np.max(output))

    return CLASSES[class_idx], confidence, class_idx






