import sqlite3
from pathlib import Path
from typing import Any


class DatabaseConnector:
    def __init__(self, database: str) -> None:
        db_dir = Path('db')
        Path.mkdir(db_dir, exist_ok= True)
        self.database = db_dir / database
        
        self.db = None
        self.cursor = None

    def __enter__(self):
        self.db = sqlite3.connect(self.database)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor is not None:
            self.cursor.close()

        if self.db is not None:
            self.db.close()

    def execute(self, query: str, parameters: tuple = ()) -> None:
        if self.cursor is None:
            raise RuntimeError('Database connection is not open.')

        self.cursor.execute(query, parameters)
        self.db.commit()

    def fetch_one(self, query: str, parameters: tuple = ()) -> Any:
        if self.cursor is None:
            raise RuntimeError('Database connection is not open.')

        self.cursor.execute(query, parameters)
        return self.cursor.fetchone()

    def fetch_all(self, query: str, parameters: tuple = ()) -> list[Any]:
        if self.cursor is None:
            raise RuntimeError('Database connection is not open.')

        self.cursor.execute(query, parameters)
        return self.cursor.fetchall()
