from app import db
from app.main import database_queries as dbq


ALLOWABLE_TEST_RESULTS = ['pass', 'abort', 'fail']
ALLOWABLE_TEST_LOCATIONS = ['artiphon', 'factory']


class Instrument(db.Model):
    __tablename__ = "instrument"
    id = db.Column(db.Integer, primary_key=True)
    development_name = db.Column(db.String(64), unique=True)
    market_name = db.Column(db.String(120), unique=True)
    tests = db.relationship('TestLog', backref='test', lazy='dynamic')

    def to_dict(self):
        return {'id': self.id,
                'development_name': self.development_name,
                'market_name': self.market_name,
                'test_count': self.tests.count()}

    def __repr__(self):
        return '<Instrument {}: {}>'.format(self.id, self.development_name)


class TestLog(db.Model):
    #
    # List of all tests run
    #
    __tablename__ = 'testlog'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(32), nullable=False, index=True)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instrument.id'), nullable=False, index=True)
    serial_number = db.Column(db.String(32), nullable=False, index=True)
    result = db.Column(db.String(8), nullable=False, index=True)
    test_duration = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String(), nullable=False, default='')
    location = db.Column(db.String(12), nullable=False, default='factory')
    test_sw_version = db.Column(db.String(12), nullable=False, default='0.0.0')
    sensors = db.relationship('SensorResult', backref='testlog', lazy='dynamic')
    calcs = db.relationship('Calculations', backref='testlog', lazy='dynamic')
    components = db.relationship('Components', backref='testlog', lazy='dynamic')

    def to_dict(self):
        return {'id': self.id,
                'timestamp': self.timestamp,
                'instrument': dbq.get_instrument_by_id(self.instrument_id).development_name,
                'serial_number': self.serial_number,
                'result': self.result,
                'test_duration': self.test_duration,
                'notes': self.notes,
                'location': self.location,
                'test_sw_version': self.test_sw_version,
                'sensor_measurement_count': self.sensors.count(),
                'calculation_count': self.calcs.count(),
                'components_count': self.components.count()}

    def __init__(self, timestamp, instrument_id, serial_number, result, test_duration,
                 notes, location, test_sw_version):
        self.timestamp = timestamp
        self.instrument_id = instrument_id
        self.serial_number = serial_number
        self.result = result.lower() if result.lower() in ALLOWABLE_TEST_RESULTS else 'fail'
        self.test_duration = test_duration
        self.notes = notes
        self.location = location.lower() if location.lower() in ALLOWABLE_TEST_LOCATIONS else 'factory'
        self.test_sw_version = test_sw_version

    def __repr__(self):
        return '<id {}: SN: {} - {}>'.format(self.id, self.serial_number, self.timestamp)


class SensorResult(db.Model):
    #
    # Sensor results from each test
    #
    __tablename__ = 'sensorresult'

    id = db.Column(db.Integer, primary_key=True)
    testlog_id = db.Column(db.Integer, db.ForeignKey('testlog.id'), nullable=False, index=True)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instrument.id'), nullable=False, index=True)
    sensor_name = db.Column(db.String(32), nullable=False, index=True)
    measurement = db.Column(db.Float, nullable=False)
    min_allowable = db.Column(db.Float, nullable=False)
    max_allowable = db.Column(db.Float, nullable=False)
    time_response_x = db.Column(db.String(), nullable=False, default='')
    time_response_y = db.Column(db.String(), nullable=False, default='')
    result = db.Column(db.String(8), nullable=False)

    def to_tuple(self):
        return (self.sensor_name,
                self.measurement,
                self.min_allowable,
                self.max_allowable,
                self.result)

    def to_dict(self):
        return {'id': self.id,
                'testlog_id': self.testlog_id,
                'instrument': dbq.get_instrument_by_id(self.instrument_id).development_name,
                'sensor_name': self.sensor_name,
                'measurement': self.measurement,
                'min_allowable': self.min_allowable,
                'max_allowable': self.max_allowable,
                'time_response_x': self.time_response_x,
                'time_response_y': self.time_response_y,
                'result': self.result}

    def __init__(self, testlog_id, instrument_id, sensor_name, measurement, min_allowable, max_allowable,
                 result, time_response_x='', time_response_y=''):
        self.testlog_id = testlog_id
        self.instrument_id = instrument_id
        self.sensor_name = sensor_name
        self.measurement = measurement
        self.min_allowable = min_allowable
        self.max_allowable = max_allowable
        self.result = result.lower() if result.lower() in ALLOWABLE_TEST_RESULTS else 'fail'
        self.time_response_x = time_response_x
        self.time_response_y = time_response_y

    def __repr__(self):
        return '<id {}: testlog_id: {}, {} - {})>'.format(self.id, self.testlog_id, self.sensor_name, self.measurement)


