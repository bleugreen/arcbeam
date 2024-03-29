import os
import itertools

class SongQueue:
    def __init__(self, base_directory):
        self.base_directory = base_directory
        self.current_file_path = None
        self.next = []

    def add(self, file_path):
        self.next.append(file_path)


    def get_next_song(self):
        if self.next:
            return self.next.pop(0)

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
        # Determine the current artist's directory
        current_artist_dir = os.path.dirname(current_dir)

        # Check for the next album in the current artist's directory
        artist_albums = sorted([d for d in os.listdir(current_artist_dir) if os.path.isdir(os.path.join(current_artist_dir, d))])
        current_album_index = artist_albums.index(os.path.basename(current_dir))
        for next_album in artist_albums[current_album_index + 1:]:
            album_path = os.path.join(current_artist_dir, next_album)
            album_files = sorted([f for f in os.listdir(album_path) if self._is_audio_file(os.path.join(album_path, f))])
            if album_files:
                return os.path.join(album_path, album_files[0])

        # If no next album in current artist's directory, move to the next artist
        for root, dirs, _ in os.walk(self.base_directory):
            dirs.sort()
            if root > current_artist_dir:
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
