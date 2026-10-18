# PitchPilot

**Open-source AI proposal and quote generator for freelancers.**

Turn a rough client brief into a professional proposal in minutes, with model
inference through locally running Gemma and Ollama. No proprietary cloud LLM
API is required.

> Local inference is not the same as a blanket offline or privacy guarantee.
> Installing Ollama and downloading the model requires internet access. A
> remotely configured Ollama host receives the prompt.

## The problem

Freelancers repeatedly translate informal client requests into a project scope,
deliverables, milestones, pricing, assumptions, and client communication.
PitchPilot turns that routine drafting into a structured, editable starting
point while leaving the freelancer in control of the final proposal.

## What it does

- Generates a full proposal, quick quote, or client-facing email.
- Uses a configurable Ollama model, defaulting to Gemma 3 4B (`gemma3:4b`).
- Requests structured JSON and validates it with mode-specific Pydantic schemas.
- Makes one correction attempt if model output is malformed or incomplete.
- Displays API, Ollama, and configured-model readiness separately.
- Lets you edit generated copy, copy it, download Markdown, or print / save to
  PDF using your browser.
- Keeps draft edits in browser memory; the app has no account, database, or
  analytics.

Pricing generated without a supplied budget is explicitly labeled as an
estimate. Review scope, rates, taxes, and contract terms before sending any
draft to a client.

## Screenshots

Screenshots have not yet been captured from a real application/model run. See
the [demo and screenshot checklist](docs/demo-checklist.md) for genuine capture
targets. No placeholder images are presented as product screenshots.

## How Gemma is used

The generation path in `app/services/ollama_service.py` sends the mode-specific
prompt to the configured Ollama `/api/generate` endpoint with the configured
model name and JSON output mode. The default model is Gemma 3 4B, installed with
`ollama pull gemma3:4b`. The UI reports the configured model name and whether
Ollama can see it. There is no proprietary cloud-model fallback.

### Why Gemma and local inference?

The project is intended for client work, where a brief may include private
business details. Using Gemma through a user's local Ollama instance makes
local inference possible without a proprietary LLM API requirement. The choice
also makes the model setup and generation path inspectable. It does not claim
that Gemma is better than another model or make an unmeasured performance
claim.

Local inference has tradeoffs: hardware and storage requirements, model
download size, inference speed that depends on the machine, output quality that
may differ from hosted models, and more involved installation. A remote Ollama
configuration sends prompts to that host.

## Privacy model

- The browser sends a brief to this FastAPI application for generation.
- The application forwards the request to the configured Ollama endpoint.
- No client-brief database, account system, or analytics are included; the app
  does not intentionally persist briefs.
- With Ollama running on your own computer, client data does not need to go to
  a proprietary cloud LLM provider.
- If `OLLAMA_BASE_URL` points to another machine or service, that endpoint
  receives the prompt. Review its access controls, network security, and
  logging.
- Model/software downloads require internet access. Once installed, inference
  can run locally if the model and Ollama are available.

The application does not control host-level, reverse-proxy, or deployment
logging. Do not use confidential client data in a shared deployment unless its
operator and Ollama host are trusted.

## Requirements

