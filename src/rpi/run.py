from celery import states
from celery.result import AsyncResult
from decouple import config
from flask import Flask, jsonify, request

from celery_app import celery, run_celery_task

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL=config('CELERY_BROKER_URL', "redis://localhost:6379/0"),
    CELERY_RESULT_BACKEND=config('CELERY_RESULT_BACKEND', "redis://localhost:6379/0"),
    EDGE_DEVICE_URL=config('EDGE_DEVICE_URL'),
    CLOUD_DEVICE_URL=config('CLOUD_DEVICE_URL'),
)


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
