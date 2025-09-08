import os

OPENAI_API_KEY: str | None = None


def get_openai_api_key() -> str:
    global OPENAI_API_KEY

    if not OPENAI_API_KEY:
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

        if not OPENAI_API_KEY:
            raise Exception("There's no OpenAI API key provided")

    return OPENAI_API_KEY
