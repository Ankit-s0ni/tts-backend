"""Create required DynamoDB tables for local testing using credentials in .env.
This mirrors the tables created by app.dynamo._ensure_tables().
"""
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(HERE, '.env'))

def main():
    region = os.getenv('DYNAMODB_REGION') or os.getenv('AWS_REGION') or 'us-west-2'
    endpoint = os.getenv('DYNAMODB_ENDPOINT_URL')
    kwargs = {'region_name': region}
    if endpoint:
        kwargs['endpoint_url'] = endpoint
        kwargs['aws_access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID', 'fake')
        kwargs['aws_secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY', 'fake')

    dynamo = boto3.resource('dynamodb', **kwargs)

    def create_table_safe(TableName, KeySchema, AttributeDefinitions):
        try:
            print('Creating table', TableName)
            dynamo.create_table(TableName=TableName, KeySchema=KeySchema, AttributeDefinitions=AttributeDefinitions, BillingMode='PAY_PER_REQUEST')
            print('Created', TableName)
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') in ('ResourceInUseException', 'TableAlreadyExistsException'):
                print('Table exists:', TableName)
            else:
                print('Error creating table', TableName, e)

    create_table_safe('counters', [{'AttributeName':'name','KeyType':'HASH'}], [{'AttributeName':'name','AttributeType':'S'}])
    create_table_safe('jobs', [{'AttributeName':'id','KeyType':'HASH'}], [{'AttributeName':'id','AttributeType':'N'}])
    create_table_safe('voices', [{'AttributeName':'id','KeyType':'HASH'}], [{'AttributeName':'id','AttributeType':'S'}])
    create_table_safe('chunks', [{'AttributeName':'job_id','KeyType':'HASH'},{'AttributeName':'idx','KeyType':'RANGE'}], [{'AttributeName':'job_id','AttributeType':'N'},{'AttributeName':'idx','AttributeType':'N'}])
    create_table_safe('users', [{'AttributeName':'user_id','KeyType':'HASH'}], [{'AttributeName':'user_id','AttributeType':'S'}])

if __name__ == '__main__':
    main()
