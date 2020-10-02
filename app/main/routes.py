import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.main.forms import ByDateForm, BySerialNumberForm
from app.main import database_queries as main_dbq
from app.main import bp
from app import create_app


@bp.route('/', methods=['GET'])
@login_required
def index():
    return render_template('main/welcome.html')
    # return redirect(url_for('reports.production_reports'))


@bp.route('/test-results/', methods=['GET', 'POST'])
@login_required
def test_results():

    by_date_form, by_sn_form = _search_forms()

    # form handling in helper function shared by three view functions
    response = _handle_search_forms(by_date_form, by_sn_form)

    if response['return_now']:
        return response['payload']
    else:
        by_sn_form, by_sn_form, active_tab = response['payload']

    # depending on form response the active tab may or may not be set, provide default option if unspecified
    active_tab = active_tab or "sn"

    return render_template('main/testresults.html',
                           by_date_form=by_date_form,
                           by_sn_form=by_sn_form,
                           active_tab=active_tab,
                           title='Test Result Search Page')


@bp.route('/test-results/<result_types>/<instrument>/<start_date>/<end_date>/', methods=['GET', 'POST'])
@login_required
def test_results_by_date(result_types, instrument, start_date, end_date):

    title = '{} Test Results: {} - {} to {}'.format(result_types.replace('-', ' ').capitalize(), instrument,
                                                    start_date, end_date)

    by_date_form, by_sn_form = _search_forms()

    # form handling in helper function shared by three view functions
    response = _handle_search_forms(by_date_form, by_sn_form)

    if response['return_now']:
        return response['payload']
    else:
        by_sn_form, by_sn_form, active_tab = response['payload']

    # depending on form response the active tab may or may not be set, provide default option if unspecified
    active_tab = active_tab or "date"

    # set date form values based on search
    by_date_form.instrument.data = instrument
    by_date_form.start_date.data = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    by_date_form.end_date.data = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    by_date_form.result.data = ['pass', 'fail'] if result_types == 'all' else [result_types]

    page, per_page = _pagination_prep()

    fields, instrument, tests = main_dbq.get_test_results_by_ins_date_range(instrument, result_types, start_date,
                                                                            end_date, page, per_page)

    base_url = url_for('main.test_results_by_date', result_types=result_types,
                       instrument=instrument, start_date=start_date, end_date=end_date)

    return render_template('main/testresults.html',
                           by_date_form=by_date_form,
                           by_sn_form=by_sn_form,
                           active_tab=active_tab,
                           fields=fields,
                           instrument=instrument,
                           tests=tests,
                           base_url=base_url,
                           title=title)


@bp.route('/test-results/<instrument>/<serial_number>/', methods=['GET', 'POST'])
@login_required
def test_results_by_sn(instrument, serial_number):

    title = 'Test Results: {}, SN: {}'.format(instrument, serial_number)

    by_date_form, by_sn_form = _search_forms()

    # form handling in helper function shared by three view functions
    response = _handle_search_forms(by_date_form, by_sn_form)

    if response['return_now']:
        return response['payload']
    else:
        by_sn_form, by_sn_form, active_tab = response['payload']

    # depending on form response the active tab may or may not be set, provide default option if unspecified
    active_tab = active_tab or "sn"

    # set form sn form values based on the search
    by_sn_form.instrument.data = instrument
    by_sn_form.serial_number.data = serial_number

    page, per_page = _pagination_prep()

    fields, instrument, tests = main_dbq.get_test_results_by_ins_sn(instrument, serial_number, page, per_page)

    base_url = url_for('main.test_results_by_sn', instrument=instrument, serial_number=serial_number)

    return render_template('main/testresults.html',
                           by_date_form=by_date_form,
                           by_sn_form=by_sn_form,
                           active_tab=active_tab,
                           fields=fields,
                           instrument=instrument,
                           tests=tests,
                           base_url=base_url,
                           title=title)


@bp.route('/test-results/id/<testlog_id>/', methods=['GET'])
@login_required
def single_test(testlog_id):

    result = main_dbq.get_test_result_by_id(testlog_id)

    return render_template('main/single_test_result.html', result=result, skipmodal=True)


@bp.route('/test-results/id/', methods=['POST'])
@login_required
def single_test_post():
    data = request.get_json()
    if isinstance(data, dict):
        if data.get('testlog_id'):
            result = main_dbq.get_test_result_by_id(data['testlog_id'])
            return render_template('main/_single_test_result.html', result=result)

    return 'Error passing testlog_id'


# helper functions to cut repetitious code
def _search_forms():
    by_date_form = ByDateForm(prefix='by_date_form')
    by_sn_form = BySerialNumberForm(prefix='by_date_form')
    by_date_form.instrument.choices = main_dbq.instrument_id_name_pairs()
    by_sn_form.instrument.choices = by_date_form.instrument.choices

    return by_date_form, by_sn_form


def _handle_search_forms(by_date_form, by_sn_form):

    active_tab = None

    if by_date_form.validate_on_submit() and by_date_form.submitbydate.data:

        instrument = by_date_form.instrument.data
        start_date = by_date_form.start_date.data
        end_date = by_date_form.end_date.data

        result_types = 'all' if len(by_date_form.result.data) > 1 else by_date_form.result.data[0]

        if start_date > end_date:
            flash('Start date must come on or before the end date.')
            return {'return_now': True,
                    'payload': render_template('main/testresults.html',
                                               by_date_form=by_date_form,
                                               by_sn_form=by_sn_form,
                                               active_tab="date")}

        return {'return_now': True,
                'payload': redirect(url_for('main.test_results_by_date',
                                            result_types=result_types,
                                            instrument=instrument,
                                            start_date=start_date,
                                            end_date=end_date))}

    elif by_sn_form.validate_on_submit() and by_sn_form.submitbysn.data:

        instrument = by_sn_form.instrument.data
        serial_number = by_sn_form.serial_number.data

        return {'return_now': True,
                'payload': redirect(url_for('main.test_results_by_sn',
                                            instrument=instrument,
                                            serial_number=serial_number))}

    if request.method == 'POST':
        # clear errors for form not submitted
        if by_date_form.submitbydate.data:
            by_sn_form.instrument.errors = []
            by_sn_form.serial_number.errors = []
            active_tab = "date"
        elif by_sn_form.submitbysn.data:
            by_date_form.instrument.errors = []
            by_date_form.start_date.errors = []
            by_date_form.end_date.errors = []
            active_tab = "sn"

    return {'return_now': False,
            'payload': (by_date_form, by_sn_form, active_tab)}


def _pagination_prep():

    page = request.args.get('page', 1, type=int)

    result_counts = _default_results_per_page()

    per_page = min([request.args.get('per-page', result_counts['default'], type=int), result_counts['max']])

    return page, per_page


def _default_results_per_page():
    app = create_app()
    with app.app_context():
        return {'default': app.config.get('DEFAULT_RESULTS_PER_PAGE') or 50,
                'max': app.config.get('MAX_RESULTS_PER_PAGE') or 250}

