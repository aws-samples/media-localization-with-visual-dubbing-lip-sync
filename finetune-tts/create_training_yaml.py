import os
import argparse
import json
import math

def process(num_lines, hyperparams, template_yaml):

    def calc_iterations( epochs, lines, batch_size ):
	    return int(math.ceil(epochs * math.ceil(lines / batch_size)))
    
    # default values
    tokenizer_json = "./modules/tortoise-tts/tortoise/data/tokenizer.json"
    validation_batch_size = 8
    optimizer = "adamw"
    validation_rate = 5
    learning_rate_scheme = "Multistep"
    validation_enabled = "false"
    save_rate = 5
    mel_lr_weight = 1
    text_lr_weight = 0.01
    gradient_accumulation_size = 16
    save_rate = 5
    half_p = "false"
    bitsandbytes = "true"
    validation_enabled = "false"
    workers = 2
    gpus = 1
    voice = "voice_default"


    if "epochs" not in hyperparams:
        raise Exception("epoch is a required hyperparameter")
    if "batch_size" not in hyperparams:
        raise Exception("batch_size is a required hyperparameter")
    if "learning_rate" not in hyperparams:
        raise Exception("learning_rate is a required hyperparameter")

    epochs = hyperparams["epochs"]
    batch_size = hyperparams["batch_size"]
    learning_rate = hyperparams["learning_rate"]

    if "tokenizer_json" in hyperparams:
        tokenizer_json = hyperparams["tokenizer_json"]
    if "validation_batch_size" in hyperparams:
        validation_batch_size = hyperparams["validation_batch_size"]
    if "optimizer" in hyperparams:
        optimizer = hyperparams["optimizer"]
    if "validation_rate" in hyperparams:
        validation_rate = hyperparams["validation_rate"]
    if "learning_rate_scheme" in hyperparams:
        learning_rate_scheme =  hyperparams["learning_rate_scheme"]
    if "validation_enabled" in hyperparams:
        validation_enabled =  hyperparams["validation_enabled"]
    if "save_rate" in hyperparams:
        save_rate =  hyperparams["save_rate"]
    if "mel_lr_weight" in hyperparams:
        mel_lr_weight =  hyperparams["mel_lr_weight"]
    if "text_lr_weight" in hyperparams:
        text_lr_weight =  hyperparams["text_lr_weight"]
    if "gradient_accumulation_size" in hyperparams:
        gradient_accumulation_size =  hyperparams["gradient_accumulation_size"]
    if "save_rate" in hyperparams:
        save_rate =  hyperparams["save_rate"]
    if "half_p" in hyperparams:
        half_p =  hyperparams["half_p"]
    if "bitsandbytes" in hyperparams:
        bitsandbytes =  hyperparams["bitsandbytes"]
    if "validation_enabled" in hyperparams:
        validation_enabled =  hyperparams["validation_enabled"]
    if "workers" in hyperparams:
        workers =  hyperparams["workers"]
    if "gpus" in hyperparams:
        gpus =  hyperparams["gpus"]
    if "voice" in hyperparams:
        voice =  hyperparams["voice"]

    iterations = calc_iterations( epochs, num_lines, batch_size )
    template_yaml = template_yaml.replace("${iterations}",str(iterations))
    template_yaml = template_yaml.replace("${voice}",str(voice))
    template_yaml = template_yaml.replace("${half_p}",str(half_p))
    template_yaml = template_yaml.replace("${bitsandbytes}",str(bitsandbytes))
    template_yaml = template_yaml.replace("${gpus}",str(gpus))
    template_yaml = template_yaml.replace("${workers}",str(workers))
    template_yaml = template_yaml.replace("${batch_size}",str(batch_size))
    template_yaml = template_yaml.replace("${tokenizer_json}",str(tokenizer_json))
    template_yaml = template_yaml.replace("${workers}",str(workers))
    template_yaml = template_yaml.replace("${validation_batch_size}",str(validation_batch_size))
    template_yaml = template_yaml.replace("${optimizer}",str(optimizer))
    template_yaml = template_yaml.replace("${learning_rate}",str(learning_rate))
    template_yaml = template_yaml.replace("${text_lr_weight}",str(text_lr_weight))
    template_yaml = template_yaml.replace("${mel_lr_weight}",str(mel_lr_weight))
    template_yaml = template_yaml.replace("${mel_lr_weight}",str(mel_lr_weight))
    template_yaml = template_yaml.replace("${gradient_accumulation_size}",str(gradient_accumulation_size))
    template_yaml = template_yaml.replace("${validation_rate}",str(validation_rate))
    template_yaml = template_yaml.replace("${learning_rate_scheme}",str(learning_rate_scheme))
    template_yaml = template_yaml.replace("${validation_enabled}",str(validation_enabled))
    template_yaml = template_yaml.replace("${save_rate}",str(save_rate))

    with open("train.yaml", "w") as f:
        f.write(template_yaml)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--hyperparam_json', type=str, help='Path to hyperparameter JSON configuration file that contains the hyperparameters for the finetuning job.', required=True) 
    parser.add_argument('--train_txt', type=str, help='Path to training dataset train.txt file.', required=True) 
    args = parser.parse_args()


    with open(args.train_txt, "rb") as f:
      num_lines = sum(1 for _ in f)

    with open(args.hyperparam_json, "r") as f:
        data = f.read() 
    hyperparams = json.loads(data)

    train_template_path = "templates/train.yaml.template"
    with open(train_template_path, "r") as f:
        template_data = f.read()

    process(num_lines, hyperparams, template_data)
    print("train.yaml file is created successfully")
