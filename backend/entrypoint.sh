sleep 3

python manage.py migrate
python manage.py collectstatic  --noinput
cp -r /app/collected_static/. /backend_static/static/
gunicorn --bind 0.0.0.0:8000 foodgram.wsgi