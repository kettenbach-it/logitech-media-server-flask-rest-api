#FROM python:3.7-alpine
FROM balenalib/raspberrypi3-alpine-python

LABEL maintainer="Volker Kettenbach <volker@ktnbch.de>"

WORKDIR /srv

COPY requirements.txt boot.sh gunicorn_config.py ./

RUN apk update \
    && apk upgrade \
    && apk add --no-cache python3 \
    && python3 -m ensurepip \
    && chmod +x boot.sh \
    && pip3 install --upgrade pip \
    && pip3 install -r requirements.txt \
    && pip3 install curl gunicorn

COPY app.py  ./

ENV FLASK_APP app.py

# Nicht mit macvlan
# EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
