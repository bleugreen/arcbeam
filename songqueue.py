import os
import itertools

class SongQueue:
    def __init__(self, base_directory):
        self.base_directory = base_directory
        self.current_file_path = None

    def get_next_song(self):
        if self.current_file_path is None:
            return self._get_first_song()

        current_dir, current_file = os.path.split(self.current_file_path)
        all_files = sorted(os.listdir(current_dir))
        audio_files = [f for f in all_files if self._is_audio_file(os.path.join(current_dir, f))]

        # Find the next song in the current album
        if current_file in audio_files:
            next_index = audio_files.index(current_file) + 1
            if next_index < len(audio_files):
                return os.path.join(current_dir, audio_files[next_index])

        # If no next song in current album, find next album or artist
        return self._find_next_album_or_artist(current_dir)

    def _find_next_album_or_artist(self, current_dir):
        # Walk the directory tree
        for root, dirs, _ in os.walk(self.base_directory):
            dirs.sort()
            if root > current_dir:
                for dir_name in dirs:
                    album_path = os.path.join(root, dir_name)
                    album_files = sorted([f for f in os.listdir(album_path) if self._is_audio_file(os.path.join(album_path, f))])
                    if album_files:
                        return os.path.join(album_path, album_files[0])
        return None  # No more songs available

    def _is_audio_file(self, filename):
        return filename.lower().endswith(('.flac', '.wav', '.mp3', '.ogg'))

    def _get_first_song(self):
        for root, dirs, _ in os.walk(self.base_directory):
            dirs.sort()
            for dir in dirs:
                album_path = os.path.join(root, dir)
                songs = sorted(os.listdir(album_path))
                if songs:
                    return os.path.join(album_path, songs[0])
        return None  # No songs found in the base directory

    def set_current_song(self, file_path):
        self.current_file_path = file_path
