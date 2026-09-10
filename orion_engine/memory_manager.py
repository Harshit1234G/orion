from abc import ABC, abstractmethod
from typing import Literal, NoReturn, Optional
from sqlite3 import Row
from utils import DatabaseConnector, logger
from .tool_manager import ToolManager


LOGGING_NAME = '[MemoryManager]'
tm = ToolManager()


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
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )

        logger.info(f'{LOGGING_NAME} Created `conversation_events` table.')

    def delete_table(self) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute('DROP TABLE IF EXISTS conversation_events')

        logger.info(f'{LOGGING_NAME} Deleted `conversation_events` table.')

    def save(
        self,
        role: Literal['user', 'assistant', 'tool'],
        content: str
    ) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute(
                '''
                INSERT INTO conversation_events (role, content)
                VALUES (?, ?)
                ''',
                parameters= (role, content)
            )

        logger.info(f'{LOGGING_NAME} Saved conversation to `conversation_events` table.')

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

            logger.info(f'{LOGGING_NAME} Retrieved {last_n} rows from `conversation_events` table.')
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

        logger.info(f'{LOGGING_NAME} Deleted row with id {id_} from `conversation_events` table.')

    def update(self) -> NoReturn:
        raise NotImplementedError(f'{LOGGING_NAME} ConversationMemory doesn\'t require updation, so `update` method is not implemented.')
        

@tm.tool
class SessionMemory:
    """
    Manages the current session's memory by updating and retrieving it. The memory contains a summary of what happened throughout the session, not the actual conversation.
    """
    def __init__(self):
        self.memory = ''

    def retrieve(self) -> str:
        """Retrieves the summary of the current session."""
        logger.info(f'{LOGGING_NAME} Asked for session memory.')
        return self.memory

    def update(self, new_memory: str) -> None:
        """Replaces the current session's memory with the provided summary."""
        logger.info(f'{LOGGING_NAME} Session Memory updated successfully.')
        self.memory = new_memory


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
