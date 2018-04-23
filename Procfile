web: gunicorn app:app --workers=2 --threads 2 
heroku ps:scale web=1
heroku config:add TZ="Canada/Eastern"
