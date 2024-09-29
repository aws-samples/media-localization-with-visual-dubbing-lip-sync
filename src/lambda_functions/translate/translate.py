"""translate.py

    Description:
        This lambda function will translate the transcript from Transcribe to the target language.
"""
import json

import requests
import boto3

# Clients
translate = boto3.client('translate')
transcribe = boto3.client('transcribe')

def lambda_handler(event, context):
    
    print(event)
    
    job_config = event['job_config']                            # Job config
    transcription_job_name = event['transcription_job_name']    # Transcribe job name
    
    # Retrieve transcript
    print(f"Retrieving transcript from Transcribe job: {transcription_job_name}")
    response = transcribe.get_transcription_job(TranscriptionJobName=transcription_job_name)
    transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
    result = json.loads(requests.get(transcript_uri).content)
    transcript = result['results']['transcripts'][0]['transcript']
    
    print(f"Received transcript: {transcript}")
    
    # Split text by sentence to translate and recombine
    print("Splitting transcript into segments for translation...")
    transcript_segments = transcript.split('.')

    translated_segments = []
    for segment in transcript_segments:
        if segment != '' and segment is not None:
            response = translate.translate_text(Text=segment + ".",
                                                SourceLanguageCode=job_config['translate_source_language_code'],
                                                TargetLanguageCode=job_config['translate_target_language_code'])
            translated_segments.append(response['TranslatedText'])
    
    print(f"Translated segments: {translated_segments}")
    
    # Return success here
    if len(translated_segments) > 0:
        print("Translation successful.")
        return {
            "statusCode": 200,
            "source_task": "translate",
            "translated_segments": translated_segments,
            "job_config": job_config
        }
    
    # Return error here
    print("Translation failed.")
    return {
        "statusCode": 400,
        "source_task": "translate",
        "error": "Translation failed: No segments were translated.",
        "job_config": job_config
    }