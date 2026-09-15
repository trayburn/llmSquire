# Koan 10: about_rtcc.py — "Readable Prompts"
#
# RTCC (Role, Task, Context, Constraints) is a prompt structure that
# makes prompts easier for HUMANS to read, review, and maintain.
#
# There is nothing magical about the structure. Adding "## Role" to your
# prompt does not make the model smarter. The model reads the same words
# whether they're in a paragraph or under a heading.
#
# So why use it? Because prompts are code. They are written once and
# read many times — by you, by your team, by auditors, by the person
# who has to debug why the output changed. RTCC makes the prompt scannable:
# a reviewer can find the constraints in 2 seconds instead of reading
# a wall of prose.
#
# The purpose of RTCC is readability and maintainability, not magic.
# A well-structured prompt is easier to review, easier to test, and
# easier to change. That's it. That's the whole point.
#
# In this koan, you will write prompts with explicit RTCC labels and
# see how the structure makes the prompt's intent clear to human readers.

from llmsquire import Koan, llm


# An unstructured prompt — the same information, but as a wall of prose.
# The model can handle this fine. The problem is that a HUMAN reviewer
# has to read every word to find the constraints.
UNSTRUCTURED_PROMPT = """You are a meeting notes summarizer. I need you to read meeting notes and produce a summary. The meeting notes will be provided as plain text. The summary should be exactly 2 sentences. Don't add any introduction or conclusion. Just the summary."""


# The same prompt with RTCC structure — same content, scannable structure.
# A human reviewer can find the constraints ("2 sentences", "no intro")
# in seconds without reading the whole prompt.
RTCC_PROMPT = """## Role
You are a meeting notes summarizer.

## Task
Read meeting notes and produce a summary.

## Context
The input is meeting notes provided as plain text.

## Constraints
- The summary must be exactly 2 sentences.
- Do not add an introduction or conclusion.
- Output only the summary text."""


SAMPLE_MEETING = """Meeting: We discussed the product launch timeline.
Alice will finalize the marketing plan by Friday.
Bob raised concerns about the API stability before the launch.
We agreed to delay the launch by one week to address Bob's concerns."""


