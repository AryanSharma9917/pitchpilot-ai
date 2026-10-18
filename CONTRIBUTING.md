# Contributing to PitchPilot

Thanks for helping make PitchPilot more useful for independent professionals.

## Set up locally

1. Install Python 3.10 or newer and Ollama.
2. Create and activate a virtual environment.
3. Install `requirements.txt`.
4. Pull the configured Gemma model (by default, `ollama pull gemma3:4b`).
5. Copy `.env.example` to `.env` if you need to change the defaults.
6. Run `uvicorn app.main:app --reload` and open `http://127.0.0.1:8000`.

## Before opening a pull request

- Run `pytest`.
- Keep new AI output typed and validated; do not render model-generated HTML.
- Do not add cloud LLM fallbacks, analytics, client-brief persistence, or secrets.
- Update the README or architecture docs when behavior or setup changes.
- Include a focused description of the change and how you tested it.

Issues and pull requests should describe any behavior that needs a local Ollama
instance separately from behavior covered by mocked tests.
