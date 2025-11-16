import os
import numpy as np
from PIL import Image
import tensorflow as tf

# Caminho do modelo TFLite
MODEL_PATH = os.path.join("ml", "cana_model_v5_TF210_COMPAT.tflite")

# Carrega o interpretador TFLite
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Tenta descobrir o tamanho da imagem a partir do modelo
# Ex.: [1, 224, 224, 3]
input_shape = input_details[0]["shape"]
if len(input_shape) == 4:
    # Assume formato [batch, height, width, channels] ou [batch, channels, height, width]
    if input_shape[3] == 3:
        IMG_SIZE = int(input_shape[1])
        CHANNELS_LAST = True
    elif input_shape[1] == 3:
        IMG_SIZE = int(input_shape[2])
        CHANNELS_LAST = False  # [1, 3, H, W]
    else:
        # fallback padrão
        IMG_SIZE = 224
        CHANNELS_LAST = True
else:
    # fallback padrão
    IMG_SIZE = 224
    CHANNELS_LAST = True

# Classes do modelo (na ordem do treinamento)
CLASSES = [
    "EyeSpot",
    "Healthy",
    "Mosaic",
    "RedLeafSpot",
    "RedRot",
    "RingSpot",
    "Rust",
    "Yellow",
]


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Abre a imagem, converte para RGB, redimensiona e normaliza
    no formato esperado pelo modelo TFLite.
    """
    img = Image.open(image_path).convert("RGB")
    img = img.resize((IMG_SIZE, IMG_SIZE))

    arr = np.asarray(img, dtype=np.float32) / 255.0  # normaliza [0, 1]

    if CHANNELS_LAST:
        # [H, W, C] -> [1, H, W, C]
        arr = np.expand_dims(arr, axis=0)
    else:
        # [H, W, C] -> [C, H, W] -> [1, C, H, W]
        arr = np.transpose(arr, (2, 0, 1))
        arr = np.expand_dims(arr, axis=0)

    return arr


def predict_image(image_path: str):
    """
    Executa inferência com o modelo TFLite e retorna:
    - nome da classe
    - confiança (0.0 a 1.0)
    - índice da classe
    """
    # Prepara input
    input_tensor = preprocess_image(image_path)
    interpreter.set_tensor(input_details[0]["index"], input_tensor)

    # Roda o modelo
    interpreter.invoke()

    # Obtém saída
    output_data = interpreter.get_tensor(output_details[0]["index"])
    # Considera batch 1
    logits = output_data[0]

    # Garante distribuição de probabilidade (softmax)
    exps = np.exp(logits - np.max(logits))
    probs = exps / np.sum(exps)

    class_idx = int(np.argmax(probs))
    confidence = float(probs[class_idx])

    if 0 <= class_idx < len(CLASSES):
        class_name = CLASSES[class_idx]
    else:
        class_name = f"class_{class_idx}"

    return class_name, confidence, class_idx
