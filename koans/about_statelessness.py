# Koan 2: about_statelessness.py — "The River You Cannot Step In Twice"
#
# Every LLM call is independent. The model has no memory of previous calls.
# If you tell it your name in one call, it will NOT know your name in the next
# call — unless YOU pass the previous conversation in the messages array.
#
# In this koan, you will experience statelessness firsthand.

from llmsquire import Koan, llm


class AboutStatelessness(Koan):

    def test_the_model_does_not_remember(self):
        # Step 1: Tell the model your name
        first_response = llm.ask(
            messages=[
                {"role": "user", "content": "My name is Alice."}
            ]
        )

        # Step 2: Ask the model what your name is — in a SEPARATE call
        second_response = llm.ask(
            messages=[
                {"role": "user", "content": "What is my name?"}
            ]
        )

        # What do you expect the model to say?
        # Think carefully — the model has NO memory of the first call.
        # Replace _fill_ with your assertion about second_response.
        # Hint: the model will NOT say "Alice" because it doesn't remember.
        self.assert_match("don't know", second_response.content)

    def test_you_must_provide_the_memory(self):
        # Now fix it: pass the previous conversation in the messages array
        # so the model "remembers" your name.
        first_message = {"role": "user", "content": "My name is Alice."}
        first_response = llm.ask(messages=[first_message])

        # Build the messages array for the second call.
        # It should include the first user message AND the first response
        # AND the new question.
        second_response = llm.ask(
            messages=[
                first_message,  # The original user message
                {"role": "assistant", "content": first_response.content},  # The assistant's first response (use first_response.content)
                {"role": "user", "content": "What is my name?"},  # The new question: "What is my name?"
            ]
        )
        # Now the model should remember!
        self.assert_match("Alice", second_response.content)