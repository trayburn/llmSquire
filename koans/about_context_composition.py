# Koan 8: about_context_composition.py — "What the Model Actually Sees"
#
# After a tool call, the context window grows. The model's next response
# is based on everything in context — the system prompt, the user's message,
# the assistant's tool call, and the tool result. Understanding exactly
# what is in context at each step is the key to effective evaluation.
#
# THE KEY INSIGHT: The model doesn't know or care whether a tool was
# actually called. It only sees the messages in its context window.
# If you put the tool result there, it's there.
#
# This means you can test skills that use tools WITHOUT actually running
# the tools — you just construct the context the skill would have seen.
#
# Open the sequence diagrams after each test to see what's in context!

from llmsquire import Koan, llm
import json

# Tools for this koan
READ_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read"}
            },
            "required": ["path"]
        }
    }
}

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the web for information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    }
}


class AboutContextComposition(Koan):

    def test_see_what_is_in_context_after_a_tool_call(self):
        # Trigger a read_file tool call. Then look at the sequence diagram
        # to see what's in the context window on the SECOND round trip.
        response = llm.ask(
            messages=[
                {"role": "user", "content": "Read the file at /etc/hosts and tell me what it contains."}
            ],
            tools=[READ_FILE_TOOL]
        )
        # The model should request to call read_file
        self.assert_tool_called(response, "read_file")

        # Now simulate executing the tool and sending the result back.
        # After this, the context window will contain:
        #   1. The user's original message
        #   2. The assistant's tool_call response
        #   3. The tool result message (role="tool")
        tool_call = response.tool_calls[0]
        tool_result = "127.0.0.1 localhost\n192.168.1.1 router"

        second_response = llm.ask(
            messages=[
                {"role": "user", "content": "Read the file at /etc/hosts and tell me what it contains."},
                {"role": "assistant", "content": response.content,
                 "tool_calls": [{"id": tool_call["id"], "type": "function",
                                 "function": {"name": "read_file", "arguments": tool_call["arguments"]}}]},
                {"role": "tool", "tool_call_id": tool_call["id"], "content": tool_result}
            ]
        )
        # The model should now "know" the file contents — they're in its context!
        self.assert_match("localhost", second_response.content)

    def test_context_grows_with_each_tool_call(self):
        # When you make multiple tool calls, the context grows with each one.
        # The model sees ALL prior tool results, not just the most recent.

        # First tool call: search
        response1 = llm.ask(
            messages=[
                {"role": "user", "content": "Search for information about Python, then search for information about Rust."}
            ],
            tools=[SEARCH_TOOL]
        )
        self.assert_tool_called(response1, "search")

        # Simulate the search result and ask the model to search for Rust
        search_result_1 = "Python is a high-level programming language known for its readability."

        response2 = llm.ask(
            messages=[
                {"role": "user", "content": "Search for information about Python, then search for information about Rust."},
                {"role": "assistant", "content": response1.content,
                 "tool_calls": [{"id": response1.tool_calls[0]["id"], "type": "function",
                                 "function": {"name": "search",
                                              "arguments": response1.tool_calls[0]["arguments"]}}]},
                {"role": "tool", "tool_call_id": response1.tool_calls[0]["id"], "content": search_result_1}
            ],
            tools=[SEARCH_TOOL]
        )
        # The model should now search for Rust (second tool call)
        self.assert_tool_called(response2, "search")

    def test_synthetic_context_works_without_real_tool_calls(self):
        # THIS IS THE KEY LESSON.
        #
        # Instead of triggering a real tool call, construct the messages
        # array manually — include the system prompt, a user message,
        # a SYNTHETIC assistant tool_call message, and a SYNTHETIC tool
        # result message with the file contents pre-filled.
        #
        # Call the model with this pre-populated context.
        # The model responds EXACTLY as if it had called the tool itself.

        # Build a synthetic conversation — no real tool calls happened!
        synthetic_messages = [
            {"role": "system", "content": "You are a helpful assistant that answers questions about files."},  # A system prompt: "You are a helpful assistant that answers questions about files."
            {"role": "user", "content": "What does the notes.txt file contain?"},  # A user message: "What does the notes.txt file contain?"
            {"role": "assistant", "content": "", "tool_calls": [{"id": "call_fake", "type": "function", "function": {"name": "read_file", "arguments": json.dumps({"path": "notes.txt"})}}]},  # A synthetic assistant tool_call: {"role": "assistant", "content": "",
                     #   "tool_calls": [{"id": "call_fake", "type": "function",
                     #     "function": {"name": "read_file", "arguments": '{"path": "notes.txt"}'}}]}
            {"role": "tool", "tool_call_id": "call_fake", "content": "Meeting notes: Buy milk. Call Bob. Submit report by Friday."},  # A synthetic tool result: {"role": "tool", "tool_call_id": "call_fake",
                     #   "content": "Meeting notes: Buy milk. Call Bob. Submit report by Friday."}
        ]

        response = llm.ask(messages=synthetic_messages)

        # The model should respond as if it read the file — because the
        # file contents ARE in its context window, even though no real
        # tool call ever happened!
        self.assert_match("milk", response.content)
        self.assert_match("Bob", response.content)

    def test_the_model_cannot_tell_the_difference(self):
        # The model has NO WAY to know whether a tool was actually called
        # or whether you constructed the context synthetically.
        # It only sees messages. If the tool result is in the messages,
        # it's in the context. That's all that matters.

        # Build two versions:
        # Version A: "real" tool call flow (simulated here)
        # Version B: synthetic context (pre-populated)

        # Version B — fully synthetic
        synthetic_messages = [
            {"role": "system", "content": "You are a helpful file assistant."},
            {"role": "user", "content": "Read config.yaml and tell me the database setting."},
            {"role": "assistant", "content": "",
             "tool_calls": [{"id": "fake_call_1", "type": "function",
                             "function": {"name": "read_file",
                                          "arguments": json.dumps({"path": "config.yaml"})}}]},
            {"role": "tool", "tool_call_id": "fake_call_1",
             "content": "database:\n  host: localhost\n  port: 5432\n  name: myapp"}
        ]

        response = llm.ask(messages=synthetic_messages)

        # The model should report the database settings — even though
        # no real tool call was ever made. The contents are in context.
        self.assert_match("5432", response.content)
        self.assert_match("localhost", response.content)

        # Reflection: "The model doesn't know or care whether a tool was
        # actually called. It only sees the messages in its context window.
        # This means you can test skills that use tools WITHOUT actually
        # running the tools — you just construct the context."

    def test_this_is_why_edd_does_not_need_file_fixtures(self):
        # If a skill reads three files and then reasons about them,
        # you do NOT need your EDD runner to put files on disk.
        # You construct the test scenario by pre-populating the context
        # window with the messages the skill would have produced.

        # Simulate: a skill that read three files and now needs to summarize them
        file_a = "Project deadline is October 31."
        file_b = "Team members: Alice, Bob, Charlie."
        file_c = "Budget approved for $50,000."

        synthetic_messages = [
            {"role": "system", "content": "You are a project summarizer. Given file contents, produce a brief summary."},
            {"role": "user", "content": "Summarize the project files I shared with you."},
            # Simulate three read_file tool calls and results
            {"role": "assistant", "content": "Let me read the project files.",
             "tool_calls": [
                 {"id": "fake_1", "type": "function", "function": {"name": "read_file", "arguments": json.dumps({"path": "deadline.txt"})}},
                 {"id": "fake_2", "type": "function", "function": {"name": "read_file", "arguments": json.dumps({"path": "team.txt"})}},
                 {"id": "fake_3", "type": "function", "function": {"name": "read_file", "arguments": json.dumps({"path": "budget.txt"})}},
             ]},
            {"role": "tool", "tool_call_id": "fake_1", "content": file_a},
            {"role": "tool", "tool_call_id": "fake_2", "content": file_b},
            {"role": "tool", "tool_call_id": "fake_3", "content": file_c},
            {"role": "user", "content": "Using the three file contents returned above, provide the requested brief project summary now."},
        ]

        response = llm.ask(messages=synthetic_messages)

        # The model should summarize all three files — because all three
        # file contents are in its context window.
        self.assert_match("October", response.content)
        self.assert_match("Alice", response.content)
        self.assert_match("50", response.content)