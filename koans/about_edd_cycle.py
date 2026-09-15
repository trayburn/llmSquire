# Koan 11: about_edd_cycle.py — "Red, Green, Refactor for Prompts"
#
# EDD applies TDD discipline to prompt engineering:
#   Red:    Write criteria, run the skill, see it fail
#   Green:  Iterate on the prompt until all criteria pass
#   Refactor: Remove dead-weight instructions (load-bearing principle)
#
# Non-determinism is real. A single evaluation run is never sufficient.
# The harness runs each evaluation 3 times and takes the majority vote.
# This is itself a lesson: non-determinism requires statistical discipline.
#
# In this koan, you will run the EDD cycle on a skill that uses tools,
# using synthetic context (from Koan 8) instead of file fixtures.

from llmsquire import Koan, llm
import json

# --- The Skill Under Test ---
# This skill reads three project files and produces a status summary.
# It's deliberately weak at first — you will improve it through EDD.

WEAK_SKILL_PROMPT = """## Role
You help with project status.

## Task
Summarize the project status.

## Context
The input may include project files.

## Constraints
- Provide a useful response."""

STRONG_SKILL_PROMPT = """## Role
You are a project status summarizer.

## Task
Given the contents of three project files, produce a structured status summary.

## Context
The input contains the contents of project files.

## Constraints
- Output must be valid JSON with these fields:
  - project_name: string
  - deadline: string
  - team_members: array of strings
  - budget: string
  - status: string (one of: "on_track", "at_risk", "delayed")
  - key_risks: array of strings

- Base your analysis ONLY on the file contents provided.
- Do not invent information."""

# --- Synthetic Context (from Koan 8) ---
# Instead of putting files on disk, we pre-populate the context window
# with the file contents as if the read_file tool had already been called.

def build_synthetic_context(skill_prompt, file_contents):
    """Build a messages array with synthetic tool results."""
    return [
        {"role": "system", "content": skill_prompt},
        {"role": "user", "content": "Summarize the project status from the files I shared."},
        {"role": "assistant", "content": "Let me read the project files.",
         "tool_calls": [
             {"id": "fake_1", "type": "function", "function": {"name": "read_file", "arguments": json.dumps({"path": "deadline.txt"})}},
             {"id": "fake_2", "type": "function", "function": {"name": "read_file", "arguments": json.dumps({"path": "team.txt"})}},
             {"id": "fake_3", "type": "function", "function": {"name": "read_file", "arguments": json.dumps({"path": "budget.txt"})}},
         ]},
        {"role": "tool", "tool_call_id": "fake_1", "content": file_contents[0]},
        {"role": "tool", "tool_call_id": "fake_2", "content": file_contents[1]},
        {"role": "tool", "tool_call_id": "fake_3", "content": file_contents[2]},
    ]

PROJECT_FILES = [
    "Project: Phoenix. Deadline: October 31. Status: on schedule.",
    "Team: Alice (lead), Bob (backend), Charlie (frontend), Diana (QA).",
    "Budget: $50,000 approved. $12,000 spent so far. Remaining: $38,000.",
]

# --- Evaluation Criteria ---

def eval_valid_json(response_text):
    """Criterion 1: Output must be valid JSON."""
    text = response_text
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def eval_has_required_fields(response_text):
    """Criterion 2: JSON must have project_name, deadline, team_members, budget."""
    text = response_text
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    try:
        data = json.loads(text)
        required = ["project_name", "deadline", "team_members", "budget"]
        return all(field in data for field in required)
    except (json.JSONDecodeError, TypeError):
        return False

def eval_uses_file_data(response_text):
    """Criterion 3: Output must reference data from the files (Phoenix, October, Alice)."""
    text = response_text.lower()
    return "phoenix" in text and "october" in text and "alice" in text


