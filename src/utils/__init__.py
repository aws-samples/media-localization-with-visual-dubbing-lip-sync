"""
utils.py

Description:
    Contains helper functions for the CDK deployment

"""


import os
import urllib.request
import zipfile
import tarfile

from huggingface_hub import hf_hub_download


def tar_filter_function(tarinfo):
    "Filters out blobs and locks in TTS model folder"
    if "blobs/" in tarinfo.name:
        return None
    return tarinfo

def is_safe_path(base_path, path):
    # Check if the path is safe (doesn't escape the base directory)
    return os.path.realpath(path).startswith(os.path.realpath(base_path))

def safe_extract(zip_path, extract_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Get list of file names in the archive
        file_list = zip_ref.namelist()
        
        # Check each file before extraction
        for file_name in file_list:
            target_path = os.path.join(extract_path, file_name)
            
            # Check if the path is safe
            if not is_safe_path(extract_path, target_path):
                print(f"Skipping potentially unsafe file: {file_name}")
                continue
            
            # Check for absolute paths or parent directory references
            if file_name.startswith('/') or '..' in file_name:
                print(f"Skipping file with suspicious path: {file_name}")
                continue
            
            # Extract the file
            zip_ref.extract(file_name, extract_path)
            print(f"Extracted: {file_name}")

def download_models(tts_dir,
                    tts_model_dir, 
                    retalking_dir, 
                    retalking_checkpoints_dir, 
                    tts_model_dest=None, 
                    retalking_model_dest=None,
                    create_archives=False,
                    override_archives=False):
    """
    Downloads and creates model.tar.gz for TTS and retalking
    
    params:
        tts_dir (str) Path to the TTS dir
        tts_model_dir (str) Path to the TTS model directory
        retalking_dir (str) Path to the Retalking Directory
        retalking_checkpoints_Dir (str) Path to the Retalking Checkpoints Directory
        tts_model_dest (str) Path to the final model-tts.tar.gz file
        retalking_model_dest (str) Path to the final model-retalking.tar.gz file
        create_archives (bool) If True, creates model archives after downloading
        override_archives (bool) If True, overrides archives even if it exists
    """
    # Define the models to download
    MODELS = {
        'autoregressive.pth': 'https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/autoregressive.pth',
        'clvp2.pth': 'https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/clvp2.pth',
        'diffusion_decoder.pth': 'https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/diffusion_decoder.pth',
        'vocoder.pth': 'https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/vocoder.pth',
    }

    tts_model_dir = os.path.abspath(tts_model_dir)
    retalking_dir = os.path.abspath(retalking_dir)
    retalking_checkpoints_dir = os.path.abspath(retalking_checkpoints_dir)
    
    if tts_model_dest:
        tts_model_dest = os.path.abspath(tts_model_dest)
        
    if retalking_model_dest:
        retalking_model_dest = os.path.abspath(retalking_model_dest)

    print("Creating directories...")
    
    
    print(retalking_checkpoints_dir)

    # Create directories if they don't exist
    print(tts_model_dir)
    os.makedirs(tts_model_dir, exist_ok=True)
    
    print(f"{tts_dir}/archive")
    os.makedirs(f"{tts_dir}/archive", exist_ok=True)
    
    print(f"{retalking_dir}/archive")
    os.makedirs(f"{retalking_dir}/archive", exist_ok=True)
    
    print(retalking_checkpoints_dir)
    os.makedirs(retalking_checkpoints_dir, exist_ok=True)


    # Download TTS models
    print("Downloading TTS models...")
    for model in MODELS.keys():
        model_path = hf_hub_download(repo_id="Manmay/tortoise-tts", filename=model, cache_dir=tts_model_dir, local_dir_use_symlinks=False)
        print(f"Downloaded {model}")

    if create_archives:
        if not os.path.exists(tts_model_dest) or override_archives is True:        
            # Create tar.gz archive of the models
            print(f"Creating tar.gz archive of TTS...{tts_model_dest}")
            # with tarfile.open(tts_model_dest, "w:gz") as tar:
            #     for root, dirs, files in os.walk(tts_model_dir, followlinks=True):
            #         for file in files:
            #             if 'blobs' not in root and '.locks' not in root:
            #                 file_path = os.path.join(root, file)
            #                 real_path = os.path.realpath(file_path)
            #                 arcname = os.path.join(os.path.basename(tts_model_dir), os.path.relpath(file_path, tts_model_dir))
            #                 tar.add(real_path, arcname=arcname, recursive=False)
         
         
            with tarfile.open(tts_model_dest, "w:gz") as tar:
                tar.dereference = True
                tar.add(f"{tts_dir}/model", "model", filter=tar_filter_function)
                tar.add(f"{tts_dir}/code", "code")

    # List of retalking files to download
    files_to_download = [
        ("30_net_gen.pth", "v0.0.1/30_net_gen.pth"),
        ("BFM.zip", "v0.0.1/BFM.zip"),
        ("DNet.pt", "v0.0.1/DNet.pt"),
        ("ENet.pth", "v0.0.1/ENet.pth"),
        ("expression.mat", "v0.0.1/expression.mat"),
        ("face3d_pretrain_epoch_20.pth", "v0.0.1/face3d_pretrain_epoch_20.pth"),
        ("GFPGANv1.3.pth", "v0.0.1/GFPGANv1.3.pth"),
        ("GPEN-BFR-512.pth", "v0.0.1/GPEN-BFR-512.pth"),
        ("LNet.pth", "v0.0.1/LNet.pth"),
        ("ParseNet-latest.pth", "v0.0.1/ParseNet-latest.pth"),
        ("RetinaFace-R50.pth", "v0.0.1/RetinaFace-R50.pth"),
        ("shape_predictor_68_face_landmarks.dat", "v0.0.1/shape_predictor_68_face_landmarks.dat")
    ]

    # Base URL for retalking downloads
    base_url = "https://github.com/vinthony/video-retalking/releases/download/"

    # Download retalking files
    print("Downloading retalking files...")
    for file_name, file_path in files_to_download:
        url = base_url + file_path
        destination = os.path.join(retalking_checkpoints_dir, file_name)
        
        if os.path.exists(destination):
            print(f"Skipping {file_name} - already exists.")
        else:
            print(f"Downloading {file_name}...")
            urllib.request.urlretrieve(url, destination)

    # Unzip BFM.zip
    bfm_zip_path = os.path.join(retalking_checkpoints_dir, "BFM.zip")
    bfm_extract_path = os.path.join(retalking_checkpoints_dir, "BFM")
    
    # Check if BFM folder already exists meaning it's been extracted
    if not os.path.exists(bfm_extract_path):
        print("Extracting BFM.zip...")
        safe_extract(bfm_zip_path, bfm_extract_path)
    else:
        print("BFM folder already exists. Skipping extraction.")

    if create_archives:
        # Create tar.gz archive of the models
        if not os.path.exists(retalking_model_dest) or override_archives is True:  
            print(f"Creating tar.gz archive of Retalking...{retalking_model_dest}")
            with tarfile.open(retalking_model_dest, "w:gz") as tar:
                tar.add(f"{retalking_dir}/code", "code")

    print("All operations completed successfully.")