import os
import random
import string
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    RemovalPolicy,
    CfnParameter,
    CfnOutput,
    aws_ecr as ecr
)

from constructs import Construct

from sagemaker import image_uris

class SageMakerSupportingInfraStack(Stack):
    """
    This stack deploys the SageMaker role and bucket requried for the SageMaker Endpoint.
    After this is deployed, model files are uploaded separately from the CDK due to the 2GB S3Deploy limitation.
    """
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    
        # SageMaker role for endpoints
        # Create a custom S3 policy
        custom_s3_policy = iam.ManagedPolicy(self, "CustomS3Policy",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "s3:GetBucketLocation",
                        "s3:ListAllMyBuckets"
                    ],
                    resources=["arn:aws:s3:::*"]
                ),
                iam.PolicyStatement(
                    actions=[
                        "s3:ListBucket",
                        "s3:GetBucketLocation"
                    ],
                    resources=["arn:aws:s3:::visual-dubbing-pipeline-*"]
                ),
                iam.PolicyStatement(
                    actions=[
                        "s3:PutObject",
                        "s3:GetObject",
                        "s3:DeleteObject"
                    ],
                    resources=["arn:aws:s3:::visual-dubbing-pipeline-*/*"]
                )
            ]
        )

        # Create the SageMaker role with the custom S3 policy
        self.sagemaker_role = iam.Role(self, "SageMakerRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                custom_s3_policy
            ]    
        )
        self.sm_role_output= CfnOutput(
            self, "SMRoleOutput",
            value=self.sagemaker_role.role_arn,
            description="Sagemaker Execution Role",
            export_name="SMRole"
        )
        
        # Buckets for endpoints
        bucket_name = CfnParameter(self, "BucketName", type="String", default=f"visual-dubbing-pipeline-sagemaker-{random_suffix}")
        self.sm_bucket = s3.Bucket(self, id="SagemakerBucket",
                              bucket_name=bucket_name.value_as_string,
                              removal_policy=RemovalPolicy.DESTROY,
                              auto_delete_objects=True)
        
        self.sm_bucket.grant_read_write(self.sagemaker_role)
        
        self.sm_bucket_name_output = CfnOutput(
            self, "SMBucketNameOutput",
            value=self.sm_bucket.bucket_name,
            description="SageMaker Bucket Name",
            export_name="SMBucketName"
        )
        
        self.retalking_repo_name = f"retalking-visual-dubbing-{random_suffix}"
        
        # Create ECR for retalking container
        self.ecr_retalking_repo = ecr.Repository(
            self, "RetalkingRepo",
            repository_name=self.retalking_repo_name,
            empty_on_delete=True,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        self.ecr_retalking_repo.grant_pull(self.sagemaker_role)
        
        self.ecr_output = CfnOutput(
            self, "ECROutput",
            value=self.retalking_repo_name,
            description="Retalking ECR repo name",
            export_name="ECRRepoName"
        )
        
        self.ecr_uri_output = CfnOutput(
            self, "ECRUriOutput",
            value=self.ecr_retalking_repo.repository_uri,
            description="Retalking ECR URI",
            export_name="ECRUri"
        )
        
        self.region_output = CfnOutput(
            self, "RegionName",
            value=self.region,
            description="Region",
            export_name="RegionName"
        )
        
        self.account_output = CfnOutput(
            self, "AccountId",
            value=self.account,
            description="Account ID",
            export_name="AccountId"
        )