import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.models.request import GenerationRequest
from app.models.response import EmailResponse, ProposalResponse, QuoteResponse
from app.services.ollama_service import OllamaService
from app.services.prompt_service import request_context


ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class InvalidModelResponse(Exception):
    pass


def extract_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    decoder = json.JSONDecoder()
    first_object = cleaned.find("{")
    while first_object != -1:
        candidate = cleaned[first_object:]
        try:
            value, _ = decoder.raw_decode(candidate)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass
        last_object = cleaned.rfind("}")
        if last_object > first_object:
            candidate = cleaned[first_object : last_object + 1]
            try:
                value = json.loads(candidate)
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(value, dict):
                    return value
        first_object = cleaned.find("{", first_object + 1)
    raise ValueError("No valid JSON object was found")


def normalize_response_payload(data: dict) -> dict:
    for key in ["client_needs", "scope", "deliverables", "assumptions", "out_of_scope"]:
        if key in data and isinstance(data[key], str):
            data[key] = [data[key]]
    for key in ["milestones", "pricing"]:
        if key in data and isinstance(data[key], dict):
            data[key] = [data[key]]
    for key in ["deliverables", "assumptions"]:
        if key in data and data[key] is None:
            data[key] = []
    return data


class ProposalService:
    def __init__(self, ollama: OllamaService):
        self.ollama = ollama

    async def _generate(
        self,
        request: GenerationRequest,
        prompt_builder,
        response_model: type[ResponseModel],
    ) -> ResponseModel:
        prompt = prompt_builder(request_context(request))
        correction = ""
        last_error = "The model returned invalid JSON."
        for attempt in range(2):
            raw = await self.ollama.generate(prompt + correction)
            try:
                data = normalize_response_payload(extract_json_object(raw))
                result = response_model.model_validate(data)
                if request.budget_type == "unknown":
                    for item in getattr(result, "pricing", []):
                        if "estimate" not in item.amount.lower():
                            item.amount = f"Estimate: {item.amount}"
                    if isinstance(result, QuoteResponse) and "estimate" not in result.total_estimate.lower():
                        result.total_estimate = f"Estimate: {result.total_estimate}"
                return result
            except (ValueError, ValidationError) as exc:
                last_error = str(exc)
                if attempt == 0:
                    correction = (
                        "\n\nCORRECTION: Your previous response did not satisfy the "
                        "required JSON schema. Return a corrected complete JSON object "
                        "only. Validation issue: " + last_error[:1500]
                    )
        raise InvalidModelResponse from None

    async def proposal(self, request: GenerationRequest) -> ProposalResponse:
        from app.prompts.proposal_prompt import build_proposal_prompt

        return await self._generate(request, build_proposal_prompt, ProposalResponse)

    async def quote(self, request: GenerationRequest) -> QuoteResponse:
        from app.prompts.quote_prompt import build_quote_prompt

        return await self._generate(request, build_quote_prompt, QuoteResponse)

    async def email(self, request: GenerationRequest) -> EmailResponse:
        from app.prompts.email_prompt import build_email_prompt

        return await self._generate(request, build_email_prompt, EmailResponse)
