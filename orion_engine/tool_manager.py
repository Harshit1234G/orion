import inspect
from functools import wraps
from typing import Any, Callable
from dataclasses import asdict
from .llm_api import Parameters, Tool, OpenAIToolNamespaceSchema


class ToolManager:
    def __init__(self):
        self.namespaces = []
        self.callable_tools = {}

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
            if param.default is not inspect.Parameter.empty:
                required.append(name)

        return Parameters(
            properties= properties,
            required= required
        )

    def tool(self, cls: type[Any]):
        @wraps(cls)
        def wrapper(*args, **kwargs):
            if not inspect.isclass(cls):
                raise ValueError(f'{cls} is not a class.')
            
            obj = cls(*args, **kwargs)
            namespace = self.__initialize_namespace(obj)
            public_methods = self.__get_public_methods(obj)

            for method in public_methods:
                callable_method = getattr(obj, method)
                self.callable_tools[method] = callable_method
    
                namespace.tools.append(
                    Tool(
                        name= method,
                        description= inspect.getdoc(callable_method),
                        parameters= self.__create_parameters_for_tools(callable_method)
                    )
                )

            self.namespaces.append(asdict(namespace))
            return obj
        
        return wrapper
