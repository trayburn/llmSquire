# Koan 18: about_punch_out.py — "The Human in the Machine"
#
# Punch-out points are explicit, provable human evacuation points where
# the workflow cannot proceed without human sign-off.
#
# Stage 4 requirements:
# - The workflow cannot proceed past these points without human sign-off
# - Punch-out points must have been actively tested — someone attempted
#   to bypass them, and the system blocked it
# - Points that exist on paper but have never been tested are a red signal
#
# In this final koan, you will implement and test a punch-out point.

from llmsquire import Koan, llm

# Skills from the workflow
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


class AboutPunchOut(Koan):

    def test_punch_out_point_returns_pending_approval(self):
        # A punch-out point returns a "pending approval" status.
        # The workflow halts until a human approves.

        def run_workflow_with_punchout(topic_text: str, approval_status: str = "pending"):
            """Run workflow with a punch-out point after research.

            approval_status: "pending", "approved", or "rejected"
            """
            # Step 1: Research
            r1 = llm.ask(
                messages=[{"role": "system", "content": RESEARCH_SKILL},
                          {"role": "user", "content": topic_text}]
            )
            research_output = r1.content

            # PUNCH-OUT POINT: human must approve research findings
            if approval_status == "pending":
                return {
                    "status": "pending_approval",  # What status should this return?
                    "message": "Research findings require human approval before summarization.",
                    "research_output": research_output,
                    "next_step": "Call this function with approval_status='approved' to continue."
                }
            elif approval_status == "rejected":
                return {
                    "status": "rejected",
                    "message": "Research findings were rejected by human reviewer.",
                    "research_output": research_output
                }

            # Approved — continue to step 2 and 3
            r2 = llm.ask(
                messages=[{"role": "system", "content": SUMMARIZE_SKILL},
                          {"role": "user", "content": research_output}]
            )
            r3 = llm.ask(
                messages=[{"role": "system", "content": EMAIL_SKILL},
                          {"role": "user", "content": r2.content}]
            )
            return {"status": "complete", "email": r3.content}

        # Run with pending approval — should halt
        result = run_workflow_with_punchout("AI grew 45%. Challenges exist. Frameworks help.")
        self.assert_equal("pending_approval", result["status"])
        self.assert_true("research_output" in result)

    def test_bypass_attempt_is_blocked(self):
        # TEST THE BYPASS: attempt to proceed without approval.
        # The system must block it. This is the active testing that
        # Stage 4 requires.

        def run_workflow_with_punchout(topic_text: str, approval_status: str = "pending"):
            r1 = llm.ask(
                messages=[{"role": "system", "content": RESEARCH_SKILL},
                          {"role": "user", "content": topic_text}]
            )
            research_output = r1.content

            if approval_status != "approved":
                return {
                    "status": "blocked",
                    "message": "Cannot proceed without explicit human approval.",
                    "research_output": research_output
                }

            r2 = llm.ask(
                messages=[{"role": "system", "content": SUMMARIZE_SKILL},
                          {"role": "user", "content": research_output}]
            )
            r3 = llm.ask(
                messages=[{"role": "system", "content": EMAIL_SKILL},
                          {"role": "user", "content": r2.content}]
            )
            return {"status": "complete", "email": r3.content}

        # Attempt to bypass by calling with "pending" — should be blocked
        result = run_workflow_with_punchout("AI grew. Challenges exist.", approval_status="pending")
        self.assert_equal("blocked", result["status"])

        # Attempt to bypass by calling with "rejected" — should also be blocked
        result = run_workflow_with_punchout("AI grew. Challenges exist.", approval_status="rejected")
        self.assert_equal("blocked", result["status"])  # What status should "rejected" produce?

    def test_approved_proceeds_to_completion(self):
        # When the human approves, the workflow proceeds normally.

        def run_workflow_with_punchout(topic_text: str, approval_status: str = "pending"):
            r1 = llm.ask(
                messages=[{"role": "system", "content": RESEARCH_SKILL},
                          {"role": "user", "content": topic_text}]
            )
            if approval_status != "approved":
                return {"status": "blocked"}

            r2 = llm.ask(
                messages=[{"role": "system", "content": SUMMARIZE_SKILL},
                          {"role": "user", "content": r1.content}]
            )
            r3 = llm.ask(
                messages=[{"role": "system", "content": EMAIL_SKILL},
                          {"role": "user", "content": r2.content}]
            )
            return {"status": "complete", "email": r3.content}

        # Approved — should complete
        result = run_workflow_with_punchout(
            "AI adoption grew 45%. Challenges include data quality. Frameworks help.",
            approval_status="approved"
        )
        self.assert_equal("complete", result["status"])
        self.assert_match("Subject", result["email"])

    def test_punch_out_must_be_tested_for_bypass(self):
        # Stage 4 requires that punch-out points have been ACTIVELY TESTED
        # for bypass attempts. Points that exist on paper but have never
        # been tested are a red signal, not proof.
        #
        # Replace _fill_ with the correct answer:

        answer = False  # True or False:
        # "A punch-out point that has never been bypass-tested is sufficient for Stage 4."

        self.assert_true(
            not answer,  # answer should be False
            "Punch-out points MUST be actively tested for bypass. "
            "Untested points are a red signal, not proof."
        )

    def test_document_the_punch_out_point(self):
        # Stage 4 requires documentation of each punch-out point:
        # - What triggers it (after which step)
        # - What the human decides (approve/reject)
        # - How it's enforced (the code that blocks progression)
        #
        # Fill in the documentation template:

        punchout_doc = {
            "trigger": "After research step, before summarization",  # After which step does the punch-out occur?
            # e.g., "After research step, before summarization"
            "human_decision": "Approve or reject the research findings",  # What does the human decide?
            # e.g., "Approve or reject the research findings"
            "enforcement": "The harness checks approval_status before calling step 2",  # How is it enforced?
            # e.g., "The harness checks approval_status before calling step 2"
            "bypass_test": "Called with pending and rejected approval statuses and verified the workflow halted",  # How was bypass tested?
            # e.g., "Called with approval_status='pending' and verified workflow halted"
        }

        # Verify the documentation has all required fields
        for key in ["trigger", "human_decision", "enforcement", "bypass_test"]:
            self.assert_true(
                key in punchout_doc and isinstance(punchout_doc[key], str) and len(punchout_doc[key]) > 5,
                f"Documentation field '{key}' must be filled in"
            )