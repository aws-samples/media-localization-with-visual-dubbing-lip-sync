"""invoke_tts.ppy

    Description:
        This lambda will take the translated segments, create tts jobs,
        upload the TTS jobs to S3, and then invoke the SageMaker Async endpoint.
"""
import json
import boto3

# Clients
s3 = boto3.resource('s3')
sagemaker = boto3.client('sagemaker-runtime')

def lambda_handler(event, context):
    # There will be two messages in the event: one from translate and one from voice samples
    print(event)
    
    # Get Parameters
    for message in event:
        if message['source_task'] == "translate":
            translated_segments = message['translated_segments']
        if message['source_task'] == "voice_samples":
            voice_samples_s3_uri = message['voice_samples_uri']
    
    job_config = event[0]['job_config']             # Job config
    bucket = job_config['bucket']                   # Bucket
    prefix_inputs = job_config['prefix_inputs']     # Inputs
    prefix_outputs = job_config['prefix_outputs']   # Outputs
    job_name = job_config['job_name']               # Job Name
    tts_model_id = job_config['tts_model_id']       # Not currently used, reserved for future use
    tts_endpoint_name = job_config['tts_endpoint_name'] # TTS endpoint name
    
    # Prepare payloads
    print("Preparing TTS job payloads")
    tts_jobs = []
    for translated_sentence,i in zip(translated_segments, range(len(translated_segments))):    
        tts_job = {"id": i,
                "text": translated_sentence, 
                    "voice_samples_s3_uri": voice_samples_s3_uri,
                    "input_s3_uri": f"s3://{bucket}/{prefix_inputs}/{job_name}/tts_jobs/{job_name}-part-{i}.json",
                    "destination_s3_uri": f"s3://{bucket}/{prefix_outputs}/{job_name}/tts/{i}.wav", 
                    "model_id": tts_model_id, 
                    "inference_params": {}}
        tts_jobs.append(tts_job)
    
    
    # Upload payloads to S3
    for tts_job in tts_jobs:
        # Upload the payloads
        print(f"Uploading {tts_job['input_s3_uri']}")
        key = "/".join(tts_job['input_s3_uri'].split("/")[3:])
        s3_object = s3.Object(bucket, key)
        s3_object.put(Body=json.dumps(tts_job).encode('utf-8'))

        # Invoke SageMaker async endpoint
        print(f"Invoking {tts_endpoint_name} with {tts_job['input_s3_uri']}")
        response = sagemaker.invoke_endpoint_async(
            EndpointName=tts_endpoint_name,
            ContentType='application/json',
            InputLocation=tts_job['input_s3_uri'],
            InvocationTimeoutSeconds=3600
        )
        
        print(response)
        
    return {
        "statusCode": 200,
        "tts_jobs": tts_jobs,
        "job_config": job_config
    }