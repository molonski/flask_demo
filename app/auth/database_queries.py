from app.auth.models import ArtiWebUser
from app import db


def get_user_by_id(user_id):
    return ArtiWebUser.query.filter(ArtiWebUser.id == user_id).first()


def get_user_by_name(username):
    return ArtiWebUser.query.filter(ArtiWebUser.username == username).first()


def create_user(username, password):
    u = ArtiWebUser(username=username)

    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return u.id


def update_user(user_id, data):
    u = ArtiWebUser.query.filter(ArtiWebUser.id == user_id).first()
    if u and isinstance(data, dict):
        if data.get('username'):
            setattr(u, 'username', data['username'])
        if data.get('password'):
            u.set_password(data['password'])

        db.session.commit()
