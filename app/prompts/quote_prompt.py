from app.prompts.proposal_prompt import PROPOSAL_INSTRUCTIONS


def build_quote_prompt(context: str) -> str:
    return (
        f"{PROPOSAL_INSTRUCTIONS}\n\n"
        "Create a concise quick quote and return ONLY valid JSON. Exact keys: "
        "project_summary:string, deliverables:string[], timeline:string, "
        "pricing:array of objects {item:string, amount:string, details:string}, "
        "assumptions:string[], total_estimate:string. Use short values and mark estimates explicitly.\n\n"
        f"PROJECT DETAILS (JSON):\n{context}"
    )
