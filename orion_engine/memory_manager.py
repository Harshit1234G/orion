from abc import ABC, abstractmethod
from typing import Literal, NoReturn, Optional
from sqlite3 import Row
from utils import DatabaseConnector, logger


LOGGING_NAME = '[MemoryManager]'


# ------------------
# Abstract class
# ------------------
class Memory(ABC):
    def __init__(self):
        super().__init__()
        self._db = 'memory.sqlite'

    @abstractmethod
    def create_table() -> None:
        ...

    @abstractmethod
    def delete_table() -> None:
        ...

    @abstractmethod
    def save(*args, **kwargs) -> None:
        ...

    @abstractmethod
    def retrieve(*args, **kwargs) -> Row:
        ...

    @abstractmethod
    def delete(*args, **kwargs) -> None:
        ...

    @abstractmethod
    def update(*args, **kwargs) -> Optional[NoReturn]:
        ...


# ----------------------
# Main memory classes
# ----------------------
class ConversationMemory(Memory):
    def __init__(self):
        super().__init__()

    def create_table(self) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute(
                '''
                CREATE TABLE IF NOT EXISTS conversation_events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
                '''
            )

    def delete_table(self) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute('DROP TABLE IF EXISTS conversation_events')

    def save(
        self,
        session_id: str,
        role: Literal['user', 'assistant', 'tool'],
        content: str
    ) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute(
                '''
                INSERT INTO conversation_events (session_id, role, content)
                VALUES (?, ?, ?)
                ''',
                parameters= (session_id, role, content)
            )

    def retrieve(self, last_n: int) -> Row:
        with DatabaseConnector(self._db) as connector:
            rows = connector.fetch_all(
                '''
                SELECT *
                FROM conversation_events
                ORDER BY id DESC
                LIMIT ?
                ''',
                parameters= (last_n,)
            )

            return rows[::-1]
            

    def delete(self, id_: int) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute(
                '''
                DELETE FROM conversation_events
                WHERE id = ?
                ''',
                parameters= (id_,)
            )

    def update(self) -> NoReturn:
        raise NotImplementedError(f'{LOGGING_NAME} ConversationMemory doesn\'t require updation, so `update` method is not implemented.')
        

class SessionMemory(Memory):
    def __init__(self):
        super().__init__()
    
    def create_table(self) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute(
                '''
                CREATE TABLE IF NOT EXISTS sessions(
                    id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
            connector.execute(
                '''
                CREATE TABLE IF NOT EXISTS session_memory(
                    session_id TEXT PRIMARY KEY,
                    memory TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
                '''
            )

    def delete_table(self) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute('DROP TABLE IF EXISTS sessions')
            connector.execute('DROP TABLE IF EXISTS session_memory')

    def save() -> None:
        ...

    def retrieve() -> Row:
        ...

    def delete() -> None:
        ...

    def update(self) -> None:
        ...


class LongTermMemory(Memory):
    def __init__(self):
        raise NotImplementedError()


class EnvironmentMemory(Memory):
    def __init__(self):
        raise NotImplementedError()

# ------------------
# Manager
# ------------------
class MemoryManager:
    ...
