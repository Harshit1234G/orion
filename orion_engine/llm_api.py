from enum import Enum
from openai import OpenAI

from utils import logger, load_api_key_from_env, load_api_key_keyring


LOGGING_NAME = '[LLM_API]'


# ----------------------------
# Helper Classes
# ----------------------------
class OpenAIModel(str, Enum):
    FAST = 'gpt-5-nano'
    GENERAL = 'gpt-5.6-luna'
    REASONING = 'gpt-5.6-terra'
    ADVANCED_REASONING = 'gpt-5.6-sol'


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
            error = f'{LOGGING_NAME} OpenAIClient Crashed: No OpenAI Key found.'
            logger.error(error)
            raise RuntimeError(error)
        
        self.client = OpenAI(api_key= api_key)
        logger.info(f'{LOGGING_NAME} Initialized Successfully.')

    def generate(
        self,
        *,
        model: str,
        messages: list[dict],
        temperature: float,
        return_response_object: bool = False,
        **kwargs
    ):

        ##TODO:  Change the API generation code
        try:
            response = self.client.responses.create(
                model= model,
                messages= messages,
                temperature= temperature,
                **kwargs
            )

            logger.info(f'{LOGGING_NAME} Response Received Successfully.')

            if return_response_object:
                return response
            
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f'{LOGGING_NAME} OpenAIClient Error: {e}')
            raise
