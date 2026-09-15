# Koan 9: about_skills.py — "Two Prompts, Not One"
#
# A skill is NOT a single prompt. It is TWO prompts, loaded at different times:
#
#   1. METADATA (~100 tokens): name + description, loaded at startup for
#      EVERY installed skill. The model sees all metadata and decides which
#      skill is relevant to the current task.
#
#   2. BODY (the full instructions): loaded ON DEMAND when the model decides
#      a skill is relevant. The model calls a tool (e.g., read_skill) to
#      request the full SKILL.md body. The harness executes the tool and
#      returns the body as a tool result.
#
# This is "progressive disclosure" — the model loads only what it needs,
# when it needs it. An agent with 50 installed skills doesn't load 50 full
# prompts into context. It loads 50 tiny metadata entries, then loads
# only the 1-2 skill bodies it actually needs for the current task.
#
# The SKILL.md format (originated by Anthropic, now an open standard at
# agentskills.io) formalizes this:
#
#   skill-name/
#     SKILL.md          — YAML frontmatter (metadata) + markdown body (instructions)
#     references/       — additional files loaded on demand (level 3+)
#     scripts/          — executable code the agent can run
#
# The frontmatter is the metadata. The body is the instructions.
# The model never sees the body until it asks for it.
#
# In this koan, you will implement progressive disclosure using a tool-based
# skill loading pattern. The model starts with only metadata, calls a tool
# to request the full skill body, and then processes the user's request.

from llmsquire import Koan, llm
import json

# --- Skill Registry ---
# In a real agent, installed skills live on the filesystem as SKILL.md files.
# Here we simulate them as a registry: skill name → full SKILL.md content.

INSTALLED_SKILLS = {
    "action-item-extractor": {
        "metadata": {
            "name": "action-item-extractor",
            "description": "Extract action items from meeting notes as structured JSON. Use when processing meeting notes to identify tasks, owners, and deadlines.",
        },
        "body": """## Role
You are an action item extractor.

## Task
Extract action items from meeting notes.

## Context
The input is meeting notes as plain text.

## Constraints
- Output valid JSON only.
- Return a JSON array.
- Each action item has: task (string), owner (string), deadline (string or null).
- Do not include non-action sentences (e.g., "we discussed") as action items.""",
    },
    "sentiment-analyzer": {
        "metadata": {
            "name": "sentiment-analyzer",
            "description": "Analyze the sentiment of text as positive, negative, or neutral. Use when evaluating the emotional tone of a message.",
        },
        "body": """## Role
You are a sentiment analyzer.

## Task
Classify the sentiment of the provided text.

## Context
The input is a text passage to analyze.

## Constraints
- Output exactly one word: positive, negative, or neutral.
- No other text or explanation.""",
    },
    "code-formatter": {
        "metadata": {
            "name": "code-formatter",
            "description": "Format code according to language conventions. Use when cleaning up code indentation, spacing, or style.",
        },
        "body": """## Role
You are a code formatter.

## Task
Format the provided code according to standard conventions.

## Context
The input is source code that may have inconsistent formatting.

## Constraints
- Preserve all logic — only change formatting.
- Use 4-space indentation.
- Add spaces around operators.
- Output only the formatted code, no explanations.""",
    },
}

# Build the metadata-only system prompt (what the model sees at startup)
# This is what a real agent injects as the system prompt — just the names
# and descriptions of all installed skills, NOT the full bodies.
SKILL_METADATA_PROMPT = "The following skills are available:\n"
for name, skill in INSTALLED_SKILLS.items():
    SKILL_METADATA_PROMPT += f"\n- {skill['metadata']['name']}: {skill['metadata']['description']}"
SKILL_METADATA_PROMPT += "\n\nIf a skill is relevant to the user's request, call the read_skill tool to load its full instructions."

# The read_skill tool definition — the model calls this to request a skill body
READ_SKILL_TOOL = {
    "type": "function",
    "function": {
        "name": "read_skill",
        "description": "Load the full instructions for a skill by name. Call this when you determine a skill is relevant to the current task.",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "The name of the skill to load",
                }
            },
            "required": ["skill_name"],
        },
    },
}


