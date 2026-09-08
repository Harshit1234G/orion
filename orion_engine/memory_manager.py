from abc import ABC, abstractmethod
from typing import Any
from utils import DatabaseConnector, logger


LOGGING_NAME = '[MemoryManager]'


# ------------------
# Abstract class
# ------------------
class Memory(ABC):
    @abstractmethod
    def create_table(*args, **kwargs) -> None:
        ...

    @abstractmethod
    def delete_table(*args, **kwargs) -> None:
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


# ------------------
# Main classes
# ------------------
class ConversationMemory(Memory):
    ...


class SessionMemory(Memory):
    ...


class LongTermMemory(Memory):
    ...


class EnvironmentMemory(Memory):
    ...
