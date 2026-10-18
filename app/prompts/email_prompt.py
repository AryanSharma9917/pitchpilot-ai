from app.prompts.proposal_prompt import PROPOSAL_INSTRUCTIONS


def build_email_prompt(context: str) -> str:
    return (
        f"{PROPOSAL_INSTRUCTIONS}\n\n"
        "Write a brief client-facing email and return ONLY valid JSON. Exact keys: "
        "subject, greeting, body, closing, signature. Keep body to 2 sentences and "
        "do not include Markdown or comments.\n\n"
        f"PROJECT DETAILS (JSON):\n{context}"
    )
