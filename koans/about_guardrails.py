# Koan 13: about_guardrails.py — "The Walls Between Rooms"
#
# Guardrails sit BETWEEN steps, not inside them.
# They validate outputs before the next step is allowed to begin.
#
# GUARDRAILS ARE ALWAYS DETERMINISTIC PYTHON FUNCTIONS.
# They NEVER call an LLM. Full stop.
#
# If you need judgment, that's what adversarial agents are for (Koan 14).
# Guardrails are infrastructure — fast, reliable, and deterministic.
#
# Guardrails that only check file existence or non-empty output are
# window dressing. Real guardrails validate structure, content, format,
# or rules that could actually fail.

import re
import json
from llmsquire import Koan, llm


class AboutGuardrails(Koan):

    def test_no_guardrails_means_errors_propagate(self):
        # Without guardrails, a bad output from step 1 flows into step 2.
        # The error compounds and produces garbage at the end.
        #
        # This test demonstrates what happens WITHOUT guardrails.
        # "Bad input" simulates a corrupted step 1 output.
        bad_step1_output = ""  # empty — step 1 failed silently

        # Step 2 receives empty input and produces garbage
        # (In a real workflow, this would cascade into worse problems)
        self.assert_true(len(bad_step1_output) == 0,
                         "Without guardrails, a bad output passes through unchecked")

    def test_guardrail_validates_non_empty(self):
        # Guardrail 1: validate that the research output is non-empty
        # and contains at least 3 findings.
        #
        # This is a deterministic Python function — no LLM calls.

        def guardrail_research_output(output: str) -> tuple:
            """Validate research step output. Returns (passes, reason)."""
            if not output or len(output.strip()) == 0:
                return (False, "Research output is empty")
            findings = [line for line in output.split("\n") if "Finding" in line]
            if len(findings) < 3:
                return (False, f"Expected 3+ findings, got {len(findings)}")
            return (True, "OK")

        # Test with good output
        good_output = "Finding: A\nFinding: B\nFinding: C"
        passes, reason = guardrail_research_output(good_output)
        self.assert_true(passes, f"Good output should pass: {reason}")

        # Test with bad output — replace _fill_ with the expected result
        bad_output = "Finding: A"
        passes, reason = guardrail_research_output(bad_output)
        self.assert_true(
            not passes,  # Should the bad output pass or fail? (True = pass, False = fail)
            "Bad output with only 1 finding should fail the guardrail"
        )

    def test_guardrail_validates_word_count(self):
        # Guardrail 2: validate that the summary is under 500 words
        # and contains no PII patterns (email addresses, phone numbers).

        def guardrail_summary(output: str) -> tuple:
            """Validate summary output. Returns (passes, reason)."""
            words = output.split()
            if len(words) > 500:
                return (False, f"Summary is {len(words)} words, max is 500")
            # Check for PII patterns
            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
            ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

            for pattern, name in [(email_pattern, "email"), (phone_pattern, "phone"), (ssn_pattern, "SSN")]:
                if pattern.search(output):
                    return (False, f"PII detected: {name} pattern found in summary")
            return (True, "OK")

        # Test with clean summary
        clean = "The project is on track with a budget of $50,000."
        passes, reason = guardrail_summary(clean)
        self.assert_true(passes, f"Clean summary should pass: {reason}")

        # Test with PII — fill in the assertion
        pii_summary = "Contact Alice at alice@example.com for details."
        passes, reason = guardrail_summary(pii_summary)
        self.assert_true(
            not passes,  # Should output with PII pass or fail?
            "Summary with email PII should fail the guardrail"
        )

    def test_guardrail_validates_json_schema(self):
        # Guardrail 3: validate that output is valid JSON with required fields

        def guardrail_json_schema(output: str, required_fields: list) -> tuple:
            """Validate JSON output. Returns (passes, reason)."""
            text = output
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            try:
                data = json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return (False, "Output is not valid JSON")
            for field in required_fields:
                if field not in data:
                    return (False, f"JSON missing required field: {field}")
            return (True, "OK")

        # Test with valid JSON
        good_json = json.dumps({"project_name": "Phoenix", "deadline": "Oct 31"})
        passes, reason = guardrail_json_schema(good_json, ["project_name", "deadline"])
        self.assert_true(passes, f"Valid JSON should pass: {reason}")

        # Test with missing field — fill in the assertion
        bad_json = json.dumps({"project_name": "Phoenix"})
        passes, reason = guardrail_json_schema(bad_json, ["project_name", "deadline"])
        self.assert_true(
            not passes,  # Should JSON with a missing required field pass or fail?
            "JSON missing required field should fail the guardrail"
        )

    def test_guardrails_never_call_an_llm(self):
        # HARD RULE: Guardrails are ALWAYS deterministic code. They NEVER call an LLM.
        # A guardrail that calls an LLM is not a guardrail — it is an adversarial agent.
        #
        # This is a reflection test. Replace _fill_ with the correct answer.
        answer = False  # True or False: "Guardrails should call an LLM to evaluate output quality"
        self.assert_true(
            not answer,  # answer should be False
            "Guardrails NEVER call an LLM. They are deterministic code only. "
            "If you need judgment, that's what adversarial agents are for (Koan 14)."
        )