# The tool implementation — the harness executes this when the model calls read_skill
def read_skill_impl(skill_name: str) -> str:
    """Return the full SKILL.md body for the requested skill."""
    skill = INSTALLED_SKILLS.get(skill_name)
    if skill is None:
        return f"Error: skill '{skill_name}' not found."
    return skill["body"]


SAMPLE_MEETING = """Meeting: We discussed the product launch.
Alice will send the marketing email by Friday.
Bob needs to update the API documentation by next Wednesday.
Charlie should review the test suite. No specific deadline mentioned.
We also talked about the budget but no action items there."""


class AboutSkills(Koan):

    def test_metadata_only_is_loaded_at_startup(self):
        # LEVEL 1 of progressive disclosure: the system prompt contains ONLY
        # skill metadata (name + description). The full bodies are NOT in context.
        #
        # Verify that the metadata prompt contains skill names and descriptions
        # but does NOT contain the full instruction bodies.
        self.assert_match("action-item-extractor", SKILL_METADATA_PROMPT)
        self.assert_match("sentiment-analyzer", SKILL_METADATA_PROMPT)
        # The metadata should contain descriptions, not full instructions
        self.assert_match("Extract action items", SKILL_METADATA_PROMPT)
        # But it should NOT contain the body's RTCC structure
        self.assert_true(
            "## Role" not in SKILL_METADATA_PROMPT,
            "Metadata prompt should NOT contain skill bodies — only name + description."
        )
        self.assert_true(
            "## Constraints" not in SKILL_METADATA_PROMPT,
            "Metadata prompt should NOT contain skill bodies — only name + description."
        )

    def test_model_calls_read_skill_tool(self):
        # LEVEL 2 of progressive disclosure: the model sees the metadata,
        # decides a skill is relevant, and CALLS A TOOL to request the full body.
        #
        # This is the key mechanism. The model does NOT magically know the
        # skill instructions. It must REQUEST them via a tool call.
        response = llm.ask(
            messages=[
                {"role": "system", "content": SKILL_METADATA_PROMPT},
                {"role": "user", "content": f"Extract action items from these meeting notes:\n\n{SAMPLE_MEETING}"},
            ],
            tools=[READ_SKILL_TOOL]
        )
        # The model should call read_skill — it needs the full instructions
        self.assert_tool_called(response, "read_skill")

    def test_full_skill_body_is_returned_as_tool_result(self):
        # When the model calls read_skill, the HARNESS executes the tool
        # and returns the full skill body as a tool result.
        #
        # Then the model processes the user's request WITH the full
        # instructions in its context window.
        #
        # This is the complete progressive disclosure flow:
        #   1. System prompt: metadata only
        #   2. Model calls read_skill("action-item-extractor")
        #   3. Harness returns the full skill body
        #   4. Model uses the instructions to process the meeting notes

        # We use llm.converse() which handles the tool-call loop automatically:
        # it calls the model, sees the tool call, executes it, sends the result
        # back, and the model produces its final answer.
        response = llm.converse(
            messages=[
                {"role": "system", "content": SKILL_METADATA_PROMPT},
                {"role": "user", "content": f"Extract action items from these meeting notes:\n\n{SAMPLE_MEETING}"},
            ],
            tools=[READ_SKILL_TOOL],
            tool_implementations={"read_skill": read_skill_impl},
        )
        # The model should have loaded the skill and produced JSON output
        # containing action items with owners and deadlines
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)
        self.assert_true(isinstance(data, list))
        self.assert_true(len(data) >= 2, f"Expected 2+ action items, got {len(data)}")
        # The skill body's constraints require owner and deadline fields
        for item in data:
            self.assert_true("owner" in item, f"Missing owner in: {item}")
            self.assert_true("task" in item, f"Missing task in: {item}")

    def test_model_loads_only_relevant_skill(self):
        # Progressive disclosure means the model loads ONLY the skill it needs.
        # With 3 installed skills, it should call read_skill for the relevant
        # one (action-item-extractor) and NOT for the others.
        response = llm.ask(
            messages=[
                {"role": "system", "content": SKILL_METADATA_PROMPT},
                {"role": "user", "content": f"Extract action items from these meeting notes:\n\n{SAMPLE_MEETING}"},
            ],
            tools=[READ_SKILL_TOOL]
        )
        # Should call read_skill — but only for the relevant skill
        self.assert_tool_called(response, "read_skill")
        # Should NOT call read_skill for irrelevant skills
        # (We can't fully control what the model does, but we can check
        # it called read_skill with a relevant skill name)
        tool_calls = response.tool_calls or []
        skill_names_requested = []
        for tc in tool_calls:
            if tc.get("name") == "read_skill":
                args = json.loads(tc.get("arguments", "{}"))
                skill_names_requested.append(args.get("skill_name", ""))
        # The model should have requested the action-item-extractor skill
        self.assert_true(
            "action-item-extractor" in skill_names_requested,
            f"Expected model to request 'action-item-extractor', but requested: {skill_names_requested}"
        )

    def test_without_skill_body_output_is_unpredictable(self):
        # CONTRAST: what happens if the model does NOT load the skill body?
        # Without the full instructions, the model guesses at the format.
        # The output is unpredictable — it might not be JSON, might not
        # have owner fields, might include non-action sentences.
        #
        # This is why progressive disclosure exists: the metadata tells the
        # model WHAT a skill does, but the body tells it HOW to do it.
        # Without the body, there are no constraints on the output.
        response = llm.ask(
            messages=[
                {"role": "system", "content": SKILL_METADATA_PROMPT},
                {"role": "user", "content": f"Extract action items from these meeting notes:\n\n{SAMPLE_MEETING}"},
            ],
            # NO tools provided — the model can't call read_skill
        )
        # The model will produce SOMETHING, but we can't predict the format
        # It might be prose, a list, a table — without the skill body's
        # constraints, the output is not deterministic
        self.assert_true(len(response.content) > 0)
        # It likely won't be valid JSON because the constraints aren't loaded
        # (We don't assert this strictly because the model might guess JSON
        #  from the description, but it's not guaranteed)

    def test_skill_is_two_prompts_not_one(self):
        # THE KEY INSIGHT: A skill is TWO prompts, loaded at different times.
        #
        # Prompt 1 (metadata): "action-item-extractor: Extract action items
        #   from meeting notes as structured JSON."
        #   → ~20 tokens. Loaded for every installed skill at startup.
        #
        # Prompt 2 (body): "## Role: You are an action item extractor. ## Task:
        #   Extract action items... ## Constraints: Output valid JSON..."
        #   → ~100 tokens. Loaded ONLY when the model decides this skill is relevant.
        #
        # This is why an agent can have 50+ skills without blowing the context
        # window. 50 metadata entries = ~1000 tokens. 50 full skill bodies
        # would be ~5000+ tokens — and most wouldn't even be relevant.
        #
        # Replace _fill_ with the number of prompt stages in a skill:

        answer = _fill_  # How many prompts does a skill consist of?

        self.assert_equal(2, answer)

    def test_progressive_disclosure_saves_context(self):
        # With 3 installed skills, calculate the token savings of progressive
        # disclosure vs loading all skill bodies upfront.
        #
        # The metadata prompt is already built in SKILL_METADATA_PROMPT.
        # The full bodies are in INSTALLED_SKILLS.
        #
        # Calculate: how many characters would all 3 full skill bodies add
        # to the context window if loaded upfront vs. loading only the one
        # the model actually needs?

        # Total metadata size (loaded always)
        metadata_size = len(SKILL_METADATA_PROMPT)

        # Total size of ALL skill bodies (if loaded upfront — wasteful)
        all_bodies_size = sum(len(skill["body"]) for skill in INSTALLED_SKILLS.values())

        # Size of ONE skill body (loaded on demand — efficient)
        one_body_size = len(INSTALLED_SKILLS["action-item-extractor"]["body"])

        # The savings: we load metadata + 1 body, not metadata + all bodies
        # Replace _fill_ with the number of characters saved:
        characters_saved = _fill_
        # Calculate: all_bodies_size - one_body_size

        self.assert_true(
            characters_saved == all_bodies_size - one_body_size,
            f"With 3 skills, progressive disclosure saves {all_bodies_size - one_body_size} characters "
            f"by loading 1 body ({one_body_size}) instead of all 3 ({all_bodies_size})."
        )
        # The savings should be significant
        self.assert_true(characters_saved > 100, "Progressive disclosure should save significant context.")