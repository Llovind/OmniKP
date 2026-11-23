"""Shared OpenRouter and local OpenAI-compatible settings for mapping and RCA clients."""
import json
import os
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

LOCAL_PROVIDER_DUMMY_KEY = "ollama-local"
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
_RAW_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/llama-3.1-70b-instruct")


def is_local_provider_url(base_url: str) -> bool:
    """Return True when base_url targets a local loopback OpenAI-compatible server."""
    try:
        parsed = urlsplit((base_url or "").strip())
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return parsed.scheme in ("http", "https") and host in ("127.0.0.1", "localhost", "::1")


def effective_provider_api_key(base_url: str, api_key: str) -> str:
    """Never forward real OpenRouter secrets to a local loopback endpoint."""
    if is_local_provider_url(base_url) and api_key.strip().lower().startswith("sk-or-"):
        return LOCAL_PROVIDER_DUMMY_KEY
    return api_key


OPENROUTER_API_KEY = effective_provider_api_key(OPENROUTER_BASE_URL, _RAW_API_KEY)


async def _prepare_local_ollama_request(request: httpx.Request) -> None:
    """Disable thinking by default on local Ollama /chat/completions for deterministic JSON."""
    if request.method != "POST" or not request.url.path.rstrip("/").endswith("/chat/completions"):
        return
    try:
        payload = json.loads(request.content.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return
    if not isinstance(payload, dict) or "reasoning_effort" in payload:
        return
    payload["reasoning_effort"] = "none"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request.stream = httpx.ByteStream(body)
    request._content = body
    request.headers["content-length"] = str(len(body))


def create_openrouter_client():
    api_key = effective_provider_api_key(OPENROUTER_BASE_URL, OPENROUTER_API_KEY)
    if is_local_provider_url(OPENROUTER_BASE_URL) and not api_key:
        api_key = LOCAL_PROVIDER_DUMMY_KEY
    options = {
        "api_key": api_key or "no-key-set",
        "base_url": OPENROUTER_BASE_URL,
    }
    if is_local_provider_url(OPENROUTER_BASE_URL):
        options["http_client"] = httpx.AsyncClient(
            event_hooks={"request": [_prepare_local_ollama_request]},
        )
    retries = os.getenv("OPENROUTER_MAX_RETRIES")
    if retries is not None:
        try:
            max_retries = int(retries)
        except ValueError:
            raise ValueError("OPENROUTER_MAX_RETRIES must be a nonnegative integer.") from None
        if max_retries < 0:
            raise ValueError("OPENROUTER_MAX_RETRIES must be a nonnegative integer.")
        options["max_retries"] = max_retries

    return AsyncOpenAI(**options)
