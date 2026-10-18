from app.services.ollama_service import OllamaService


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "PitchPilot" in response.text


def test_health_reports_api_and_model_readiness(client, monkeypatch):
    async def ready():
        return {"ollama": True, "model": "gemma3:4b", "model_available": True}

    monkeypatch.setattr(client.app.state.ollama_service, "model_status", ready)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "ollama": True,
        "model": "gemma3:4b",
        "model_available": True,
        "ai_ready": True,
    }


def test_health_does_not_claim_ai_ready_when_ollama_is_unavailable(client, monkeypatch):
    async def unavailable():
        return {"ollama": False, "model": "gemma3:4b", "model_available": False}

    monkeypatch.setattr(client.app.state.ollama_service, "model_status", unavailable)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["ai_ready"] is False
    assert response.json()["ollama"] is False


def test_model_status_distinguishes_missing_model(client, monkeypatch):
    async def missing():
        return {"ollama": True, "model": "gemma3:4b", "model_available": False}

    monkeypatch.setattr(client.app.state.ollama_service, "model_status", missing)
    assert client.get("/api/model/status").json()["status"] == "model_missing"


def test_ollama_connection_failure_is_reported_as_unavailable(monkeypatch):
    import httpx

    from app.config import Settings

    original_client = httpx.AsyncClient

    def failing_client(**kwargs):
        async def handler(request):
            raise httpx.ConnectError("connection refused", request=request)

        return original_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr("app.services.ollama_service.httpx.AsyncClient", failing_client)
    service = OllamaService(Settings(ollama_base_url="http://localhost:11434"))

    from asyncio import run

    assert run(service.model_status()) == {
        "ollama": False,
        "model": "gemma3:4b",
        "model_available": False,
    }