class AboutRtcc(Koan):

    def test_unstructured_prompt_works(self):
        # The unstructured prompt works fine — the model can parse prose.
        # This is the key point: RTCC doesn't make the prompt "better" for
        # the model. The model reads the same words either way.
        response = llm.ask(
            messages=[
                {"role": "system", "content": UNSTRUCTURED_PROMPT},
                {"role": "user", "content": SAMPLE_MEETING}
            ]
        )
        self.assert_true(len(response.content) > 0)

    def test_rtcc_prompt_produces_same_quality(self):
        # The RTCC-structured prompt produces the same quality output.
        # The model doesn't perform better because of the headings.
        # The headings are for HUMANS, not for the model.
        response = llm.ask(
            messages=[
                {"role": "system", "content": RTCC_PROMPT},
                {"role": "user", "content": SAMPLE_MEETING}
            ]
        )
        self.assert_true(len(response.content) > 0)
        # Both prompts should produce a 2-sentence summary
        sentences = [s for s in response.content.strip().split(".") if s.strip()]
        self.assert_true(
            len(sentences) <= 3,
            f"Expected ~2 sentences, got {len(sentences)}. RTCC doesn't change model behavior."
        )

    def test_role_tells_the_model_who_it_is(self):
        # ## Role defines the model's identity for this task.
        # It shapes tone, perspective, and expertise level.
        # A clear role is like a job title — it sets expectations.
        response = llm.ask(
            messages=[
                {"role": "system", "content": _fill_},
                # Write a prompt with just the Role section:
                # ## Role
                # You are a pirate. Speak like a pirate in all responses.
                {"role": "user", "content": "Tell me about the sea."}
            ]
        )
        # The role should produce pirate-like language
        pirate_words = ["arr", "matey", "ahoy", "ye", "aye", "ship",
                       "sea", "sailor", "treasure", "captain", "hoist",
                       "landlubber", "buccaneer", "parrot", "rum"]
        content_lower = response.content.lower()
        found = [w for w in pirate_words if w in content_lower]
        self.assert_true(
            len(found) >= 1,
            f"Expected pirate language from the role. Found: {found}. Response: {response.content[:200]}..."
        )

    def test_task_tells_the_model_what_to_do(self):
        # ## Task defines the specific action the model should take.
        # Without a clear task, the model guesses what you want.
        # "Help me with meeting notes" is not a task — it's a topic.
        # "Extract action items from meeting notes" is a task.
        response = llm.ask(
            messages=[
                {"role": "system", "content": _fill_},
                # Write a prompt with Role and Task sections:
                # ## Role
                # You are an action item extractor.
                # ## Task
                # Extract action items from meeting notes, identifying
                # the task, the owner, and the deadline for each.
                {"role": "user", "content": "Alice will send the email by Friday. Bob needs to update the docs."}
            ]
        )
        # With a clear task, the model should identify action items
        self.assert_match("Alice", response.content)
        self.assert_match("Bob", response.content)

    def test_context_tells_the_model_what_it_has(self):
        # ## Context defines what information the model has access to.
        # This is where you describe the input format, the source of data,
        # and any background the model needs.
        #
        # Context is NOT the input itself (that goes in the user message).
        # Context describes the input: "The input is meeting notes as
        # plain text" tells the model what format to expect.
        response = llm.ask(
            messages=[
                {"role": "system", "content": _fill_},
                # Write a prompt with Role, Task, and Context sections:
                # ## Role
                # You are a JSON formatter.
                # ## Task
                # Convert the provided text into a JSON object with
                # "summary" and "word_count" fields.
                # ## Context
                # The input is a single paragraph of plain text.
                # The word count is the number of whitespace-separated tokens.
                {"role": "user", "content": "The quick brown fox jumps over the lazy dog."}
            ]
        )
        # The context told the model the input format, so it should
        # produce valid JSON with a word count
        import json
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        data = json.loads(content)
        self.assert_true("summary" in data)
        self.assert_true("word_count" in data)

    def test_constraints_tell_the_model_what_rules_to_follow(self):
        # ## Constraints define the rules the model must follow.
        # Constraints are what make output predictable and testable.
        # Without constraints, the model produces reasonable but
        # unpredictable output. With constraints, you can write
        # evaluation criteria (see Koan 11).
        #
        # Constraints are the most important section for evaluation.
        # Every constraint is a potential test case.
        response = llm.ask(
            messages=[
                {"role": "system", "content": _fill_},
                # Write a prompt with all 4 RTCC sections:
                # ## Role
                # You are a technical summarizer.
                # ## Task
                # Summarize technical articles in bullet points.
                # ## Context
                # The input is a technical article as plain text.
                # ## Constraints
                # - Output exactly 3 bullet points.
                # - Each bullet point starts with "- ".
                # - Each bullet point is exactly one sentence.
                # - No introduction or conclusion.
                {"role": "user", "content": "Container orchestration manages deployment, scaling, and operations of containerized applications. Kubernetes is the most popular orchestrator. It uses pods as the smallest deployable units. Services provide network abstraction. Deployments manage rolling updates and rollbacks."}
            ]
        )
        # The constraints make this testable:
        # - Must have bullet points
        self.assert_match("-", response.content)
        # - Must have ~3 bullet points (not 1, not 10)
        lines = [l for l in response.content.strip().split("\n") if l.strip().startswith("-")]
        self.assert_true(
            len(lines) >= 2,
            f"Expected 2+ bullet points (constraint: exactly 3). Got {len(lines)}."
        )

    def test_rtcc_is_for_humans_not_the_model(self):
        # THE KEY INSIGHT: RTCC structure does not make the model perform
        # better. It makes the PROMPT easier for humans to read, review,
        # and maintain. The model reads the same words either way.
        #
        # The value of RTCC is:
        # 1. A reviewer can find the constraints in 2 seconds (scan for ## Constraints)
        # 2. A team member can update the task without reading the whole prompt
        # 3. An auditor can verify all constraints are present
        # 4. A test engineer can turn each constraint into an evaluation criterion
        #
        # None of that benefits the model. All of it benefits the humans
        # who have to maintain the prompt over time.
        #
        # Replace _fill_ with the correct answer:
        # What is the PRIMARY purpose of RTCC structure?
        # A) Making the model produce better output
        # B) Making the prompt easier for humans to read and maintain
        # C) Reducing token count
        # D) Improving tool calling accuracy

        answer = _fill_  # "A", "B", "C", or "D"

        self.assert_equal("B", answer)

    def test_every_constraint_is_a_test_case(self):
        # The practical value of RTCC: every line under ## Constraints
        # is a potential evaluation criterion. If you write 4 constraints,
        # you can write 4 test cases. This is why RTCC enables EDD
        # (Evaluation-Driven Development, Koan 12).
        #
        # Look at the RTCC_PROMPT defined at the top of this file.
        # It has 3 constraints:
        # 1. "The summary must be exactly 2 sentences."
        # 2. "Do not add an introduction or conclusion."
        # 3. "Output only the summary text."
        #
        # Each of those can be tested:
        # 1. Count sentences — should be 2
        # 2. Check for intro/conclusion phrases
        # 3. Check that output is just the summary (no extra text)
        #
        # Replace _fill_ with the number of constraints in RTCC_PROMPT:

        constraint_count = _fill_  # Count the ## Constraints items in RTCC_PROMPT

        self.assert_equal(3, constraint_count)