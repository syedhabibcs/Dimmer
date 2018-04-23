web: gunicorn server:app -w 1 --threads 2 
heroku ps:scale web=1
heroku config:add TZ="Canada/Eastern"
