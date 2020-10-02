import os
import sys
import logging
import datetime
import time
import pandas as pd
import numpy as np
from app.productiontest.constants import *
from app.productiontest.tests.tap_test import TapTest
from app.productiontest.tests.result_check import result_check
from app.productiontest.test_api.test_api import TestApi
from app.productiontest import __version__ as test_sw_version
from app.productiontest.instruments.instrument1 import Instrument1
import pdb


class TestMain(object):
    """
    Main class of Artiphon Test Setup

    """

    def __init__(self, inst, sn, log_file_name):

        # test details =======================================================
        self.instrument_name = inst
        self.serial_number = sn
        self.test_start = datetime.datetime.utcnow()
        self.test_end = None

        # logger =======================================================
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # file logger and format
        self.log_file_name = log_file_name
        self.log_file_fullpath = self._set_log_file_path(log_file_name)
        file_logger = logging.FileHandler(self.log_file_fullpath)
        file_logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # add handles to the logger
        self.logger.addHandler(file_logger)

        # test plan =======================================================
        # load test plan from CSV based on instrument name
        self.test_plan = pd.read_csv('app//productiontest//test_plans//{}.csv'.format(self.instrument_name.lower()))
        self.logger.info('{} test plan loaded'.format(self.instrument_name))

        # add columns to test plan
        for col in COLUMNS_TO_ADD:
            if col not in self.test_plan.columns:
                self.test_plan[col] = None

        # instrument object =======================================================
        self.instrument = self.log_file_fullpath

    def connect_to_instrument(self):

        # instrument object =======================================================
        if self.instrument_name.lower() == 'instrument1':
            self.instrument = Instrument1()
        elif self.instrument_name.lower() == 'delorean':
            self.instrument = None

        if self.instrument and self.instrument.attached:
            self.logger.info('{} connected.'.format(self.instrument_name))
            return True

        self.logger.error('{} not detected.'.format(self.instrument_name))
        return False

    def perform_tests(self):

        # perform tap test
        if TAP_TEST_IDENTIFIER in self.test_plan[TEST_TYPE_OR_COMPONENT].values:
            self._perform_tap_test()

        if CALCULATION_IDENTIFIER in self.test_plan[MEASUREMENT_TYPE].unique():
            self._run_calcs()

    def _perform_tap_test(self):

        tt = TapTest(self.logger, self.test_plan, self.instrument)
        if tt.mc_connected:
            tt.perform_test()

        # copy result back to test_main test plan
        self.test_plan = tt.test_plan

    @staticmethod
    def _set_log_file_path(log_file_name):

        current_directory = os.path.dirname(os.path.realpath(__file__))
        top_level_directory = os.path.sep.join(current_directory.rstrip(os.path.sep).split(os.path.sep)[:-2])

        path = os.path.join(top_level_directory, TEST_LOG_FOLDER)

        if not os.path.isdir(path):
            os.makedirs(path)

        return os.path.join(path, log_file_name)

    def _run_calcs(self):

        batch_inds = self.test_plan[self.test_plan[MEASUREMENT_TYPE] == CALCULATION_IDENTIFIER].index

        if batch_inds.any():
            self.logger.info('Running Batch Calculations...')

        for ind in batch_inds:

            calc_name = self.test_plan.loc[ind, MEASUREMENT_NAME]

            if '_' in calc_name:
                name_identifier, test_type = calc_name.rsplit('_', 1)
            else:
                name_identifier = ''
                test_type = calc_name

            vals = [self.test_plan.loc[row_ind, MEASUREMENT] for row_ind in self.test_plan.index
                    if (name_identifier in self.test_plan.loc[row_ind, MEASUREMENT_NAME]
                        and ~np.isnan(self.test_plan.loc[row_ind, MEASUREMENT])
                        and self.test_plan.loc[row_ind, MEASUREMENT_TYPE] == self.test_plan.loc[ind, MEASUREMENT_TYPE]
                        )]

            if vals:
                if test_type == 'mean':
                    val = float(np.round(np.mean(vals), 6))

                elif test_type == 'std':
                    val = float(np.round(np.std(vals), 6))

                pass_fail = result_check(self.test_plan.loc[ind, COMPARISON_TYPE],
                                         self.test_plan.loc[ind, MIN_ALLOW],
                                         self.test_plan.loc[ind, MAX_ALLOW],
                                         self.test_plan.loc[ind, MEASUREMENT])

                self.test_plan.loc[ind, MEASUREMENT] = val
                self.test_plan.loc[ind, PASS_FAIL] = pass_fail

                # log result
                self.logger.info('{} - {} - {}'.format(calc_name, val, pass_fail))

    def write_result_to_csv(self):

        self.logger.info('Writing result to CSV...')

        current_directory = os.path.dirname(os.path.realpath(__file__))
        top_level_directory = os.path.sep.join(current_directory.rstrip(os.path.sep).split(os.path.sep)[:-2])

        path = os.path.join(top_level_directory, TEST_RESULTS_FOLDER)

        if not os.path.isdir(path):
            os.makedirs(path)

        filename = '{}'.format(self.log_file_name).replace('.txt', '.csv')
        full_path = os.path.join(path, filename)

        self.results_csv_path = full_path

        self.test_plan[COLUMNS_TO_EXPORT].to_csv(full_path)

        self.logger.info('Results written to CSV: {}'.format(filename))

        return full_path

    def convert_result_to_dict(self):
        # convert pandas dataframe to dictionary
        # convert timestamps to strings, but allow requests library convert the dict to json

        self.logger.info('Converting test result to JSON')

        test_results = self.test_plan[PASS_FAIL].unique().tolist()

        # see the TestLog database table names in app.main.models
        result = {'result': 'pass' if len(test_results) == 1 and 'pass' in test_results else 'fail',
                  'test_sw_version': test_sw_version,
                  'sensors': [],
                  'components': [],
                  'calculations': []
                  }

        for ind in self.test_plan.index:

            # name = self.test_plan.loc[ind, MEASUREMENT_NAME]
            # self.logger.info('ind: {} - {}'.format(ind, name))

            min_allow = self.test_plan.loc[ind, MIN_ALLOW]
            max_allow = self.test_plan.loc[ind, MAX_ALLOW]

            val = self.test_plan.loc[ind, MEASUREMENT]
            if ~np.isnan(val):
                if self.test_plan.loc[ind, MEASUREMENT_TYPE] == SENSOR_IDENTIFIER:
                    # see the SensorResult database table names in app.main.models
                    new_measurement = {'sensor_name': self.test_plan.loc[ind, MEASUREMENT_NAME],
                                       'measurement': float(val) if val else None,
                                       'min_allowable': float(min_allow) if min_allow else None,
                                       'max_allowable': float(max_allow) if min_allow else None,
                                       'comparison_type': self.test_plan.loc[ind, COMPARISON_TYPE],
                                       'time_response_x': self.test_plan.loc[ind, TX],
                                       'time_response_y': self.test_plan.loc[ind, TY],
                                       'result': self.test_plan.loc[ind, PASS_FAIL]
                                       }
                    result['sensors'].append(new_measurement)

                elif self.test_plan.loc[ind, MEASUREMENT_TYPE] == COMPONENT_IDENTIFIER:
                    # see the Component database table names in app.main.models
                    new_component = {'component_name': self.test_plan.loc[ind, MEASUREMENT_NAME],
                                     'measurement_name': self.test_plan.loc[ind, TEST_TYPE_OR_COMPONENT],
                                     'value': float(val) if val else None,
                                     'min_allowable': float(min_allow) if min_allow else None,
                                     'max_allowable': float(max_allow) if min_allow else None,
                                     'comparison_type': self.test_plan.loc[ind, COMPARISON_TYPE],
                                     'result': self.test_plan.loc[ind, PASS_FAIL]
                                     }
                    result['components'].append(new_component)

                elif self.test_plan.loc[ind, MEASUREMENT_TYPE] == CALCULATION_IDENTIFIER:
                    # see the Calculations table names in app.main.models
                    new_calculation = {'calc_name': self.test_plan.loc[ind, MEASUREMENT_NAME],
                                       'value': float(val) if val else None,
                                       'min_allowable': float(min_allow) if min_allow else None,
                                       'max_allowable': float(max_allow) if min_allow else None,
                                       'comparison_type': self.test_plan.loc[ind, COMPARISON_TYPE],
                                       'result': self.test_plan.loc[ind, PASS_FAIL]
                                       }
                    result['calculations'].append(new_calculation)

        return result

    def upload_result_to_database(self, results_dict):
        api = TestApi(results_dict, self.logger)
        api.upload_result()


def run_test(instrument, sn, log_file_name):
    test_obj = TestMain(instrument, sn, log_file_name)
    connected = test_obj.connect_to_instrument()
    csv_path = ''

    if connected:

        test_obj.instrument.set_development_mode(True)
        test_obj.perform_tests()
        csv_path = test_obj.write_result_to_csv()

        test_obj.logger.info('Automated Test Routine Complete.')

    else:

        test_obj.logger.error('Aborting Automated Test Routine. No Instrument dectected.')

    result = test_obj.convert_result_to_dict()

    return {'log_file_path': test_obj.log_file_fullpath,
            'results_csv_path': csv_path,
            'result': result}


def debug_i1_tap_test():

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    test_plan = pd.read_csv('app//productiontest//test_plans//Instrument1.csv')

    tap_test = TapTest(logger, test_plan)
    tap_test.perform_test(step_through=True)


if __name__ == "__main__":

    instrument_name = sys.argv[1]

    if instrument_name == 'debug_i1_tap':
        debug_i1_tap_test()

    else:

        serial_number = sys.argv[2]
        log_file_name = sys.argv[3]

        run_test(instrument_name, serial_number, log_file_name)
