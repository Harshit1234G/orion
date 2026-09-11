import sqlite3
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Sequence, Generator


class DatabaseConnector:
    def __init__(self) -> None:
        db_dir = Path('database')
        db_dir.mkdir(exist_ok= True)
        self.database = db_dir / 'orion_db.sqlite'

        # establishing connection and config
        self.db = sqlite3.connect(self.database)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')    # Write-Ahead Logging
        self.db.execute('PRAGMA foreign_keys=ON')

    def _check_connection(self) -> None:
        if self.db is None:
            raise RuntimeError('Database connection is closed.')

    # execution methods
    def execute(
        self, 
        query: str, 
        parameters: Sequence = ()
    ) -> sqlite3.Cursor:
        self._check_connection()
        return self.db.execute(query, parameters)

    def execute_many(
        self,
        query: str,
        parameters: Sequence[Sequence],
    ) -> sqlite3.Cursor:
        self._check_connection()
        return self.db.executemany(query, parameters)

    # fetching methods
    def fetch_one(
        self, 
        query: str, 
        parameters: Sequence = ()
    ) -> sqlite3.Row | None:
        self._check_connection()
        cursor = self.db.execute(query, parameters)
        return cursor.fetchone()

    def fetch_all(
        self, 
        query: str, 
        parameters: Sequence = ()
    ) -> list[sqlite3.Row]:
        self._check_connection()
        cursor = self.db.execute(query, parameters)
        return cursor.fetchall()

    # transaction control
    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection]:
        self._check_connection()

        try:
            yield self.db

        except Exception:
            self.db.rollback()
            raise

        else:
            self.db.commit()

    def commit(self) -> None:
        self._check_connection()
        self.db.commit()

    def rollback(self) -> None:
        self._check_connection()
        self.db.rollback()

    def close(self) -> None:
        if self.db is not None:
            self.db.close()
            self.db = None
