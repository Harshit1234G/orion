import os
from dotenv import load_dotenv, set_key
import keyring


SERVICE_NAME = 'ORION'
KEY = 'OPENAI_API_KEY'

def load_api_key_from_env() -> str | None:
    load_dotenv()
    return os.getenv(KEY)

def save_api_key_to_env(api_key: str) -> None:
    set_key(
        dotenv_path= '.env', 
        key_to_set= KEY, 
        value_to_set= api_key
    )

def load_api_key_keyring() -> str | None:
    return keyring.get_password(
        service_name= SERVICE_NAME,
        username= KEY
    )

def save_api_key_keyring(api_key) -> None:
    keyring.set_password(
        service_name= SERVICE_NAME,
        username= KEY,
        password= api_key
    )

def delete_api_key_keyring() -> None:
    keyring.delete_password(
        service_name= SERVICE_NAME,
        username= KEY
    )
