from flask import jsonify, request
from app.api.auth import token_auth
from app.main import database_queries
from app.api import bp


@bp.route("/instrument/<int:instrument_id>", methods=['GET'])
@token_auth.login_required
def get_instrument(instrument_id):
    instrument = database_queries.get_instrument_by_id(instrument_id)
    return jsonify(instrument.to_dict()) if instrument else jsonify({'error': 'invalid instrument id'})


@bp.route('/instrument/', methods=['POST'])
@token_auth.login_required
def add_instrument():
    data = request.get_json()
    required_keys = ['development_name', 'market_name']
    if set(required_keys).issubset(data.keys()):

        if database_queries.get_instrument_by_dev_name(data['development_name']):
            return jsonify({'error': 'instrument development name already in use'})

        if database_queries.get_instrument_by_market_name(data['market_name']):
            return jsonify({'error': 'instrument market name already in use'})

        instrument_id = database_queries.create_new_instrument(data['development_name'], data['market_name'])
        instrument = database_queries.get_instrument_by_id(instrument_id)
        return jsonify(instrument.to_dict())
    else:
        return jsonify({'error': 'invalid submission'})
