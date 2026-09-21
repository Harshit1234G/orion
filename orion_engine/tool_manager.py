import inspect
from typing import Any, Callable, Optional, ClassVar, Union, get_args, get_origin
import types
from dataclasses import asdict
import re

from .llm_api import Parameters, Tool, OpenAIToolNamespaceSchema
from utils import logger, OrionEngineException


LOGGING_NAME = '[ToolManager]'


class ToolManager:
    """Manages tool registration, schema generation, and tool execution.

    ToolManager discovers public methods from registered classes, converts
    their type annotations into JSON-compatible parameter schemas, and
    maintains a mapping between tool names and their callable methods.

    Registered tools are grouped into namespaces corresponding to the class
    they belong to.
    """
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
        """Create a namespace schema for a registered object.

        The object's class name is converted to snake_case and used as the
        namespace name. The object's class docstring is used as the namespace
        description.

        Args:
            obj: The object whose class will define the namespace.

        Returns:
            A new namespace schema containing the object's name,
            description, and an empty tool list.
        """
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
        """Return the names of public bound methods defined on an object."""
        methods = inspect.getmembers(obj, predicate= inspect.ismethod)
        return [
            method for method, _ in methods 
            if not method.startswith('_')
        ]

    #** method to convert py objects to json schema
    def __annotation_to_schema(self, annotation: Any) -> dict:
        """
        Convert a Python type annotation into a JSON schema fragment.

        Supports basic Python types, `Any`, lists, dictionaries, tuples,
        and union types.
        """
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

        # TODO: Add Literal annotation support if needed

        raise TypeError(
            f'Unsupported annotation: {annotation!r}'
        )

    def __create_parameters_for_tools(self, method: Callable) -> Parameters:
        """Build a parameter schema from a callable's signature.

        Parameter annotations are converted into JSON schema fragments.
        Parameters without default values are marked as required.
        Variadic positional and keyword parameters are ignored.

        Args:
            method: The callable whose parameters should be inspected.

        Returns:
            A ``Parameters`` object describing the callable's accepted
            parameters.

        Raises:
            TypeError: If a tool parameter does not have a type annotation
                or its annotation cannot be converted to a supported schema.
        """
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
        """
        Register a single method as a callable tool.

        The method is added to the callable tool registry and a corresponding
        tool schema is appended to the provided namespace.
        """
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
        """Instantiate and register a class as a tool namespace.

        All public methods of the instantiated object are registered as
        callable tools unless their names are included in ``exclude``.

        Args:
            class_: The class to instantiate and register.
            exclude: Method names that should not be registered.
            *args: Positional arguments passed to the class constructor.
            **kwargs: Keyword arguments passed to the class constructor.

        Returns:
            The instantiated object whose public methods were registered.

        Raises:
            TypeError: If ``class_`` is not a class.
            OrionEngineException: If class instantiation or tool
                registration fails.
        """
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
    def tool(
        self, 
        *, 
        exclude: Optional[set[str]] = None
    ) -> Callable:
        """Create a decorator for registering a class as a tool namespace.

        The decorated class is instantiated when the resulting wrapper is
        called, and all of its public methods are automatically registered
        as tools. Methods listed in ``exclude`` are skipped.

        Args:
            exclude: Optional set of method names that should not be
                registered as tools.

        Returns:
            A class decorator that registers the decorated class when
            instantiated.

        Example:
            ```python
            @tool(exclude={"internal_method"})
            class MyTools:
                ...
            ```
        """
        exclude = exclude or set()    # `or` returns the first truthy set object

        def decorator(class_: type[Any]):
            def wrapper(*args, **kwargs):
                return self._register_class(class_, exclude, *args, **kwargs)
            return wrapper
        return decorator

    def call(self, name: str, *args, **kwargs) -> Any:
        """Execute a registered tool by its fully qualified name.

        Args:
            name: The registered tool name, typically in the
                ``namespace.method`` format.
            *args: Positional arguments passed to the tool.
            **kwargs: Keyword arguments passed to the tool.

        Returns:
            The value returned by the registered tool.

        Raises:
            OrionEngineException: If no tool with the specified name
                is registered.
        """
        try:
            func = self.callable_tools[name]

        except KeyError as e:
            raise OrionEngineException(
                f'{LOGGING_NAME} Unknown tool: `{name}`.'
            ) from e

        return func(*args, **kwargs)
        #TODO: eventually could add parameter validation, permissions, streaming, async, etc.
