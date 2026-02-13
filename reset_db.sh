rm -rf db.sqlite3
python3 manage.py migrate
python manage.py shell -c "from seed import seed_db; seed_db()"
