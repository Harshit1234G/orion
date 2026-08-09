from enum import Enum
from dataclasses import dataclass
from openai import OpenAI

from utils import logger, load_api_key_from_env, load_api_key_keyring


# ----------------------------
# Helper Classes
# ----------------------------
class OpenAIModel(str, Enum):
    FAST = 'gpt-5-nano'
    GENERAL = 'gpt-5.6-luna'
    REASONING = 'gpt-5.6-terra'
    ADVANCED_REASONING = 'gpt-5.6-sol'


@dataclass(frozen= True)
class Capability:
    name: str
    purpose: str
    model: OpenAIModel
    temperature: float = 0.0


# ----------------------------
# Main Classes
# ----------------------------
class OpenAIClient:
    def __init__(self):
        api_key = load_api_key_from_env() or load_api_key_keyring()

        if api_key is None:
            logger.error('No OpenAI API key found. OpenAIClient crashed.')
            raise ValueError('No OpenAI API key found. OpenAIClient crashed.')
        
        self.client = OpenAI(api_key= api_key)
        logger.info('OpenAIClient loaded successfully')

    def generate(
        self,
        *,
        model: OpenAIModel,
        messages: list[dict],
        temperature: float,
        return_response_object: bool = False,
        **kwargs
    ):
        response = self.client.chat.completions.create(
            model= model,
            messages= messages,
            temperature= temperature,
            **kwargs
        )

        if return_response_object:
            return response
        
        return response.choices[0].message.content


class APIRouter:
    def __init__(self):
        self._capabilities = {}

    def register(self, capability: Capability) -> None:
        self._capabilities[capability.name] = capability

    def get_capability(self, name: str) -> Capability | None:
        return self._capabilities.get(name)

