import json
import os
import boto3
import datetime

database = boto3.resource('dynamodb')


def handler(event, context):

    print('Statistics request received')
    raw_data = StatisticsHandler().get_raw_data()

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(raw_data)
    }


class StatisticsHandler():
    def __init__(self):
        super().__init__()
        self.table = database.Table(os.environ['LOG_TABLE_NAME'])
    
    def get_raw_data(self):
        response = self.table.scan(
            ProjectionExpression='#t, image_array',
            ExpressionAttributeNames={
                '#t': 'timestamp',
            },
        )
        return response['Items']