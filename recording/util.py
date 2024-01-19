import os
from config import  REC_FOLDER_RAW, REC_FOLDER_TRIM

def clear_temp_files():
    for folder in [REC_FOLDER_RAW, REC_FOLDER_TRIM]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
