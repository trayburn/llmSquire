# Koan 17: about_harness_audit.py — "The Cost of Everything"
#
# Every step execution must record: model, input tokens, output tokens, cost.
# This is the "cost-adjusted capacity" metric — you cannot manage what you
# do not measure.
#
# The conversation traces from self.llm provide token counts and model
# information automatically — you just need to extract and log them.
#
# In this koan, you extend the harness with audit logging and calculate
# the end-to-end success rate.

import json
from llmsquire import Koan, llm

# Skills (same as Koans 15-16)
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


class AboutHarnessAudit(Koan):

    def test_extract_token_counts_from_trace(self):
        # The llm.ask() response has a .usage attribute with token counts.
        # Each call records: input_tokens, output_tokens, model, latency_ms.

        response = llm.ask(
            messages=[
                {"role": "system", "content": RESEARCH_SKILL},
                {"role": "user", "content": "AI adoption grew 45%. Challenges include data quality."}
            ]
        )

        # The usage attribute has input_tokens and output_tokens
        usage = response.usage
        self.assert_true(usage.input_tokens > 0, "Should have input tokens")
        self.assert_true(usage.output_tokens > 0, "Should have output tokens")
        self.assert_true(len(usage.model) > 0, "Should record the model name")

    def test_audit_log_records_each_step(self):
        # Build a harness that records an audit entry for each step.
        # Each entry includes: step name, model, input tokens, output tokens,
        # cost, timestamp, and pass/fail status.

        def run_workflow_with_audit(topic_text: str) -> dict:
            """Run workflow and return an audit log."""
            audit_log = []

            # Step 1: Research
            r1 = llm.ask(
                messages=[{"role": "system", "content": RESEARCH_SKILL},
                          {"role": "user", "content": topic_text}]
            )
            audit_log.append({
                "step": "research",
                "model": r1.usage.model,
                "input_tokens": r1.usage.input_tokens,
                "output_tokens": r1.usage.output_tokens,
                "latency_ms": r1.usage.latency_ms,
                "status": "pass"
            })

            # Step 2: Summarize
            r2 = llm.ask(
                messages=[{"role": "system", "content": SUMMARIZE_SKILL},
                          {"role": "user", "content": r1.content}]
            )
            audit_log.append({
                "step": "summarize",
                "model": r2.usage.model,  # Extract from r2.usage
                "input_tokens": r2.usage.input_tokens,
                "output_tokens": r2.usage.output_tokens,
                "latency_ms": r2.usage.latency_ms,
                "status": "pass"
            })

            # Step 3: Email
            r3 = llm.ask(
                messages=[{"role": "system", "content": EMAIL_SKILL},
                          {"role": "user", "content": r2.content}]
            )
            audit_log.append({
                "step": "email",
                "model": r3.usage.model,
                "input_tokens": r3.usage.input_tokens,
                "output_tokens": r3.usage.output_tokens,
                "latency_ms": r3.usage.latency_ms,
                "status": "pass"
            })

            return {"audit_log": audit_log, "final_output": r3.content}

        result = run_workflow_with_audit(
            "AI adoption grew 45%. Challenges include data quality. Frameworks help."
        )
        log = result["audit_log"]
        self.assert_equal(3, len(log))

        # Each entry should have all required fields
        for entry in log:
            self.assert_true("step" in entry)
            self.assert_true("model" in entry)
            self.assert_true("input_tokens" in entry)
            self.assert_true("output_tokens" in entry)

    def test_tokens_compound_across_steps(self):
        # The output of step 1 becomes input context for step 2.
        # So input tokens GROW across steps. This is the compounding cost.

        r1 = llm.ask(
            messages=[{"role": "system", "content": RESEARCH_SKILL},
                      {"role": "user", "content": "AI grew 45%. Challenges exist. Frameworks help."}]
        )
        r2 = llm.ask(
            messages=[{"role": "system", "content": SUMMARIZE_SKILL},
                      {"role": "user", "content": r1.content}]
        )

        # Step 2's input tokens include step 1's output as context
        # So step 2 input_tokens should generally be >= step 1 input_tokens
        # (or at least both should be positive and trackable)
        self.assert_true(r1.usage.input_tokens > 0)
        self.assert_true(r2.usage.input_tokens > 0)

        # Total tokens = sum of all input + output tokens across all steps
        total_tokens = (r1.usage.input_tokens + r1.usage.output_tokens +
                        r2.usage.input_tokens + r2.usage.output_tokens)
        self.assert_true(total_tokens > 0)

    def test_end_to_end_success_rate(self):
        # At 95% per-step accuracy, a 3-step pipeline succeeds ~86% of the time.
        # At 90%, only ~73%. Compounding error is the enemy.
        #
        # Run the workflow multiple times and track success.

        def run_single_workflow(topic_text: str) -> bool:
            """Run the 3-step workflow. Return True if it produces an email."""
            try:
                r1 = llm.ask(
                    messages=[{"role": "system", "content": RESEARCH_SKILL},
                              {"role": "user", "content": topic_text}]
                )
                r2 = llm.ask(
                    messages=[{"role": "system", "content": SUMMARIZE_SKILL},
                              {"role": "user", "content": r1.content}]
                )
                r3 = llm.ask(
                    messages=[{"role": "system", "content": EMAIL_SKILL},
                              {"role": "user", "content": r2.content}]
                )
                return "Subject" in r3.content
            except Exception:
                return False

        # Run 3 times and count successes (keep it small for cost)
        successes = 0
        total_runs = 3
        for _ in range(total_runs):
            if run_single_workflow("AI adoption grew. Challenges exist. Frameworks help."):
                successes += 1

        success_rate = successes / total_runs
        # With a good model and simple workflow, we expect at least 1 success
        self.assert_true(
            success_rate > 0,
            f"Success rate: {successes}/{total_runs} = {success_rate:.0%}. "
            f"At 95% per-step, 3 steps → ~86%. At 90%, ~73%. Compounding error matters."
        )

    def test_audit_log_as_structured_json(self):
        # The audit log should be writable as structured JSON for persistence.
        # Stage 4 requires per-step model/token/cost data in the audit trail.

        sample_audit = [
            {"step": "research", "model": "deepseek-v4-flash-0731", "input_tokens": 50, "output_tokens": 100, "cost_usd": 0.0001},
            {"step": "summarize", "model": "deepseek-v4-flash-0731", "input_tokens": 150, "output_tokens": 80, "cost_usd": 0.0001},
            {"step": "email", "model": "deepseek-v4-flash-0731", "input_tokens": 230, "output_tokens": 120, "cost_usd": 0.0002},
        ]

        # Write the audit log as JSON
        json_str = json.dumps(sample_audit, indent=2)
        self.assert_true(len(json_str) > 0)

        # Read it back and verify structure
        parsed = json.loads(json_str)
        self.assert_equal(3, len(parsed))

        # Each entry should have model, tokens, and cost
        for entry in parsed:
            self.assert_true("model" in entry)
            self.assert_true("input_tokens" in entry)
            self.assert_true("output_tokens" in entry)
            self.assert_true("cost_usd" in entry)