"""
poll_tts.ppy

    Description:
        This lambda will poll Amazon S3 to see if the files has been generated after the TTS.
"""

import boto3

# S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):
    
    print(event)
    
    tts_jobs = event['tts_jobs']    # TTS audio segment jobs
    num_jobs = len(tts_jobs)
    completed_jobs = set()

    # Checks each job
    for index, tts_job in enumerate(tts_jobs):
        
        # If it's already completed, check the next one
        if index in completed_jobs:
            continue

        destination_s3_uri = tts_job['destination_s3_uri']
        bucket, key = parse_s3_uri(destination_s3_uri)

        # If completed, add to the set
        if object_exists(bucket, key):
            completed_jobs.add(index)
            print(f"Completed {len(completed_jobs)} out of {num_jobs}")
        else:
            print(f"Job {index+1} not completed.")
            
    # Returns completed when all jobs are done otherwise returns in progress
    if len(completed_jobs) >= num_jobs:
        print("All jobs completed")
        return {
            "statusCode": 200,
            "job_status": "COMPLETED",
            "tts_jobs": event['tts_jobs'],
            "job_config": event['job_config']
        }
    else:
        return {
            "statusCode": 200,
            "job_status": "IN_PROGRESS",
            "tts_jobs": event['tts_jobs'],
            "job_config": event['job_config']
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
            
           