from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_events,
    aws_events_targets as targets,
    )


class EmailSummaryAppStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        
        main_lambda = _lambda.Function(self,
            'MainHandler',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset('lambda'),
            handler= 'main_lambda.handler',
            memory_size= 128,
            )
        
        run_rule = aws_events.Rule(self, 'CronRule',schedule=aws_events.Schedule.expression("cron(0/15 * * * ? *)"))
        run_rule.add_target(target=targets.LambdaFunction(main_lambda))

