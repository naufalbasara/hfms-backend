FROM --platform=linux/amd64 python:3.11-slim

ARG PIP_DISABLE_PIP_VERSION_CHECK=1
ARG PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev
RUN apt-get update && apt-get install -y pkg-config

RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["gunicorn", "-b", ":8080", "--timeout", "360", "--chdir", "/app/flaskr", "webserver:app"]