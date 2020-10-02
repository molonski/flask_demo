import numpy as np
from app import create_app
from app.main.models import Instrument, TestLog, SensorResult, Calculations, Components
from rq import get_current_job


def production_report(instrument, start_date, end_date):
    data = {'instrument': instrument,
            'start_date': start_date,
            'end_date': end_date,
            'test_count': 0
            }

    # start the job status reporting - 0 %
    _job_progress_reporting(additional_steps=1)

    # find instrument id
    instrument_id = _instrument_lookup(instrument)

    data = _test_log_analysis(instrument_id, start_date, end_date, data)

    # table headers for the sensor, calc, and component results
    data['table_column_names'] = [{"title": col} for col in
                                  ['name', '# passed', '# failed', '% passed', 'mean reading', 'std ']]

    data = _sensor_result_analysis(instrument_id, data)

    data = _calc_analysis(instrument_id, data)

    data = _component_analysis(instrument_id, data)

    # test log ids were needed for filtering sensor, calc, and component data, no longer needed so drop here
    if data.get('testlog_ids'):
        del data['testlog_ids']

    return data


def _job_progress_reporting(current_step=None, additional_steps=None):

    job = get_current_job()
    if job:

        if additional_steps:
            total_steps = job.meta.get('total_steps', 0)
            job.meta['total_steps'] = total_steps + additional_steps

        else:
            job.meta['current_step'] = current_step if current_step else job.meta.get('current_step', 0) + 1
            job.meta['progress'] = np.round(100.0 * job.meta['current_step'] / job.meta.get('total_steps', 100), 2)

        job.save_meta()


def _instrument_lookup(instrument):
    app = create_app()

    with app.app_context():
        options = {ins.development_name: ins.id for ins in Instrument.query.all()}
        return options.get(instrument)


def _test_log_analysis(instrument_id, start_date, end_date, data={}):
    app = create_app()

    with app.app_context():
        tests = TestLog.query.with_entities(TestLog.id,
                                            TestLog.timestamp,
                                            TestLog.serial_number,
                                            TestLog.result,
                                            TestLog.test_duration
                                            ).filter(TestLog.instrument_id == instrument_id,
                                                     TestLog.timestamp >= start_date,
                                                     TestLog.timestamp <= end_date).all()

        data['test_count'] = len(tests)
        if tests:

            # all test pass fail
            data['testlog_ids'] = [t[0] for t in tests]

            pass_sn = [t[2] for t in tests if t[3] == 'pass']
            fail_sn = [t[2] for t in tests if t[3] == 'fail']

            data['all_pie'] = {'values': [len(pass_sn), len(fail_sn)],
                               'labels': ['pass', 'fail'],
                               'colors': ['#99ee99', '#ee9999']}

            # unique serial numbers
            data['unique_sn'] = len(set(pass_sn + fail_sn))

            # test durations
            durations = [t[4] for t in tests]
            data['duration_avg'] = np.round(np.mean(durations), 2)
            data['duration_std'] = np.round(np.std(durations), 2)

            # minute second test duration
            minute = int(data['duration_avg'] / 60)
            sec = int(data['duration_avg'] - minute * 60)
            sec_string = ' and {} second{}'.format(sec, 's' if sec > 1 else '') if sec else ''
            data['duration_min_sec'] = '{} minutes{}'.format(minute, sec_string)

            # duration histogram - note durations are converted to minutes
            hist_arrays, hist_edges = np.histogram([d / 60.0 for d in durations], 20)
            hist_arrays = hist_arrays.tolist()
            hist_width = np.round(np.mean(np.diff(hist_edges)), 2)
            hist_center = np.round(hist_edges + hist_width / 2, 2).tolist()
            data['duration_bar'] = {'x': hist_center,
                                    'y': hist_arrays,
                                    'widths': [hist_width for _ in hist_center]}

            # sort tests by serial numbers
            tests_by_sn = {}
            for sn in pass_sn:
                if sn in tests_by_sn:
                    tests_by_sn[sn].append(1)
                else:
                    tests_by_sn[sn] = [1]

            for sn in fail_sn:
                if sn in tests_by_sn:
                    tests_by_sn[sn].append(0)
                else:
                    tests_by_sn[sn] = [0]

            # retests - sort by number of times tested
            test_pie = {}
            retest_bar = {}
            for sn in tests_by_sn.keys():

                num_tests = len(tests_by_sn[sn])
                rs = 'pass' if any(tests_by_sn[sn]) else 'fail'
                key = '{} after {} test{}'.format(rs, num_tests, 's' if num_tests > 1 else '')

                # for retest pie chart
                if key in test_pie:
                    test_pie[key].append(sn)
                else:
                    test_pie[key] = [sn]

                # for retest bar chart
                if num_tests in retest_bar:
                    retest_bar[num_tests].append(sn)
                else:
                    retest_bar[num_tests] = [sn]

            # serial number pie chart
            data['sn_pie'] = {'values': [sum([len(test_pie[key]) for key in test_pie if 'pass' in key]),
                                         sum([len(test_pie[key]) for key in test_pie if 'fail' in key])],
                              'labels': ['pass', 'fail'],
                              'colors': ['#99ee99', '#ee9999']}

            # retest pie chart
            labels = sorted([key for key in test_pie.keys() if 'tests' in key])
            values = [len(test_pie[label]) for label in labels]
            colors = []

            retest_fail_count = sum([1 for label in labels if 'fail' in label])
            retest_pass_count = sum([1 for label in labels if 'pass' in label])
            fail_step = int(9 / retest_fail_count) if retest_fail_count else 9
            pass_step = int(9 / retest_pass_count) if retest_pass_count else 9
            for label in labels:
                num = int(label.split(' ')[2])
                colors.append('#{0}{0}ee{0}{0}'.format(9 - (num - 2) * pass_step) if 'pass' in label else
                              '#ee{0}{0}{0}{0}'.format(9 - (num - 2) * fail_step))

            data['retest_pie'] = {'values': values,
                                  'labels': labels,
                                  'colors': colors}

            data['total_retests'] = sum([len(test_pie[key]) for key in labels])

            # retest bar chart
            del retest_bar[1]  # deleted tested one times
            data['retest_bar'] = {'x': sorted(retest_bar.keys())}
            data['retest_bar']['y'] = [len(retest_bar[x]) for x in data['retest_bar']['x']]
            data['retest_bar']['widths'] = [1 for _ in data['retest_bar']['x']]
            data['retest_bar']['sns'] = retest_bar  # retest_bar is a dict, keys: # of tests, values: serial number list

        return data


