from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.models.request import GenerationRequest
from app.models.response import EmailResponse, ProposalResponse, QuoteResponse
from app.services.ollama_service import (
    GenerationTimeout,
    ModelNotFound,
    OllamaUnavailable,
)
from app.services.proposal_service import InvalidModelResponse

router = APIRouter(prefix="/api")


@router.get("/health")
async def health(request: Request) -> dict:
    model_status = await request.app.state.ollama_service.model_status()
    return {
        "status": "ok",
        **model_status,
        "ai_ready": model_status["ollama"] and model_status["model_available"],
    }


@router.get("/model/status")
async def model_status(request: Request) -> dict:
    result = await request.app.state.ollama_service.model_status()
    result["status"] = (
        "ready"
        if result["ollama"] and result["model_available"]
        else "model_missing"
        if result["ollama"]
        else "unavailable"
    )
    return result


async def generate(request: Request, data: GenerationRequest, mode: str):
    if len(data.brief) > settings.max_brief_length:
        raise HTTPException(
            status_code=413,
            detail=f"Client brief exceeds the configured {settings.max_brief_length:,}-character limit.",
        )
    service = request.app.state.proposal_service
    try:
        return await getattr(service, mode)(data)
    except OllamaUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable. Start Ollama and check OLLAMA_BASE_URL.",
        ) from None
    except ModelNotFound:
        raise HTTPException(
            status_code=503,
            detail=f"Model '{settings.ollama_model}' is not installed. Pull it with Ollama before generating.",
        ) from None
    except GenerationTimeout:
        raise HTTPException(
            status_code=504,
            detail="Local model generation timed out. Try a smaller brief or increase REQUEST_TIMEOUT.",
        ) from None
    except InvalidModelResponse:
        raise HTTPException(
            status_code=502,
            detail="The model did not return a valid response after one correction attempt. Please try again.",
        ) from None


@router.post("/generate/proposal", response_model=ProposalResponse)
async def generate_proposal(
    data: GenerationRequest, request: Request
) -> ProposalResponse:
    return await generate(request, data, "proposal")


@router.post("/generate/quote", response_model=QuoteResponse)
async def generate_quote(data: GenerationRequest, request: Request) -> QuoteResponse:
    return await generate(request, data, "quote")


@router.post("/generate/email", response_model=EmailResponse)
async def generate_email(data: GenerationRequest, request: Request) -> EmailResponse:
    return await generate(request, data, "email")
