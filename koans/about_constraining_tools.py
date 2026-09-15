# Koan 7: about_constraining_tools.py — "The Power of No"
#
# What you DON'T give the model is as important as what you do.
# Constraining available tools shapes worker behavior.
#
# A worker is defined by its tools. Change the tools, change the worker.
# By limiting what tools are available, you define what a worker CAN do
# and, critically, what it CANNOT do.
#
# This is how you build specialized workers rather than general-purpose chatbots.

from llmsquire import Koan, llm


# Pre-defined tools for this koan:

CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform arithmetic calculations. Provide a mathematical expression to evaluate.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
            },
            "required": ["expression"]
        }
    }
}

FILE_WRITER_TOOL = {
    "type": "function",
    "function": {
        "name": "file_writer",
        "description": "Write content to a file on disk.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Name of the file to write"},
                "content": {"type": "string", "description": "Content to write to the file"}
            },
            "required": ["filename", "content"]
        }
    }
}

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the web for information on a given query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    }
}

SUMMARIZE_TOOL = {
    "type": "function",
    "function": {
        "name": "summarize",
        "description": "Summarize a block of text into a concise summary.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to summarize"}
            },
            "required": ["text"]
        }
    }
}


class AboutConstrainingTools(Koan):

    def test_with_both_tools_model_uses_both(self):
        # Give the model BOTH the calculator and file_writer tools.
        # Ask it to calculate 2+2 and write the result to a file.
        response = llm.ask(
            messages=[
                {"role": "user", "content": "Calculate 2+2 and write the result to result.txt"}
            ],
            tools=[CALCULATOR_TOOL, FILE_WRITER_TOOL]
        )
        # The model should call both tools (calculator first, then file_writer)
        self.assert_tool_called(response, "calculator")
        self.assert_tool_called(response, "file_writer")

    def test_with_calculator_only_model_cannot_write(self):
        # Now give the model ONLY the calculator tool.
        # Ask the same question. The model should call the calculator
        # but it CANNOT call file_writer because it's not available.
        response = llm.ask(
            messages=[
                {"role": "user", "content": "Calculate 2+2 and write the result to result.txt"}
            ],
            tools=[CALCULATOR_TOOL]  # Give the model ONLY the calculator tool
        )
        # The model should call the calculator
        self.assert_tool_called(response, "calculator")
        # But it should NOT call file_writer (it's not available!)
        self.assert_tool_not_called(response, "file_writer")

    def test_wrong_tool_means_model_cannot_do_the_task(self):
        # Give the model ONLY the search tool.
        # Ask it to summarize an article. It can't — it doesn't have a summarize tool.
        # The model may call search, but it won't call summarize.
        response = llm.ask(
            messages=[
                {"role": "user", "content": "Summarize this article: 'The quick brown fox jumps over the lazy dog. It was a sunny day and the fox was hungry.'"}
            ],
            tools=[SEARCH_TOOL]  # Give the model ONLY the search tool
        )
        # The model should NOT call summarize (it's not available)
        self.assert_tool_not_called(response, "summarize")

    def test_right_tool_unlocks_the_task(self):
        # Now give the model the summarize tool.
        # Ask the same question. The model should use it.
        response = llm.ask(
            messages=[
                {"role": "user", "content": "Summarize this article: 'The quick brown fox jumps over the lazy dog. It was a sunny day and the fox was hungry.'"}
            ],
            tools=[SUMMARIZE_TOOL]  # Give the model the summarize tool
        )
        # The model should call summarize
        self.assert_tool_called(response, "summarize")

    def test_reflection(self):
        # A worker is defined by its tools. Change the tools, change the worker.
        # When you build an LLM worker, you are NOT just writing a prompt.
        # You are defining the boundary of what the worker CAN and CANNOT do.
        # The tools are the boundary. The prompt is the instructions within that boundary.

        # This test just checks that you understand the concept.
        # Replace _fill_ with the correct answer.
        answer = True  # True or False: constraining tools is how you build specialized workers
        self.assert_true(answer)