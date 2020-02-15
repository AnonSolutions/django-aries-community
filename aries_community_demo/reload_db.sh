rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata sample-data

