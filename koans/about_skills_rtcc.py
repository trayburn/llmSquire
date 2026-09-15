# Koan 9: about_skills_rtcc.py — "The Job Description"
#
# A skill is a written job description for a unit of work.
# The RTCC framework provides the structure:
#   R = Role     — who the model is
#   T = Task     — what the model should do
#   C = Context  — what information the model has
#   C = Constraints — rules the model must follow
#
# The prompt IS the code. A well-structured skill produces consistent output.
# A poorly-structured skill is unpredictable.
#
# In this koan, you will write skills using RTCC and see the difference.

from llmsquire import Koan, llm


# A poorly-structured prompt — no RTCC, just a vague request
WEAK_PROMPT = "Help me extract action items from meeting notes."


class AboutSkillsRtcc(Koan):

    def test_weak_prompt_produces_unpredictable_output(self):
        # A weak prompt with no structure produces unpredictable output.
        # The model doesn't know its role, what format to use, or what constraints to follow.
        response = llm.ask(
            messages=[
                {"role": "user", "content": WEAK_PROMPT + "\n\nMeeting: We discussed the launch. Alice will send the email by Friday. Bob needs to update the docs."}
            ]
        )
        # The model will respond, but the output format and quality are unpredictable
        # It might be a paragraph, a list, or a table — we can't be sure
        self.assert_true(len(response.content) > 0)

    def test_rtcc_role(self):
        # R = Role: tell the model WHO it is
        # A clear role shapes the model's behavior and output style.
        response = llm.ask(
            messages=[
                {"role": "system", "content": "You are an action item extractor. You identify tasks, owners, and deadlines from meeting notes."},
                # Write a system prompt that defines the role:
                # "You are an action item extractor. You identify tasks, owners, and deadlines from meeting notes."
                {"role": "user", "content": "Meeting: We discussed the launch. Alice will send the email by Friday. Bob needs to update the docs."}
            ]
        )
        # With a clear role, the model should identify Alice's task
        self.assert_match("Alice", response.content)

    def test_rtcc_task_and_constraints(self):
        # T = Task, C = Constraints: tell the model WHAT to do and WHAT rules to follow
        # Constraints make output predictable and testable.
        response = llm.ask(
            messages=[
                {"role": "system", "content": """You are an action item extractor.
Extract action items from meeting notes.
Input is meeting notes as plain text.
Output must be valid JSON. Each action item has: task (string), owner (string), deadline (string or null). Return a JSON array and no other text."""},
                # Write a COMPLETE RTCC skill:
                # Role: "You are an action item extractor."
                # Task: "Extract action items from meeting notes."
                # Context: "Input is meeting notes as plain text."
                # Constraints: "Output must be valid JSON. Each action item has: task (string),
                #   owner (string), deadline (string or null). Return a JSON array."
                {"role": "user", "content": "Meeting: Alice will send the launch email by Friday. Bob needs to update the API docs. Charlie should review the tests."}
            ]
        )
        # With constraints requiring JSON, the output should be parseable as JSON
        import json
        try:
            data = json.loads(response.content)
            self.assert_true(isinstance(data, list))
            self.assert_true(len(data) >= 2)
        except json.JSONDecodeError:
            # The model might wrap JSON in markdown — try to extract it
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                raise AssertionError(f"Response is not valid JSON: {content[:200]}")
            data = json.loads(json_str)
            self.assert_true(isinstance(data, list))
            self.assert_true(len(data) >= 2)

    def test_complete_skill_from_scratch(self):
        # Write a COMPLETE skill from scratch for a different task:
        # "Summarize a technical article in 3 bullet points"
        #
        # Fill in the system prompt with full RTCC structure.
        response = llm.ask(
            messages=[
                {"role": "system", "content": """You are a technical summarizer.
Summarize technical articles in exactly 3 bullet points.
Input is a technical article as plain text.
Output exactly 3 bullet points, each starting with '- '. Each bullet point must be one sentence. No introduction or conclusion."""},
                # Write the full RTCC skill here:
                # Role: "You are a technical summarizer."
                # Task: "Summarize technical articles in exactly 3 bullet points."
                # Context: "Input is a technical article as plain text."
                # Constraints: "Output exactly 3 bullet points, each starting with '- '.
                #   Each bullet point should be one sentence. No introduction or conclusion."
                {"role": "user", "content": "Container orchestration manages deployment, scaling, and operations of containerized applications. Kubernetes is the most popular orchestrator. It uses pods as the smallest deployable units. Services provide network abstraction. Deployments manage rolling updates and rollbacks."}
            ]
        )
        # The response should contain bullet points
        self.assert_match("-", response.content)
        # And should be relatively short (3 bullet points)
        lines = [l for l in response.content.strip().split("\n") if l.strip().startswith("-")]
        self.assert_true(len(lines) >= 2, f"Expected 2+ bullet points, got {len(lines)}")