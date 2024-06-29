
FROM python:3.11.3-slim-buster

COPY . '/app'
RUN pip3 install -r requirements.txt

CMD ["flask", "--app", "flaskr/webserver.py", "run"]

EXPOSE 5000:5000