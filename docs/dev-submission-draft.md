# PitchPilot: drafting freelancer proposals with local Gemma

This is a submission for the Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle

> Before publishing: replace the demo placeholder with a real public demo or
> video, add genuine screenshots, and remove any optional section you cannot
> support. Do not publish this note as part of the entry.

## What I Built

PitchPilot is an open-source proposal and quote generator for freelancers. It
helps developers, designers, consultants, and other independent professionals
turn a rough client brief into a structured proposal, a concise estimate, or a
client-facing email.

The problem is repetitive but consequential: a freelancer has to translate an
informal request into scope, milestones, pricing, assumptions, and a clear next
step. A draft that is easy to review and edit can make that work less tedious,
while leaving the freelancer responsible for the final offer. This is a
plausible paid-tool problem because proposal preparation is part of paid
professional work, but willingness to pay has not been tested with users.

## Demo

[DEMO URL TO BE ADDED]

## Code

[PitchPilot on GitHub](https://github.com/AryanSharma9917/pitchpilot-ai)

## How I Built It

The interface is semantic HTML, CSS, and vanilla JavaScript. A small FastAPI
application validates the form with Pydantic, assembles a prompt for the chosen
mode, and sends it to the configured Ollama instance. The default model is
Gemma 3 4B (`gemma3:4b`).

The model is asked for JSON, but generation is not trusted as a schema
guarantee. PitchPilot extracts a JSON object, validates it against the response
model for proposals, quotes, or emails, and makes one correction attempt when
the first output is malformed or incomplete. The UI builds readable sections
from the validated data and inserts model-provided text as text, not HTML.
Freelancers can edit the draft before copying, downloading Markdown, or using
the browser print dialog.

The first implementation challenge was treating structured output as a
failure-prone boundary rather than assuming that a JSON request always yields
complete, valid JSON. Explicit schemas and a bounded retry make that boundary
visible and testable. Ollama connectivity and model availability are checked
separately, so a running API is not presented as ready AI when the model is
missing.

Local inference suits this use because client briefs can contain confidential
business context. With Ollama running on the user's own computer, a proprietary
cloud LLM API is not required. This is not a blanket offline or privacy
guarantee: initial software/model downloads require internet, a remote Ollama
host receives the prompt, and operators must account for their own network and
logging setup.

The tradeoffs are meaningful: a local model needs compatible hardware and
storage, model downloads take time and bandwidth, generation speed depends on
the machine, output quality can differ from hosted services, and setup is more
involved than a hosted chat product. Pricing and timelines are drafts, not
commercial advice; users must verify the scope, amounts, taxes, and terms.

This build uses FastAPI, Pydantic, Ollama, and Gemma with mocked tests that do
not need model weights. Real Gemma generation, screenshots, and first-user
feedback should only be added after those activities actually happen.

## Why Does Open Innovation Matter?

Open innovation gives users and contributors more control over model choice and
where inference runs. PitchPilot's generation path uses Ollama and the
configured open-weight model rather than requiring a proprietary LLM API.
Running inference locally can avoid sending a brief to such a provider and can
change the cost model, but the computer, electricity, storage, and setup still
have costs. A user can configure another Ollama-compatible model, while the
default and intended workflow use Gemma.

The same openness brings tradeoffs: hardware requirements, model download
size, local inference speed, variation in output quality, and setup complexity.
Local execution alone does not guarantee confidentiality if the Ollama endpoint
is remote or the machine is managed in a way that records prompts.

## My Agent Session

[OPTIONAL - ADD REAL SESSION OR REMOVE]

## My First User

[ADD ONLY AFTER REAL USER TESTING]

## Prize Categories

- Best Use of Gemma
- Best Use of GitHub Copilot (include only if you describe how Copilot was used)

#devchallenge #hf26challenge
