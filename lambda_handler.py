from __future__ import print_function
import os
import io
import boto3
import json
import csv
import urllib
import re


#0v1#  JC Sept 14, 2018


# grab environment variables
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
runtime= boto3.client('runtime.sagemaker')

test_vector_for_lambda="""
    {
      "Records": [
        {
          "eventVersion": "2.0",
          "eventTime": "1970-01-01T00:00:00.000Z",
          "requestParameters": {
            "sourceIPAddress": "127.0.0.1"
          },
          "s3": {
            "configurationId": "testConfigRule",
            "object": {
              "eTag": "0123456789abcdef0123456789abcdef",
              "sequencer": "0A1B2C3D4E5F678901",
              "key": "sagemaker/small_pot.mp4",
              "size": 1024
            },
            "bucket": {
              "arn": "arn:aws:s3:::mybucket",
              "name": "tests-road-damange",
              "ownerIdentity": {
                "principalId": "EXAMPLE"
              }
            },
            "s3SchemaVersion": "1.0"
          },
          "responseElements": {
            "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH",
            "x-amz-request-id": "EXAMPLE123456789"
          },
          "awsRegion": "us-east-1",
          "eventName": "ObjectCreated:Put",
          "userIdentity": {
            "principalId": "EXAMPLE"
          },
          "eventSource": "aws:s3"
        }
      ]
    }
    """

#https://aws.amazon.com/blogs/machine-learning/call-an-amazon-sagemaker-model-endpoint-using-amazon-api-gateway-and-aws-lambda/

#ENDPOINT_NAME is an environment variable that holds the name of the SageMaker model endpoint you just deployed using the sample 
#endpoint name you created, if it is different. 
#The event that invokes the Lambda function is triggered by API Gateway. API Gateway simply passes the test data through an event.   
    
    
def handle_lambda(event,context,called_local=False):
    #**Use above event if running manual test on amazon
    
    #1/  GET S3 file creation event
    #############################################################333
    print("EVENT: "+str(event))
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'])
    print("Using bucket name: "+bucket_name)
    print("Using key: "+key)
    
    if not re.search(r'_output\.',key):
        #2/  Call sagemaker endpoint invocation
        #>  note: will likley timeout by default
        payload={}
        payload['input']={}
        payload['input']['s3_source_filename']=key
        payload['input']['s3_bucket']=bucket_name
        payload['input']['is_live']=False
    
        print("Calling endpoint...")
        response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME, ContentType='application/json', Body=json.dumps(payload))
        print("RESPONSE:")
        print(response)
        #result = json.loads(response['Body'].read().decode())
    else:
        print("New file appears like output: _output -- skipping: "+str(key))
    return "Standard response"
