- Python 3.10 or newer.
- [Ollama](https://ollama.com/download) installed and running.
- A Gemma model available to Ollama. Default: Gemma 3 4B, `gemma3:4b`.
- Hardware capable of running the selected model. Actual speed and resource
  use depend on the host; no benchmark is claimed.

## Install and run

### 1. Install Ollama and Gemma

Install Ollama for your platform from [ollama.com/download](https://ollama.com/download),
then start its local service. Pull the default model:

```bash
ollama pull gemma3:4b
```

Check that it is available:

```bash
ollama list
```

### 2. Install PitchPilot

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate the environment with:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The defaults in `.env.example` use `gemma3:4b` and
`http://localhost:11434`. Edit `.env` to change configuration. The app reads
`.env` at startup; environment variables already set in the process take
precedence.

Available settings:

| Variable | Default | Meaning |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama HTTP endpoint |
| `OLLAMA_MODEL` | `gemma3:4b` | Exact configured model tag |
| `REQUEST_TIMEOUT` | `300` | Ollama generation timeout in seconds |
| `MAX_BRIEF_LENGTH` | `12000` | Maximum client-brief characters (up to 20,000) |
| `MAX_REQUEST_BYTES` | `30000` | Maximum generation JSON body size |

The UI has a 12,000-character brief limit matching the default. The backend
enforces the configured brief limit and a separate full-request size limit.
Limits are also bounded by the application schema.

### 3. Start the application

With Ollama running:

```bash
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). API documentation is at
[http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs).

If Ollama is unavailable, the web application still starts and the status
indicator explains that Ollama cannot be reached. If the model is missing, the
status reports that separately; install the configured model with
`ollama pull gemma3:4b` (or substitute your configured model tag).

### Example workflow

1. Enter the client, project, timeline, and a brief. Use real or sanitized
   client information.
2. Choose a known fixed/hourly budget or select unknown / needs estimate.
3. Set your name, expertise, tone, and optional constraints.
4. Choose Full proposal, Quick quote, or Client email and generate.
5. Check every claim, amount, timeline, assumption, and term. Use **Edit** to
   revise copy in place.
6. Copy the draft, download Markdown, or use **Print / save PDF** in the browser.

The [fictional sample brief](examples/sample_client_brief.md) and
[illustrative sample output](examples/sample_output.md) are examples only, not
outputs from a claimed model run or client engagement.

## API

All generation endpoints accept the same JSON request. The `brief`,
`client_name`, `project_name`, `project_type`, `timeline`, and
`freelancer_name` fields are required. For `budget_type` set `fixed` or
`hourly`, provide `budget_amount`; for `unknown`, omit the amount. Currency is
a three-letter uppercase code.

- `GET /api/health` — API health plus Ollama reachability and model availability.
- `GET /api/model/status` — `ready`, `unavailable`, or `model_missing`.
- `POST /api/generate/proposal` — full proposal response.
- `POST /api/generate/quote` — quick quote response.
- `POST /api/generate/email` — client email response.

Generation responses are JSON objects validated against the relevant
`ProposalResponse`, `QuoteResponse`, or `EmailResponse` schema. Errors use
understandable HTTP responses (including 413 for oversized input, 422 for
invalid form data, 502 for invalid model output, 503 for unavailable Ollama or
missing model, and 504 for generation timeout). Stack traces are not returned
to the browser.

## Testing

Install the same dependencies above, then run:

```bash
pytest
```

The suite uses mocked model behavior and does not download weights or need a
live Ollama service. It covers health readiness, request/response validation,
prompt construction, JSON parsing and correction retry, pricing labels, and
unavailable/missing-model errors.

## Docker

The repository includes a web-application `Dockerfile` and intentionally no
Docker Compose file. The web container does not install or manage Ollama or
download model weights. Ollama networking varies by host:

On macOS/Windows with Docker Desktop, `host.docker.internal` normally reaches
the host:

```bash
docker build -t pitchpilot .
docker run --rm -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=gemma3:4b pitchpilot
```

On Linux, add the host gateway mapping if supported by the Docker version:

```bash
docker run --rm -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=gemma3:4b pitchpilot
```

Configure the host Ollama service to accept the required container connection
only if you understand and intentionally permit that network access. Do not
expose Ollama to an untrusted network. Native Python setup is the simplest
local workflow.

## Project structure

```text
app/
  api/routes.py             Health and generation endpoints
  config.py                 Environment and .env configuration
  models/                   Request and response contracts
  prompts/                  Mode-specific prompt builders
  services/                 Ollama, prompt and generation logic
  static/css/               Responsive styles and print layout
  static/js/                Form, status, rendering and export behavior
  templates/index.html      Semantic application interface
tests/                      Mocked API, validation and prompt tests
examples/                   Fictional client brief and illustrative output
docs/                       Architecture, demo, testing and submission docs
```

## Limitations

- Generated text, scope, estimates, and timelines may be inaccurate. A
  freelancer must review and approve all content.
- There is no built-in PDF library; use the browser's print dialog and
  print-specific layout to save a PDF.
- Output quality and generation time depend on the configured model and host
  hardware; they have not been benchmarked here.
- Local inference is possible but not guaranteed by this application. A remote
  Ollama URL sends prompts to the configured remote service.
- No user study or product-market-fit testing has been completed as part of the
  repository implementation.

## Security and privacy considerations

PitchPilot has no authentication and is intended as a local tool. Do not expose
it or Ollama to an untrusted network without adding deployment-appropriate
access control and transport security. The application validates bounded
inputs, does not use dynamic file paths for downloads, renders generated text
through DOM text nodes, and does not store briefs in a database or browser
localStorage. Review logging and reverse-proxy behavior for any deployment.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run the tests, document behavior
changes, and do not add cloud LLM fallbacks, analytics, brief persistence, or
secrets.

## Hacktoberfest 2026

PitchPilot is being prepared as a new project for the Hacktoberfest
Open-Source AI Challenge Week 2: Side Hustle. Its intended Gemma category is
**Best Use of Gemma** because Gemma is used in the working Ollama generation
path. Challenge eligibility and acceptance have not been independently
verified. See the [DEV submission draft](docs/dev-submission-draft.md) and
[demo checklist](docs/demo-checklist.md).

The repository was started during the Week 2 build window. Work completed after
the submission deadline, if any, should be identified here and in the DEV post
as required by the challenge rules.

## Acknowledgements

- The Ollama project for local model serving.
- The Gemma model family and its maintainers.
- FastAPI and Pydantic for the API and validation foundation.
- Hacktoberfest and the open-source contributors who make projects like this
  possible.

## License

MIT. See [LICENSE](LICENSE).
