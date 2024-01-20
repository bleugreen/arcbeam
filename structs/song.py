import re
import time
from dataclasses import dataclass, replace
from backend import MusicDatabase
from .lockable import LockableValue


def sanitize_for_exfat(name):
    # Define a regular expression pattern for disallowed characters
    # Includes control characters (U+0000 to U+001F), and specific symbols
    pattern = r'[\x00-\x1F"*/:<>?\\|]'

    # Replace any occurrence of the disallowed characters with an underscore
    sanitized_name = re.sub(pattern, '_', name)

    # Additional rule: Remove leading and trailing spaces
    sanitized_name = sanitized_name.strip()

    return sanitized_name

@dataclass
class SongData:
    rec_id: str
    db: MusicDatabase
    hex_id: LockableValue
    title: LockableValue
    artist: LockableValue
    album: LockableValue
    composer: LockableValue
    genre: LockableValue
    length: LockableValue

    def __init__(self, rec_id='NO_ID', db=None):
        self.rec_id = rec_id
        self.db = db
        self.db_id = None
        self.db_state = None
        self.hex_id = LockableValue()
        self.title = LockableValue()
        self.artist = LockableValue()
        self.album = LockableValue()
        self.composer = LockableValue()
        self.genre = LockableValue()
        self.length = LockableValue(
            verbose=True, timeout=60, repeat_lock=False)
        self.last_update = None

    def copy(self):
        # Use the dataclasses.replace() for a shallow copy
        return replace(self)

    def __str__(self):
        return f"rec_id: {self.rec_id}\n" \
               f"hex_id: {self.hex_id}\n" \
               f"title: {self.title}\n" \
               f"artist: {self.artist}\n" \
               f"album: {self.album}\n" \
               f"composer: {self.composer}\n" \
               f"genre: {self.genre}\n" \
               f"length: {self.length}"
    def to_dict(self):
        return {
            'rec_id': str(self.rec_id),
            'hex_id': str(self.hex_id.value),
            'title': str(self.title.value),
            'artist': str(self.artist.value),
            'album': str(self.album.value),
            'composer': str(self.composer.value),
            'genre': str(self.genre.value),
            'length': self.length.value
        }

    def is_locked(self):
        return self.hex_id.locked and\
            self.title.locked and\
            self.artist.locked and\
            self.album.locked

    def eat_bundle(self, bundle):
        if bundle.get('Persistent ID'):
            if self.hex_id.locked and self.hex_id.value != bundle.get('Persistent ID'):
                print('not my data')
                return False

            self.hex_id.update(bundle.get('Persistent ID'))
            print(f'Update hex id = {self.hex_id}')
        if bundle.get('Album Name'):
            self.album.update(sanitize_for_exfat(bundle.get('Album Name')))
            print(f'Update album = {self.album}')
        if bundle.get('Artist'):
            self.artist.update(sanitize_for_exfat(bundle.get('Artist')))
            print(f'Update artist = {self.artist}')
        if bundle.get('Composer'):
            self.composer.update(bundle.get('Composer'))
        if bundle.get('Genre'):
            self.genre.update(bundle.get('Genre'))
        if bundle.get('Title'):
            self.title.update(sanitize_for_exfat(bundle.get('Title')))
            print(f'Update title = {self.title}')
        if bundle.get('Track length'):

            length = int(bundle.get('Track length').split(' ')[0])
            self.length.update(length)
            print(f'{self.title} - new len: {length} :: {self.length}')
        self.last_update = time.time()
        if self.db is not None and self.db_id is None:
            self.save_song()
        return True

    def save_song(self):
        if self.is_locked() and\
                self.hex_id.value is not None and\
                self.title.value is not None and\
                self.artist.value is not None and\
                self.album.value is not None:
            db_id, status = self.db.song_exists(str(self.title), str(
                self.artist), str(self.album), include_status=True)
            if db_id is not None:
                self.db_id = db_id
                self.db_state = status
            else:
                self.db_id = self.db.add_song(str(self.hex_id), str(self.title), str(self.artist), str(
                    self.album), str(self.composer), str(self.genre), self.length.value)
                self.db_state = 'NEW'
