# PitchPilot architecture

PitchPilot is a small, stateless web application: browser UI, FastAPI, prompt
builders, and an Ollama instance running the configured open-weight model. The
default model is `gemma3:4b`; the model name and Ollama URL are configurable.

```text
Browser (form and editable proposal preview)
   |
   v
FastAPI (validation, limits, status and generation endpoints)
   |
   v
Prompt builder (mode-specific instructions + JSON-encoded request)
   |
   v
Ollama (configured local or explicitly configured remote instance)
   |
   v
Gemma (structured JSON generation)
   |
   v
JSON extraction + Pydantic response validation
   |       malformed output -> one schema-correction retry
   v
Browser renders text-only DOM nodes; user edits, copies, downloads or prints
```

## Components

- `app/main.py` serves the static interface, applies a request-body limit, and
  registers API error handling. It intentionally does not configure permissive
  cross-origin access.
- `app/api/routes.py` reports API/Ollama/model health and exposes full proposal,
  quote, and client-email generation.
- `app/models/request.py` validates the brief and project settings. Brief length
  and complete JSON request size have separate limits.
- `app/prompts/` defines the mode-specific JSON contracts and shared guardrails:
  use the supplied facts, preserve the currency and budget, and label pricing
  as an estimate when appropriate.
- `app/services/ollama_service.py` checks `/api/tags` and calls Ollama's
  `/api/generate` endpoint with JSON output mode. It handles connectivity,
  timeout, and missing-model cases.
- `app/services/proposal_service.py` extracts a JSON object, validates it
  against the mode schema, and retries one time with a correction prompt if the
  model output is malformed or incomplete.
- `app/static/` and `app/templates/` provide a plain HTML/CSS/JavaScript
  interface. Model output is inserted with `textContent`/DOM creation, not
  interpreted as HTML. Draft edits remain in browser memory.

## Data handling

The application has no database, account system, analytics, or intentional
server-side brief persistence. A request is held transiently while it is
validated and sent to the configured Ollama endpoint. If that endpoint is
remote, it receives the prompt; deployments should secure and trust that host.
Normal web-server, proxy, or host logs may still contain request metadata, so
production operators should review their own logging configuration.

## Model inference

The default is Gemma 3 4B through Ollama (`gemma3:4b`). The model identifier is
visible in the interface and selected through `OLLAMA_MODEL`. The application
does not call proprietary LLM APIs or silently switch models. Initial Ollama
and model installation requires internet access; inference can run locally
after the software and model are installed and available.
