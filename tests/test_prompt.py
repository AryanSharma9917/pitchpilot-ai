from app.models.request import GenerationRequest
from app.prompts.email_prompt import build_email_prompt
from app.prompts.proposal_prompt import build_proposal_prompt
from app.prompts.quote_prompt import build_quote_prompt
from app.services.prompt_service import request_context


def test_context_is_json_encoded_and_preserves_brief(valid_request):
    request = GenerationRequest.model_validate(valid_request)
    context = request_context(request)
    assert '"brief":"Build a responsive five-page website with a contact form."' in context
    assert '"currency":"USD"' in context


def test_mode_prompts_require_structured_json_and_estimate_safety(valid_request):
    request = GenerationRequest.model_validate(valid_request)
    context = request_context(request)
    proposal = build_proposal_prompt(context)
    quote = build_quote_prompt(context)
    email = build_email_prompt(context)

    assert "Return one JSON object" in proposal
    assert "do not invent" in proposal.lower()
    assert "estimate" in quote.lower()
    assert "total_estimate" in quote
    assert "subject, greeting, body, closing, signature" in email
    for prompt in (proposal, quote, email):
        assert context in prompt
        assert "USD" in prompt
