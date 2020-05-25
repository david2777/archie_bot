FROM python:3.8.2

MAINTAINER David DuVoisin "daduvo11@gmail.com"

RUN mkdir /app

WORKDIR /app

COPY . /app/

RUN pip install -r requirements.txt

CMD [ "flask", "run", "--host", "0.0.0.0"]