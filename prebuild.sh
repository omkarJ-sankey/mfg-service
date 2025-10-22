#!/bin/sh
apt-get update && apt-get install -y --no-install-recommends unixodbc 
apt-get install -y g++ unixodbc-dev
apt-get update && apt-get install -y gnupg2
apt-get install -y curl
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
apt update
ACCEPT_EULA=Y apt-get install msodbcsql17
pip3 install -r requirements.txt
python3 manage.py makemigrations run_admin_server
echo "Before  migrate"
python3 manage.py migrate run_admin_server
echo "Starting Server"
python3 manage.py runserver run_admin_server 8000
