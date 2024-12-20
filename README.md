# Build a Media Localization solution with Visual Dubbing using generative AI

Authors: Wei Teh (weteh@amazon.com), Ross Alas (alasross@amazon.com), Marc Perussich (marcperu@amazon.com),
and J-S Labonte (ljeanseb@amazon.com)

Using this visual dubbing and lipsync pipeline, it allows you to translate a source video
into a different language by first transcribing the source video, translating it to the
target language, a text-to-speech system is used to create the audio, tempo synced,
and then lip synced to the original video.

## Prerequisites

You will need to have the following prerequisites:
* An AWS account with Identity and Access Management Permissions (IAM) role:
    * AWS CloudFormation
    * Amazon Transcribe
    * Amazon Translate
    * Amazon S3
    * Amazon SageMaker
    * AWS Lambda
    * Amazon Step Functions
* AWS CLI installed and configured with a region
* Service Quota set to at least 2 for "Amazon SageMaker/ml.g5.xlarge for endpoint usage"
* MacOS or Linux (Note: this repo is not tested on Windows)
* Python 3.11 or later
* Virtualenv
* Docker (You must be part of the docker group to use docker as part of the build process)
* At least 60 GiB of local free space
* JupyterLab
* ffmpeg
* make
* git
* wget
* Node.js 16 or later

For deploying the solution using CDK, 
* Amazon CDKv2 See https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html

## Deployment

__Prerequisites__
Create your virtual environment in the root of the repo and install packages
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

There are two ways to deploy this solution:

1) Jupyter Notebooks. Follow the following notebooks
    * notebooks/1 - Deploy SageMaker Endpoint.ipynb
    * notebooks/2 - Dubbing Pipeline.ipynb

2) Automated End-to-End Pipeline deployed using CDK. For an automated end to end solution.
    * Follow the instructions below, Deploy Visual Dubbing Lipsync using CDK, to deploy
    * Follow notebooks/3 - Dubbing Pipeline with CDK.ipynb

### Deploy Visual Dubbing Lipsync using CDK
Using the CDK code provided allows you to deploy a fully automated solution end-to-end using
Step Functions and SageMaker endpoints including the TTS and retalking endpoints.

1. Download the models

```
make download
```

2. If you have not bootstrapped CDK yet, bootstrap it

```
make bootstrap
```

3. Build the video retalking container

```
make build
```

4. Synthesize
```
make synth
```

5. Deploy the solution
```
make deploy
```

6. Follow notebooks/3 - Dubbing Pipeline with CDK.ipynb

7. Once you're done with the solution, you can clean up 
```
make destroy
```
8. Clean up docker. Delete the image and build cache.

### Finetune your own Tortoise TTS Model
1. It's possible to finetune tortoise TTS model using your own data. Please follow the instruction [here](finetune-tts/README.md) on how to do that with SageMaker.

2. Once you have a fine-tuned model using the instructions in Step 1,
download the `model.tar.gz` file from S3 output location in the training job in the previous step, and extract it locally to get the autoregressive.pth file. 

3. If you have not done so already, run the download step
```
make download
```

4. As part of the download step, it creates ./src/tts/model folder.
Create a subdirectory within that folder, and place the autoregressive.pth file
in there. e.g., ./src/tts/model/speaker_a/autoregressive.pth.

1. To use the custom model, you need to provide a "model_id". The model_id must be unique and cannot have any spaces. An example of model_id could be: `speaker_a`. Follow the steps below to make the modifications:

If using the step-by-step notebook,
refer to [2 - Dubbing Pipeline.ipynb](notebooks/2%20-%20Dubbing%20Pipeline.ipynb), replace 'model_id' with the `model_id` that you decided on. 

```python
payload = { 
            "id": i,
            "text": translated_sentence, 
            "voice_samples_s3_uri": f"s3://{bucket}/{prefix_voice_samples}/{s3_reference_voice_folder}",
            "input_s3_uri": f"s3://{bucket}/{prefix_inputs}/{inference_id}/{inference_id}-part-{i}.json",
            "destination_s3_uri": f"s3://{bucket}/{prefix_outputs}/{inference_id}/{i}.wav", 
            "model_id": '[your model_id]',  # Used for fine-tune model use
            "inference_params": {}
          } 
```

OR

If using the CDK pipeline,
refer to [3 - Dubbing Pipeline with CDK.ipynb](notebooks/3%20-%20Dubbing%20Pipeline%20with%20CDK.ipynb), replace 'model_id' with the `model_id` that you decided on:

```python
job = {
    "bucket": bucket,
    "prefix_inputs": "inputs",
    "prefix_outputs": "outputs",
    "job_name": job_name,
    "transcribe_source_language_code": transcribe_source_language_code,
    "media_format": "mp4",
    "translate_source_language_code": translate_source_language_code,
    "translate_target_language_code": translate_target_language_code,
    "tts_endpoint_name": stacks_output_dict['SageMakerTTSEndpointOutput'],
    "model_id": '[your model_id]', # Used for fine-tuned models
    "retalking_endpoint_name": stacks_output_dict['SageMakerRetalkingEndpointOutput'],
    "source_file_s3_uri": f"s3://{bucket}/{input_video_key}",
    "destination_s3_uri": f"s3://{bucket}/{output_video_key}"
}
```

The inference script will dynamically load the fine-tune model. 
If you don't specify a model_id, it will be use the default
English speaker model.

### Credits
Thanks to the following, this solution was made possible:

Tortoise-TTS - https://github.com/neonbjb/tortoise-tts

VideoReTalking - https://github.com/OpenTalker/video-retalking

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
