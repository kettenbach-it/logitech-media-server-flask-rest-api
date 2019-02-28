#FROM python:3.7-alpine
FROM balenalib/raspberrypi3-alpine-python

LABEL maintainer="Volker Kettenbach <volker@vicosmo.de>"

WORKDIR /srv

COPY requirements.txt boot.sh ./

RUN apk update \
    && apk upgrade \
    && apk add --no-cache python3 \
    && python3 -m ensurepip \
    && chmod +x boot.sh \
    && pip3 install --upgrade pip \
    && pip3 install -r requirements.txt \
    && pip3 install gunicorn

#COPY patch/player.py /usr/local/lib/python3.7/site-packages/pylms/player.py
COPY patch/player.py /usr/lib/python3.6/site-packages/pylms/player.py
COPY app.py ./

ENV FLASK_APP app.py

# Nicht mit macvlan
# EXPOSE 5000
ENTRYPOINT ["./boot.sh"]