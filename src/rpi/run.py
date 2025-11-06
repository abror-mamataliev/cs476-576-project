from base64 import b64decode
from time import time

from decouple import config
from flask import Flask, jsonify, request
from requests import post


class Device:
    EDGE = "edge"
    CLOUD = "cloud"


app = Flask(__name__)
app.config.update(EDGE_DEVICE_URL=config('EDGE_DEVICE_URL'), CLOUD_DEVICE_URL=config('CLOUD_DEVICE_URL'))


@app.route("/")
def index():
    return jsonify({'status': "Running"})


@app.route("/run/", methods=["POST"])
def run_task():
    input_data = request.get_json()
    device_type = input_data.get('device_type', Device.EDGE).lower()
    url = app.config['EDGE_DEVICE_URL' if device_type == Device.EDGE else 'CLOUD_DEVICE_URL']
    body = input_data.get('body', {})

    image = body['image']
    image_bytes = b64decode(image)
    size = len(image_bytes) / 1024  # Size in KB

    start = time()
    try:
        response = post(url, json=body)
        latency = (time() - start) * 1000
        return {
            'result': {
                'status_code': response.status_code, 'response': response.json()
            },
            'image': {
                'size': size, 'format': "jpeg"
            },
            'stats': {
                'device': device_type, 'latency': latency
            }
        }
    except Exception as e:
        latency = (time() - start) * 1000
        return {
            'result': {
                'status_code': 500,
                'response': {
                    'error': f"Error communicating with {device_type} device: {e}"
                }
            },
            'image': {
                'size': size, 'format': "jpeg"
            },
            'stats': {
                'device': device_type, 'latency': latency
            }
        }, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
