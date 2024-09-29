
import os
import logging
import json
import tempfile
import subprocess
import boto3

logger = logging.getLogger(__name__)

class DefaultPytorchInferenceHandler(object):
    def default_model_fn(self, model_dir):
        """
        Placeholder, does nothing
        """
        
        logger.info('Loading models')
        logger.info('Current working directory %s', os.getcwd())
        logger.info('Checkpoints found %s', os.listdir('/opt/ml/model/code/checkpoints'))
        
        return None

    def default_predict_fn(self, input_data, model):
        
        logger.info('Starting prediction')
        s3 = boto3.client('s3')
        
        with tempfile.TemporaryDirectory() as tmpDir:
        
            logger.info('Creating temporary dir %s', tmpDir)    
        
            # Input Video
            input_video_bucket = self.get_bucket(input_data['input_video_s3_uri'])
            input_video_key = self.get_key(input_data['input_video_s3_uri'])
            input_video_filename = self.get_object_name(input_data['input_video_s3_uri'])
            
            input_video_filepath = os.path.join(tmpDir, input_video_filename)
            
            logger.info('Downloading input video from s3://%s/%s to %s', input_video_bucket, 
                        input_video_key, input_video_filepath)
            
            s3.download_file(input_video_bucket, input_video_key, input_video_filepath)
            logger.info("Downloaded input video.")
            
            # Input Audio
            input_audio_bucket = self.get_bucket(input_data['input_audio_s3_uri'])
            input_audio_key = self.get_key(input_data['input_audio_s3_uri'])
            input_audio_filename = self.get_object_name(input_data['input_audio_s3_uri'])
            input_audio_filepath =  os.path.join(tmpDir, input_audio_filename)
            
            logger.info('Downloading input audio from s3://%s/%s to %s', input_audio_bucket,
                        input_audio_key, input_audio_filepath)
            
            s3.download_file(input_audio_bucket, input_audio_key, input_audio_filepath)
            logger.info("Downloaded input audio")
            
            # Output video
            output_video_bucket = self.get_bucket(input_data['output_video_s3_uri'])
            output_video_key =  self.get_key(input_data['output_video_s3_uri'])
            output_video_filename = self.get_object_name(input_data['output_video_s3_uri'])
            output_video_filepath = os.path.join(tmpDir, output_video_filename)
            
            logger.info("Starting inference")
            command = ["python", "inference_retalking.py", 
                    "--face", input_video_filepath , 
                    "--audio", input_audio_filepath, 
                    "--outfile", output_video_filepath,
                    "--tmp_dir", tmpDir
            ] 
            logger.info('Running command: %s', command)
            result = subprocess.run(command, capture_output=True, cwd="/opt/ml/model/code")
            logger.info("Inference complete")
            
            print(result)
            
            # Check if output file exists
            if not os.path.exists(output_video_filepath) or result.returncode != 0:
                logging.error("Output video file not found or inference failed: %s", output_video_filepath)
                raise ValueError(f"Output video file not found: {output_video_filepath}")
            
            # Upload file
            logger.info('Uploading output video from %s to s3://%s/%s', output_video_filepath,
                        output_video_bucket, output_video_key)
            s3.upload_file(output_video_filepath, output_video_bucket, output_video_key)
            logger.info("Successfully uploaded output video")
            
        return {
            "output_video_s3_uri": f"s3://{output_video_bucket}/{output_video_key}"
        }

        
    def default_input_fn(self, request_body, request_content_type):
        """
        Deserializes the input request body and prepares data for retalking
        
        Args:
            request_body (str): A JSON string containing the following fields:
                
                input_video_s3_uri (str): The S3 URI of the input video
                input_audio_s3_uri (str): The S3 URI of the input audio to lip sync with
                output_video_s3_uri (str): The S3 URI of where the new video will be outputted to
                
            
            request_content_type (str): The request content type

        Returns:
            dict: The request body deserialized as a dictionary
        """
        
        logger.info('Received input: %s', request_body)
        if request_content_type == "application/json":
            try:
                request = json.loads(request_body)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in requset body")
        else:
            raise ValueError("Unsupported content type: {}".format(request_content_type))
        
        logger.info('Processing input')
        # Extract and validate required fields
        required_fields = ["input_video_s3_uri", "input_audio_s3_uri", "output_video_s3_uri"]
        missing_fields = [field for field in required_fields if field not in request]
        if missing_fields:
            logger.error("Missing required fields: %s", ", ".join(missing_fields))
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        logger.info('Input processing completed.')
        return {
            "input_video_s3_uri": request["input_video_s3_uri"],
            "input_audio_s3_uri": request["input_audio_s3_uri"],
            "output_video_s3_uri": request["output_video_s3_uri"],
            "inference_params": request.get("inference_params", {}),
        }

    def default_output_fn(self, response_body, response_content_type):

        """
        Serialize and prepare the prediction output
        """

        logger.info('Returning response')
        return {
            "statusCode": 200,
            "output_video_s3_uri": response_body['output_video_s3_uri']
        }

    def get_bucket(self, uri):
        """
        Takes an S3 URI and returns the bucket name
        """
        parts = uri.split('//')[1].split('/')
        return parts[0]


    def get_key(self, uri):
        """
        Takes an S3 URI and returns the key name
        """
        parts = uri.split('//')[1].split('/')
        return '/'.join(parts[1:])

    def get_object_name(self, uri):
        """
        Takes an S3 URI and returns the object name
        """
        return uri.split('/')[-1]
    
    def delete_dir_contents(self, path):
        """
        Recursively delete all contents under a path
        """
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                self.delete_dir_contents(full_path)
        