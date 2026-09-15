# Koan 3: about_context_window.py — "The Edge of Memory"
#
# The context window is finite. You must choose what goes in it.
# What you leave OUT is as important as what you put IN.
#
# In this koan, you will experience context limits and learn to trim history.

from llmsquire import Koan, llm


class AboutContextWindow(Koan):

    def test_short_conversation_works(self):
        # A short conversation works fine
        messages = [
            {"role": "user", "content": f"Message number {i}"} for i in range(5)
        ]
        messages.append({"role": "user", "content": "What was the number of the first message?"})
        response = llm.ask(messages=messages)
        # The model should be able to answer since it's all in context
        self.assert_true(
            "0" in response.content or "zero" in response.content.lower(),
            f"Expected the model to identify message number 0. Response: {response.content[:200]}..."
        )

    def test_trim_history_to_last_n_messages(self):
        # Write a function that trims conversation history to the last N messages.
        # This is YOUR function — replace _fill_ with the implementation.

        def trim_history(messages, n=10):
            # Return only the last n messages
            return messages[-n:]

        # Test it: create 10 messages, trim to last 3
        messages = [
            {"role": "user", "content": f"Message {i}"} for i in range(10)
        ]
        trimmed = trim_history(messages, 3)
        self.assert_equal(3, len(trimmed))
        self.assert_equal("Message 7", trimmed[0]["content"])