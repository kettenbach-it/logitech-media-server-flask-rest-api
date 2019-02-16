#!/bin/sh
#flask db upgrade
#flask translate compile
exec gunicorn -b :80 --access-logfile - --error-logfile - app:app