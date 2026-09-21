from enum import Enum
from dataclasses import dataclass
from typing import Any
from openai import OpenAI, Stream
from openai.types.responses import Response, ResponseStreamEvent

from utils import logger, load_api_key_from_env, load_api_key_keyring


LOGGING_NAME = '[LLM_API]'


# ----------------------------
# Model enum & tool schemas
# ----------------------------
class OpenAIModels(str, Enum):
    FAST = 'gpt-5-nano'
    GENERAL = 'gpt-5.6-luna'
    REASONING = 'gpt-5.6-terra'
    ADVANCED_REASONING = 'gpt-5.6-sol'


@dataclass(frozen= True)
class Parameters:
    properties: dict[dict]      # this will contain all the function parameters and there dtype as "<parameter>": {"type": "<dtype>"}
    required: list[str]
    type: str = 'object'
    additionalProperties: bool = False


@dataclass(frozen= True)
class Tool:
    name: str
    description: str
    parameters: Parameters
    type: str = 'function'


@dataclass(frozen= True)
class OpenAIToolNamespaceSchema:
    name: str
    description: str
    tools: list[Tool]
    type: str = 'namespace'


# ----------------------------
# Main Classes
# ----------------------------
class OpenAIClient:
    """A lightweight wrapper around the OpenAI API client. 

    Automatically loads the OpenAI API key from the environment or system keyring and initializes an OpenAI client instance. 
    
    Raises: 
        RuntimeError: If no OpenAI API key can be found.
    """
    def __init__(self) -> None:
        api_key = (
            load_api_key_from_env() 
            or 
            load_api_key_keyring()
        )

        if api_key is None:
            raise RuntimeError(f'{LOGGING_NAME} OpenAIClient Crashed: No OpenAI Key found.')
        
        self.client = OpenAI(api_key= api_key)
        logger.info(f'{LOGGING_NAME} Initialized Successfully.')

    def generate(
        self,
        *,
        model: OpenAIModels,
        input: Any,
        **kwargs
    ) -> Response | Stream[ResponseStreamEvent]:
        """Generate a response using the OpenAI Responses API.

        Args:
            model (OpenAIModels): The OpenAI model to use for generation.
            input (Any): The input provided to the model. This can be a string or a supported structured input accepted by the Responses API.
            **kwargs: Additional keyword arguments forwarded directly to `client.responses.create()`.
            
        Returns:
            Response | Stream[ResponseStreamEvent]: The response object returned by the OpenAI Responses API.
        """
        response = self.client.responses.create(
            model= model,
            input= input,
            **kwargs
        )

        logger.info(f'{LOGGING_NAME} Response Received Successfully.')
        return response
