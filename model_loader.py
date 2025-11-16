import numpy as np
from PIL import Image
import tflite_runtime.interpreter as tflite

# Carrega o modelo TFLite na inicialização do servidor
interpreter = tflite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Definir classes do modelo (IGUAL ao seu treinamento)
CLASSES = ["Broca", "Ferrugem", "Sadia"]


def preprocess_image(image_path, target_size=(224, 224)):
    """Carrega e prepara imagem para o TFLite."""
    image = Image.open(image_path).convert("RGB")
    image = image.resize(target_size)

    img_array = np.array(image, dtype=np.float32)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    return img_array


def predict_image(image_path):
    """Executa inferência no modelo TFLite."""
    img = preprocess_image(image_path)

    interpreter.set_tensor(input_details[0]["index"], img)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details[0]["index"])[0]

    class_idx = int(np.argmax(output))
    confidence = float(output[class_idx])
    predicted_class = CLASSES[class_idx]

    return predicted_class, confidence, class_idx

