FROM python:3.11-slim

ARG PIP_DISABLE_PIP_VERSION_CHECK=1
ARG PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev
RUN apt-get update && apt-get install -y libhdf5-dev hdf5-tools pkg-config

RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-binary=h5py h5py

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["gunicorn", "-b", ":8080", "--workers", "1", "--chdir", "/app/flaskr", "webserver:app"]