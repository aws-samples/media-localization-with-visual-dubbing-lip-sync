"""
invoke_retalking.py

    Description:
        This Lambda will invoke the SageMaker Retalking endpoint using the original
        video and the new translated audio.
"""
import os
import json
import tempfile 
import subprocess

import boto3
from pydub import AudioSegment

# Clients
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
sagemaker = boto3.client('sagemaker-runtime')

def lambda_handler(event, context):
    
    print(event)
    
    tts_jobs = event['tts_jobs']                                # One or more TTS audio segments
    job_config = event['job_config']                            # Job config
    job_name = job_config['job_name']                           # Job name
    bucket = job_config['bucket']                               # Bucket name
    prefix_inputs = job_config['prefix_inputs']                 # Input prefix
    
    # Filename to join the TTS audio segments
    final_output_filename = job_config['job_name'] + '.wav'
    src_bucket, src_key = parse_s3_uri(job_config['source_file_s3_uri'])
    
    # Create a local temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        
        # Audio segment to join the TTS audio segments to
        final_output_audio = AudioSegment.empty()
        
        for tts_job in tts_jobs:
            # Download the TTS audio segment
            print(f"Downloading {tts_job['destination_s3_uri']}")
            bucket, key = parse_s3_uri(tts_job['destination_s3_uri'])
            
            local_filepath = os.path.join(tmpdir, key.split("/")[-1])
            s3.download_file(bucket, key, local_filepath)
            print(f"Successfully downloaded {local_filepath}")
            
            # Concatenate the audio segment
            print(f"Concatenating {local_filepath} to {final_output_filename}")
            final_output_audio += AudioSegment.from_wav(local_filepath)
            print(f"Successfully concatenated {local_filepath} to {final_output_filename}")
        
        # Export to file
        final_output_filepath = os.path.join(tmpdir, final_output_filename)
        print(f"Creating final audio {final_output_filepath}")
        final_output_audio.export(final_output_filepath, format="wav")
        print(f"Successfully created {final_output_filepath}")
        
        ## Tempo adjustment
        print("Adjusting tempo to match original video length")
        
        # Download the original .mp4 
        print(f"Downloading original video: {job_config['source_file_s3_uri']}")
        src_local_filepath = os.path.join(tmpdir, src_key.split("/")[-1])
        s3.download_file(src_bucket, src_key, src_local_filepath)
        print(f"Successfully downloaded {src_local_filepath}")
        
        # Calculate tempo adjustment
        print("Calculating tempo adjustment ratio")
        src_audio_segment = AudioSegment.from_file(src_local_filepath)
        src_duration = len(src_audio_segment)
        dubbed_duration = len(final_output_audio)
        atempo = dubbed_duration/src_duration
        print(f"Calculated tempo adjustment factor: {atempo}")


        final_output_dubbed_w_tempo_adj_filename = os.path.join(tmpdir, job_config['job_name'] + "-dubbed-tempo.wav")
        print(f"Adjusting tempo, final output: {final_output_dubbed_w_tempo_adj_filename}")
        # Adjust final audio
        subprocess.run([
            'ffmpeg', '-i', final_output_filepath, '-filter:a', f'atempo={atempo}', '-y', final_output_dubbed_w_tempo_adj_filename
        ])
        print(f"Successfully adjusted tempo, final output: {final_output_dubbed_w_tempo_adj_filename}")
                
        # Build the key for the final output_audio
        key = f"{prefix_inputs}/{job_name}/tts_combined/{final_output_dubbed_w_tempo_adj_filename.split("/")[-1]}"
        final_output_audio_s3_uri = f"s3://{bucket}/{key}"
        
        print(f"Uploading adjusted file to s3://{bucket}/{key}")
        # Upload to S3
        s3.upload_file(final_output_dubbed_w_tempo_adj_filename, Bucket=bucket, Key=key)
        print(f"Successfully uploaded adjusted file to s3://{bucket}/{key}")
        
        # Prepare payloads for retalking async
        print("Preparing retalking job payload")
        retalking_job_key = f"{prefix_inputs}/{job_name}/retalking_jobs/{job_name}.json"
        retalking_job_s3_uri = f"s3://{bucket}/{retalking_job_key}"
        
        retalking_job = {
                "input_s3_uri": retalking_job_s3_uri,
                "input_video_s3_uri": job_config['source_file_s3_uri'],
                "input_audio_s3_uri": final_output_audio_s3_uri,
                "output_video_s3_uri": job_config['destination_s3_uri'],
                "inference_params": {},
            }
        
        # Upload the retalking_job json
        print(f"Uploading retalking job {retalking_job_s3_uri}")
        retalking_job_s3_object = s3_resource.Object(bucket, retalking_job_key)
        retalking_job_s3_object.put(Body=json.dumps(retalking_job).encode('utf-8'))
        
        # Invoke SageMaker asyncendpoint
        print(f"Invoking {job_config['retalking_endpoint_name']}")
        response = sagemaker.invoke_endpoint_async(
            EndpointName=job_config['retalking_endpoint_name'],
            InputLocation=retalking_job_s3_uri,
            ContentType='application/json',
            InvocationTimeoutSeconds=3600
        )
        
        print(response)
        
        return {
            "statusCode": 200,
            "retalking_job": retalking_job,
            "job_config": job_config
        }
        
def parse_s3_uri(s3_uri):
    """Parses bucket and key from the S3 uri"""
    parts = s3_uri.split('/', 3)
    bucket = parts[2]
    key = parts[3]
    return bucket, key
