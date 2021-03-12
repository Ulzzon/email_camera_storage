from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_events,
    aws_events_targets as targets,
    )
from email_summary_app.email_construct import EmailConstruct

class EmailSummaryAppStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        email_lambda = EmailConstruct(self, 'EmailLambda')
        
        run_rule = aws_events.Rule(self, 'CronRule',schedule=aws_events.Schedule.expression("cron(0 7,19 * * ? *)"))
        run_rule.add_target(target=targets.LambdaFunction(email_lambda.handler))
