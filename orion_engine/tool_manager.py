import inspect
from typing import Any, Callable, Optional, ClassVar, Union, get_args, get_origin
import types
from dataclasses import asdict
import re

from .llm_api import Parameters, Tool, OpenAIToolNamespaceSchema
from utils import logger, OrionEngineException


LOGGING_NAME = '[ToolManager]'


class ToolManager:
    namespaces: ClassVar[list[dict]] = []
    callable_tools: ClassVar[dict[str, Callable]] = {}

    # -------------------
    # Class methods
    # -------------------
    @classmethod
    def append_to_namespaces(cls, namespace: dict) -> None:
        cls.namespaces.append(namespace)

    @classmethod
    def add_to_callable_tools(cls, tool: str, func: Callable) -> None:
        cls.callable_tools[tool] = func

    # -------------------------
    # schema building methods
    # -------------------------
    def __initialize_namespace(self, obj: object) -> OpenAIToolNamespaceSchema:
        name = obj.__class__.__name__
        # converting to snake case
        name = re.sub(
            r'(?<!^)(?=[A-Z])',
            '_',
            name
        ).lower()

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

    #** method to convert py objects to json schema
    def __annotation_to_schema(self, annotation: Any) -> dict:
        if annotation is Any:
            return {}

        if annotation is type(None):
            return {'type': 'null'}

        if annotation is str:
            return {'type': 'string'}

        if annotation is int:
            return {'type': 'integer'}

        if annotation is float:
            return {'type': 'number'}

        if annotation is bool:
            return {'type': 'boolean'}

        if annotation is dict:
            return {'type': 'object'}

        if annotation is list:
            return {'type': 'array'}

        if annotation is tuple:
            return {'type': 'array'}

        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin is list:
            return {
                'type': 'array',
                'items': self.__annotation_to_schema(args[0])
            }

        if origin is dict:
            return {
                'type': 'object'
            }

        if origin in (Union, types.UnionType):
            schemas = [
                self.__annotation_to_schema(arg)
                for arg in args
            ]

            return {
                'anyOf': schemas
            }

        raise TypeError(
            f'Unsupported annotation: {annotation!r}'
        )

    def __create_parameters_for_tools(self, method: Callable) -> Parameters:
        sig = inspect.signature(method)
        properties = {}
        required = []

        for name, param in sig.parameters.items():
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD
            ):
                continue

            if param.annotation is inspect.Parameter.empty:
                raise TypeError(
                    f'{LOGGING_NAME} Tool parameter `{name}` has no type annotation.'
                )

            properties[name] = self.__annotation_to_schema(param.annotation)

            if param.default is inspect.Parameter.empty:
                required.append(name)

            else:
                properties[name]['default'] = param.default

        return Parameters(
            properties= properties,
            required= required
        )

    # ----------------------
    # Registration methods
    # ----------------------
    def _register_method(
        self,
        namespace: OpenAIToolNamespaceSchema,
        obj: object,
        method_name: str
    ) -> None:
        callable_method = getattr(obj, method_name)
        tool_name = f'{namespace.name}.{method_name}'

        if tool_name in self.callable_tools:
            raise ValueError(f'{LOGGING_NAME} Tool already regisered: {tool_name}')

        self.add_to_callable_tools(tool_name, callable_method)

        namespace.tools.append(
            Tool(
                name= method_name,
                description= inspect.getdoc(callable_method),
                parameters= self.__create_parameters_for_tools(callable_method)
            )
        )

        logger.debug(f'{LOGGING_NAME} Registered tool: {tool_name}.')

    def _register_class(
        self,
        class_: type[Any], 
        exclude: Optional[set[str]],
        *args, 
        **kwargs
    ) -> object:
        if not inspect.isclass(class_):
            raise TypeError(f'{LOGGING_NAME} {class_} is not a class.')

        try:
            obj = class_(*args, **kwargs)
            namespace = self.__initialize_namespace(obj)

            for method_name in self.__get_public_methods(obj):
                if method_name in exclude:
                    continue

                self._register_method(
                    namespace,
                    obj,
                    method_name
                )

            self.append_to_namespaces(asdict(namespace))
            logger.info(
                f'{LOGGING_NAME} Namespace registered successfully. '
                f'NAMESPACE: "{namespace.name}", TOTAL_CALLABLE_TOOLS: {len(namespace.tools)}'
            )

            return obj

        except Exception as e:
            raise OrionEngineException(
                f'{LOGGING_NAME} Failed to register tool {namespace.name}.{method_name}.'
            ) from e

    # -------------------
    # Public methods
    # -------------------
    def tool(self, *, exclude: Optional[set[str]] = None):
        exclude = exclude or set()    # `or` returns the first truthy set object

        def decorator(class_: type[Any]):
            def wrapper(*args, **kwargs):
                return self._register_class(class_, exclude, *args, **kwargs)
            return wrapper
        return decorator

    def call(self, name: str, *args, **kwargs) -> Any:
        try:
            func = self.callable_tools[name]

        except KeyError as e:
            raise OrionEngineException(
                f'{LOGGING_NAME} Unknown tool: `{name}`.'
            ) from e

        return func(*args, **kwargs)
        #TODO: eventually could add parameter validation, permissions, streaming, async, etc.
