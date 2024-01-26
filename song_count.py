import os

def count_songs(library_path):
    song_count = 0
    for root, dirs, files in os.walk(library_path):
        for file in files:
            song_count += 1
    return song_count

# Usage
song_count = count_songs('/home/dev/crec')
print(f"Song count: {song_count}")