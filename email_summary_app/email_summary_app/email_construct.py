from aws_cdk import (
    aws_lambda as _lambda,
    aws_dynamodb as ddb,
    core,
    aws_s3,
)
from aws_cdk.core import Duration, RemovalPolicy
from aws_cdk.aws_s3 import BlockPublicAccess

class EmailConstruct(core.Construct):

    @property
    def table(self):
        return self._table

    @property
    def image_bucket(self):
        return self._image_bucket

    @property
    def handler(self):
        return self._handler

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self._table = ddb.Table( self,
            'Log',
            partition_key={'name': 'mail_id', 'type': ddb.AttributeType.STRING},
        )

        self._image_bucket = aws_s3.Bucket(self,
            'ImageBucket',
            block_public_access=BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            )

        self._handler = _lambda.Function(self,
            'MainHandler',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset('lambdas'),
            handler= 'main_lambda.handler',
            memory_size= 128,
            timeout=Duration.seconds(60),
            environment={
                'LOG_TABLE_NAME': self._table.table_name,
                'S3_BUCKET_NAME': self._image_bucket.bucket_name,
            },
            )

        self.image_bucket.grant_read_write(self._handler)
        self._table.grant_read_write_data(self.handler)
