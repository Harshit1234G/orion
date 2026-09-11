from abc import ABC, abstractmethod
from typing import Literal, NoReturn, Optional
import dateutil
from sqlite3 import Row

from utils import DatabaseConnector, logger
import db_queries as queries
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
            connector.execute(queries.CONVERSATION_MEMORY_CREATE_TABLE)

        logger.info(f'{LOGGING_NAME} Created `conversation_events` table.')

    def delete_table(self) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute(
                queries.DROP_TABLE,
                parameters= ('conversation_events',)
            )

        logger.info(f'{LOGGING_NAME} Deleted `conversation_events` table.')

    def save(
        self,
        role: Literal['user', 'assistant', 'tool'],
        content: str
    ) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute(
                queries.SAVE_CONVERSATION,
                parameters= (role, content)
            )

        logger.info(f'{LOGGING_NAME} Saved conversation to `conversation_events` table.')

    def retrieve(self, last_n: int) -> Row:
        with DatabaseConnector(self._db) as connector:
            rows = connector.fetch_all(
               queries.RETRIEVE_CONVERSATION,
                parameters= (last_n,)
            )

        logger.info(f'{LOGGING_NAME} Retrieved {last_n} rows from `conversation_events` table.')
        return rows[::-1]
            

    def delete(self, id_: int) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute(
                queries.DELETE_CONVERSATION,
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
        super().__init__()

    def create_table(self) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute(queries.LONG_TERM_MEMORY_CREATE_TABLE)

        logger.info(f'{LOGGING_NAME} Created `long_term_memory` table.')

    def delete_table(self) -> None:
        with DatabaseConnector(self._db) as connector:
            connector.execute(
                queries.DROP_TABLE,
                parameters= ('long_term_memory',)
            )

        logger.info(f'{LOGGING_NAME} Deleted `long_term_memory` table.')

    def save(
        self,
        key: str,
        content: str,
        category: str,
        expires_at: str,
        importance: int = 5
    ) -> None:
        expires_at = dateutil.parser.parse(expires_at) if expires_at != 'never' else expires_at
        
        with DatabaseConnector(self._db) as connector:
            connector.execute(
                queries.SAVE_LONG_TERM_MEMORY,
                parameters= (key, content, category, importance, expires_at)
            )

        logger.info(f'{LOGGING_NAME} Saved long term memory to `long_term_memory` table.')

    def __retrieve_from_id(self, id: int) -> Row:
        with DatabaseConnector(self._db) as connector:
            return connector.fetch_one(
                queries.RETRIEVE_FROM_ID,
                parameters= (id,)
            )

    def __retrieve_from_key(self, key: str) -> Row:
        with DatabaseConnector(self._db) as connector:
            return connector.fetch_one(
                queries.RETRIEVE_FROM_KEY,
                parameters= (key,)
            )

    def retrieve(
        self,
        *,
        from_id: Optional[int] = None,
        from_key: Optional[str] = None,
        grouped_by_category: Optional[str] = None,
        with_higher_importance_than: Optional[int] = None,
        with_lower_importance_than: Optional[int] = None,
        is_active: Optional[bool] = True 
    ) -> Row:
            # if from_id or from_key is provided than all other args will be ignored
            if from_id is not None:
                logger.info(f'{LOGGING_NAME} Ignored all arguments and retrieved from id.')
                return self.__retrieve_from_id(from_id)

            if from_key is not None:
                logger.info(f'{LOGGING_NAME} Ignored all arguments and retrieved from key.')
                return self.__retrieve_from_key(from_key)

            # building dynamic conditions
            conditions = []
            parameters = []

            if grouped_by_category is not None:
                conditions.append('category = ?')
                parameters.append(grouped_by_category)

            if with_higher_importance_than is not None:
                conditions.append('importance > ?')
                parameters.append(with_higher_importance_than)

            if with_lower_importance_than is not None:
                conditions.append('importance < ?')
                parameters.append(with_lower_importance_than)

            if is_active is not None:
                conditions.append('is_active = ?')
                parameters.append(int(is_active))

            query = 'SELECT * FROM long_term_memory'

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            logger.info(f'{LOGGING_NAME} Retrieving long term memory based on {len(conditions)} conditions.')

            with DatabaseConnector(self._db) as connector:
                return connector.fetch_all(query, parameters)


    def delete(
        self, 
        key: str,
        *, 
        permanently: bool = False
    ) -> None:
        if permanently:
            with DatabaseConnector(self._db) as connector:
                connector.execute(
                    queries.DELETE_LONG_TERM_MEMORY,
                    parameters= (key,)
                )

                logger.info(f'{LOGGING_NAME} Permanently deleted long term memory with {key = }')
                return

        self.update()


    def update(
        self,
        content: Optional[str] = None,

    ) -> None:
        ...


class EnvironmentMemory(Memory):
    def __init__(self):
        raise NotImplementedError()

# ------------------
# Manager
# ------------------
class MemoryManager:
    ...
