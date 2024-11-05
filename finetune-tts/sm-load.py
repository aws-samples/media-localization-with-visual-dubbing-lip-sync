from src.utils import load_tts, setup_args, get_model_path

get_model_path('dvae.pth')
setup_args(cli=True)
load_tts()
