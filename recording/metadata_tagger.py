import logging
import os
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.easymp4 import EasyMP4
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import TPE1, TIT2, TALB, TCON, TCOM

logger = logging.getLogger(__name__)


class MetadataTagger:
    @staticmethod
    def tag_file(filepath: str, song_data) -> None:
        """
        Apply metadata tags to an audio file.

        :param filepath: Path to the audio file.
        :param song_data: SongData object containing metadata.
        """
        try:
            audio = MetadataTagger._load_audio_file(filepath)
            if audio:
                MetadataTagger._apply_metadata_tags(audio, song_data)
                audio.save()
        except Exception as e:
            logger.error(f"Error tagging song: {e}")

    @staticmethod
    def _load_audio_file(filepath: str):
        """Load the appropriate audio file based on its extension."""
        file_loader = {
            '.flac': FLAC,
            '.mp3': MP3,
            '.ogg': OggVorbis,
            '.m4a': EasyMP4,
        }
        file_ext = os.path.splitext(filepath)[1].lower()
        return file_loader.get(file_ext, lambda: None)(filepath)

    @staticmethod
    def _apply_metadata_tags(audio, song_data) -> None:
        """Apply metadata tags to the audio file based on its format."""
        if isinstance(audio, MP3):
            MetadataTagger._tag_mp3(audio, song_data)
        elif isinstance(audio, FLAC):
            MetadataTagger._tag_base(audio, song_data)
        elif isinstance(audio, EasyMP4):
            MetadataTagger._tag_base(audio, song_data)
        elif isinstance(audio, OggVorbis):
            MetadataTagger._tag_base(audio, song_data)

    @staticmethod
    def _tag_mp3(audio, song_data):
        """Tag an MP3 file."""
        audio['TPE1'] = TPE1(encoding=3, text=[str(song_data.artist)])
        audio['TIT2'] = TIT2(encoding=3, text=[str(song_data.title)])
        audio['TALB'] = TALB(encoding=3, text=[str(song_data.album)])
        audio['TCON'] = TCON(encoding=3, text=[str(song_data.genre)])
        audio['TCOM'] = TCOM(encoding=3, text=[str(song_data.composer)])

    @staticmethod
    def _tag_base(audio, song_data):
        """Tag a file."""
        audio['artist'] = str(song_data.artist)
        audio['title'] = str(song_data.title)
        audio['album'] = str(song_data.album)
        audio['genre'] = str(song_data.genre)
        audio['composer'] = str(song_data.composer)
