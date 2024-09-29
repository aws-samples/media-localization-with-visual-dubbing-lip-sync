"""
upload_models.py

Description:
    This scripts uploads the TTS and retalking model files to the S3 bucket
    created by the CDK deployments. The model files are then used
    for the SageMaker endpoints.
"""


import boto3

# Create clients
cf_client = boto3.client('cloudformation')
s3_client = boto3.client('s3')


# Specify the stack that creates the SageMaker buckets
stack_name = "SageMakerSupportingInfraStack"

# Specify the model files to be uploaded
tts_model_file = "tts/archive/model-tts.tar.gz"
tts_model_key = "tts/model/model-tts.tar.gz"

retalking_model_file = "retalking/archive/model-retalking.tar.gz"
retalking_model_key = "retalking/model/model-retalking.tar.gz"

# Retrieve the stack
print(f"Retrieving CF stack details: {stack_name}")
response = cf_client.describe_stacks(StackName=stack_name)

# Get the outputs
print("Parsing response")
outputs = response['Stacks'][0]['Outputs']

# Convert the outputs to a dictionary
output_dict = {output['OutputKey']: output['OutputValue'] for output in outputs}

# Extracts the bucket name
bucket_name = output_dict['SMBucketNameOutput']

# Upload the model files
print(f"Uploading TTS model file - s3://{bucket_name}/{tts_model_key}")
s3_client.upload_file(tts_model_file, bucket_name, tts_model_key)
print(f"Uploading Retalking model file - s3://{bucket_name}/{retalking_model_key}")
s3_client.upload_file(retalking_model_file, bucket_name, retalking_model_key)
