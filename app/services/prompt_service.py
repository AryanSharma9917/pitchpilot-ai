import json

from app.models.request import GenerationRequest


def request_context(request: GenerationRequest) -> str:
    return json.dumps(
        request.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
    )
