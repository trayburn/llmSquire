# Koan 4: about_system_prompts.py — "Setting the Stage"
#
# The system prompt sets the model's role, behavior, and constraints.
# It is the foundation of the RTCC framework (Role, Task, Context, Constraints).
#
# In this koan, you will see how a system prompt transforms the model's behavior.

from llmsquire import Koan, llm


class AboutSystemPrompts(Koan):

    def test_without_system_prompt(self):
        # Without a system prompt, the model answers normally
        response = llm.ask(
            messages=[
                {"role": "user", "content": "Tell me about yourself."}
            ]
        )
        # The model should respond with something
        self.assert_true(len(response.content) > 0)

    def test_with_system_prompt_pirate(self):
        # WITH a system prompt, the model adopts the persona
        response = llm.ask(
            messages=[
                {"role": "system", "content": "You are a pirate. Speak like a pirate always."},
                {"role": "user", "content": "Tell me about yourself."}
            ]
        )
        # The response should contain pirate-like language
        # Think about what words a pirate would use...
        self.assert_match("matey", response.content)

    def test_system_prompt_with_constraints(self):
        # You can add constraints to the system prompt
        response = llm.ask(
            messages=[
                {"role": "system", "content": "You are a pirate who only speaks in 3-word sentences."},
                # Hint: "You are a pirate who only speaks in 3-word sentences."
                {"role": "user", "content": "Tell me about the sea."}
            ]
        )
        # The response should be short (pirate constraint: 3-word sentences)
        words = response.content.split()
        # With the constraint, the response should be quite short
        self.assert_true(len(words) < 15)