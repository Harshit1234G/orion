from enum import Enum
from openai import OpenAI


# ----------------------------
# Helper Classes
# ----------------------------
class OpenAIModel(str, Enum):
    FAST = 'gpt-5-nano'
    GENERAL = 'gpt-5.6-luna'
    REASONING = 'gpt-5.6-terra'
    ADVANCED_REASONING = 'gpt-5.6-sol'


class TaskType(str, Enum):
    ...


class MODEL_CONFIG:
    ...


# ----------------------------
# Main Classes
# ----------------------------
class LLMClient:
    ...


class APIRouter:
    ...

