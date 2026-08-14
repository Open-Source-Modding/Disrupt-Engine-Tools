import sqlite3
from os.path import dirname, abspath, join, getmtime, basename
from pickle import loads as pickle_loads
from Common.file_helpers import get_files
from os import remove
from re import sub


class SQLiteDB:
    def __init__(self, d_type, version):
        super().__init__()
        self.type = d_type
        self.version = version
        self.path = dirname(abspath(__file__)) + r'\resources'
        self.name = d_type + '_v' + str(self.version) + '.db'
        self.db_filename = join(self.path, self.name)
        self.check_version()

    def connect_to_db(self):
        conn = sqlite3.connect(self.db_filename)
        return conn

    def check_version(self):
        db_files = get_files(self.path, '.db')
        for file in db_files:
            if self.type.lower() not in file.lower():
                continue
            file_version = int(sub(r'\D', '', basename(file)))
            if file_version != self.version:
                remove(file)

    @staticmethod
    def disconnect_from_db(conn):
        conn.commit()
        conn.close()

    @staticmethod
    def create_tables(cursor):
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file (
                    path TEXT NOT NULL,
                    timestamp FLOAT,
                    content BLOB,
                    type TEXT,
                    UNIQUE (path)
                    )
               ''')

        cursor.execute(''' PRAGMA main.page_size = 4096 ''')
        cursor.execute(''' PRAGMA main.cache_size=10000 ''')
        cursor.execute(''' PRAGMA main.locking_mode=EXCLUSIVE ''')
        cursor.execute(''' PRAGMA main.synchronous=NORMAL ''')
        cursor.execute(''' PRAGMA main.journal_mode=WAL ''')
        cursor.execute(''' PRAGMA main.cache_size=5000 ''')
        cursor.execute(''' PRAGMA auto_vacuum = FULL ''')

    @staticmethod
    def get_timestamps(cursor):
        cursor.execute(''' SELECT path,timestamp FROM file''')
        timestamps = dict((x, y) for x, y in cursor.fetchall())
        return timestamps

    @staticmethod
    def check_timestamp(file_name, timestamps):
        timestamp_in_db = timestamps.get(file_name)
        if timestamp_in_db is None:
            return None

        timestamp = getmtime(file_name)
        if timestamp != timestamp_in_db:
            return False

        return True

    @staticmethod
    def insert_files(cursor, files_to_insert):
        query_create_file_line = ''' INSERT INTO file(path,timestamp,content,type) VALUES(?,?,?,?) '''
        cursor.executemany(query_create_file_line, files_to_insert)

    @staticmethod
    def delete_files(cursor, files_to_delete):
        query_delete_file_line = ''' DELETE FROM file WHERE path = ? '''
        cursor.executemany(query_delete_file_line, files_to_delete)

    @staticmethod
    def get_objects_from_db(cursor, d_type, progress_window=None):
        query = ''' SELECT content FROM file WHERE type = ? '''
        cursor.execute(query, (d_type,))
        rows = cursor.fetchall()

        if progress_window is not None:
            progress_window.ui.bar_2.setMaximum(len(rows))

        d_objects = set()
        for row in rows:
            d_objects.add(pickle_loads(row[0]))
            if progress_window is not None:
                progress_window.update_bar_2()

        return d_objects
