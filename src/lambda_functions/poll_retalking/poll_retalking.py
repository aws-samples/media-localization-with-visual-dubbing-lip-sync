"""
poll_retalking.ppy

    Description:
        This lambda will poll Amazon S3 to see if the files has been generated after the retalking.
"""

import boto3

# Amazon S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):
    
    print(event)
    
    retalking_job = event['retalking_job']      # Retalking job
    job_config = event['job_config']            # Job config
    bucket, key = parse_s3_uri(retalking_job['output_video_s3_uri'])    # Get bucket and key of output object
    
    # Checks if it object exists
    if object_exists(bucket, key):
        print(f"Found {retalking_job['output_video_s3_uri']}")
        return {
            "statusCode": 200,
            "job_status": "COMPLETED",
            "retalking_job": retalking_job,
            "job_config": job_config
        }
    else:
        print(f"The object still does not exist: {retalking_job['output_video_s3_uri']}")
        return {
            "statusCode": 200,
            "job_status": "IN PROGRESS",
            "retalking_job": retalking_job,
            "job_config": job_config
        }

def parse_s3_uri(s3_uri):
    """Parses bucket and key from the S3 uri"""
    parts = s3_uri.split('/', 3)
    bucket = parts[2]
    key = parts[3]
    return bucket, key

def object_exists(bucket, key):
    """Checks if the object exists"""
    try:
        print(f"Checking if object exists: s3://{bucket}/{key}")
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        print(f"Object does not exist: s3://{bucket}/{key}")
        return False
            
           