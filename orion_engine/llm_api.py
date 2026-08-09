from enum import Enum
from dataclasses import dataclass
from openai import OpenAI
from utils import logger


# ----------------------------
# Helper Classes
# ----------------------------
class OpenAIModel(str, Enum):
    FAST = 'gpt-5-nano'
    GENERAL = 'gpt-5.6-luna'
    REASONING = 'gpt-5.6-terra'
    ADVANCED_REASONING = 'gpt-5.6-sol'


@dataclass(frozen= True)
class LLMRequirements:
    name: str
    model: OpenAIModel
    temperature: float = 0.0


# ----------------------------
# Main Classes
# ----------------------------
class OpenAIClient:
    ...


class APIRouter:
    ...

