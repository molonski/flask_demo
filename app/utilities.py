import os
import sys
import json
import requests
import psycopg2
from app import create_app
from app.auth.database_queries import create_user
from app.main.database_queries import create_new_instrument


users = [{'username': 'interview',
          'password': 'hire'
          },
         {'username': 'chris',
          'password': 'cowbell'}]

instruments = ['Cool-Instrument-Name']

# =======================================================================
# local utilities


def add_user(username, password):
    app = create_app()
    with app.app_context():
        user_id = create_user(username, password)
        print('new user created, name: {}, id: {}'.format(username, user_id))


def add_instrument(name):
    app = create_app()
    with app.app_context():
        instrument= create_new_instrument(name, name)
        print('new instrument created, name: {}, id: {}'.format(name, instrument.id))


# ========================================================================
# remote utilities

def get_token(usr, pwd, url_base):

    token = ':('
    session = requests.Session()
    session.auth = (usr, pwd)
    r = session.post(url_base + 'api/tokens')
    try:
        token = r.json()['token']
        print('token: {}'.format(token))
    except json.decoder.JSONDecodeError:
        raise Exception('problem loggin in to get user token')

    return token


def add_user_remote(new_usr, new_pwd, token, url_base):
    url = url_base + 'api/users/'

    data = {'username': new_usr, 'password': new_pwd}

    r = requests.post(url, json=data,
                      headers={'Authorization': 'Bearer {}'.format(token)})

    try:
        print('success, new user id is: {}'.format(r.json()['user_id']))
    except json.decoder.JSONDecodeError:
        print('problem creating new user')


def add_instrument_remote(inst_name, token, url_base):
    url = url_base + 'api/instrument/'

    data = {'development_name': inst_name,
            'market_name': inst_name}

    r = requests.post(url, json=data,
                      headers={'Authorization': 'Bearer {}'.format(token)})

    try:
        print('success, new instrument: {}'.format(r.json()))
    except json.decoder.JSONDecodeError:
        print('problem creating new instrument')

# =======================================================================
# docker setup utilities

def docker_setup():

    for user in users:
        add_user(user['username'], user['password'])

    for instrument in instruments:
        add_instrument(instrument)

    load_sample_data()

def load_sample_data():
    # sample_data.sql is placed in the working directory
    # by the Dockerfile

    print('Loading sample test results...')

    db_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    with open('sample_data.sql', 'r') as f:
        data = f.read().split('\n')

    for line in data:
        if "INSERT" in line:
            cur.execute(line)

    conn.commit()
    cur.close()
    conn.close()

    print('\t... completed data import.')


# =======================================================================


if __name__ == "__main__":

    func = sys.argv[1]

    if func == 'docker_setup':
        # add users and instruments
        docker_setup()

    elif func == 'add_user':
        usr = sys.argv[2]
        pwd = sys.argv[3]
        add_user(usr, pwd)

    elif func == 'add_instrument':
        instrument_name = sys.argv[2]
        add_instrument(instrument_name)

    elif func == 'add_user_remote':
        usr = sys.argv[2]
        pwd = sys.argv[3]
        new_usr = sys.argv[4]
        new_pwd = sys.argv[5]
        try:
            url_base = sys.argv[6]
        except:
            url_base = 'http://artiphon-production.herokuapp.com/'

        token = get_token(usr, pwd, url_base)
        add_user_remote(new_usr, new_pwd, token, url_base)

    elif func == 'add_instrument_remote':
        usr = sys.argv[2]
        pwd = sys.argv[3]
        inst_name = sys.argv[4]
        try:
            url_base = sys.argv[5]
        except:
            url_base = 'http://artiphon-production.herokuapp.com/'

        token = get_token(usr, pwd, url_base)
        add_instrument_remote(inst_name, token, url_base)

        instrument_name = sys.argv[2]
        add_instrument(instrument_name)
