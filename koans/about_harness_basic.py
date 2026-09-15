# Koan 15: about_harness_basic.py — "The Harness Executes"
#
# A harness is a script that EXECUTES the workflow end-to-end:
# calls agents in sequence, passes outputs between steps, fires guardrails.
# A YAML config that documents step order is NOT a harness.
# If a human has to type the command for each step, the human IS the workflow.
#
# In this koan, you will write a basic harness that runs the 3-step workflow
# from Koan 12 (research → summarize → email) with guardrails from Koan 13.
#
# The harness uses llm.converse() — the high-level helper that handles
# the tool-call loop internally. You focus on the orchestration, not the
# mechanics of tool calling.

from llmsquire import Koan, llm

# Skills from Koan 12 — available for your harness
RESEARCH_SKILL = """You are a research analyst.
Extract 3 key findings from the provided text.
Output each finding as a line starting with "Finding: ".
Base findings only on the provided text."""

SUMMARIZE_SKILL = """You are a summarizer.
Given a list of findings, produce a 2-sentence summary.
Output only the summary text, no introduction."""

EMAIL_SKILL = """You are an email writer.
Given a summary, draft a professional email report.
Include a subject line starting with "Subject: ".
Include a greeting, the summary, and a closing."""

# Guardrail from Koan 13 — deterministic Python, never calls an LLM
def guardrail_research_output(output: str) -> tuple:
    """Validate research step output. Returns (passes, reason)."""
    if not output or len(output.strip()) == 0:
        return (False, "Research output is empty")
    findings = [line for line in output.split("\n") if "Finding" in line]
    if len(findings) < 2:
        return (False, f"Expected 2+ findings, got {len(findings)}")
    return (True, "OK")


class AboutHarnessBasic(Koan):

    def test_harness_runs_three_steps_in_sequence(self):
        # Write a harness function that runs the 3-step workflow.
        # Each step calls the model with the appropriate skill prompt.
        # The output of each step becomes the input to the next.

        def run_workflow(topic_text: str) -> str:
            """Run the 3-step research → summarize → email workflow.

            Returns the final email output.
            """
            # Step 1: Research
            step1_response = llm.ask(
                messages=[
                    {"role": "system", "content": RESEARCH_SKILL},
                    {"role": "user", "content": topic_text}
                ]
            )
            research_output = step1_response.content

            # Step 2: Summarize (input = step 1 output)
            step2_response = llm.ask(messages=[
                {"role": "system", "content": SUMMARIZE_SKILL},
                {"role": "user", "content": research_output}
            ])  # Call llm.ask with SUMMARIZE_SKILL and research_output
            summary_output = step2_response.content

            # Step 3: Email (input = step 2 output)
            step3_response = llm.ask(messages=[
                {"role": "system", "content": EMAIL_SKILL},
                {"role": "user", "content": summary_output}
            ])  # Call llm.ask with EMAIL_SKILL and summary_output
            email_output = step3_response.content

            return email_output

        # Run the workflow
        result = run_workflow(
            "AI adoption grew 45% in 2023. Main challenges: data quality and skill gaps. "
            "Companies with evaluation frameworks see 3x higher success rates."
        )
        # The final output should be an email with a subject line
        self.assert_match("Subject", result)

    def test_harness_fires_guardrail_between_steps(self):
        # A real harness fires guardrails BETWEEN steps, not inside them.
        # The guardrail validates step 1's output before step 2 begins.

        def run_workflow_with_guardrail(topic_text: str) -> str:
            """Run the workflow with a guardrail after step 1."""
            # Step 1: Research
            step1_response = llm.ask(
                messages=[
                    {"role": "system", "content": RESEARCH_SKILL},
                    {"role": "user", "content": topic_text}
                ]
            )
            research_output = step1_response.content

            # Guardrail: validate research output BEFORE step 2
            passes, reason = guardrail_research_output(research_output)
            if not passes:
                return f"WORKFLOW HALTED: Guardrail failed — {reason}"

            # Step 2: Summarize
            step2_response = llm.ask(
                messages=[
                    {"role": "system", "content": SUMMARIZE_SKILL},
                    {"role": "user", "content": research_output}
                ]
            )

            # Step 3: Email
            step3_response = llm.ask(
                messages=[
                    {"role": "system", "content": EMAIL_SKILL},
                    {"role": "user", "content": step2_response.content}
                ]
            )
            return step3_response.content

        # Run with good input — should produce an email
        result = run_workflow_with_guardrail(
            "Cloud adoption reached 90%. Security is the top concern. "
            "Multi-cloud strategies are becoming standard."
        )
        self.assert_match("Subject", result)

    def test_harness_halts_on_guardrail_failure(self):
        # When a guardrail fails, the harness should halt — not continue
        # with bad input. This is the difference between Stage 2 and Stage 4.

        def run_workflow_with_guardrail(topic_text: str) -> str:
            step1_response = llm.ask(
                messages=[
                    {"role": "system", "content": RESEARCH_SKILL},
                    {"role": "user", "content": topic_text}
                ]
            )
            research_output = step1_response.content

            # Guardrail
            passes, reason = guardrail_research_output(research_output)
            if not passes:
                return f"WORKFLOW HALTED: {reason}"  # What should the harness return when the guardrail fails?
                # Return something like: f"WORKFLOW HALTED: {reason}"

            # Step 2 and 3 would follow...
            return "continued"

        # Run with input that might produce insufficient findings
        result = run_workflow_with_guardrail("ok")
        # If the guardrail caught a problem, the workflow should have halted
        # (Either it halted with a message, or it continued — both are valid
        # outcomes depending on whether the model produced enough findings)
        self.assert_true(len(result) > 0)

    def test_harness_definition_not_a_harness(self):
        # A YAML config that documents step order is NOT a harness.
        # A harness EXECUTES. If a human has to type the command for each
        # step, the human IS the workflow (Stage 2, not Stage 4).
        #
        # Replace _fill_ with the correct answer.

        # Which of these is a real harness?
        # A) A YAML file that lists step names and their order
        # B) A Python script that calls each step and passes outputs between them
        # C) A diagram showing the workflow architecture
        #
        # Enter the letter of the correct answer:
        answer = "B"  # "A", "B", or "C"

        self.assert_equal("B", answer)