class AboutEddCycle(Koan):

    def test_red_weak_skill_fails_evaluation(self):
        # RED: Run the weak skill and evaluate it. It should fail.
        messages = build_synthetic_context(WEAK_SKILL_PROMPT, PROJECT_FILES)
        response = llm.ask(messages=messages)

        # Score against all 3 criteria
        score = 0
        if eval_valid_json(response.content):
            score += 1
        if eval_has_required_fields(response.content):
            score += 1
        if eval_uses_file_data(response.content):
            score += 1

        # The weak prompt should NOT pass all criteria
        self.assert_true(
            score < 3,
            f"Weak skill scored {score}/3 — expected it to fail at least one criterion (RED)."
        )

    def test_green_strong_skill_passes_evaluation(self):
        # GREEN: Run the strong skill (with RTCC structure) and evaluate it.
        messages = build_synthetic_context(STRONG_SKILL_PROMPT, PROJECT_FILES)
        response = llm.ask(messages=messages)

        score = 0
        if eval_valid_json(response.content):
            score += 1
        if eval_has_required_fields(response.content):
            score += 1
        if eval_uses_file_data(response.content):
            score += 1

        self.assert_true(
            score >= 2,
            f"Strong skill scored {score}/3 — expected it to pass at least 2 criteria (GREEN)."
        )

    def test_non_determinism_means_single_run_is_not_enough(self):
        # Run the strong skill 3 times. Observe that scores can vary.
        # This is why EDD requires majority voting over multiple runs.
        scores = []
        for _ in range(3):
            messages = build_synthetic_context(STRONG_SKILL_PROMPT, PROJECT_FILES)
            response = llm.ask(messages=messages)
            score = 0
            if eval_valid_json(response.content):
                score += 1
            if eval_has_required_fields(response.content):
                score += 1
            if eval_uses_file_data(response.content):
                score += 1
            scores.append(score)

        # The scores might not all be the same — that's non-determinism.
        # The majority vote is what we trust.
        from collections import Counter
        vote_counts = Counter(scores)
        majority_score = vote_counts.most_common(1)[0][0]

        # Log the runs so the learner can see non-determinism in action
        # (The sequence diagram also shows all 3 runs)
        self.assert_true(
            majority_score >= 2,
            f"3 runs scored: {scores}. Majority: {majority_score}/3. "
            f"Non-determinism is real — majority vote is how we build confidence."
        )

    def test_refactor_remove_dead_weight(self):
        # REFACTOR: Review the strong skill prompt for load-bearing instructions.
        # An instruction is "load-bearing" if removing it would cause an evaluation
        # to fail. Instructions that can be removed without causing failures are
        # "dead weight" and should be removed.
        #
        # The strong skill prompt has 8 instructions:
        # 1. "You are a project status summarizer." (Role)
        # 2. "Given the contents of three project files, produce a structured status summary." (Task)
        # 3. "Output must be valid JSON with these fields:" (Constraint)
        # 4. The field list (project_name, deadline, etc.) (Constraint detail)
        # 5. "Base your analysis ONLY on the file contents provided." (Constraint)
        # 6. "Do not invent information." (Constraint)
        #
        # Which of these are load-bearing?
        # Replace _fill_ with the number of load-bearing instructions (out of 6).

        # Hint: "Do not invent information" (6) is nearly identical to
        # "Base your analysis ONLY on the file contents provided" (5).
        # One of them is dead weight — removing it won't cause any evaluation to fail.

        load_bearing_count = 5  # How many of the 6 instructions are load-bearing?

        # At least 4 instructions should be load-bearing
        self.assert_true(
            load_bearing_count >= 4,
            f"Expected at least 4 load-bearing instructions, got {load_bearing_count}"
        )

    def test_context_window_testing_no_file_fixtures_needed(self):
        # THE KEY LESSON FROM KOAN 8 APPLIED TO EDD:
        # We evaluated a skill that "reads three files" without ever
        # putting files on disk. We constructed the context synthetically.
        #
        # This makes EDD runners simpler, faster, and more deterministic
        # because we eliminate file I/O and tool execution from the test loop.
        #
        # Replace _fill_ with True or False:
        # "EDD for a skill that uses tools requires real file fixtures on disk."
        answer = False  # True or False?
        self.assert_true(
            not answer if answer is True else not answer,
            "EDD does NOT require real file fixtures. You can construct the "
            "context window synthetically with pre-populated tool results."
        )