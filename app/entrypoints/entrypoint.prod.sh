#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# in the actual production setting the db won't be
# initialized each time the container is started

flask db init

flask db migrate

flask db upgrade

# nginx requires the static files be collected from
# flask blueprint directories and put in the app/static
# directory

flask collect

# in the actual production setting docker setup
# utility won't be needed to load data into the db

python utilities.py docker_setup

exec "$@"