from app import db, create_app
from app.main.models import Instrument, TestLog, SensorResult, Calculations, Components
import pdb

# =======================================================
# instrument queries

def create_new_instrument(development_name, market_name):
    instrument = Instrument(development_name=development_name, market_name=market_name)
    db.session.add(instrument)
    db.session.commit()
    return instrument


def get_instrument_by_dev_name(development_name):
    return Instrument.query.filter(Instrument.development_name == development_name).first()


def get_instrument_by_market_name(market_name):
    return Instrument.query.filter(Instrument.development_name == market_name).first()


def get_instrument_by_id(instrument_id):
    return Instrument.query.filter(Instrument.id == instrument_id).first()


def instrument_id_name_pairs():
    return [(inst.development_name, inst.development_name) for inst
            in Instrument.query.order_by('development_name')]

# =======================================================
# testlog results queries

def get_test_results_by_ins_sn(instrument_name, serial_number, page=1, per_page=100, timestamp=None):
    app = create_app()

    with app.app_context():
        fields = ['timestamp', 'instrument', 'serial number', 'result', 'duration']
        instrument_lookup = {ins.development_name: ins.id for ins in Instrument.query.all()}
        if timestamp:
            tests = TestLog.query.with_entities(TestLog.id,
                                                TestLog.timestamp,
                                                TestLog.serial_number,
                                                TestLog.result,
                                                TestLog.test_duration
                                                ).filter(TestLog.instrument_id == instrument_lookup[instrument_name],
                                                         TestLog.serial_number == serial_number,
                                                         TestLog.timestamp == timestamp).paginate(
                                                            page, per_page, False)
        else:
            tests = TestLog.query.with_entities(TestLog.id,
                                                TestLog.timestamp,
                                                TestLog.serial_number,
                                                TestLog.result,
                                                TestLog.test_duration
                                                ).filter(TestLog.instrument_id == instrument_lookup[instrument_name],
                                                         TestLog.serial_number == serial_number).paginate(
                                                            page, per_page, False)

        return fields, instrument_name, tests


def get_test_results_by_ins_date_range(instrument_name, results_type, start_date, end_date, page, per_page):
    app = create_app()

    with app.app_context():

        fields = ['timestamp', 'instrument', 'serial number', 'result', 'duration']
        instrument_lookup = {ins.development_name: ins.id for ins in Instrument.query.all()}

        if results_type == 'all':
            tests = TestLog.query.with_entities(TestLog.id,
                                                TestLog.timestamp,
                                                TestLog.serial_number,
                                                TestLog.result,
                                                TestLog.test_duration
                                                ).filter(TestLog.instrument_id == instrument_lookup[instrument_name],
                                                         TestLog.timestamp >= start_date,
                                                         TestLog.timestamp <= end_date
                                                         ).order_by(TestLog.timestamp).paginate(
                                                                    page, per_page, False)
        else:
            tests = TestLog.query.with_entities(TestLog.id,
                                                TestLog.timestamp,
                                                TestLog.serial_number,
                                                TestLog.result,
                                                TestLog.test_duration
                                                ).filter(TestLog.instrument_id == instrument_lookup[instrument_name],
                                                         TestLog.timestamp >= start_date,
                                                         TestLog.timestamp <= end_date,
                                                         TestLog.result == results_type,
                                                         ).order_by(TestLog.timestamp).paginate(
                                                                    page, per_page, False)

        return fields, instrument_name, tests

# =======================================================
# single test result


def enter_new_test_result(result):

    app = create_app()

    with app.app_context():

        # search by development name instrument
        instrument = get_instrument_by_dev_name(result['instrument_name'])
        # if no result search by market name
        if not instrument:
            instrument = get_instrument_by_market_name(result['instrument_name'])

        # check to see if result exists in database
        _, _, existing = get_test_results_by_ins_sn(instrument.development_name,
                                                    result['serial_number'],
                                                    timestamp=result['timestamp'])
        # existing will be a tuple
        # keys, instrument, pagination object containing results tuples in the items attribute
        if not existing.items:
            new_testlog_entry = TestLog(timestamp=result['timestamp'],
                                        instrument_id=instrument.id,
                                        serial_number=result['serial_number'],
                                        result=result['result'],
                                        test_duration=result['test_duration'],
                                        notes=result['notes'],
                                        location=result['location'],
                                        test_sw_version=result['test_sw_version'])

            db.session.add(new_testlog_entry)
            db.session.commit()

            for measurement in result.get('measurements', []):
                new_measurement = SensorResult(testlog_id=new_testlog_entry.id,
                                               instrument_id=instrument.id,
                                               sensor_name=measurement[0],
                                               measurement=measurement[1],
                                               min_allowable=measurement[2],
                                               max_allowable=measurement[3],
                                               result=measurement[6],
                                               time_response_x=measurement[4],
                                               time_response_y=measurement[5])

                db.session.add(new_measurement)
                db.session.commit()

            for calc in result.get('calculations', []):
                new_calc = Calculations(testlog_id=new_testlog_entry.id,
                                        instrument_id=instrument.id,
                                        calc_name=calc[0],
                                        value=calc[1],
                                        min_allowable=calc[2],
                                        max_allowable=calc[3],
                                        result=calc[4])

                db.session.add(new_calc)
                db.session.commit()

            for component in result.get('components', []):
                new_comp = Components(testlog_id=new_testlog_entry.id,
                                      instrument_id=instrument.id,
                                      component_name=component['component_name'],
                                      measurement_name=component['measurement_name'],
                                      value=component['value'],
                                      min_allowable=component['min_allowable'],
                                      max_allowable=component['max_allowable'],
                                      result=component['result'])

                db.session.add(new_comp)
                db.session.commit()

            return new_testlog_entry.id

        else:
            return -1


def get_test_result_by_id(testlog_id):
    result = TestLog.query.filter(TestLog.id == testlog_id).first()
    test_result = {}

    if result:
        test_result = result.to_dict()

        measurements = _get_sensor_results_by_testlog_id(testlog_id)
        if measurements:
            test_result['measurement_keys'] = ['sensor_name', 'measurement', 'min_allowable',
                                               'max_allowable', 'result']
            test_result['measurements'] = [m.to_tuple() for m in measurements]

        calcs = _get_calcs_by_testlog_id(testlog_id)
        if calcs:
            test_result['calc_keys'] = ['calc_name', 'value', 'min_allowable',
                                        'max_allowable', 'result']
            test_result['calcs'] = [c.to_tuple() for c in calcs]

        components = _get_components_by_testlog_id(testlog_id)
        if calcs:
            test_result['component_keys'] = ['component_name', 'component_measurement', 'value', 'min_allowable',
                                             'max_allowable', 'result']
            test_result['components'] = [c.to_tuple() for c in components]

    return test_result


def _get_sensor_results_by_testlog_id(testlog_id):
    return SensorResult.query.filter(SensorResult.testlog_id == testlog_id).order_by(SensorResult.sensor_name).all()


def _get_calcs_by_testlog_id(testlog_id):
    return Calculations.query.filter(Calculations.testlog_id == testlog_id).order_by(Calculations.calc_name).all()


def _get_components_by_testlog_id(testlog_id):
    return Components.query.filter(Components.testlog_id == testlog_id).order_by(Components.component_name).all()
