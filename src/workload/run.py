from base64 import b64decode
from os import remove
from os.path import exists
from tempfile import NamedTemporaryFile

from cv2 import IMREAD_GRAYSCALE, imread, resize
from flask import Flask, request, jsonify
from numpy import argmax, max
from tensorflow.keras.datasets import mnist
from tensorflow.keras.models import load_model, Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.utils import to_categorical

app = Flask(__name__)
model_path = "model.h5"

if not exists(model_path):
    # Load dataset
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train = x_train / 255.0
    x_test = x_test / 255.0

    y_train = to_categorical(y_train, 10)
    y_test = to_categorical(y_test, 10)

    # Build model
    model = Sequential([
        Flatten(input_shape=(28, 28)),
        Dense(128, activation="relu"),
        Dense(10, activation="softmax")
    ])

    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    model.fit(x_train, y_train, validation_split=0.1, epochs=5)

    model.save(model_path)

# Load model once at startup
model = load_model(model_path)


def preprocess_image(image_path):
    """Load image, convert to MNIST format (28x28 grayscale)"""
    img = imread(image_path, IMREAD_GRAYSCALE)
    img = resize(img, (28, 28))  # Resize to MNIST size
    img = 255 - img  # Invert colors (MNIST is white digit on black bg)
    img = img / 255.0  # Normalize 0-1
    img = img.reshape(1, 28, 28, 1)  # Shape for model
    return img


@app.route("/run", methods=["POST"])
def run():
    body = request.get_json()
    if 'image' not in body:
        return jsonify({'error': "No image provided"}), 400

    image_data = body['image']  # base64 string

    # Save to temporary file
    with NamedTemporaryFile(delete=False, suffix=".jpg") as temp_img:
        if "," in image_data:
            image_data = image_data.split(",")[1]

        temp_img.write(b64decode(image_data))
        temp_img_path = temp_img.name

    # Preprocess image
    img = preprocess_image(temp_img_path)
    remove(temp_img_path)  # Clean up temp file

    # Predict
    prediction = model.predict(img)
    predicted_digit = int(argmax(prediction))

    return jsonify({
        'digit': predicted_digit,
        'confidence': round(float(max(prediction)), 3)
    })


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
