from flask import jsonify
import random
import string
import boto3
import requests


def get_aws_region():
    try:
        # Fetch the token
        token_response = requests.put(
            'http://169.254.169.254/latest/api/token',
            headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}
        )
        token_response.raise_for_status()
        token = token_response.text

        # Use the token to fetch the region
        response = requests.get(
            'http://169.254.169.254/latest/dynamic/instance-identity/document',
            headers={'X-aws-ec2-metadata-token': token}
        )
        response.raise_for_status()
        return response.json()['region']
    except requests.RequestException as e:
        print(f"Error fetching AWS region: {e}")
        return None

current_region = get_aws_region()
print(f"AWS_REGION={current_region}")
dynamodb = boto3.resource('dynamodb', current_region)
table_name = None


def get_table_name():
    global table_name
    if table_name is not None:
        return table_name
    # Create a CloudFormation client
    cloudformation = boto3.client('cloudformation', region_name=current_region)

    try:
        # Describe the stack to get the output values
        response = cloudformation.describe_stacks(StackName='GravitonID-ec2')
        stacks = response['Stacks']
        if stacks:
            stack = stacks[0]
            outputs = stack['Outputs']
            for output in outputs:
                if output['OutputKey'] == 'EC2ModuleDynamoDBTable':
                    table_name = output['OutputValue']
                    return table_name
        return None
    except Exception as e:
        return str(e)


def retrive_from_dynamo(short_url):
    dynamodb = boto3.resource('dynamodb', current_region)
    table_name = get_table_name()
    table = dynamodb.Table(table_name)

    try: 
        # Get item from the table
        response = table.get_item(
            Key={
                'short_url': short_url
            }
        )
        print('retrive_from_dynamo')
        return response['Item']
    except Exception as e:
        return str(e)


# create a function to shortening url
def create_short_url(url):
    try:
        # create a random string of length 10
        letters = string.ascii_lowercase
        short_url = ''.join(random.choice(letters) for i in range(10))
        save_in_dynamo(short_url, url)
        # append the random string generated to the url
        return jsonify({'shortURL':short_url, 'originalURL':url}) 
    except Exception as e:
        return str(e)
    

def save_in_dynamo(short_url, original_url):
    try:
        table_name = get_table_name()
        table = dynamodb.Table(table_name)
        # Put item in the table
        response = table.put_item(
            Item={
                'short_url': short_url,
                'url': original_url
            }
        )
        print('save_in_dynamo')
    except Exception as e:
        return str(e)

    return response
