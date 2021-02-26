
from aws_cdk import core

from email_summary_app.email_summary_app_stack import EmailSummaryAppStack


app = core.App()
EmailSummaryAppStack(app, "email-summary-app")

app.synth()
