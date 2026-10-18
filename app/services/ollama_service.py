from typing import Any

import httpx

from app.config import Settings


class OllamaUnavailable(Exception):
    pass


class ModelNotFound(Exception):
    pass


class GenerationTimeout(Exception):
    pass


class OllamaService:
    def __init__(self, config: Settings):
        self.config = config

    async def model_status(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=min(self.config.request_timeout, 5.0)) as client:
                response = await client.get(f"{self.config.ollama_base_url}/api/tags")
                response.raise_for_status()
                payload = response.json()
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError):
            return {
                "ollama": False,
                "model": self.config.ollama_model,
                "model_available": False,
            }

        if not isinstance(payload, dict):
            return {
                "ollama": False,
                "model": self.config.ollama_model,
                "model_available": False,
            }
        models = payload.get("models", [])
        if not isinstance(models, list):
            models = []
        available = any(
            isinstance(model, dict)
            and isinstance(model.get("name"), str)
            and model["name"].split(":")[0] == self.config.ollama_model.split(":")[0]
            and (
                ":" not in self.config.ollama_model
                or model["name"] == self.config.ollama_model
            )
            for model in models
        )
        return {
            "ollama": True,
            "model": self.config.ollama_model,
            "model_available": available,
        }

    async def generate(self, prompt: str) -> str:
        status = await self.model_status()
        if not status["ollama"]:
            raise OllamaUnavailable
        if not status["model_available"]:
            raise ModelNotFound

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout) as client:
                response = await client.post(
                    f"{self.config.ollama_base_url}/api/generate",
                    json={
                        "model": self.config.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.2,
                            "top_p": 0.9,
                        },
                    },
                )
                if response.status_code == 404:
                    raise ModelNotFound
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            raise GenerationTimeout from exc
        except httpx.RequestError as exc:
            raise OllamaUnavailable from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ModelNotFound from exc
            raise OllamaUnavailable from exc
        except ValueError as exc:
            raise OllamaUnavailable from exc

        if not isinstance(payload, dict):
            return ""
        result = payload.get("response")
        if not isinstance(result, str) or not result.strip():
            return ""
        return result
