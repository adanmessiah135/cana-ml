import tensorflow as tf
import numpy as np
import cv2
import os

# Caminho correto para o modelo
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_best.tflite")

# Carrega o modelo TFLite
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Tamanho da imagem esperado
IMG_SIZE = (224, 224)

# Classes do dataset
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
    """Lê, redimensiona e normaliza a imagem."""
    img = cv2.imread(image_path)
    img = cv2.resize(img, IMG_SIZE)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)
    return img

def predict(image_path):
    """Executa o modelo TFLite e retorna a classe, confiança e índice."""
    img = preprocess_image(image_path)

    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details[0]['index'])
    class_index = int(np.argmax(output))
    confidence = float(np.max(output))

    return CLASSES[class_index], confidence, class_index