class Calculations(db.Model):
    #
    # Instrument tests may include calculations on groups of sensor data
    #
    __tablename__ = 'calculations'

    id = db.Column(db.Integer, primary_key=True)
    testlog_id = db.Column(db.Integer, db.ForeignKey('testlog.id'), nullable=False, index=True)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instrument.id'), nullable=False, index=True)
    calc_name = db.Column(db.String(32), nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    min_allowable = db.Column(db.Float, nullable=False)
    max_allowable = db.Column(db.Float, nullable=False)
    result = db.Column(db.String(8), nullable=False)

    def to_tuple(self):
        return (self.calc_name,
                self.value,
                self.min_allowable,
                self.max_allowable,
                self.result)

    def to_dict(self):
        return {'id': self.id,
                'testlog_id': self.testlog_id,
                'instrument': dbq.get_instrument_by_id(self.instrument_id).development_name,
                'calc_name': self.calc_name,
                'value': self.value,
                'min_allowable': self.min_allowable,
                'max_allowable': self.max_allowable,
                'result': self.result}

    def __init__(self, testlog_id, instrument_id, calc_name, value, min_allowable,
                 max_allowable, result):
        self.testlog_id = testlog_id
        self.instrument_id = instrument_id
        self.calc_name = calc_name
        self.value = value
        self.min_allowable = min_allowable
        self.max_allowable = max_allowable
        self.result = result.lower() if result.lower() in ALLOWABLE_TEST_RESULTS else 'fail'

    def __repr__(self):
        return '<id {}: testlog_id: {}, {} - {})>'.format(self.id, self.testlog_id,
                                                          self.calc_name, self.value)


class Components(db.Model):
    #
    # In addition to sensor measurements, quality tests can a review of component testing
    # Components are defined as non senor components, batteries, blue tooth, speakers, etc
    #
    __tablename__ = 'components'

    id = db.Column(db.Integer, primary_key=True)
    testlog_id = db.Column(db.Integer, db.ForeignKey('testlog.id'), nullable=False, index=True)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instrument.id'), nullable=False, index=True)
    component_name = db.Column(db.String(32), nullable=False, index=True)
    measurement_name = db.Column(db.String(32), nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    min_allowable = db.Column(db.Float, nullable=False)
    max_allowable = db.Column(db.Float, nullable=False)
    result = db.Column(db.String(8), nullable=False)

    def to_tuple(self):
        return (self.component_name,
                self.measurement_name,
                self.value,
                self.min_allowable,
                self.max_allowable,
                self.result)

    def to_dict(self):
        return {'id': self.id,
                'testlog_id': self.testlog_id,
                'instrument': dbq.get_instrument_by_id(self.instrument_id).development_name,
                'component_name': self.component_name,
                'measurement_name': self.measurement_name,
                'value': self.value,
                'min_allowable': self.min_allowable,
                'max_allowable': self.max_allowable,
                'result': self.result}

    def __init__(self, testlog_id, instrument_id, component_name, measurement_name, value, min_allowable,
                 max_allowable, result):
        self.testlog_id = testlog_id
        self.instrument_id = instrument_id
        self.component_name = component_name
        self.measurement_name = measurement_name
        self.value = value
        self.min_allowable = min_allowable
        self.max_allowable = max_allowable
        self.result = result.lower() if result.lower() in ALLOWABLE_TEST_RESULTS else 'fail'

    def __repr__(self):
        return '<id {}: testlog_id: {}, {} {} - {})>'.format(self.id, self.testlog_id, self.component_name,
                                                             self.measurement_name, self.value)
