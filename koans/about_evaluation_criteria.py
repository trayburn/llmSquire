# Koan 10: about_evaluation_criteria.py — "How Do You Know It Works?"
#
# A skill without evaluation is an opinion. Evaluation criteria make it engineering.
#
# Evaluation criteria transform subjective "looks good" into objective pass/fail.
# Stage 3 certification requires at least 3 distinct evaluation criteria.
#
# In this koan, you will write criteria and score skill outputs against them.

from llmsquire import Koan, llm
import json
import re

# A skill prompt we'll evaluate — extracts action items as JSON
ACTION_ITEM_SKILL = """## Role
You are an action item extractor.

## Task
Extract action items from meeting notes.

## Context
The input is meeting notes as plain text.

## Constraints
- Output must be valid JSON. Each action item is an object with:
  - task: string describing the action
  - owner: string name of the person responsible
  - deadline: string deadline or null
- Return a JSON array of action items and no other text."""

SAMPLE_MEETING = """Meeting: We discussed the product launch.
Alice will send the marketing email by Friday.
Bob needs to update the API documentation by next Wednesday.
Charlie should review the test suite. No specific deadline mentioned.
We also talked about the budget but no action items there."""


class AboutEvaluationCriteria(Koan):

    def test_run_a_skill_multiple_times(self):
        # Run the skill and get output
        response = llm.ask(
            messages=[
                {"role": "system", "content": ACTION_ITEM_SKILL},
                {"role": "user", "content": SAMPLE_MEETING}
            ]
        )
        # The model should produce some output
        self.assert_true(len(response.content) > 0)

    def test_criterion_valid_json(self):
        # Criterion 1: "Output must be valid JSON"
        # This is a deterministic check — no LLM judge needed.
        response = llm.ask(
            messages=[
                {"role": "system", "content": ACTION_ITEM_SKILL},
                {"role": "user", "content": SAMPLE_MEETING}
            ]
        )
        # Write the validation check. Replace _fill_ with code that
        # tries to parse the response as JSON.
        def is_valid_json(text):
            # Handle markdown-wrapped JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            try:
                json.loads(text)
                return True  # Parse the text as JSON and return True if it works
            except (json.JSONDecodeError, TypeError):
                return False

        self.assert_true(is_valid_json(response.content))

    def test_criterion_all_items_have_owner(self):
        # Criterion 2: "All action items must have an owner"
        response = llm.ask(
            messages=[
                {"role": "system", "content": ACTION_ITEM_SKILL},
                {"role": "user", "content": SAMPLE_MEETING}
            ]
        )
        # Parse the JSON and check each item has an "owner" field
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)

        # Check that every item has an "owner" key with a non-empty value
        for item in data:
            self.assert_true("owner" in item and item["owner"])  # Replace with: "owner" in item and item["owner"]

    def test_criterion_no_non_action_sentences(self):
        # Criterion 3: "No non-action sentences should be included as action items"
        # The meeting mentions "We also talked about the budget but no action items there."
        # That sentence should NOT appear as an action item.
        response = llm.ask(
            messages=[
                {"role": "system", "content": ACTION_ITEM_SKILL},
                {"role": "user", "content": SAMPLE_MEETING}
            ]
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)

        # Check that "budget" does not appear as a task in any action item
        for item in data:
            task = item.get("task", "").lower()
            self.assert_true(
                "budget" not in task,  # Replace with: "budget" not in task
                f"Non-action sentence about budget was incorrectly included: {item}"
            )

    def test_three_criteria_make_objective_evaluation(self):
        # Reflection: with 3 criteria, we can score any skill output objectively:
        # 1. Is it valid JSON?
        # 2. Does every item have an owner?
        # 3. Are non-action sentences excluded?
        #
        # Each criterion is a yes/no check. The score is X out of 3.
        # This transforms "looks good" into engineering.

        # Run the skill and score it against all 3 criteria
        response = llm.ask(
            messages=[
                {"role": "system", "content": ACTION_ITEM_SKILL},
                {"role": "user", "content": SAMPLE_MEETING}
            ]
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        score = 0
        total = 3

        # Criterion 1: valid JSON
        try:
            data = json.loads(content)
            score += 1
        except (json.JSONDecodeError, TypeError):
            data = []

        # Criterion 2: all items have owner
        if data and all("owner" in item and item["owner"] for item in data):
            score += 1

        # Criterion 3: no budget items
        if data and all("budget" not in item.get("task", "").lower() for item in data):
            score += 1

        # A good skill should pass at least 2 of 3 criteria
        self.assert_true(
            score >= 2,
            f"Skill only scored {score}/{total}. Criteria make evaluation objective."
        )