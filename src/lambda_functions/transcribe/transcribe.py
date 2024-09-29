"""
transcribe_lambda.py

Description:
    This lambda will start an Amazon Transcribe job given a JSON job object.
"""

import boto3
import json
import time

# Clients
s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')

def lambda_handler(event, context):
    
    print(event)

    # Parse an event bridge notification to get the JSON job object from S3
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']
    
    # Download the JSON job object
    response = s3.get_object(Bucket=bucket, Key=key)
    job_config = json.loads(response['Body'].read())
    
    print(job_config)
    # Create a transcription job name based of the source file name from the S3URI with a timestamp and -job suffix
    job_name = job_config['source_file_s3_uri'].split('/')[-1].split('.')[0] + '-' + str(int(time.time())) + '-job'
    
    # Start an Amazon Transcribe Job 
    print(f"Starting Transcribe job: {job_name}")
    transcribe_job = transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_config['source_file_s3_uri']},
        MediaFormat=job_config['media_format'],
        LanguageCode=job_config['transcribe_source_language_code']
    )
    
    print(transcribe_job)
    # Return the transcribe job name
    return {
        "statusCode": 200,
        "transcription_job_name": transcribe_job['TranscriptionJob']['TranscriptionJobName'],
        "job_config": job_config
    }