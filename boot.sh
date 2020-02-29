#!/bin/sh
#flask db upgrade
#flask translate compile
exec gunicorn -c gunicorn_config.py app:app
