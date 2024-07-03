FROM python:3.11

ARG PIP_DISABLE_PIP_VERSION_CHECK=1
ARG PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip setuptools wheel

RUN apt-get update && apt-get install -y libhdf5-dev

# RUN pip3 install --no-binary h5py h5py

RUN pip3 install -r requirements.txt

EXPOSE 80

# CMD ["flask", "--app", "flaskr/webserver.py", "run"]
CMD ["gunicorn", "-b", "0.0.0.0:80", "--timeout", "300", "--chdir", "/app/flaskr", "webserver:app"]