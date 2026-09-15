# Koan 14: about_adversarial_review.py — "The Red Team"
#
# Adversarial review agents challenge the prior step's output from a
# DIFFERENT perspective. They are NOT redundant second opinions —
# they are trying to find what went wrong.
#
# An adversarial agent must have:
#   1. A distinct purpose or lens (security, compliance, accuracy — not "quality")
#   2. Its own prompt designed to find problems, not confirm quality
#   3. An explicitly adversarial posture — it is trying to find what went wrong
#
# Contrast with guardrails (Koan 13): guardrails are deterministic code.
# Adversarial agents are LLM-based. They are complementary but distinct.

from llmsquire import Koan, llm

# A producing agent (the one whose output we review)
PRODUCER_SKILL = """You are a research analyst.
Extract key findings from the provided text.
Output each finding as a line starting with "Finding: ".
Include source citations when available."""

# An adversarial reviewer — note the DISTINCT perspective and adversarial posture
ADVERSARIAL_REVIEWER_SKILL = """You are a fact-checking adversarial reviewer.
Your job is to FIND PROBLEMS in the research output, not confirm its quality.
Specifically, check for:
1. Factual claims made WITHOUT any source or evidence
2. Overgeneralizations (broad claims from limited data)
3. Missing context that would change the interpretation
Output a list of problems found. If no problems, output "No issues found."
Be skeptical. You are trying to find what went wrong, not validate what went right."""

# A "verification" agent (NOT adversarial — just re-checks the same criteria)
VERIFICATION_SKILL = """You are a research quality verifier.
Check if the research output:
1. Contains findings
2. Is formatted correctly
3. Covers the main points
Output "PASS" if all checks pass, "FAIL" with reasons otherwise."""


SAMPLE_TEXT = """A 2023 study by Gartner found that 80% of enterprises have adopted AI in some form.
The global AI market is projected to reach $500 billion by 2025.
Most companies report significant productivity gains from AI automation."""

SAMPLE_RESEARCH_OUTPUT = """Finding: 80% of enterprises have adopted AI (Gartner 2023)
Finding: The global AI market will reach $500 billion by 2025
Finding: Most companies report significant productivity gains from AI automation"""


class AboutAdversarialReview(Koan):

    def test_adversarial_agent_finds_unsourced_claims(self):
        # The adversarial reviewer should find problems that a
        # verification agent would miss.
        response = llm.ask(
            messages=[
                {"role": "system", "content": ADVERSARIAL_REVIEWER_SKILL},
                {"role": "user", "content": f"Review this research output:\n\n{SAMPLE_RESEARCH_OUTPUT}\n\nOriginal text:\n{SAMPLE_TEXT}"}
            ]
        )
        # The adversarial reviewer should identify issues
        # (e.g., "productivity gains" claim lacks specific source)
        self.assert_true(len(response.content) > 0)

    def test_verification_agent_misses_what_adversarial_finds(self):
        # The verification agent just re-checks the same criteria.
        # It confirms quality rather than finding problems.
        response = llm.ask(
            messages=[
                {"role": "system", "content": VERIFICATION_SKILL},
                {"role": "user", "content": f"Verify this research output:\n\n{SAMPLE_RESEARCH_OUTPUT}"}
            ]
        )
        # The verification agent likely says "PASS" — it doesn't look for problems
        # that the producing agent didn't already check.
        self.assert_true(len(response.content) > 0)

    def test_adversarial_has_distinct_perspective(self):
        # An adversarial agent is NOT the same as a verification agent.
        # It has a DIFFERENT prompt, a DIFFERENT role, and an
        # EXPLICITLY ADVERSARIAL posture.
        #
        # Replace _fill_ with the key difference:

        difference = "An adversarial agent actively tries to find errors and weaknesses while a verification agent checks whether expected criteria are satisfied."  # Complete this sentence (as a string):
        # "An adversarial agent ___ while a verification agent ___"

        self.assert_true(
            isinstance(difference, str) and len(difference) > 10,
            "Describe the key difference between adversarial and verification agents."
        )

    def test_adversarial_catches_planted_errors(self):
        # Plant errors in the research output and see if the adversarial
        # agent catches them.
        output_with_errors = """Finding: 80% of enterprises have adopted AI (Gartner 2023)
Finding: The global AI market will reach $500 TRILLION by 2025
Finding: ALL companies report ZERO productivity issues from AI automation"""

        response = llm.ask(
            messages=[
                {"role": "system", "content": ADVERSARIAL_REVIEWER_SKILL},
                {"role": "user", "content": f"Review this research output for errors and overgeneralizations:\n\n{output_with_errors}\n\nOriginal text:\n{SAMPLE_TEXT}"}
            ]
        )
        # The adversarial reviewer should catch the planted errors:
        # - "$500 TRILLION" contradicts the original "$500 billion"
        # - "ZERO productivity issues" contradicts "significant productivity gains"
        # - "ALL companies" is an overgeneralization
        # The adversarial reviewer should catch the planted errors.
        # It should identify problems — we check for error-finding language
        # rather than exact words, since the model may paraphrase.
        content_lower = response.content.lower()
        # Should mention at least one of the planted errors or use
        # error-finding language
        error_indicators = ["trillion", "zero", "all companies", "error",
                           "incorrect", "wrong", "contradict", "overgeneral",
                           "misstat", "exaggerat", "false", "problem",
                           "issue", "inaccurac"]
        found = [word for word in error_indicators if word in content_lower]
        self.assert_true(
            len(found) >= 2,
            f"Adversarial reviewer should catch at least 2 issues. "
            f"Found indicators: {found}. Response: {response.content[:300]}..."
        )