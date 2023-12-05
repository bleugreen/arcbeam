import os
from mutagen.flac import FLAC

from db import MusicDatabase


def list_flac_files(directory):
    flac_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".flac"):
                path = os.path.join(root, file)
                metadata = FLAC(path)

                # Extracting song, album, and artist from the file path
                parts = path.split(os.sep)
                song = parts[-1][:-5]  # Remove '.flac' from the filename
                album = parts[-2] if len(parts) > 2 else None
                artist = parts[-3] if len(parts) > 3 else None

                # Extracting other metadata
                meta_dict = {key: metadata[key][0] for key in metadata}
                song_length_ms = int(metadata.info.length * 1000)
                flac_files.append(
                    (song, album, artist, meta_dict, song_length_ms))

    return flac_files


db = MusicDatabase()
# Example usage
flac_list = list_flac_files('/home/dev/crec')
for flac in flac_list:
    title, album, artist, metadata, rec_length = flac
    genre = metadata.get('genre', 'None')
    composer = metadata.get('genre', 'None')
    print(title, album, artist, genre, composer, rec_length)
    try:
        song_id = db.add_song("None", title, artist, album, composer, genre, 0)
        if song_id:
            db.add_recording(song_id, rec_length)
    except Exception as e:
        print(e)
        continue
