import pytest
from pydantic import ValidationError

from app.models.request import GenerationRequest
from app.models.response import EmailResponse, ProposalResponse, QuoteResponse


def test_valid_request_schema(valid_request):
    result = GenerationRequest.model_validate(valid_request)
    assert result.project_name == "Business website"
    assert result.budget_type == "unknown"


def test_empty_or_whitespace_brief_is_rejected(valid_request):
    valid_request["brief"] = "  \n "
    with pytest.raises(ValidationError):
        GenerationRequest.model_validate(valid_request)


def test_missing_required_request_fields_are_rejected(valid_request):
    del valid_request["freelancer_name"]
    with pytest.raises(ValidationError):
        GenerationRequest.model_validate(valid_request)


def test_fixed_budget_requires_amount(valid_request):
    valid_request.update(budget_type="fixed", budget_amount=None)
    with pytest.raises(ValidationError, match="budget amount"):
        GenerationRequest.model_validate(valid_request)


def test_budget_currency_and_input_bounds_are_validated(valid_request):
    valid_request.update(budget_type="hourly", budget_amount="90/hour", currency="US")
    with pytest.raises(ValidationError):
        GenerationRequest.model_validate(valid_request)
    valid_request.update(budget_type="unknown", budget_amount=None, brief="x" * 20001)
    with pytest.raises(ValidationError):
        GenerationRequest.model_validate(valid_request)


def test_all_generation_response_schemas_validate():
    proposal = {
        "title": "Website proposal",
        "executive_summary": "A responsive site.",
        "client_needs": ["A five-page website"],
        "proposed_solution": "Build and deploy the requested pages.",
        "scope": ["Design and implementation"],
        "deliverables": ["Live website"],
        "milestones": [{"name": "Build", "duration": "4 weeks", "description": "Implementation"}],
        "pricing": [{"item": "Website", "amount": "Estimate: $3,000", "details": ""}],
        "assumptions": ["Content is supplied by the client."],
        "out_of_scope": ["Ongoing maintenance"],
        "terms": "Final terms to be agreed.",
        "next_steps": "Review the scope.",
    }
    quote = {
        "project_summary": "Build the website.",
        "deliverables": ["Live website"],
        "timeline": "4 weeks",
        "pricing": [{"item": "Website", "amount": "Estimate: $3,000", "details": ""}],
        "assumptions": ["Client supplies copy."],
        "total_estimate": "Estimate: $3,000",
    }
    email = {
        "subject": "Website proposal",
        "greeting": "Hello,",
        "body": "Please review this draft proposal.",
        "closing": "Happy to discuss.",
        "signature": "Alex",
    }
    assert ProposalResponse.model_validate(proposal).title == "Website proposal"
    assert QuoteResponse.model_validate(quote).total_estimate == "Estimate: $3,000"
    assert EmailResponse.model_validate(email).subject == "Website proposal"


def test_response_missing_required_field_is_rejected():
    with pytest.raises(ValidationError):
        QuoteResponse.model_validate({"project_summary": "Incomplete"})


def test_response_rejects_blank_list_items_and_unexpected_fields():
    with pytest.raises(ValidationError):
        QuoteResponse.model_validate({
            "project_summary": "A project",
            "deliverables": ["   "],
            "timeline": "2 weeks",
            "pricing": [{"item": "Build", "amount": "$500", "details": ""}],
            "assumptions": ["Client supplies copy."],
            "total_estimate": "$500",
        })

    request = {
        "subject": "Project",
        "greeting": "Hello,",
        "body": "Here is the draft.",
        "closing": "Regards,",
        "signature": "Alex",
        "html": "<script>alert(1)</script>",
    }
    with pytest.raises(ValidationError):
        EmailResponse.model_validate(request)
