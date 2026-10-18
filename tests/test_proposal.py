import asyncio
import json

import pytest
from pydantic import ValidationError

from app.models.response import QuoteResponse
from app.services.proposal_service import (
    InvalidModelResponse,
    ProposalService,
    extract_json_object,
)


class FakeOllama:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    async def generate(self, prompt):
        self.prompts.append(prompt)
        return self.responses.pop(0)


def test_json_parser_safely_extracts_object_from_fences_or_surrounding_text():
    assert extract_json_object('Result: ```json\n{"value": 3}\n```') == {"value": 3}
    with pytest.raises(ValueError):
        extract_json_object("not json")


def test_malformed_model_response_is_corrected_once_and_validated(valid_request):
    output = {
        "project_summary": "Build the requested site.",
        "deliverables": ["Responsive website"],
        "timeline": "4 weeks",
        "pricing": [{"item": "Build", "amount": "Estimate: $3,000", "details": ""}],
        "assumptions": ["Copy supplied by client."],
        "total_estimate": "Estimate: $3,000",
    }
    ollama = FakeOllama(["not-json", f"Here is the quote: {json.dumps(output)}"])
    service = ProposalService(ollama)
    from app.models.request import GenerationRequest

    result = asyncio.run(service.quote(GenerationRequest.model_validate(valid_request)))
    assert result.total_estimate == "Estimate: $3,000"
    assert result.pricing[0].amount == "Estimate: $3,000"
    assert len(ollama.prompts) == 2
    assert "CORRECTION" in ollama.prompts[1]


def test_missing_required_output_fields_retry_then_return_clear_error(valid_request):
    service = ProposalService(FakeOllama(['{"project_summary":"incomplete"}'] * 2))
    from app.models.request import GenerationRequest

    with pytest.raises(InvalidModelResponse):
        asyncio.run(service.quote(GenerationRequest.model_validate(valid_request)))


def test_pricing_output_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        QuoteResponse.model_validate({
            "project_summary": "A project",
            "deliverables": ["A result"],
            "timeline": "2 weeks",
            "pricing": [],
            "assumptions": ["An assumption"],
            "total_estimate": "Estimate pending",
        })


def test_unavailable_ollama_becomes_understandable_api_error(client, valid_request, monkeypatch):
    from app.services.ollama_service import OllamaUnavailable

    async def unavailable(_):
        raise OllamaUnavailable

    monkeypatch.setattr(client.app.state.proposal_service, "proposal", unavailable)
    response = client.post("/api/generate/proposal", json=valid_request)

    assert response.status_code == 503
    assert "Start Ollama" in response.json()["detail"]


@pytest.mark.parametrize(
    ("mode", "output"),
    [
        (
            "proposal",
            {
                "title": "Website proposal",
                "executive_summary": "A responsive website.",
                "client_needs": ["Five pages"],
                "proposed_solution": "Build the pages.",
                "scope": ["Design and build"],
                "deliverables": ["Website"],
                "milestones": [
                    {"name": "Build", "duration": "4 weeks", "description": "Develop"}
                ],
                "pricing": [{"item": "Build", "amount": "$3,000", "details": ""}],
                "assumptions": ["Client supplies content."],
                "out_of_scope": ["Maintenance"],
                "terms": "To be agreed.",
                "next_steps": "Review the scope.",
            },
        ),
        (
            "quote",
            {
                "project_summary": "Build the website.",
                "deliverables": ["Website"],
                "timeline": "4 weeks",
                "pricing": [{"item": "Build", "amount": "$3,000", "details": ""}],
                "assumptions": ["Client supplies content."],
                "total_estimate": "$3,000",
            },
        ),
        (
            "email",
            {
                "subject": "Website proposal",
                "greeting": "Hello,",
                "body": "Please review the proposal.",
                "closing": "Happy to discuss.",
                "signature": "Alex",
            },
        ),
    ],
)
def test_generation_routes_return_validated_mode_outputs(
    client, valid_request, monkeypatch, mode, output
):
    async def generate(_request):
        return output

    monkeypatch.setattr(
        client.app.state.proposal_service,
        {"proposal": "proposal", "quote": "quote", "email": "email"}[mode],
        generate,
    )
    response = client.post(f"/api/generate/{mode}", json=valid_request)

    assert response.status_code == 200
    if mode == "email":
        assert response.json()["subject"] == "Website proposal"
    else:
        assert response.json()["deliverables"] == ["Website"]


def test_missing_model_and_malformed_response_are_reported_without_traceback(
    client, valid_request, monkeypatch
):
    from app.services.ollama_service import ModelNotFound

    async def missing(_):
        raise ModelNotFound

    monkeypatch.setattr(client.app.state.proposal_service, "quote", missing)
    response = client.post("/api/generate/quote", json=valid_request)
    assert response.status_code == 503
    assert "not installed" in response.json()["detail"]

    async def invalid(_):
        raise InvalidModelResponse

    monkeypatch.setattr(client.app.state.proposal_service, "email", invalid)
    response = client.post("/api/generate/email", json=valid_request)
    assert response.status_code == 502
    assert "valid response" in response.json()["detail"]
    assert "Traceback" not in response.text


def test_generation_rejects_empty_brief_and_oversized_request(client, valid_request):
    valid_request["brief"] = " "
    assert client.post("/api/generate/proposal", json=valid_request).status_code == 422
    response = client.post(
        "/api/generate/proposal",
        content=b"x" * 30001,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
