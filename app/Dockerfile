FROM python:3.8.3-alpine

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV HOME /usr/src
ENV APP_HOME $HOME/app

RUN mkdir -p $HOME
RUN mkdir $APP_HOME

WORKDIR $HOME

# install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev linux-headers

# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt $APP_HOME
RUN pip install -r $APP_HOME/requirements.txt

# copy project
COPY . $APP_HOME

# move flask_demo.py file, utilities.py, entrypoint.sh,
# and sample_data.sql up one directory level above app
RUN mv $APP_HOME/flask_demo.py $HOME/flask_demo.py
RUN mv $APP_HOME/utilities.py $HOME/utilities.py
RUN mv $APP_HOME/entrypoints/entrypoint.sh $HOME/entrypoint.sh
RUN mv $APP_HOME/sample_data.sql $HOME/sample_data.sql

# run entrypoint.sh
ENTRYPOINT ["/usr/src/entrypoint.sh"]
