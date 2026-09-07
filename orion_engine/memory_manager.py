from abc import ABC, abstractmethod
from utils import DatabaseConnector


class Memory(ABC):
    @abstractmethod
    def save() -> None:
        ...

    @abstractmethod
    def retrieve() -> ...:
        ...


class ConversationMemory(Memory):
    ...


class SessionMemory(Memory):
    ...


class LongTermMemory(Memory):
    ...


class EnvironmentMemory(Memory):
    ...
