import os
import random
import string
from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_s3 as s3,
    RemovalPolicy,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
    CfnParameter,
    CfnOutput
)
from constructs import Construct

class VisualDubbingLipsyncPipelineStack(Stack):
    """
    Deploys the step functions for the pipeline
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Common Lambda/State Function Role
        self.lambda_role = iam.Role(self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
            inline_policies={
                "TranscribePermissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "transcribe:StartTranscriptionJob",
                                "transcribe:GetTranscriptionJob"
                            ],
                            resources=["*"]
                        )
                    ]
                ),
                "TranslatePermissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "translate:TranslateText"
                            ],
                            resources=["*"]
                        )
                    ]
                ),
                "SageMakerPermissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "sagemaker:InvokeEndpoint"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        
        # Create an S3 Bucket
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        
        bucket_name = CfnParameter(self, "BucketName", type="String", default=f"visual-dubbing-pipeline-{random_suffix}")
        self.s3_bucket = s3.Bucket(self, id="MainBucket",
                              bucket_name=bucket_name.value_as_string,
                              removal_policy=RemovalPolicy.DESTROY,
                              auto_delete_objects=True,
                              event_bridge_enabled=True)
        
        
        self.s3_bucket.grant_read_write(self.lambda_role)

        self.s3_bucket_output= CfnOutput(
            self, "VDBucketOutput",
            value=self.s3_bucket.bucket_name,
            description="Visual Dubbing S3 Bucket",
            export_name="VDS3BucketName"
        )

        # FFMPEG Layer
        self.ffmpeg_layer = lambda_.LayerVersion(self, "FFMPEGLayer",
            code=lambda_.Code.from_asset("layers/ffmpeg"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
            description="FFMPEG Layer"
        )
        
        # Requests Layer
        self.requests_layer = lambda_.LayerVersion(self, "RequestsLayer",
            code=lambda_.Code.from_asset("layers/requests"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
            description="Requests Layer"
        )
        
        # Pydub layer
        self.pydub_layer = lambda_.LayerVersion(self, "PydubLayer",
            code=lambda_.Code.from_asset("layers/pydub"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
            description="Pydub Layer"
        )

        # Transcribe Lambda function
        self.transcribe_lambda = lambda_.Function(self, "TranscribeLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="transcribe.lambda_handler",
            code=lambda_.Code.from_asset("lambda_functions/transcribe"),
            role=self.lambda_role,
            timeout=Duration.seconds(300)
        )

        # Poll Lambda Function
        self.poll_transcribe_lambda = lambda_.Function(self, "PollTranscribeLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="poll_transcribe.lambda_handler",
            code=lambda_.Code.from_asset("lambda_functions/poll_transcribe"),
            role=self.lambda_role,
            timeout=Duration.seconds(300),
        )
        
        # Translate Lambda Function
        self.translate_lambda = lambda_.Function(self, "TranslateLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="translate.lambda_handler",
            code=lambda_.Code.from_asset("lambda_functions/translate"),
            role=self.lambda_role,
            timeout=Duration.seconds(300),
            layers=[self.requests_layer]
        )
        
        # Voice Sample Lambda
        self.voice_samples_lambda = lambda_.Function(self, "VoiceSamplesLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="voice_samples.lambda_handler",
            code=lambda_.Code.from_asset("lambda_functions/voice_samples"),
            role=self.lambda_role,
            timeout=Duration.seconds(300),
            layers=[self.ffmpeg_layer, self.requests_layer, self.pydub_layer]
        )
        
        # Invoke TTS Lambda
        self.invoke_tts_lambda = lambda_.Function(self, "InvokeTTSLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="invoke_tts.lambda_handler",
            code=lambda_.Code.from_asset("lambda_functions/invoke_tts"),
            role=self.lambda_role,
            timeout=Duration.seconds(300)
        )
        
        # Poll TTS Lambda
        self.poll_tts_lambda = lambda_.Function(self, "PollTTSLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="poll_tts.lambda_handler",
            code=lambda_.Code.from_asset("lambda_functions/poll_tts"),
            role=self.lambda_role,
            timeout=Duration.seconds(300)
        )
        
        # Invoke Retalking Lambda
        self.invoke_retalking_lambda = lambda_.Function(self, "InvokeRetalkingLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="invoke_retalking.lambda_handler",
            code=lambda_.Code.from_asset("lambda_functions/invoke_retalking"),
            role=self.lambda_role,
            timeout=Duration.seconds(300),
            layers=[self.ffmpeg_layer, self.pydub_layer]
        )   
        
        # Poll Retalking Lambda
        self.poll_retalking_lambda = lambda_.Function(self, "PollRetalkingLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="poll_retalking.lambda_handler",
            code=lambda_.Code.from_asset("lambda_functions/poll_retalking"),
            role=self.lambda_role,
            timeout=Duration.seconds(300)
        )
        
        
        # Create the Step Function
        transcribe_job = tasks.LambdaInvoke(self, "Transcribe Task",
            lambda_function=self.transcribe_lambda,
            output_path="$.Payload"
        )
        
        poll_transcribe_job = tasks.LambdaInvoke(self, "Poll Transcribe Task",
            lambda_function=self.poll_transcribe_lambda,
            output_path="$.Payload"
        )
        
        translate_job = tasks.LambdaInvoke(self, "Translate Task",
            lambda_function=self.translate_lambda,
            output_path="$.Payload"
        )
        
        voice_samples_job = tasks.LambdaInvoke(self, "Voice Samples Task",
            lambda_function=self.voice_samples_lambda,
            output_path="$.Payload"
        )
        
        invoke_tts_job = tasks.LambdaInvoke(self, "Invoke TTS Task",
            lambda_function=self.invoke_tts_lambda,
            output_path="$.Payload"
        )
        
        poll_tts_job = tasks.LambdaInvoke(self, "Poll TTS Task",
            lambda_function=self.poll_tts_lambda,
            output_path="$.Payload"
        )
        
        invoke_retalking_job = tasks.LambdaInvoke(self, "Invoke Retalking Task",
            lambda_function=self.invoke_retalking_lambda,
            output_path="$.Payload"
        )
        
        poll_retalking_job = tasks.LambdaInvoke(self, "Poll Retalking Task",
            lambda_function=self.poll_retalking_lambda,
            output_path="$.Payload"
        )
        
        
        poll_transcribe_job_again = sfn.Wait(
            self, "WaitBeforeTranscribePollAgain", time=sfn.WaitTime.duration(Duration.seconds(5))
        ).next(poll_transcribe_job)
        
        
        poll_tts_job_again = sfn.Wait(
            self, "WaitBeforeTTSPollAgain", time=sfn.WaitTime.duration(Duration.seconds(5))
        ).next(poll_tts_job)
        
        poll_retalking_job_again = sfn.Wait(
            self, "WaitBeforeRetalkingPollAgain", time=sfn.WaitTime.duration(Duration.seconds(5))
        ).next(poll_retalking_job)
        
        retalking_loop = invoke_retalking_job.next(poll_retalking_job).next(
            sfn.Choice(self, "Retalking Complete?")
            .when(sfn.Condition.string_equals("$.job_status", "COMPLETED"), sfn.Succeed(self, "Completed"))
            .otherwise(poll_retalking_job_again)
        )
        
        tts_loop = invoke_tts_job.next(poll_tts_job).next(
            sfn.Choice(self, "TTS Complete?")  
            .when(sfn.Condition.string_equals("$.job_status", "COMPLETED"), retalking_loop)
            .otherwise(poll_tts_job_again)
        )
        
        parallel_job = sfn.Parallel(self, "Parallel Execution") \
                            .branch(translate_job) \
                            .branch(voice_samples_job).next(tts_loop)
        
        chain = transcribe_job.next(poll_transcribe_job).next(
            sfn.Choice(self, "Transcription Complete?")
            .when(sfn.Condition.string_equals("$.job_status", "COMPLETED"), parallel_job)
            .otherwise(poll_transcribe_job_again)
        )
        
        # Log Group for StateMachine
        state_machine_log_group = logs.LogGroup(self, "StateMachineLogGroup",
            log_group_name=f"/aws/vendedlogs/states/VisualDubbing-{random_suffix}-logs",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY
        )
        
        state_machine = sfn.StateMachine(
            self, "StateMachine",
            definition_body=sfn.DefinitionBody.from_chainable(chain),
            timeout=Duration.minutes(60),
            logs=sfn.LogOptions(level=sfn.LogLevel.ALL,
                                include_execution_data=True,
                                destination=state_machine_log_group)
        )
        
        event_rule = events.Rule(
            self, "TriggerStepFunction",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={"bucket": {"name": [self.s3_bucket.bucket_name]},
                        "object": {
                            "key": [
                                {
                                    "wildcard": "inputs/*/pipeline_job/*.json"
                                }
                            ]
                        }
                }
            ),
            targets=[targets.SfnStateMachine(state_machine)]
        )
        
        self.pipeline_input_location= CfnOutput(
            self, "VDInputLocation",
            value=f"s3://{self.s3_bucket.bucket_name}/inputs",
            description="Visual Dubbing S3 input uri",
            export_name="VDS3InputLocation"
        )
        
