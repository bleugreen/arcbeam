import sqlite3


class MusicDatabase:
    def __init__(self, db_name="data/music.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS artist (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS album (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                artist_id INTEGER,
                cover_path TEXT,
                UNIQUE(name, artist_id),
                FOREIGN KEY(artist_id) REFERENCES artist(id)
            );
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS song (
                id INTEGER PRIMARY KEY,
                hex_id TEXT,
                title TEXT NOT NULL,
                artist_id INTEGER,
                album_id INTEGER,
                composer TEXT,
                genre TEXT,
                length INTEGER,
                rec_length INTEGER DEFAULT 0,
                saved BOOLEAN DEFAULT 0,
                exported BOOLEAN DEFAULT 0,
                UNIQUE(title, artist_id, album_id),
                FOREIGN KEY(artist_id) REFERENCES artist(id),
                FOREIGN KEY(album_id) REFERENCES album(id)
            );
        """)

    def add_artist(self, name):
        try:
            self.conn.execute("INSERT INTO artist (name) VALUES (?)", (name,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"Artist with name '{name}' already exists.")

    def add_album(self, name, artist_id, cover_path):
        try:
            self.conn.execute(
                "INSERT INTO album (name, artist_id, cover_path) VALUES (?, ?, ?)", (name, artist_id, cover_path))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(
                f"Album with name '{name}' for artist_id '{artist_id}' already exists.")

    def add_song(self, hex_id, title, artist_name, album_name, composer, genre, length):
        # Get or create artist
        artist_id = self.get_or_create_artist(artist_name)

        # Get or create album
        album_id = self.get_or_create_album(album_name, artist_id)

        # Insert the song
        try:
            self.conn.execute("INSERT INTO song (hex_id, title, artist_id, album_id, composer, genre, length) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (hex_id, title, artist_id, album_id, composer, genre, length))
            self.conn.commit()
            print(
                f'DB INSERT: {title} - {artist_name} / {album_name} [{composer}, {genre}, {length}]')
            # Return the id of the new song
            return self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        except sqlite3.IntegrityError as e:
            print(f"Error adding song: {e}")
            return None

    def add_recording(self, song_id, rec_length):
        self.conn.execute(
            "UPDATE song SET saved = 1, rec_length = ? WHERE id = ?", (rec_length, song_id))
        self.conn.commit()
        print('DB UPDATE: Recording updated w/ len', rec_length)

    def get_or_create_artist(self, artist_name):
        # Check if the artist exists
        result = self.conn.execute(
            "SELECT id FROM artist WHERE name = ?", (artist_name,)).fetchone()
        if result:
            return result[0]
        # Insert new artist
        self.conn.execute(
            "INSERT INTO artist (name) VALUES (?)", (artist_name,))
        self.conn.commit()
        return self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_or_create_album(self, album_name, artist_id):
        # Check if the album exists for this artist
        result = self.conn.execute(
            "SELECT id FROM album WHERE name = ? AND artist_id = ?", (album_name, artist_id)).fetchone()
        if result:
            return result[0]
        # Insert new album
        self.conn.execute(
            "INSERT INTO album (name, artist_id) VALUES (?, ?)", (album_name, artist_id))
        self.conn.commit()
        return self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def query_songs(self, artist_name=None, album_name=None):
        query = """
            SELECT song.id, song.hex_id, song.title, artist.name AS artist_name, album.name AS album_name, song.composer, song.genre, song.length, song.saved, song.exported
            FROM song
            JOIN artist ON song.artist_id = artist.id
            JOIN album ON song.album_id = album.id
        """
        params = ()
        conditions = []

        if artist_name:
            conditions.append("artist.name = ?")
            params += (artist_name,)

        if album_name:
            conditions.append("album.name = ?")
            params += (album_name,)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        return self.conn.execute(query, params).fetchall()

    def close(self):
        self.conn.close()

    def get_songs(self, exported=False, saved=False):
        query = f"""
            SELECT id, title, artist_id, album_id
            FROM song
            WHERE exported = {exported} AND saved = {saved}
        """
        return self.conn.execute(query).fetchall()

    def set_exported(self, song_id):
        self.conn.execute(
            "UPDATE song SET exported = 1 WHERE id = ?", (song_id,))
        self.conn.commit()
        print(f"exported {song_id}")

    def song_exists(self, title, artist_name, album_name, include_status=False):
        query = """
            SELECT song.id, song.saved, song.exported
            FROM song
            JOIN artist ON song.artist_id = artist.id
            JOIN album ON song.album_id = album.id
            WHERE song.title = ? AND artist.name = ? AND album.name = ?
        """
        result = self.conn.execute(
            query, (title, artist_name, album_name)).fetchone()
        if not result:
            return None, "UNKNOWN"
        elif include_status:
            if not result[1] and not result[2]:
                return result[0], 'KNOWN'
            elif result[1] and not result[2]:
                return result[0], 'SAVED'
            elif result[1] and result[2]:
                return result[0], 'EXPORTED'
        else:
            return result[0], 'UNKNOWN'

    def borked_the_export(self):
        query = """
            UPDATE song
            SET exported = 0, saved = 0
            WHERE exported = 1
        """
        self.conn.execute(query)
        self.conn.commit()
        print("BORK UNCORKED")
