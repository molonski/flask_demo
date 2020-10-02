import base64
import datetime
import requests
from app.productiontest.constants import *


class TestApi(object):
    """
    Test result database API interactions

    """

    def __init__(self, result, logger):

        self.logger = logger
        self.result = result

        self.token = None

    def upload_result(self):

        self.logger.info('requesting api token.')
        self.token = self._get_api_token()

        if self.token:

            self.logger.info('received api token.')

            # push results to database
            self.logger.info('posting result to database.')
            r = self._push_result_to_db(self.result)
            job_id = r.json()['job_id']
            self.logger.info('job id of database insertion: {}'.format(job_id))

            # check job status
            t_submit = datetime.datetime.utcnow()
            testlog_id = -1

            while datetime.datetime.utcnow() < t_submit + \
                    datetime.timedelta(seconds=VALIDATION_TIMEOUT) and testlog_id < 1:
                r = self._check_submission_status(job_id)
                if 'testlog_id' in r.json().keys():
                    testlog_id = r.json()['testlog_id']

            if testlog_id > 0:
                self.logger.info('result submission successful. Testlog_id: {}'.format(testlog_id))

                # get result from database
                r = self._fetch_result_from_db(testlog_id)

                # compare submission to requested result
                # comparison = self._compare_results(self.result, r.json())
                # if comparison.get('success'):
                #     self.logger.info('test result matches : {}'.format(testlog_id))
                #
                # else:
                #     self.logger.warning('test result in database differs from local result')
            else:
                self.logger.info('Instrument, Serial Number, and Time Stamp combo already exist in the database.')

        else:
            self.logger.warning('could not connect to API in order to submit test result.')

    def _get_api_token(self):
        token = None
        session = requests.Session()
        session.auth = self._get_pdub()
        url_base = DEV_API if DEV else PROD_API
        r = session.post('{}{}'.format(url_base, TOKEN_URL))
        if r.ok and 'token' in r.json():
            token = r.json()['token']
        return token

    def _push_result_to_db(self, result):
        url_base = DEV_API if DEV else PROD_API
        return requests.post('{}{}'.format(url_base, JOB_SUBMISSION_URL), json=result,
                             headers={'Authorization': 'Bearer {}'.format(self.token)})

    def _check_submission_status(self, job_id):
        url_base = DEV_API if DEV else PROD_API
        return requests.get('{}{}{}'.format(url_base, JOB_STATUS_URL, job_id),
                            headers={'Authorization': 'Bearer {}'.format(self.token)})

    def _fetch_result_from_db(self, testlog_id):
        url_base = DEV_API if self.dev else PROD_API
        return requests.get('{}{}{}'.format(url_base, TESTLOG_URL, testlog_id),
                            headers={'Authorization': 'Bearer {}'.format(self.token)})

    # needs work
    # def _compare_results(self, result, db_result):
    #     comparison = {'success': False,
    #                   'diffs': []}
    #
    #     if result == db_result:
    #         comparison['success'] = True
    #     else:
    #         # log diffs
    #         pass
    #
    #     return comparison

    @staticmethod
    def _get_pdub():
        with open('pdub', 'r') as f:
            up = f.read().split('\n')
            name = base64.b64decode(up[0])
            code = base64.b64decode(up[1])
            return name, code
