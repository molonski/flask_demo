from flask import jsonify, g, request
from app.api.auth import token_auth
from app.auth import database_queries
from app.api import bp


@bp.route("/users/<int:user_id>/", methods=['GET'])
@token_auth.login_required
def get_user(user_id):
    user = database_queries.get_user_by_id(user_id)
    return jsonify(user.to_dict()) if user else jsonify({'error': 'invalid user id'})


@bp.route('/users/', methods=['POST'])
@token_auth.login_required
def create_user():
    data = request.get_json()
    required_keys = ['username', 'password']

    if set(required_keys).issubset(data.keys()):

        if database_queries.get_user_by_name(data['username']):
            return jsonify({'error': 'username already exists'})

        user_id = database_queries.create_user(data['username'], data['password'])
        return jsonify({'user_id': user_id})

    else:
        return jsonify({'error': 'username and password keys required'})


@bp.route('/users/<int:user_id>/', methods=['PUT'])
@token_auth.login_required
def update_user(user_id):
    if g.current_user.id != user_id and g.current_user.username != 'chris':
        jsonify({'error': 'insufficient permissions'})
    else:
        database_queries.update_user(user_id, data=request.get_json())
        return get_user(user_id)
