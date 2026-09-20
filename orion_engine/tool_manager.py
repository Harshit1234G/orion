import inspect
from functools import wraps
from typing import Any, Callable, Optional, ClassVar
from dataclasses import asdict

from .llm_api import Parameters, Tool, OpenAIToolNamespaceSchema
from utils import logger, OrionEngineException


LOGGING_NAME = '[ToolManager]'


class ToolManager:
    namespaces: ClassVar[list[dict]] = []
    callable_tools: ClassVar[dict[str, Callable]] = {}

    @classmethod
    def _append_to_namespaces(cls, namespace: dict) -> None:
        cls.namespaces.append(namespace)

    @classmethod
    def _add_to_callable_tools(cls, tool: str, func: Callable) -> None:
        cls.callable_tools[tool] = func

    def __initialize_namespace(self, obj: object) -> OpenAIToolNamespaceSchema:
        try:
            name = "".join(
                [
                    f'_{c.lower()}' 
                    if c.isupper() else c 
                    for c in obj.__class__.__name__
                ]
            ).lstrip('_')

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

    def __register_method(
        self,
        namespace: OpenAIToolNamespaceSchema,
        obj: object,
        method_name: str
    ) -> None:
        callable_method = getattr(obj, method_name)
        self._add_to_callable_tools(f'{namespace.name}.{method_name}', callable_method)

        namespace.tools.append(
            Tool(
                name= method_name,
                description= inspect.getdoc(callable_method),
                parameters= self.__create_parameters_for_tools(callable_method)
            )
        )

    def __register_class(
        self,
        class_: type[Any], 
        exclude: Optional[set[str]],
        *args, 
        **kwargs
    ) -> None:
        if not inspect.isclass(class_):
            raise TypeError(f'{LOGGING_NAME} {class_} is not a class.')
        
        obj = class_(*args, **kwargs)
        namespace = self.__initialize_namespace(obj)

        for method_name in self.__get_public_methods(obj):
            if method_name in exclude:
                continue

            self.__register_method(
                namespace,
                obj,
                method_name
            )

        self._append_to_namespaces(asdict(namespace))
        logger.info(f'{LOGGING_NAME} Namespace registered successfully. NAMESPACE: "{namespace.name}", TOTAL_CALLABLE_TOOLS: {len(namespace.tools)}')

    def tool(self, *, exclude: Optional[set[str]] = None):
        exclude = exclude or set()    # `or` returns the first truthy set object

        def decorator(class_: type[Any]):
            # @wraps(class_)
            def wrapper(*args, **kwargs):
                try:
                    self.__register_class(class_, exclude, *args, **kwargs)
                    return class_

                except Exception as e:
                    raise OrionEngineException(
                        f'{LOGGING_NAME} An error occured while registering namespace.'
                    ) from e
            
            return wrapper
        return decorator

    def call(self, name: str, *args, **kwargs) -> Any:
        return self.callable_tools[name](*args, **kwargs)
