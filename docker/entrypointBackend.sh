#!/bin/bash

echo "For Baackend"
echo "Apply database migrations"
python3 manage.py makemigrations
echo "Before  migrate"
python3 manage.py migrate
echo "Apply Static Images"
python3 manage.py collectstatic --noinput
echo "Removing cached data"
python3 cache_remover_script.py
echo "Starting Server"
python3 manage.py runserver 0.0.0.0:8001