from abc import ABC, abstractmethod
from typing import NoReturn, Optional, Iterator
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
    @abstractmethod
    def create_table() -> None:
        """Create the required storage structure."""
        ...

    @abstractmethod
    def delete_table() -> None:
        """Delete the storage structure."""
        ...

    @abstractmethod
    def reset_table() -> None:
        """Reset the storage structure to its initial state."""
        ...

    @abstractmethod
    def save(*args, **kwargs) -> None:
        ...

    @abstractmethod
    def retrieve(*args, **kwargs) -> list[Row]:
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
@tm.tool(
    exclude= {
        'create_table', 
        'delete_table', 
        'reset_table', 
        'save', 
        'delete', 
        'update'
    }
)
class ConversationMemory(Memory):
    """
    Retrieve conversations from the current session, including user messages, model responses, and tool call results.
    """
    table_name = 'conversation_events'

    def __init__(self, connector: DatabaseConnector) -> None:
        super().__init__()
        self.connector = connector
        self.prev_convo_length = 0

    def create_table(self) -> None:
        with self.connector.transaction():
            self.connector.execute(queries.CONVERSATION_MEMORY_CREATE_TABLE)

        logger.info(f'{LOGGING_NAME} Created `{self.table_name}` table.')

    def delete_table(self) -> None:
        with self.connector.transaction():
            self.connector.execute(
                queries.DROP_TABLE,
                parameters= (self.table_name,)
            )

        logger.info(f'{LOGGING_NAME} Deleted `{self.table_name}` table.')

    def reset_table(self) -> None:
        with self.connector.transaction():
            self.connector.execute(
                queries.RESET_TABLE,
                parameters= (self.table_name,)
            )

        logger.info(f'{LOGGING_NAME} Reseted `{self.table_name}` table.')

    def save(
        self,
        conversation: Iterator     # like zip(roles, contents)
    ) -> None:
        with self.connector.transaction():
            self.connector.execute_many(
                queries.SAVE_CONVERSATION,
                parameters= conversation
            )

        self.prev_convo_length = len(conversation)
        logger.info(f'{LOGGING_NAME} Saved conversation.')

    def retrieve_previous_conversation(self) -> list[Row]:
        """Retrieve the most recent conversation entries from the current session."""
        return self.retrieve(last_n= self.prev_convo_length)

    def retrieve(self, last_n: int) -> list[Row]:
        """Retrieve the specified number of recent conversation entries from the current session."""
        rows = self.connector.fetch_all(
            queries.RETRIEVE_CONVERSATION,
            parameters= (last_n,)
        )

        logger.info(f'{LOGGING_NAME} Retrieved {last_n} rows of conversation.')
        return rows[::-1]
            

    def delete(self, id_: int) -> None:
        with self.connector.transaction():
            self.connector.execute(
                queries.DELETE_CONVERSATION,
                parameters= (id_,)
            )

        logger.info(f'{LOGGING_NAME} Deleted conversation with id {id_}.')

    def update(self) -> NoReturn:
        raise NotImplementedError(f'{LOGGING_NAME} ConversationMemory doesn\'t require updation, so `update` method is not implemented.')
        

@tm.tool()
class SessionMemory:
    """
    Manages the current session's memory. The memory is just a summary of the session.
    """
    def __init__(self):
        self.memory = ''

    def retrieve(self) -> str:
        """Retrieves the summary of the current session."""
        logger.info(f'{LOGGING_NAME} Asked for session memory.')
        return self.memory

    def update(self, summary: str) -> None:
        """
        Replaces the current session memory with the provided summary. Preserve all existing information while updating; only condense or shorten the content when the memory becomes large.
        """
        self.memory = summary
        logger.info(f'{LOGGING_NAME} Session Memory updated successfully.')


