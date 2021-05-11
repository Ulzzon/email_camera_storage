from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_events,
    aws_events_targets as targets,
    aws_apigateway as api_gw,
    )
from email_summary_app.email_construct import EmailConstruct


class EmailSummaryAppStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        email_lambda = EmailConstruct(self, 'EmailLambda')

        statistics_lambda = _lambda.Function(self, 
            'StatisticsLambda', 
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset('lambdas'),
            handler='statistics_lambda.handler',
            memory_size=128,
            environment={
                'LOG_TABLE_NAME': email_lambda._table.table_name,
            }
        )

        image_lambda = _lambda.Function(self, 
            'ImageLambda', 
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset('lambdas'),
            handler='image_lambda.handler',
            memory_size=128,
            environment={
                'S3_BUCKET_NAME': email_lambda._image_bucket.bucket_name,
            }
        )
        image_filter_lambda = _lambda.Function(self, 
            'ImageFilterLambda', 
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset('lambdas'),
            handler='image_filter_lambda.handler',
            memory_size=128,
            environment={
                'S3_BUCKET_NAME': email_lambda._image_bucket.bucket_name,
                'LOG_TABLE_NAME': email_lambda._table.table_name,
            }
        )

    # Permissions
        email_lambda.table.grant_read_data(statistics_lambda)
        email_lambda.image_bucket.grant_read(image_lambda)
        email_lambda.image_bucket.grant_read(image_filter_lambda)
        email_lambda.table.grant_read_data(image_filter_lambda)

    # API definition
        api = api_gw.RestApi(self, 'Endpoint', rest_api_name='Statistics API')

        get_statistics_integration = api_gw.LambdaIntegration(statistics_lambda,
                request_templates={"application/json": '{ "statusCode": "200" }'})

        api.root.add_method("GET", get_statistics_integration)   # GET /
        api.root.resource_for_path('image').add_method("GET", api_gw.LambdaIntegration(image_filter_lambda))
        api.root.resource_for_path('image/{id}').add_method("GET", api_gw.LambdaIntegration(image_lambda))

        # Cron event
        run_rule = aws_events.Rule(self, 'CronRule',schedule=aws_events.Schedule.expression("cron(0 7,19 * * ? *)"))
        run_rule.add_target(target=targets.LambdaFunction(email_lambda.handler))
