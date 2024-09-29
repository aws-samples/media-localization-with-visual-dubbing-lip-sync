"""
upload_models.py

Description:
    This scripts uploads the TTS and retalking model files to the S3 bucket
    created by the CDK deployments. The model files are then used
    for the SageMaker endpoints.
"""

import boto3
import subprocess

# Create clients
cf_client = boto3.client('cloudformation')
ecr_client = boto3.client('ecr')


# Specify the stack that creates the SageMaker buckets
stack_name = "SageMakerSupportingInfraStack"

# Retrieve the stack
print(f"Retrieving CF stack details: {stack_name}")
response = cf_client.describe_stacks(StackName=stack_name)

# Get the outputs
print("Parsing response")
outputs = response['Stacks'][0]['Outputs']

# Convert the outputs to a dictionary
output_dict = {output['OutputKey']: output['OutputValue'] for output in outputs}
ecr_repo_name = output_dict['ECROutput']
region = output_dict['RegionName']
account_id = output_dict['AccountId']

print(ecr_repo_name)
print(region)
print(account_id)

docker_tag = "retalking:1.0"
destination_tag = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{ecr_repo_name}:latest"

# Authenticate 

print(f"Uploading retalking image to {ecr_repo_name}")
try:
    # Get ECR login password
    ecr_login_cmd = ["aws", "ecr", "get-login-password", "--region", region]
    ecr_password_result = subprocess.run(ecr_login_cmd, capture_output=True, text=True, check=True)
    ecr_password = ecr_password_result.stdout.strip()

    # Docker login
    docker_login_cmd = ["docker", "login", "--username", "AWS", "--password-stdin", f"{account_id}.dkr.ecr.{region}.amazonaws.com"]
    subprocess.run(docker_login_cmd, input=ecr_password, capture_output=True, text=True, check=True)

    # Docker tag
    docker_tag_cmd = ["docker", "tag", docker_tag, destination_tag]
    subprocess.run(docker_tag_cmd, capture_output=True, text=True, check=True)

    # Docker push
    docker_push_cmd = ["docker", "push", destination_tag]
    result = subprocess.run(docker_push_cmd, capture_output=True, text=True, check=True)

    print("All commands executed successfully.")
    print("Output:", result.stdout)

except subprocess.CalledProcessError as e:
    print(f"An error occurred: {e}")
    print(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
    print(f"Stdout: {e.stdout}")
    print(f"Stderr: {e.stderr}")

if result.returncode == 1:
    raise Exception(f"Failed to upload docker image. Error: {result.stderr}")

else:
    print("Successfully uploaded docker image")