import numpy as np
from PIL import Image
import tflite_runtime.interpreter as tflite

# Caminho do modelo TFLite dentro do projeto
MODEL_PATH = "model_best.tflite"

# Carrega intérprete
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

# Pegamos os detalhes de entrada e saída
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Tamanho esperado de entrada
IMG_SIZE = 224  # ajuste se for diferente no seu modelo


def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((IMG_SIZE, IMG_SIZE))

    img = np.array(img, dtype=np.float32)
    img = img / 255.0  # normalização
    img = np.expand_dims(img, axis=0)
    return img


CLASSES = ["EyeSpot", "Healthy", "Mosaic", "RedLeafSpot", "RedRot", "RingSpot", "Rust", "Yellow"]


def predict_image(image_path):
    # prepara imagem
    input_data = preprocess_image(image_path)

    interpreter.set_tensor(input_details[0]["index"], input_data)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details[0]["index"])[0]

    class_index = np.argmax(output)
    confidence = float(output[class_index])
    class_name = CLASSES[class_index]

    return class_name, confidence, class_index


