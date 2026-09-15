# Koan 6: about_tool_calling.py — "The Call and Response"
#
# Tool calling is a multi-turn dance:
#   1. The user asks something
#   2. The model decides to call a tool and returns a tool_call in its response
#   3. YOU execute the tool and get the result
#   4. YOU send the tool result back to the model as a "tool" role message
#   5. The model reads the result and produces its final answer
#
# The LLM doesn't execute tools. YOU execute tools. The LLM only decides
# which tools to call and with what arguments.
#
# In this koan, you will implement the full tool-call loop using llm.ask().
# This is the manual approach — you manage each step yourself so you can
# see exactly what happens at each round trip.
#
# Open the sequence diagram after each test to see the round trips!

from llmsquire import Koan, llm
import json

# A simple calculator tool — already implemented for you.
CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform arithmetic. Provide an expression like '2 + 2'.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
            },
            "required": ["expression"]
        }
    }
}


def calculator(expression):
    """Execute the calculator tool."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


class AboutToolCalling(Koan):

    def test_the_model_requests_a_tool_call(self):
        # Step 1: Send a message that should trigger a tool call
        response = llm.ask(
            messages=[
                {"role": "user", "content": "What is 7 multiplied by 8? Use the calculator tool."}
            ],
            tools=[CALCULATOR_TOOL]
        )
        # The response should contain a tool call
        self.assert_tool_called(response, "calculator")

    def test_extract_tool_name_and_arguments(self):
        # When the model calls a tool, the response has .tool_calls
        # Each tool call has a "name" and "arguments" (a JSON string)
        response = llm.ask(
            messages=[
                {"role": "user", "content": "What is 15 + 27? Use the calculator tool."}
            ],
            tools=[CALCULATOR_TOOL]
        )

        # Extract the first tool call
        tool_call = response.tool_calls[0]
        tool_name = tool_call["name"]
        # The arguments are a JSON string — parse it to get the expression
        args = json.loads(tool_call["arguments"])
        expression = args["expression"]

        # What should the tool name be?
        self.assert_equal("calculator", tool_name)
        # The expression should contain the numbers we asked about
        self.assert_match("15", expression)
        self.assert_match("27", expression)

    def test_the_full_tool_call_loop(self):
        # Now implement the FULL loop: ask → tool_call → execute → result → final answer

        # Step 1: Ask the model a question that requires the calculator
        first_response = llm.ask(
            messages=[
                {"role": "user", "content": "What is 9 times 6? Use the calculator tool."}
            ],
            tools=[CALCULATOR_TOOL]
        )

        # Step 2: Extract the tool call
        tool_call = first_response.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = json.loads(tool_call["arguments"])
        tool_call_id = tool_call["id"]

        # Step 3: Execute the tool
        result = calculator(tool_args["expression"])  # Call the calculator function with the expression from tool_args

        # Step 4: Send the tool result back to the model
        # Build the messages array with the full conversation:
        #   - The original user message
        #   - The assistant's tool-call response
        #   - The tool result message (role="tool", tool_call_id, content=result)
        second_response = llm.ask(
            messages=[
                {"role": "user", "content": "What is 9 times 6? Use the calculator tool."},  # The original user message (ask about 9 times 6)
                {"role": "assistant", "content": first_response.content,
                 "tool_calls": [{"id": tool_call_id, "type": "function",
                                 "function": {"name": tool_name, "arguments": tool_call["arguments"]}}]},  # The assistant's response with the tool call
                {"role": "tool", "tool_call_id": tool_call_id, "content": result},  # The tool result: {"role": "tool", "tool_call_id": tool_call_id, "content": result}
            ]
        )

        # Step 5: The model should now have the answer
        # It should mention 54 (9 * 6 = 54) in its final response
        self.assert_match("54", second_response.content)

    def test_the_model_cannot_execute_tools_itself(self):
        # Key insight: the model only DECIDES to call a tool.
        # It cannot execute anything. YOU are the one who runs the code.
        response = llm.ask(
            messages=[
                {"role": "user", "content": "What is 3 + 4? Use the calculator tool."}
            ],
            tools=[CALCULATOR_TOOL]
        )
        # The model will REQUEST a tool call, but the result is not in the first response
        # The first response contains a tool_call, not the answer "7"
        # (The model might say something like "Let me calculate that..." but it
        #  does not have the result until YOU provide it.)
        self.assert_tool_called(response, "calculator")