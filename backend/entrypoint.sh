sleep 3

python manage.py makemigrations --no-input
python manage.py migrate --no-input
python manage.py collectstatic --no-input
cp -r /app/collected_static/. /backend_static/static/
gunicorn --bind 0.0.0.0:8000 backend.wsgi