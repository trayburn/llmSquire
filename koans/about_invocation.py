# Koan 1: about_invocation.py — "The First Call"
#
# An LLM is a function that takes text and returns text.
# You call it through an API, passing messages with roles and content.
#
# In this koan, you will make your first LLM call using llm.ask().
# The response is a structured object with a .content attribute
# that contains the model's text response.
#
# Replace _fill_ with the correct values to make the tests pass.

from llmsquire import Koan, llm


class AboutInvocation(Koan):

    def test_the_first_call(self):
        # Call the model with a simple message
        response = llm.ask(
            messages=[
                {"role": "user", "content": "Say hello in one word."}
            ]
        )
        # The response should contain some text
        self.assert_true(len(response.content) > 0)

    def test_understand_the_role(self):
        # The role of a user message is "user"
        response = llm.ask(
            messages=[
                {"role": "user", "content": "Say hello in one word."}
            ]
        )
        # The model should respond with something
        self.assert_true(len(response.content) > 0)

    def test_response_has_content(self):
        # The response object has a .content attribute with the model's text
        response = llm.ask(
            messages=[
                {"role": "user", "content": "What is 2 + 2? Reply with just the number."}
            ]
        )
        # Fill in what we expect to find in the response
        self.assert_match("4", response.content)