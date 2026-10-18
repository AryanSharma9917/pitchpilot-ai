import asyncio
import json

import httpx
import pytest

from app.config import Settings
from app.services.ollama_service import ModelNotFound, OllamaService


def mocked_async_client(monkeypatch, handler):
    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        "app.services.ollama_service.httpx.AsyncClient",
        lambda **kwargs: original_client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
    )


def test_ollama_generation_uses_configured_model_and_json_response(monkeypatch):
    requests = []

    async def handler(request):
        requests.append(request)
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "gemma3:4b"}]})
        return httpx.Response(200, json={"response": '{"title":"Draft"}'})

    mocked_async_client(monkeypatch, handler)
    service = OllamaService(Settings(ollama_model="gemma3:4b"))

    result = asyncio.run(service.generate("prompt"))

    assert result == '{"title":"Draft"}'
    assert [request.url.path for request in requests] == ["/api/tags", "/api/generate"]
    body = json.loads(requests[1].content)
    assert body == {
        "model": "gemma3:4b",
        "prompt": "prompt",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "top_p": 0.9},
    }


def test_ollama_generation_refuses_to_fallback_when_model_is_missing(monkeypatch):
    requests = []

    async def handler(request):
        requests.append(request)
        return httpx.Response(
            200, json={"models": [{"name": "qwen2.5-coder:3b"}]}
        )

    mocked_async_client(monkeypatch, handler)
    service = OllamaService(Settings(ollama_model="gemma3:4b"))

    with pytest.raises(ModelNotFound):
        asyncio.run(service.generate("prompt"))
    assert [request.url.path for request in requests] == ["/api/tags"]
