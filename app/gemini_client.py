import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


_client = None


def get_client():
    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Please add it to your .env file."
            )

        _client = genai.Client(api_key=api_key)

    return _client