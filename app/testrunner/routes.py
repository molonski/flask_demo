import os
from flask import request, render_template, redirect, url_for, jsonify, current_app
from flask_login import login_required
from rq.job import Job
from rq.exceptions import NoSuchJobError
from app.testrunner import bp
from app.testrunner.forms import InstrumentForm
from app.main.database_queries import instrument_id_name_pairs
from app.productiontest.constants import TEST_LOG_FOLDER


@bp.route('/', methods=['GET', 'POST'])
@login_required
def testrunner_page():

    inst_form = InstrumentForm(prefix='instrument')
    inst_form.instrument.choices = instrument_id_name_pairs()

    if inst_form.validate_on_submit() and inst_form.submitinst.data:

        instrument = inst_form.instrument.data

        return redirect(url_for('testrunner.instrument_test', instrument=instrument))

    return render_template('testrunner/instrument_selection.html', title='Test Runner', form=inst_form)


@bp.route('/<instrument>', methods=['GET'])
@login_required
def instrument_test(instrument):

    title = '{} Test'.format(instrument)

    return render_template('testrunner/instrument_test.html', title=title, instrument=instrument,
                           check_install_url=url_for('testrunner.check_install'),
                           automated_submit_url=url_for('testrunner.perform_automated_test'),
                           polling_url=url_for('testrunner.get_report_status'),
                           log_file_url=url_for('testrunner.get_log_file'))


@bp.route('/production-test-install/', methods=['POST'])
@login_required
def check_install():
    try:
        import app.productiontest.test_main
        return jsonify({'install': True})
    except ModuleNotFoundError:
        return jsonify({'install': False,
                        'message': 'Production test package not available on this machine.'})


@bp.route('/automated-test-submit/', methods=['POST'])
@login_required
def perform_automated_test():

    from app.productiontest.test_main import run_test

    data = request.get_json()
    if isinstance(data, dict):
        instrument = data.get('instrument')
        serial_number = data.get('serial_number')
        log_file_name = data.get('log_file_name')

        # submit automated test job
        job = current_app.task_queue.enqueue_call(
            func=run_test,
            args=(instrument, serial_number, log_file_name),
            result_ttl=5000
        )

        return jsonify({'submission_success': True,
                        'job_id': job.get_id()})

    return jsonify({'submission_success': False,
                    'message': 'Problem starting automated testing.'})


@bp.route("/job-status/", methods=['POST'])
@login_required
def get_report_status():

    data = request.get_json()

    if data:
        job_key = data.get('job_id')
        try:
            job = Job.fetch(job_key, connection=current_app.redis)
            vals = {'complete': False,
                    'data': None}

            if job.is_finished:
                vals['complete'] = True
                vals['data'] = job.result

            return jsonify(vals)

        except NoSuchJobError:
            return jsonify({'complete': True, 'errors': ['job_id: {} is not available.'.format(job_key)]})


@bp.route("/log-file/", methods=['POST'])
@login_required
def get_log_file():

    data = request.get_json()

    ret = {}

    if data:
        log_file_name = data.get('log_file_name')
        numlines = data.get('numlines')

        # file to open
        current_directory = os.path.dirname(os.path.realpath(__file__))
        top_level_directory = os.path.sep.join(current_directory.rstrip(os.path.sep).split(os.path.sep)[:-2])
        path = os.path.join(top_level_directory, TEST_LOG_FOLDER, log_file_name)

        try:
            with open(path, 'r') as f:
                contents = f.read()

                # drop data before line number
                if contents:
                    contents = '\n'.join(contents.replace('\n\r', '\n').split('\n')[numlines:])

                ret['html'] = contents
        except:
            ret['errors'] = ['Error: Unable to read log file.']

    else:
        ret['errors'] = ['Error: Bad post request formatting.']

    return jsonify(ret)
