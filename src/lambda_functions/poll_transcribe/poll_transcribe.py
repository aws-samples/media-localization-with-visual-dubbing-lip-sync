"""
poll_transcribe.py

    Description:
        This lambda polls the transcribe job to see if it's completed.
"""
import boto3

# Transcribe client
transcribe = boto3.client('transcribe')

def lambda_handler(event, context):
    
    print(event)
    
    job_config = event['job_config']    # Job config
    
    print(f"Checking status of {event['transcription_job_name']}")
    response = transcribe.get_transcription_job(TranscriptionJobName=event['transcription_job_name'])
    print(response)

    return {
        "statusCode": 200,
        "transcription_job_name": event['transcription_job_name'],
        "job_status": response['TranscriptionJob']['TranscriptionJobStatus'],
        "job_config": job_config
    }

    
    
