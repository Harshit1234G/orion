import inspect
from functools import wraps
from typing import Any, Callable
from dataclasses import asdict

from .llm_api import Parameters, Tool, OpenAIToolNamespaceSchema
from utils import logger, OrionEngineException


LOGGING_NAME = '[ToolManager]'


class ToolManager:
    namespaces = []
    callable_tools = {}

    @classmethod
    def append_to_namespaces(cls, namespace: dict) -> None:
        cls.namespaces.append(namespace)

    @classmethod
    def add_to_callable_tools(cls, tool: str, func: Callable) -> None:
        cls.callable_tools[tool] = func

    def __initialize_namespace(self, obj: object) -> OpenAIToolNamespaceSchema:
        try:
            name = inspect.getmodule(obj).__name__.split('.')[1]

        except:
            name = f'namespace_{len(self.namespaces)}'

        return OpenAIToolNamespaceSchema(
            name= name,
            description= inspect.getdoc(obj),
            tools= []
        )

    @staticmethod
    def __get_public_methods(obj: object) -> list[str]:
        methods = inspect.getmembers(obj, predicate= inspect.ismethod)
        return [
            method for method, _ in methods 
            if not method.startswith('_')
        ]

    @staticmethod
    def __py_to_json(obj: object) -> str:
        py_to_json = {
            str: 'string',
            int: 'number',
            float: 'number',
            dict: 'object',
            list: 'array',
            tuple: 'array',
            bool: 'boolean',
            None: 'null'
        }
        return py_to_json[obj]

    def __create_parameters_for_tools(self, method: Callable) -> Parameters:
        annotations = inspect.get_annotations(method)
        del annotations['return']
        properties = {
            key: {'type': self.__py_to_json(value)}
            for key, value in annotations.items()
        }

        required = []
        sig = inspect.signature(method)
        for name, param in sig.parameters.items():
            if param.default is inspect.Parameter.empty:
                required.append(name)

        return Parameters(
            properties= properties,
            required= required
        )

    def tool(self, cls: type[Any]):
        @wraps(cls)
        def wrapper(*args, **kwargs):
            if not inspect.isclass(cls):
                raise TypeError(f'{LOGGING_NAME} {cls} is not a class.')

            try:
                obj = cls(*args, **kwargs)
                namespace = self.__initialize_namespace(obj)
                public_methods = self.__get_public_methods(obj)

                for method in public_methods:
                    callable_method = getattr(obj, method)
                    self.add_to_callable_tools(method, callable_method)
        
                    namespace.tools.append(
                        Tool(
                            name= method,
                            description= inspect.getdoc(callable_method),
                            parameters= self.__create_parameters_for_tools(callable_method)
                        )
                    )

                self.append_to_namespaces(asdict(namespace))

            except Exception as e:
                raise OrionEngineException(f'{LOGGING_NAME} An error occured while registering namespace: {e}')

            logger.info(f'{LOGGING_NAME} Namespace registered successfully. NAMESPACE: "{namespace.name}", TOTAL_CALLABLE_TOOLS: {len(namespace.tools)}')
            logger.info(f'{LOGGING_NAME} TOTAL_NAMESPACES: {len(self.namespaces)}, OVERALL_CALLABLE_TOOLS: {len(self.callable_tools)}')

            return obj
        
        return wrapper

    def call(self, name: str, *args, **kwargs) -> Any:
        return self.callable_tools[name](*args, **kwargs)
