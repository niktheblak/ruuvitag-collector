import datetime
import sqlite3

from exporter import Exporter

class SQLiteExporter(Exporter):
    def __init__(self, db_file):
        self._conn = sqlite3.connect(db_file)
        self.create_table_if_needed()
    
    def name(self):
        return "SQLite"
    
    def export(self, measurements, ts=None):
        if ts is None:
            ts = datetime.datetime.utcnow()
        for mac, content in measurements:
            self._conn.execute('''INSERT INTO sensors
                (timestamp, mac, name, temperature, humidity, pressure)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (ts, mac, content['name'], content['temperature'], content['humidity'], content['pressure']))
        self._conn.commit()

    def close(self):
        self._conn.close()
    
    def create_table_if_needed(self):
        cursor = self._conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sensors'")
        row = cursor.fetchone()
        if row is None:
            print("Creating local database table")
            self._conn.execute('''CREATE TABLE sensors (
                id              INTEGER     PRIMARY KEY AUTOINCREMENT NOT NULL,
                timestamp       DATETIME    DEFAULT CURRENT_TIMESTAMP,
                mac             TEXT        NOT NULL,
                name            TEXT,
                temperature     REAL,
                humidity        REAL,
                pressure        REAL
            );''')
        print("Table created successfully")
