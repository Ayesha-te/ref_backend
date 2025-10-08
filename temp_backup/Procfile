web: cd ref_backend && gunicorn core.wsgi:application --config gunicorn.conf.py
release: cd ref_backend && python manage.py migrate && python manage.py collectstatic --noinput