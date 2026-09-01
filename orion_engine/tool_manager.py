from functools import wraps
from typing import Callable
from .llm_api import Parameters, Tool, OpenAIToolNamespaceSchema


class ToolManager:
    def __init__(self):
        self.tools = []

    @staticmethod
    def tool(func: Callable):
        @wraps
        def wrapper(self, *args, **kwargs):
            ...