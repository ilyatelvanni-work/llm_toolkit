import os

OPENAI_API_KEY: str | None = None
UVICORN_PORT: int | None = None


class ConfigValueException(BaseException):
    pass


def get_openai_api_key() -> str:
    global OPENAI_API_KEY

    if not OPENAI_API_KEY:
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

        if not OPENAI_API_KEY:
            raise ConfigValueException("There's no OpenAI API key provided")

    return OPENAI_API_KEY


def get_uvicorn_port() -> int:
    global UVICORN_PORT

    if not UVICORN_PORT:
        try:
            backend_port_str = os.environ.get('BACKEND_PORT')

            if backend_port_str is None:
                raise ConfigValueException("There's no backend port provided")

            UVICORN_PORT = int(backend_port_str)

        except ValueError:
            raise ConfigValueException(f"Wrong backend port value provided: '{backend_port_str}'")

    return UVICORN_PORT
