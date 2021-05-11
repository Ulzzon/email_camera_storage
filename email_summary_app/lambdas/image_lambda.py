import json
import os
import boto3
import base64

s3 = boto3.client('s3')


def handler(event, context):
    try:
        image_id = event.path.id
#        image_id = event['queryStringParameters']['id']
    except KeyError:
        return {
        'statusCode': 400,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': 'Bad request, missing parameter'
    }
    print('Image request received')
    raw_data = ImageHandler().get_image(image_id)
    image_name = image_id.split('/')[1]

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'image/jpeg',
            'Content-Disposition': 'attachment', 
            'filename': f'{image_name}'
        },
        'body': base64.b64encode(raw_data),
        'isBase64Encoded': True,
    }


class ImageHandler():
    def __init__(self):
        super().__init__()
        self.bucket_name = os.environ['S3_BUCKET_NAME']

    def get_image(self, image_id):
        image_key = f'/images/{image_id}'
        response = s3.get_object(Bucket= self.bucket_name, Key=image_key)
        print(response)
        return response['Body'].read()
