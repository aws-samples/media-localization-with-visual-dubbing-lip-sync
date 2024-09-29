"""
voice_sample.py

    Description:
        Extracts voice samples using the uploaded video file and Transcribe Job results.
"""
import os
import json
from tempfile import TemporaryDirectory

import boto3
import requests

from pydub import AudioSegment

# Clients
s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')

def lambda_handler(event, context):
    
    print(event)
    
    # Get job_config
    job_config = event['job_config']    # Job config
    
    # Get results of the transcribe job
    transcribe_job_name = event['transcription_job_name']   # Transcribe job name
    
    print(f"Retrieving transcription job: {transcribe_job_name}")
    response = transcribe.get_transcription_job(TranscriptionJobName=transcribe_job_name)
    transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
    result = json.loads(requests.get(transcript_uri).content)
    print(f"Successfully retrieved transcribe results: {result}")
    
    # Retrieve the .mp4 file
    
    source_file_s3_uri = job_config['source_file_s3_uri']
    
    print(f"Retrieving source video file: {source_file_s3_uri}")
    bucket = source_file_s3_uri.split('/')[2]
    key = "/".join(source_file_s3_uri.split('/')[3:])
    filename = key.split('/')[-1]
    
    # Creates a local temporary directory
    with TemporaryDirectory() as tmpdir:
        
        print(f"Downloading {filename} to {tmpdir}/{filename}")
        # Download the .mp4 file to a temporary directory
        s3.download_file(bucket, key, f'{tmpdir}/{filename}')
        print(f"Downloaded {filename} to {tmpdir}/{filename}")
        
        # Load audio from .mp4
        print(f"Loading audio from {tmpdir}/{filename}")
        source_audio = AudioSegment.from_file(f'{tmpdir}/{filename}')
        print(f"Loaded audio from {tmpdir}/{filename}")
        
        print("Extracting voice samples")
        # Build sentence splits
        sentences = []

        current_sentence = ""
        sentence_start_time = None
        sentence_end_time = None

        for item in result['results']['items']:
            
            # Punctuations don't have start and end_times
            if item['type'] != 'punctuation':
                
                #Set the start_time if it's a new sentence
                if sentence_start_time is None:
                    sentence_start_time = item['start_time']
                
                #Update the end time until the final word before a period    
                sentence_end_time = item['end_time']
                
            # Concatenate the current word to the current sentence
            
            if item['type'] != 'punctuation':
                current_sentence = current_sentence + ' ' + item['alternatives'][0]['content']
            
            if item['type'] == 'punctuation':
                current_sentence = current_sentence + item['alternatives'][0]['content'] + ' '
            
            if item['type'] == 'punctuation' and item['alternatives'][0]['content'] == '.':        
                sentences.append({
                    "sentence": current_sentence.strip(),
                    "sentence_start_time": float(sentence_start_time),
                    "sentence_end_time": float(sentence_end_time),
                    "sentence_duration": float(sentence_end_time) - float(sentence_start_time)
                })
                
                current_sentence = ""
                sentence_start_time = None
                sentence_end_time = None
                
        # Select segments that are >2 and <= 10 seconds in length
        selected_sentences = []
        for sentence in sentences:
            if sentence['sentence_duration'] > 2 and sentence['sentence_duration'] <= 10:
                selected_sentences.append(sentence)
                
        print(f"Selected {len(selected_sentences)} voice samples")
        print(selected_sentences)
        
        # Fail this step if no voice samples are found
        if len(selected_sentences) == 0:
            print("No voice samples found. There must be at least one utterance >2 and <=10 seconds long")
            
            return {
                "statusCode": 400,
                "source_task": "transcribe",
                "error": "Voice sample extraction failed. No suitable voice samples found.",
                "job_config": job_config
            }
        
        # Build voice samples
        print("Creating voice samples")
        voice_samples_dir = os.path.join(tmpdir, "voice_samples")
        os.makedirs(voice_samples_dir)

        # Split and save audio
        i = 0
        for sentence in selected_sentences:
            start_time_ms = sentence['sentence_start_time'] * 1000
            end_time_ms = sentence['sentence_end_time'] * 1000
            
            segment = source_audio[start_time_ms:end_time_ms]
            print("Exporting segment", i, "to", f"{voice_samples_dir}/{i}.wav")
            segment.export(f"{voice_samples_dir}/{i}.wav", format="wav")
            i+=1
            
        # Upload voice samples to S3
        # Sample URI: s3://bucket/inputs/job_name/voice_samples
        print("Uploading voice samples to S3")
        bucket = job_config['bucket']
        prefix_voice_samples = job_config['prefix_inputs'] + "/" \
                             + job_config['job_name'] + "/" \
                             + "voice_samples"
        
        for root, _, files in os.walk(voice_samples_dir):
            for file in files:
                full_path = os.path.join(root, file)
                key =  prefix_voice_samples + "/" + file
                print(f"Uploading {full_path} to s3://{bucket}/{key}")
                s3.upload_file(full_path, bucket,key)
                print(f"Uploaded {full_path} to s3://{bucket}/{key}")
                
        print("Completed voice samples extraction")

    return {
        "statusCode": 200,
        "source_task": "voice_samples",
        "voice_samples_uri": f"s3://{bucket}/{prefix_voice_samples}",
        "job_config": job_config
    }