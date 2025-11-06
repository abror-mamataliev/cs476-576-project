FROM python:3.9-slim

WORKDIR /srv/app

COPY requirements.txt .

RUN python -m pip install -U pip
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY run.py .

EXPOSE 5000

CMD ["python", "run.py"]
