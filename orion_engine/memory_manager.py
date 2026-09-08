from abc import ABC, abstractmethod
from typing import Any
from utils import DatabaseConnector, logger


LOGGING_NAME = '[MemoryManager]'


# ------------------
# Abstract class
# ------------------
class Memory(ABC):
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
    def retrieve(*args, **kwargs) -> Any:
        ...

    @abstractmethod
    def delete(*args, **kwargs) -> None:
        ...


# ----------------------
# Main memory classes
# ----------------------
class ConversationMemory(Memory):
    def __init__(self):
        super().__init__()

    def create_table() -> None:
        with DatabaseConnector('memory.sqlite') as connector:
            connector.execute(
                '''
                CREATE TABLE conversation_events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    role TEXT,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
                '''
            )

    def delete_table() -> None:
        with DatabaseConnector('memory.sqlite') as connector:
            connector.execute('DROP TABLE IF EXISTS conversation_events')
        

class SessionMemory(Memory):
    def __init__(self):
        super().__init__()
    
    def create_table() -> None:
        with DatabaseConnector('memory.sqlite') as connector:
            connector.execute(
                '''
                CREATE TABLE sessions(
                    id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
            connector.execute(
                '''
                CREATE TABLE session_memory(
                    session_id TEXT PRIMARY KEY,
                    memory TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
                '''
            )

    def delete_table() -> None:
        with DatabaseConnector('memory.sqlite') as connector:
            connector.execute('DROP TABLE IF EXISTS sessions')
            connector.execute('DROP TABLE IF EXISTS session_memory')


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
