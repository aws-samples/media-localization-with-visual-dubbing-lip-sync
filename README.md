# Build a Media Localization solution with Visual Dubbing using generative AI

Authors: Wei Teh (weteh@amazon.com), Ross Alas (alasross@amazon.com), Marc Perussich (marcperu@amazon.com),
and J-S Labonte (ljeanseb@amazon.com)

Using this visual dubbing and lipsync pipeline, it allows you to translate a source video
into a different language by first transcribing the source video, translating it to the
target language, a text-to-speech system is used to create the audio, tempo synced,
and then lip synced to the original video.

## Prerequisites

You will need to have the following prerequisites:
* An AWS account with Identity and Access Management Permissions (IAM) for:
    * Amazon Transcribe
    * Amazon Translate
    * Amazon S3
    * Amazon SageMaker
    * AWS Lambda
    * Amazon Step Functions
* Service Quota set to at least 2 for "Amazon SageMaker/ml.g5.xlarge for endpoint usage"
* MacOS or Linux (Note: this repo is not tested on Windows)
* Python 3.11 or later
* Docker
* Virtualenv
* At least 60 GiB of local free space
* JupyterLab
* ffmpeg
* make

For deploying the solution using CDK, 
* Amazon CDKv2 See https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html

Create your virtual environment and install packages
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Deployment
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

1. If you have not bootstrapped CDK yet, bootstrap it

```
cd src
cdk bootstrap
```

Run the following in the directory where the Makefile is:
2. Download the models

```
make download
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

### Credits
Thanks to the following, this solution was made possible:

Tortoise-TTS - https://github.com/neonbjb/tortoise-tts
VideoReTalking - https://github.com/OpenTalker/video-retalking


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
