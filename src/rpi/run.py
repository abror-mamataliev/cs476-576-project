from base64 import b64decode
from time import time

from celery import Celery, states
from celery.result import AsyncResult
from decouple import config
from flask import Flask, jsonify, request
from requests import post


class Device:
    EDGE = "edge"
    CLOUD = "cloud"


app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL=config.get('CELERY_BROKER_URL', "redis://localhost:6379/0"),
    CELERY_RESULT_BACKEND=config.get('CELERY_RESULT_BACKEND', "redis://localhost:6379/0"),
    EDGE_DEVICE_URL=config.get('EDGE_DEVICE_URL'),
    CLOUD_DEVICE_URL=config.get('CLOUD_DEVICE_URL'),
)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])


@celery.task
def run_celery_task(input_data: dict):
    device_type = input_data.get('device', Device.EDGE)
    url = app.config['CLOUD_DEVICE_URL' if device_type == 'cloud' else 'EDGE_DEVICE_URL']
    body = input_data.get('body', {})

    image = body['image']
    image_bytes = b64decode(image)
    size = len(image_bytes) / 1024  # Size in KB

    start = time()
    try:
        response = post(url, json=body, timeout=600)
        latency = (time() - start) * 1000
        return {
            'result': {
                'status_code': response.status_code,
                'response': response.json()
            },
            'image': {
                'base64': image,
                'size': size,
                'format': "jpeg"
            },
            'stats': {
                'device': device_type,
                'latency': latency
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
                'base64': image,
                'size': size,
                'format': "jpeg"
            },
            'stats': {
                'device': device_type,
                'latency': latency
            }
        }


@app.route("/")
def index():
    return jsonify({'status': "Running"})


@app.route("/run/", methods=["POST"])
def run_task():
    body = request.get_json()
    if 'request_id' in body:
        request_id = body['request_id']
        task = AsyncResult(request_id, app=celery)
        match task.state:
            case states.FAILURE:
                return jsonify({'status': states.FAILURE, 'error': str(task.result)}), 500
            case states.SUCCESS:
                return jsonify({'status': states.SUCCESS, 'result': task.result}), 200
            case _:
                return jsonify({'status': task.state})

    task = run_celery_task.delay(body)
    return jsonify({'task_id': task.id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
