from enum import Enum
from dataclasses import dataclass
from openai import OpenAI

from utils import logger, load_api_key_from_env, load_api_key_keyring


LOGGING_NAME = '[LLM_API]'


# ----------------------------
# Helper Classes
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
    def __init__(self):
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
        input: str,
        return_response_object: bool = True,
        **kwargs
    ):
        response = self.client.responses.create(
            model= str(model),
            input= input,
            **kwargs
        )

        logger.info(f'{LOGGING_NAME} Response Received Successfully.')

        if return_response_object:
            return response
        
        return response.output_text
