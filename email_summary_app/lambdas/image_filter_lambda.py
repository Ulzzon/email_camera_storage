import json
import os
import boto3
import base64

s3 = boto3.client('s3')
database = boto3.client('dynamodb')


def handler(event, context):
    try:
        start_filter = event['queryStringParameters']['start']
        end_filter = event['queryStringParameters']['end']
    except KeyError:
        return {
        'statusCode': 400,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': 'Bad request, missing parameter'
    }
    print('Image request received')
    encoded_images = ImageHandler().get_images_in_range(start_filter, end_filter)

    if encoded_images:        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps(encoded_images),
            'isBase64Encoded': True,
        }
    else:
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'text/plain',
            },
            'body': 'Image not found',
        }


class ImageHandler():
    def __init__(self):
        super().__init__()
        self.bucket_name = os.environ['S3_BUCKET_NAME']
        self.table_name = os.environ['LOG_TABLE_NAME']
    
    def get_images_in_range(self, start_filter, end_filter):
        list_of_image_info = self._get_list_of_all_images(start_filter, end_filter)
        image_data = {}
        for image in list_of_image_info:
            image_key = image['image_array']['S']   # S indicates the variable typ as key in response from DB
            image_id = image['timestamp']['S']
            image = self._get_image_from_s3(image_key)
            encoded_image = base64.b64encode(image)
            image_data[image_id] = encoded_image.decode('utf-8')
        return image_data

    def _get_image_from_s3(self, image_key):
        response = s3.get_object(Bucket= self.bucket_name, Key=image_key)
        print(response)
        return response['Body'].read()

    def _get_list_of_all_images(self, start_filter, end_filter):
        # Use the DynamoDB client query method to get songs by artist Arturus Ardvarkian
        # that have a song attribute value BETWEEN 'D' and 'Bz'
        response = database.scan(
            TableName=self.table_name,
            FilterExpression='#timestamp BETWEEN :start AND :end',
            ExpressionAttributeNames={'#timestamp': 'timestamp' },
            ExpressionAttributeValues={
                ':start': {'S': start_filter},
                ':end': {'S': end_filter}
            }
        )
        print(response['Items'])
        return response['Items']
