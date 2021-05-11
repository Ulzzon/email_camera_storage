import json
import pytest

from aws_cdk import core
from email_summary_app.email_summary_app_stack import EmailSummaryAppStack


class TestCDK:

    def get_template(self):
        app = core.App()
        EmailSummaryAppStack(app, "email-summary-app")
        app.synth().get_stack("email-summary-app").template
        return json.dumps(app.synth().get_stack("email-summary-app").template)


    def test_lambda_function_created(self):
        assert('AWS::Lambda::Function' in self.get_template())

    def test_dynamodb_created(self):
        assert('AWS::DynamoDB::Table' in self.get_template())

    def test_runtime_environment_version(self):
        assert('Runtime": "python3.8"')

    def test_runtime_environment_version(self):
        assert('Runtime": "python3.8"')

