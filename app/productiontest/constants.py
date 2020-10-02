# all references to column names here in case the column names change

# =============================================
# directory names
TEST_LOG_FOLDER = 'test_logs'
TEST_RESULTS_FOLDER = 'test_results'

# ==============================================
# Test Plan Columns

MEASUREMENT_TYPE = 'measurement_type'
TEST_TYPE_OR_COMPONENT = 'test_type'
MEASUREMENT_NAME = 'measurement_name'
MEASUREMENT = 'measurement'
PASS_FAIL = 'result'
COMPARISON_TYPE = 'comparison_type'
MIN_ALLOW = 'min_allowable'
MAX_ALLOW = 'max_allowable'
TX = 'time_response_x'
TY = 'time_response_y'
TIMESTAMP = 'timestamp'
X_COL = 'x (mm)'
Y_COL = 'y (mm)'
Z_COL = 'z (mm)'
SORT_COL = 'tap_test_path'
FORCE_SCALE = 'force_scale'
FORCE_STEPS = 5.0

# i1 specific
MEASUREMENT_DEV_NAME = 'measurement_dev_name'

COLUMNS_TO_ADD = [MEASUREMENT, TIMESTAMP, PASS_FAIL, TX, TY]
COLUMNS_TO_EXPORT = [MEASUREMENT_TYPE, TEST_TYPE_OR_COMPONENT, MEASUREMENT_NAME, COMPARISON_TYPE,
                     MIN_ALLOW, MAX_ALLOW, MEASUREMENT, PASS_FAIL, TIMESTAMP, TX, TY]

# ==============================================================================
# terms used to identify sensor, component, calculation in testplan spread sheet
SENSOR_IDENTIFIER = 'sensor'
CALCULATION_IDENTIFIER = 'calc'
COMPONENT_IDENTIFIER = 'component'
TAP_TEST_IDENTIFIER = 'tap_test'
SPEAKER_TEST_IDENTIFIER = 'speaker_test'

# ======================================================================================
# FOR API

TOKEN_URL = 'tokens/'
JOB_SUBMISSION_URL = 'job-submission/'
JOB_STATUS_URL = 'job-status/'
TESTLOG_URL = 'testlog/'

SENSOR_RESULT_DBS = ['sensor_name', 'measurement', 'min_allowable', 'max_allowable',
                     'time_response_x', 'time_response_y', 'result', 'timestamp']

DEV = False
DEV_API = 'http://localhost:5000/api/'
PROD_API = 'http://artiphon-production.heroku.com/api/'
VALIDATION_TIMEOUT = 120

