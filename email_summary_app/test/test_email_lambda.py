import pytest
import os
from lambdas.main_lambda import EmailHandler
import unittest.mock
import datetime


class TestEmailLambda:

    def set_environment_variables(self):
        os.environ['LOG_TABLE_NAME'] = 'test_table_name'
        os.environ['S3_BUCKET_NAME'] = 'test_bucket_name'

    def _test_parser(self):
        self.set_environment_variables()
        dirname = os.path.dirname(__file__)
        testdatafile = os.path.join(dirname, 'test_email_data.txt')
        expecter_time_in_iso = datetime.datetime.strptime('Fri, 19 Mar 2021 17:07:38', '%a, %d %b %Y %H:%M:%S')
        email_handler = EmailHandler('some@email.com', 'NotMyPassword')
        with open(testdatafile) as data_file:
            mock_email = data_file.read().split(',')
            print(mock_email)
        (mail_date, attachment_key, attachment_data) = email_handler.parse_email(email_data=mock_email)
        assert mail_date == expecter_time_in_iso.isoformat()