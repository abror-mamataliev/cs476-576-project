from base64 import b64decode
from time import time

from celery import Celery
from decouple import config
from requests import post


class Device:
    EDGE = "edge"
    CLOUD = "cloud"


celery = Celery(
    __name__,
    broker=config('CELERY_BROKER_URL', "redis://localhost:6379/0"),
    backend=config('CELERY_RESULT_BACKEND', "redis://localhost:6379/0")
)


@celery.task
def run_celery_task(input_data: dict):
    from run import app

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
