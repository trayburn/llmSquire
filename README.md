# llmSquire

Koans for mastering LLM invocation, harness creation, skills, and evaluation-driven development.

## What Is This?

llmSquire is a hands-on learning journey in the tradition of Ruby Koans and Squire (C# Kihon). You progress through a sequence of exercises — each one failing until you provide the correct implementation. The runner stops at the first failure and points you to the exact file and line to meditate on.

By the end, you will have internalized through your own hands-on work:

- LLMs are stateless — every call is a fresh start, and context management is your job
- Tool calling is the core primitive — interesting workers emerge from constraining what tools are available
- A skill is TWO prompts (metadata + body) loaded via progressive disclosure, not one
- RTCC (Role, Task, Context, Constraints) makes prompts readable for humans, not magical for models
- Evaluation-driven development (EDD) is how you know your worker actually works
- Guardrails are always deterministic code — if you need judgment, that's an adversarial agent
- Complex workflows decompose into individually testable steps, wired together by a harness that executes

## Quick Start

### Prerequisites

- Python 3.9+
- An API key for an OpenAI-compatible LLM provider (Ollama Cloud, Fireworks AI, or any compatible endpoint)

### Setup

```bash
# Clone
git clone https://github.com/trayburn/llmSquire.git
cd llmSquire

# Install dependencies
pip install -e ".[dev]"

# Configure your API key
cp .env.example .env
# Edit .env with your API key and provider settings
```

Alternatively, use the setup script (configures Ollama Cloud):

```bash
bash setup-api-key.sh
```

### Run the Koans

```bash
python -m llmsquire
```

The runner executes each koan in order. When a koan fails, it stops and shows you:

```
Thinking AboutStatelessness
  test_the_model_does_not_remember has damaged your karma.

You have not yet reached enlightenment ...
Expected 'don' in response, but it was not found.

Please meditate on the following code:
./koans/about_statelessness.py:33

mountains are merely mountains
```

Open the file it points you to, find the `_fill_` blanks, replace them with the correct values, and run again. That's the loop — fail, meditate, fix, progress.

## Sequence Diagrams

After each exercise, the runner prints a path to an HTML sequence diagram. Open it in any browser to see exactly what happened:

- Every API call and response (full payloads, not summaries)
- Every tool call the model requested and every result the harness returned
- The growing context window at each round trip (expandable panels)
- Token counts and timing for each step

The diagrams show three lifelines: **Learner / Koan / Harness** (left), **LLM** (center), and **Tools** (right). Tool execution arrows span the full width from Harness to Tools — because the LLM never touches tools. It requests tool calls; the harness executes them.

## The Path

19 koans across 5 phases:

### Phase 1: Foundations
1. **about_invocation** — your first LLM call, the request/response cycle
2. **about_statelessness** — the model has no memory between calls
3. **about_context_window** — the context is finite; what you leave out matters
4. **about_system_prompts** — setting the model's role and constraints

### Phase 2: Tool Calling
5. **about_tool_definitions** — defining tools with JSON schema
6. **about_tool_calling** — the full tool-call loop (you execute, not the model)
7. **about_constraining_tools** — limiting tools shapes worker behavior
8. **about_context_composition** — what the model sees after tool calls, and why synthetic context changes everything about testing

### Phase 3: Skills and Prompts
9. **about_skills** — a skill is two prompts (metadata + body), loaded via progressive disclosure using the SKILL.md open standard
10. **about_rtcc** — RTCC (Role, Task, Context, Constraints) is for human readability, not model magic
11. **about_evaluation_criteria** — objective pass/fail criteria transform "looks good" into engineering
12. **about_edd_cycle** — Red/Green/Refactor for prompts with majority-vote evaluation

### Phase 4: Workflows
13. **about_decomposition** — breaking complex workflows into individually testable steps
14. **about_guardrails** — deterministic code validation between steps (never LLM-based)
15. **about_adversarial_review** — LLM agents that actively find problems, not confirm quality

### Phase 5: Harness
16. **about_harness_basic** — a script that executes the workflow end-to-end
17. **about_harness_failure** — retry logic and failure traceability
18. **about_harness_audit** — per-step model/token/cost logging and success rates
19. **about_punch_out** — human evacuation points that cannot be bypassed

## Project Structure

```
llmSquire/
├── README.md                       # You are here
├── PRD.md                          # Full product requirements document
├── pyproject.toml                  # Package config, dependencies
├── .env.example                    # API key configuration template
├── setup-api-key.sh                # Ollama Cloud setup helper
├── llmsquire/                      # The harness (you don't edit these)
│   ├── sensei.py                   # Test runner — stops at first failure
│   ├── koan.py                     # Base class, _fill_ sentinel, assertions
│   ├── llm_client.py               # OpenAI-compatible LLM client with tracing
│   ├── proxy.py                    # Module-level llm proxy (delegates to per-test client)
│   ├── diagram.py                  # HTML sequence diagram generator
│   └── path_to_enlightenment.py    # Ordered list of koan modules
├── koans/                          # The exercises (you edit these)
│   ├── about_invocation.py
│   ├── about_statelessness.py
│   └── ... (19 koan files)
├── diagrams/                       # Auto-generated sequence diagrams (HTML)
└── tests/                          # Tests for the harness itself
```

You only ever edit files in `koans/`. The `llmsquire/` directory is the grading infrastructure — you don't need to read it.

## API Configuration

The client supports any OpenAI-compatible endpoint. Configure via `.env`:

**Ollama Cloud:**
```
LLMSQUIRE_API_BASE=https://api.ollama.com/v1
LLMSQUIRE_MODEL=deepseek-v4-flash:cloud
LLMSQUIRE_API_KEY=your-key-here
```

**Fireworks AI:**
```
LLMSQUIRE_API_BASE=https://api.fireworks.ai/inference/v1
LLMSQUIRE_MODEL=accounts/fireworks/models/deepseek-v4-flash-0731
LLMSQUIRE_API_KEY=your-key-here
```

Any other OpenAI-compatible provider works the same way — set the base URL, model name, and API key.

## Copyright

© 2026 Improving. All rights reserved.

This material is proprietary to Improving. Permission is granted to all current employees of Improving to use, copy, and run this software and associated learning materials for their own professional development and internal training purposes.

No open-source license is granted. This software and its content may not be redistributed, published, modified for distribution, or made available to parties other than current Improving employees without explicit written permission from Improving.

## Acknowledgments

llmSquire follows the tradition of Ruby Koans and Squire (C# Kihon). The SKILL.md progressive disclosure pattern is an open standard originated by Anthropic and adopted across developer harnesses. The Stage 3/4 certification concepts are drawn from the Improving Intelligence Operating System.