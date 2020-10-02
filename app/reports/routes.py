import datetime
from flask import render_template, request, url_for, jsonify, current_app, flash, redirect
from flask_login import login_required
from rq.job import Job
from rq.exceptions import NoSuchJobError
from app.reports import bp
from app.reports.forms import ProductionReportForm
from app.main import database_queries as main_dbq
from app.reports import database_queries as reports_dbq


@bp.route('/', methods=['GET', 'POST'])
@login_required
def production_reports():

    production_report_form = ProductionReportForm(prefix='production_report')
    production_report_form.instrument.choices = main_dbq.instrument_id_name_pairs()

    if production_report_form.validate_on_submit() and production_report_form.submit.data:

        instrument = production_report_form.instrument.data
        start_date = production_report_form.start_date.data
        end_date = production_report_form.end_date.data

        if start_date > end_date:
            flash('Start date must come on or before the end date.')
            return render_template('reports/production_reports.html', form=production_report_form)

        return redirect(url_for('reports.production_report_submit',
                                instrument=instrument,
                                start_date=start_date,
                                end_date=end_date))

    return render_template('reports/production_reports.html',
                           title='Production Report',
                           form=production_report_form)


@bp.route('/<instrument>/<start_date>/<end_date>/', methods=['GET', 'POST'])
@login_required
def production_report_submit(instrument, start_date, end_date):

    production_report_form = ProductionReportForm(prefix='production_report')
    production_report_form.instrument.choices = main_dbq.instrument_id_name_pairs()

    if production_report_form.validate_on_submit() and production_report_form.submit.data:

        instrument = production_report_form.instrument.data
        start_date = production_report_form.start_date.data
        end_date = production_report_form.end_date.data

        if start_date > end_date:
            flash('Start date must come on or before the end date.')
            return redirect(url_for('reports.production_reports'))

        return redirect(url_for('reports.production_report_submit',
                                instrument=instrument,
                                start_date=start_date,
                                end_date=end_date))

    production_report_form.instrument.data = instrument
    production_report_form.start_date.data = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    production_report_form.end_date.data = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    # submit report job
    job = current_app.task_queue.enqueue_call(
        func=reports_dbq.production_report,
        args=(instrument, start_date, end_date,),
        result_ttl=5000
    )

    return render_template('reports/production_reports.html',
                           title='Production Report: {} {}-{}'.format(instrument, start_date, end_date),
                           form=production_report_form,
                           job_id=job.get_id())


@bp.route("/job-status/", methods=['POST'])
@login_required
def get_report_status():

    data = request.get_json()

    if data:
        job_key = data.get('job_id')
        try:
            job = Job.fetch(job_key, connection=current_app.redis)

            if job.is_finished:

                data = job.result

                return jsonify({'complete': True,
                                'progress': 100.0,
                                'html': render_template('reports/_report.html', data=data),
                                'data': data})
            else:
                return jsonify({'complete': False, 'progress': job.meta.get('progress', 0)})

        except NoSuchJobError:
            return jsonify({'complete': True, 'progress': 0.0, 'errors': ['job_id: {} is not available.'.format(job_key)]})
