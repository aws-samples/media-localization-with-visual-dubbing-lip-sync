"""
download_models.py

Description:
    Downloads the pretrained models for TTS and retalking
"""

import os
import sys

sys.path.append(os.path.abspath('./src'))

from utils import download_models

tts_dir = "./src/tts"
tts_model_dir = "./src/tts/model"
retalking_dir = "./src/retalking"
retalking_checkpoints_dir = "./src/retalking/code/checkpoints"

# Final outputs
tts_model_file = "./src/tts/archive/model-tts.tar.gz"
retalking_model_file = "./src/retalking/archive/model-retalking.tar.gz"

download_models(tts_dir=tts_dir,
                tts_model_dir=tts_model_dir, 
                retalking_dir=retalking_dir, 
                retalking_checkpoints_dir=retalking_checkpoints_dir,
                tts_model_dest=tts_model_file,
                retalking_model_dest=retalking_model_file,
                create_archives=True,
                override_archives=False)