def _sensor_result_analysis(instrument_id, data):
    app = create_app()

    with app.app_context():

        sensor_names = SensorResult.query.with_entities(SensorResult.sensor_name).\
            filter(SensorResult.instrument_id == instrument_id).distinct().all()

        sensor_data = []

        _job_progress_reporting(additional_steps=len(sensor_names))

        for ind, sensor_name in enumerate(sensor_names):

            _job_progress_reporting()

            sendata = SensorResult.query.with_entities(SensorResult.measurement,
                                                       SensorResult.result
                                                       ).filter(SensorResult.instrument_id == instrument_id,
                                                                SensorResult.sensor_name == sensor_name,
                                                                SensorResult.testlog_id.in_(data['testlog_ids'])
                                                                ).all()

            sensor_pass = [s[0] for s in sendata if s[1] == 'pass' and ~np.isnan(s[0])]
            sensor_fail = [s[0] for s in sendata if s[1] == 'fail' and ~np.isnan(s[0])]

            del sendata

            sensor_avg = np.round(np.mean(sensor_pass + sensor_fail), 3)
            sensor_std = np.round(np.std(sensor_pass + sensor_fail), 3)
            sensor_data.append([sensor_name,
                                str(len(sensor_pass)),
                                str(len(sensor_fail)),
                                str(np.round(float(len(sensor_pass)) / (len(sensor_pass) + len(sensor_fail)) * 100.0, 2)),
                                str(sensor_avg),
                                str(sensor_std)])

        data['sensors'] = sensor_data

    return data


def _calc_analysis(instrument_id, data):
    app = create_app()

    with app.app_context():

        calc_names = [c[0] for c in Calculations.query.with_entities(Calculations.calc_name).filter(
            Calculations.instrument_id == instrument_id).distinct().all()]

        _job_progress_reporting(additional_steps=len(calc_names))

        calc_data = []
        for calc_name in calc_names:

            _job_progress_reporting()

            calcdata = SensorResult.query.with_entities(Calculations.value,
                                                        Calculations.result
                                                        ).filter(Calculations.instrument_id == instrument_id,
                                                                 Calculations.calc_name == calc_name,
                                                                 Calculations.testlog_id.in_(data['testlog_ids'])
                                                                 ).all()

            calc_pass = [s[0] for s in calcdata if s[1] == 'pass' and ~np.isnan(s[0])]
            calc_fail = [s[0] for s in calcdata if s[1] == 'fail' and ~np.isnan(s[0])]

            del calcdata

            calc_avg = np.round(np.mean(calc_pass + calc_fail), 3)
            calc_std = np.round(np.std(calc_pass + calc_fail), 3)
            calc_data.append([calc_name,
                              str(len(calc_pass)),
                              str(len(calc_fail)),
                              str(np.round(float(len(calc_pass)) / (len(calc_pass) + len(calc_fail)) * 100.0, 2)),
                              str(calc_avg),
                              str(calc_std)])

        data['calcs'] = calc_data

    return data


def _component_analysis(instrument_id, data):
    app = create_app()

    with app.app_context():

        component_names = [cp[0] for cp in Components.query.with_entities(Components.component_name).filter(
            Components.instrument_id == instrument_id).distinct().all()]

        comp_data = []

        _job_progress_reporting(additional_steps=len(component_names))

        # two layers to components
        #   - component_name (e.g. battery)
        #   - measurement_name (e.g. charge_level)
        #   - name will be reported as battery.charge_level
        # and two for loops required

        for component_name in component_names:

            _job_progress_reporting()

            compdata = SensorResult.query.with_entities(Components.value,
                                                        Components.result,
                                                        Components.measurement_name
                                                        ).filter(
                Components.instrument_id == instrument_id,
                Components.component_name == component_name,
                Components.testlog_id.in_(data['testlog_ids'])
            ).all()

            comp_measurments = list(set([s[2] for s in compdata]))

            for comp_measurment in comp_measurments:
                comp_name = '{}.{}'.format(component_name, comp_measurment)

                comp_pass = [s[0] for s in compdata if (s[1] == 'pass' and s[2] == comp_measurment and ~np.isnan(s[0]))]
                comp_fail = [s[0] for s in compdata if (s[1] == 'fail' and s[2] == comp_measurment and ~np.isnan(s[0]))]

                del compdata
                comp_avg = np.round(np.mean(comp_pass + comp_fail), 3)
                comp_std = np.round(np.std(comp_pass + comp_fail), 3)
                comp_data.append([comp_name,
                                  str(len(comp_pass)),
                                  str(len(comp_fail)),
                                  str(np.round(float(len(comp_pass)) / (len(comp_pass) + len(comp_fail)) * 100.0, 2)),
                                  str(comp_avg),
                                  str(comp_std)])

        data['components'] = comp_data

    return data
