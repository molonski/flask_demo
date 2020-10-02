import datetime
from flask import jsonify, request
from app.api.auth import token_auth
from app.main import database_queries, forms
from app.api import bp


@bp.route("/testlog/<int:testlog_id>", methods=['GET'])
@token_auth.login_required
def get_test_result_by_id(testlog_id):

    # database_functions.get_test_result_by_id
    testlog = database_queries.get_test_result_by_id(testlog_id)

    if testlog:
        result = testlog.to_dict()

        measurements = database_queries.get_sensor_results_by_testlog_id(testlog_id)

        if measurements:
            result['measurements'] = []
            for m in measurements:
                result['measurements'].append(m.to_dict())

        return jsonify(result)
    else:
        return jsonify({'error': 'no result for id: {}'.format(testlog_id)})


@bp.route('/testresults-by-date-range/', methods=['POST'])
@token_auth.login_required
def get_test_results_by_date_range():
    form = forms.ReviewResultsForm()

    validations = [form.instrument.data, form.start_date.data, form.end_date.data,
                   isinstance(form.start_date.data, datetime.date),
                   isinstance(form.end_date.data, datetime.date)]

    if all(validations):
        test_results = database_queries.get_test_results_by_ins_date_range(form.instrument.data,
                                                                             form.start_date.data.strftime('%Y-%m-%d'),
                                                                             form.end_date.data.strftime('%Y-%m-%d'))
        return jsonify(test_results)

    return jsonify({'error': 'invalid form selections'})


@bp.route('/testresults-by-pn-sn/', methods=['POST'])
@token_auth.login_required
def get_test_results_by_pn_sn():
    data = request.get_json()
    return jsonify({'instrument': data['instrument'],
                    'serial_number': data['serial_number']})