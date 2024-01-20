import yaml
import os

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Recording Settings
REC_PATH = config['recording']['path']
REC_FOLDER_RAW = os.path.join(REC_PATH, 'raw')
REC_FOLDER_TRIM = os.path.join(REC_PATH, 'trim')
REC_FILETYPE = config['recording']['filetype']
REC_OVERLAP = config['recording']['overlap_sec']
REC_BUFFER = config['recording']['process_buffer']
REC_NICE = config['recording']['nice_priority']
REC_FORMAT = config['recording']['format']

# Library Settings
LIB_PATH = config['library']['path']
LIB_FILETYPE = config['library']['filetype']
LIB_DELETE_ON_EXPORT = config['library']['delete_on_export'] == 'true'

# Audio Settings
AUDIO_DEVICE = config['audio']['device']
SAMPLE_RATE = config['audio']['samplerate']
CHANNELS = config['audio']['channels']
PACKETS = config['audio']['channels']

PYTHON_PATH = config['system']['python_path']
