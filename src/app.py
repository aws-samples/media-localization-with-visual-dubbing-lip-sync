#!/usr/bin/env python3
"""
app.py

Description:
    Used for the CDK stack deployment

"""

import os

import aws_cdk as cdk

from stacks.sagemaker_supporting_infra_cdk_stack import SageMakerSupportingInfraStack
from stacks.sagemaker_endpoints_cdk_stack import SageMakerEndpointsStack
from stacks.visual_dubbing_lipsync_cdk_stack import VisualDubbingLipsyncPipelineStack

app = cdk.App()
SageMakerSupportingInfraStack(app, "SageMakerSupportingInfraStack")
SageMakerEndpointsStack(app, "SageMakerEndpointsStack")
VisualDubbingLipsyncPipelineStack(app, "VisualDubbingLipsyncCdkStack")

app.synth()
