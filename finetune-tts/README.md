## Finetune a Tortoise TTS Model
This page contains the instructions for finetuning the state of the art open source TTS model called Tortoise TTS on [Amazon SageMaker](https://aws.amazon.com/pm/sagemaker).

Tortoise is a text-to-speech program built with the following priorities:

* Strong multi-voice capabilities.
* Highly realistic prosody and intonation.

The science paper for Tortoise-TTS can be found [here](https://arxiv.org/abs/2305.07243)

The instructions given below is based on the open source project [ai-voice-cloning](https://github.com/JarodMica/ai-voice-cloning) that standardizes components required to train a model using own dataset and configurations. 

## Getting Started
By default, Tortoise-TTS offers multi voice English voices out of the box without any finetuning needed. However, there are many reasons why one might consider finetuning a TTS model, training a TTS model that speaks different language is an example. The following guide focuses on finetuning a Tortoise model to adapt to any use cases or scenarios. 

## Prerequisites
1. A machine / laptop with Docker installed. This instructions have been tested using a `SageMaker Jupyter Notebook Instance`(https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html). 
   
2. IAM policy with permissions for starting a SageMaker training job, upload / access files in an S3 bucket, permissions to create ECR repository and pushing images to it.
3. Clone the github repository: 
   
```
git clone https://github.com/aws-samples/media-localization-with-visual-dubbing-lip-sync
cd finetune-tts
```   

1. Prepare training dataset - The training data consists of wav files and the corresponding transcriptions. The wav/transcription pair makes a single entry for the training data. As a general rule, more data used for training the model yields better results. Additionally, data quality matters, that means only feed high quality audios with clear recordings. Feeding around 10-14 hours of audio/transcription samples would yield really good results. This is especially true for training the model with a new language. Additionally, you may need to preprocess the audio files to match the required sample rate (typically 22050 Hz for Tortoise TTS). 

2. Create a Training Data file - The training dataset follows the structure of [LJ-Speech](https://keithito.com/LJ-Speech-Dataset/) dataset format. An example row of a data file looks like the following:
   
   ```
   audio/1_00006.wav| Then, on the other hand, it's a romantic drama.
   ```

   You can name the file `train.txt`. We'll need this file later for training and configuration file generation purposes.

3. (Optional) Create a validation dataset for testing the performance of the model. While not required, validation dataset is useful to evaluate the performance of the model based on training/validation loss. If you have validation dataset, name the file `validation.txt`.
   
4.  Create a file called `train.json` that will be used as the model hyperparameters. Here're an example of hyperparameters supported by the model:

```json
{
        "epochs": 500,
        "learning_rate": 1e-05,
        "mel_lr_weight": 1,
        "text_lr_weight": 0.01,
        "learning_rate_scheme": "Multistep",
        "batch_size": 128,
        "gradient_accumulation_size": 16,
        "save_rate": 5,
        "validation_rate": 5,
        "half_p": false,
        "bitsandbytes": true,
        "validation_enabled": false,
        "workers": 2,
        "gpus": 1,
        "source_model": "./models/tortoise/autoregressive.pth",
        "voice": "[a unique name for the voice]"
}
```

*Note:* `epochs`, `learning_rate` and `batch_size` are the only required parameters. There are default values for the optional parameters. Do play around with the parameters if you the model did not yield the desired accuracy. 

5. In a CLI terminal, run the following command:

```bash
python create_training_yaml.py --hyperparam_json train.json --train_txt train.txt 
```

The above command should generate a `train.yaml` file in the current directory. You'll need to use this file for finetuning the model.
  
6. *Important* - Upload **audio files (wav or mp3), train.txt, validation.txt (optional), train.yaml** to a S3 bucket input location. The audio files in S3 should be relative to the audio file path for `train.txt`. For example, if the location of the audio wav file in the train.txt file has `audio/0001.wav`, then your 0001.wav file should be located in the `/audio` folder. Here's a complete folder structure on S3 with all the required files:

```
|-train.txt
|-validation.txt
|-train.json
|-train.yaml
|-|
  |-audio
        |-0001.wav
        |-0002.wav
```

## Build a Docker Image as a training container
In a CLI console, run the following script:

```
build_and_push_docker.sh -a [AWS account number] -r [AWS Region]
```
Here's a log output from a successful job execution:

```
Login Succeeded
The push refers to repository [************.dkr.ecr.*********.amazonaws.com/tortoise-tts-training]
abc917d54f0e: Pushed 
5b804d1f3871: Pushed 
7b8b6942374f: Pushed 
328b4a858cca: Pushed 
...
e6c05e83c163: Layer already exists 
256d88da4185: Pushed 
latest: digest: sha256:bcff08720760175c23f164bfe0890edb616c7aa6a4fa4ec3a0db8ce8509e3300 size: 8315
```
The docker image should be pushed to the following ECR URI: [AWS_ACCT].dkr.ecr.[REGION].amazonaws.com/tortoise-tts-training
Make a note of the URI as you'll need it for training a model, which is described in the following section.


## Train
Open Jupyter notebook `train.ipynb` and follow the instructions to finetune a TTS model. In the notebook, replace the following:

* An S3 input location to the dataset and configuration files that you prepared and specified in the previous step.
* An S3 output location for the trained model.
* ECR URI for the training image prepared in the previous step

The training job writes the evaluation metrics for every epoch in Cloudwatch log. To access these logs, to go `SageMaker console`->`Training`->`Training Jobs` and click on the specific training job. Then click on `View Logs` to access the latest cloudwatch logs. An example of a log message with evaluation metrics:
```
{
    "loss_text_ce": 4.652981758117676,
    "loss_mel_ce": 2.767702102661133,
    "loss_gpt_total": 2.8142318725585938,
    "lr": 0.000005,
    "it": 10,
    "step": 2,
    "steps": 2,
    "epoch": 4,
    "iteration_rate": 12.116708517074585
}
```