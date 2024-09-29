import os
import random
import string
from aws_cdk import (
    Stack,
    Fn,
    aws_sagemaker as sagemaker,
    CfnOutput
)

from constructs import Construct

from sagemaker import image_uris

class SageMakerEndpointsStack(Stack):
    """
    Deploys the SageMaker TTS and Retalking Async endpoints
    """
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)    
        
        self.sm_bucket_name = Fn.import_value("SMBucketName")
        self.sm_role_arn = Fn.import_value("SMRole")
        self.tts_model_asset_key = "tts/model/model-tts.tar.gz"
        self.retalking_model_asset_key = "retalking/model/model-retalking.tar.gz"
        self.retalking_repo_uri = Fn.import_value("ECRUri")
        
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        
        # TTS endpoint setup
        # Retrieve the SageMaker container for inference
        image_uri = image_uris.retrieve(
            framework="pytorch",
            version="2.1",
            py_version="py310",
            instance_type="ml.g5.xlarge",
            region=os.environ.get("CDK_DEFAULT_REGION"),
            image_scope="inference"
        )
        
        # TTS endpoint
        self.tts_model = sagemaker.CfnModel(
            self, "TTSModel",
            execution_role_arn=self.sm_role_arn,
            primary_container=sagemaker.CfnModel.ContainerDefinitionProperty(
                image=image_uri,
                model_data_url=f"s3://{self.sm_bucket_name}/{self.tts_model_asset_key}",
                environment={
                    "SAGEMAKER_PROGRAM": "inference.py",
                    "SAGEMAKER_TS_RESPONSE_TIMEOUT": "900",
                    "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code"
                }
            )
        )
        
        self.tts_async_output_location = f"s3://{self.sm_bucket_name}/tts-async-endpoint-outputs"
        
        self.tts_endpoint_config = sagemaker.CfnEndpointConfig(
            self, "TTSEndpointConfig",
            async_inference_config=sagemaker.CfnEndpointConfig.AsyncInferenceConfigProperty(
                output_config=sagemaker.CfnEndpointConfig.AsyncInferenceOutputConfigProperty(
                    s3_output_path=self.tts_async_output_location
                )         
            ),
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    model_name=self.tts_model.attr_model_name,
                    instance_type="ml.g5.xlarge",
                    initial_instance_count=1,
                    variant_name="TTS"
                )
            ]   
        )
        
        self.tts_endpoint = sagemaker.CfnEndpoint(
            self, "TTSEndpoint",
            endpoint_config_name=self.tts_endpoint_config.attr_endpoint_config_name,
            endpoint_name=f"tortoise-tts-sm-async-{random_suffix}"
        )
        
        self.tts_endpoint_output = CfnOutput(self, "SageMakerTTSEndpointOutput",
            value=self.tts_endpoint.attr_endpoint_name,
            description="The TTS endpoint name",
            export_name="TTSEndpointName"
        )
        
        self.tts_async_output = CfnOutput(self, "SageMakerTTSEndpointAsyncOutputLocation",
            value=self.tts_async_output_location,
            description="The output location of the async endpoint",
            export_name="TTSAsyncOutputLocation"
        )
        
        # Retalking endpoint
        self.retalking_model = sagemaker.CfnModel(
            self, "RetalkingModel",
            execution_role_arn=self.sm_role_arn,
            primary_container=sagemaker.CfnModel.ContainerDefinitionProperty(
                image=f"{self.retalking_repo_uri}:latest",
                model_data_url=f"s3://{self.sm_bucket_name}/{self.retalking_model_asset_key}",
                environment={'SAGEMAKER_TS_RESPONSE_TIMEOUT': '900', 
                     "TS_DEFAULT_RESPONSE_TIMEOUT": "1000",
                    "MMS_DEFAULT_RESPONSE_TIMEOUT": "900"
                }
            )
        )
        
        self.retalking_async_output_location = f"s3://{self.sm_bucket_name}/tts-async-endpoint-outputs"
        
        self.retalking_endpoint_config = sagemaker.CfnEndpointConfig(
            self, "RetalkingEndpointConfig",
            async_inference_config=sagemaker.CfnEndpointConfig.AsyncInferenceConfigProperty(
                output_config=sagemaker.CfnEndpointConfig.AsyncInferenceOutputConfigProperty(
                    s3_output_path=self.retalking_async_output_location
                )         
            ),
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    model_name=self.retalking_model.attr_model_name,
                    instance_type="ml.g5.xlarge",
                    initial_instance_count=1,
                    variant_name="Retalking"
                )
            ]   
        )
        
        self.retalking_endpoint = sagemaker.CfnEndpoint(
            self, "RetalkingEndpoint",
            endpoint_config_name=self.retalking_endpoint_config.attr_endpoint_config_name,
            endpoint_name=f"retalking-sm-async-{random_suffix}"
        )
        
        self.retalking_endpoint_output = CfnOutput(self, "SageMakerRetalkingEndpointOutput",
            value=self.retalking_endpoint.attr_endpoint_name,
            description="The retalking endpoint name",
            export_name="RetalkingEndpointName"
        )
        
        self.retalking_async_output = CfnOutput(self, "SageMakerRetalkingEndpointAsyncOutputLocation",
            value=self.tts_async_output_location,
            description="The output location of the async endpoint",
            export_name="RetalkingAsyncOutputLocation"
        )

        
        