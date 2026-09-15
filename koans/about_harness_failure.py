# Koan 16: about_harness_failure.py — "When Things Go Wrong"
#
# A production harness handles failures gracefully.
# If a guardrail fails, retry the step once, then halt.
# The failure must be traceable to its origin step.
#
# In this koan, you extend the basic harness from Koan 15 with
# failure handling and retry logic.

from llmsquire import Koan, llm

# Skills (same as Koan 15)
RESEARCH_SKILL = """## Role
You are a research analyst.

## Task
Extract 3 key findings from the provided text.

## Context
The input is source text to analyze.

## Constraints
- Output each finding as a line starting with "Finding: ".
- Base findings only on the provided text."""

SUMMARIZE_SKILL = """## Role
You are a summarizer.

## Task
Given a list of findings, produce a 2-sentence summary.

## Context
The input is a list of research findings.

## Constraints
- Output only the summary text, with no introduction."""

EMAIL_SKILL = """## Role
You are an email writer.

## Task
Given a summary, draft a professional email report.

## Context
The input is a summary of research findings.

## Constraints
- Include a subject line starting with "Subject: ".
- Include a greeting, the summary, and a closing."""

# Guardrails (same as Koan 13)
def guardrail_research_output(output: str) -> tuple:
    if not output or len(output.strip()) == 0:
        return (False, "Research output is empty")
    findings = [line for line in output.split("\n") if "Finding" in line]
    if len(findings) < 2:
        return (False, f"Expected 2+ findings, got {len(findings)}")
    return (True, "OK")

def guardrail_summary_output(output: str) -> tuple:
    words = output.split()
    if len(words) > 500:
        return (False, f"Summary is {len(words)} words, max is 500")
    if len(words) < 5:
        return (False, f"Summary is too short: {len(words)} words")
    return (True, "OK")


class AboutHarnessFailure(Koan):

    def test_retry_on_guardrail_failure(self):
        # When a guardrail fails, retry the step ONCE with the same input.
        # If the retry also fails, halt the workflow.

        def run_step_with_retry(skill_prompt, user_input, guardrail, step_name, max_retries=1):
            """Run a step with retry on guardrail failure."""
            attempts = 0
            while attempts <= max_retries:
                response = llm.ask(
                    messages=[
                        {"role": "system", "content": skill_prompt},
                        {"role": "user", "content": user_input}
                    ]
                )
                output = response.content
                passes, reason = guardrail(output)
                if passes:
                    return output, None  # success
                attempts += 1
                if attempts > max_retries:
                    return None, f"{step_name} failed after {max_retries + 1} attempts: {reason}"
                # Retry — the model might produce better output on the second try

            return None, f"{step_name} exhausted retries"

        # Test with good input — should succeed on first try
        output, error = run_step_with_retry(
            RESEARCH_SKILL,
            "AI adoption grew 45%. Challenges include data quality. Frameworks help.",
            guardrail_research_output,
            "research"
        )
        self.assert_true(output is not None, f"Good input should succeed: {error}")
        self.assert_match("Finding", output)

    def test_halt_after_retry_exhausted(self):
        # If the retry also fails, halt with a clear error that traces
        # the failure to its origin step.

        def run_step_with_retry(skill_prompt, user_input, guardrail, step_name, max_retries=1):
            attempts = 0
            while attempts <= max_retries:
                response = llm.ask(
                    messages=[
                        {"role": "system", "content": skill_prompt},
                        {"role": "user", "content": user_input}
                    ]
                )
                output = response.content
                passes, reason = guardrail(output)
                if passes:
                    return output, None
                attempts += 1
                if attempts > max_retries:
                    return None, f"{step_name} failed guardrail after {max_retries + 1} attempts: {reason}. Output: {output}"
                    # Return: None (no output) and an error message that includes:
                    # - Which step failed (step_name)
                    # - Which guardrail caught it
                    # - What the output was
                    # - What the guardrail expected
            return None, "exhausted"

        # Simulate a very strict guardrail that always fails
        def strict_guardrail(output):
            return (False, "Always fails for testing")

        output, error = run_step_with_retry(
            RESEARCH_SKILL, "test input", strict_guardrail, "research_step"
        )
        # The harness should have halted with a traceable error
        self.assert_true(output is None, "Should halt after retry exhausted")
        self.assert_match("research_step", error)

    def test_failure_traces_to_origin_step(self):
        # Stage 4 requires that any failure can be traced to its origin step.
        # The error message must include: which step, which guardrail, what failed.

        def run_workflow_with_failure_tracking(topic_text: str) -> dict:
            """Run workflow and return a structured result with traceability."""
            result = {"steps": [], "success": False, "error": None}

            # Step 1: Research
            response = llm.ask(
                messages=[{"role": "system", "content": RESEARCH_SKILL},
                          {"role": "user", "content": topic_text}]
            )
            passes, reason = guardrail_research_output(response.content)
            result["steps"].append({
                "step": "research",
                "guardrail_passed": passes,
                "guardrail_reason": reason,
                "output_length": len(response.content)
            })
            if not passes:
                result["error"] = f"Step 'research' failed guardrail: {reason}"  # Build an error message that traces to the research step
                return result

            # Step 2: Summarize
            response2 = llm.ask(
                messages=[{"role": "system", "content": SUMMARIZE_SKILL},
                          {"role": "user", "content": response.content}]
            )
            passes2, reason2 = guardrail_summary_output(response2.content)
            result["steps"].append({
                "step": "summarize",
                "guardrail_passed": passes2,
                "guardrail_reason": reason2,
                "output_length": len(response2.content)
            })
            if not passes2:
                result["error"] = f"Step 'summarize' failed guardrail: {reason2}"
                return result

            result["success"] = True
            return result

        # Run with real input
        result = run_workflow_with_failure_tracking(
            "AI adoption grew 45%. Challenges include data quality. Frameworks help."
        )
        # The result should have step-by-step tracking
        self.assert_true(len(result["steps"]) >= 1)
        # Each step should have a name and guardrail status
        for step in result["steps"]:
            self.assert_true("step" in step)
            self.assert_true("guardrail_passed" in step)