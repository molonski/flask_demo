FROM python:3.8.3-alpine

# docker-compose file specifies
# /usr/src/app as a shared volume with the web app
# make the working directory one level up so
# import app works

WORKDIR /usr/src

# install psycopg2 dependencies
RUN apk update \
    && apk add make automake postgresql-dev gcc g++ python3-dev musl-dev

# install python dependencies
COPY ./requirements.txt .
RUN pip install -r requirements.txt
