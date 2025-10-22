#!/bin/bash

echo "For Admin"
echo "Apply database migrations"
python3 manage.py makemigrations
echo "Before  migrate"
python3 manage.py migrate
echo "Apply Static Images"
python3 manage.py collectstatic --noinput
echo "Starting Server"
python3 manage.py runserver 0.0.0.0:8000