@tm.tool(exclude= {'create_table', 'delete_table', 'reset_table'})
class LongTermMemory(Memory):
    """Store, retrieve, update, and delete persistent long-term memories."""
    table_name = 'long_term_memory'
    
    def __init__(self, connector: DatabaseConnector) -> None:
        super().__init__()
        self.connector = connector

    def create_table(self) -> None:
        with self.connector.transaction():
            self.connector.execute(queries.LONG_TERM_MEMORY_CREATE_TABLE)

        logger.info(f'{LOGGING_NAME} Created `{self.table_name}` table.')

    def delete_table(self) -> None:
        with self.connector.transaction():
            self.connector.execute(
                queries.DROP_TABLE,
                parameters= (self.table_name,)
            )

        logger.info(f'{LOGGING_NAME} Deleted `{self.table_name}` table.')

    def reset_table(self) -> None:
        with self.connector.transaction():
            self.connector.execute(
                queries.RESET_TABLE,
                parameters= (self.table_name,)
            )

        logger.info(f'{LOGGING_NAME} Reseted `{self.table_name}` table.')

    def save(
        self,
        key: str,
        content: str,
        category: str,
        expires_at: str,
        importance: int = 5
    ) -> None:
        """Save a new long-term memory."""
        expires_at = dateutil.parser.parse(expires_at) if expires_at != 'never' else expires_at
        
        with self.connector.transaction():
            self.connector.execute(
                queries.SAVE_LONG_TERM_MEMORY,
                parameters= (key, content, category, importance, expires_at)
            )

        logger.info(f'{LOGGING_NAME} Saved long term memory.')

    def get_all_keys(self) -> list[str]:
        """Retrieve the keys of all stored long-term memories."""
        keys = self.connector.fetch_all(queries.GET_ALL_KEYS)
        return [key[0] for key in keys]

    def retrieve(
        self,
        *,
        from_id: Optional[int] = None,
        from_key: Optional[str] = None,
        grouped_by_category: Optional[str] = None,
        with_higher_importance_than: Optional[int] = None,
        with_lower_importance_than: Optional[int] = None,
        is_active: Optional[bool] = True 
    ) -> list[Row]:
        """Retrieve long-term memories using an ID, key, or optional filters.

        Use ``from_id`` or ``from_key`` to retrieve a specific memory. When
        either is provided, all other filters are ignored. Otherwise, memories
        can be filtered by category, importance range, and active status.
        """
        self.__update_last_accessed_at(from_key)

        # if from_id or from_key is provided than all other args will be ignored
        if from_id is not None:
            logger.info(f'{LOGGING_NAME} Ignored all arguments and retrieved from id.')
            return self.connector.fetch_one(
                queries.RETRIEVE_FROM_ID,
                parameters= (from_id,)
            )

        if from_key is not None:
            logger.info(f'{LOGGING_NAME} Ignored all arguments and retrieved from key.')
            return self.connector.fetch_one(
                queries.RETRIEVE_FROM_KEY,
                parameters= (from_key,)
            )

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
        return self.connector.fetch_all(query, parameters)

    def delete(self, key: str) -> None:
        """Permanently delete a long-term memory by its key."""
        with self.connector.transaction():
            self.connector.execute(
                queries.DELETE_LONG_TERM_MEMORY,
                parameters= (key,)
            )

        logger.info(f'{LOGGING_NAME} Permanently deleted long term memory with {key = }')

    def __update_last_accessed_at(self, key: str) -> None:
        with self.connector.transaction():
            self.connector.execute(
                queries.UPDATE_LAST_ACCESSED_AT,
                parameters= (key,)
            )

    def update(
        self,
        key: str,
        content: str,
        *,
        category: Optional[str] = None,
        importance: Optional[int] = None,
        expires_at: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> None:
        """Update an existing long-term memory.

        The memory is identified by its key. The content is always updated,
        while category, importance, expiration, and active status are updated
        only when their corresponding values are provided. Unspecified optional
        properties remain unchanged.
        """
        parameters = [content]
        variables = ['content = ?']

        if category is not None:
            parameters.append(category)
            variables.append('category = ?')

        if importance is not None:
            parameters.append(importance)
            variables.append('importance = ?')

        if expires_at is not None:
            parameters.append(expires_at)
            variables.append('expires_at = ?')

        if is_active is not None:
            parameters.append(is_active)
            variables.append('is_active = ?')

        variables.append('updated_at = CURRENT_TIMESTAMP')
        parameters.append(key)

        query = 'UPDATE long_term_memory SET '
        query = query + ', '.join(variables) + ' WHERE key = ?'

        with self.connector.transaction():
            self.connector.execute(query, parameters)

        logger.info(f'{LOGGING_NAME} Updated long term memory with {key = }')


class EnvironmentMemory(Memory):
    def __init__(self):
        raise NotImplementedError()

# ------------------
# Manager
# ------------------
class MemoryManager:
    def __init__(self) -> None:
        self.db_conn = DatabaseConnector()
        self.conversation = ConversationMemory(self.db_conn)
        self.session = SessionMemory()
        self.long_term = LongTermMemory(self.db_conn)
        # self.environment_memory = EnvironmentMemory(self.db_conn)        # will throw error 

    def simplify_conversation(self) -> Iterator:
        ...

    def shutdown(self) -> None:
        self.db_conn.close()
        
