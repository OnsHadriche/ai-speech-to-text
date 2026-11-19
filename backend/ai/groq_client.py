
from functools import lru_cache

from groq import Groq

from app.core.config import settings


@lru_cache(maxsize=1)
def get_groq_client() -> Groq:
    """
    Return a reusable Groq client.

    The client is initialized only when first requested.
    """

    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Please add it to your .env file."
        )

    return Groq(
        api_key=settings.groq_api_key,
        timeout=60.0,
        max_retries=2,
    )


def get_groq_model() -> str:
    """Return the configured Groq model."""

    if not settings.groq_model:
        raise RuntimeError(
            "GROQ_MODEL is not configured."
        )

    return settings.groq_model
