# Koan 5: about_tool_definitions.py — "Giving the Model Hands"
#
# Tools are the bridge between the LLM's text reasoning and the real world.
# You define tools using a JSON schema that tells the model what it can call,
# what arguments to provide, and what the tool does.
#
# In this koan, you will define tools and see the model choose to call them.
# The tool definition has three key parts:
#   - name: what the tool is called
#   - description: what the tool does (the model reads this to decide when to call it)
#   - parameters: a JSON schema describing the arguments
#
# Replace _fill_ with the correct values to make the tests pass.

from llmsquire import Koan, llm


# A calculator tool — already defined for you. Study its structure.
CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform arithmetic calculations. Provide a mathematical expression to evaluate.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A mathematical expression to evaluate, e.g. '2 + 2' or 'sqrt(16)'"
                }
            },
            "required": ["expression"]
        }
    }
}


class AboutToolDefinitions(Koan):

    def test_the_model_calls_a_tool_when_appropriate(self):
        # Give the model the calculator tool and ask it a math question
        response = llm.ask(
            messages=[
                {"role": "user", "content": "What is 2 + 2? Use the calculator tool."}
            ],
            tools=[CALCULATOR_TOOL]
        )
        # The model should decide to call the calculator tool
        self.assert_tool_called(response, "calculator")

    def test_define_a_simple_tool(self):
        # Define a "greeting" tool that takes a name and returns a greeting.
        # Fill in the missing parts of the tool definition.
        GREETING_TOOL = {
            "type": "function",
            "function": {
                "name": "greeting",  # What should this tool be called?
                "description": "Generate a greeting for a given person name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",  # What type is a name?
                            "description": "The name of the person to greet"
                        }
                    },
                    "required": ["name"]  # Which parameter is required?
                }
            }
        }

        response = llm.ask(
            messages=[
                {"role": "user", "content": "Say hello to Alice using the greeting tool."}
            ],
            tools=[GREETING_TOOL]
        )
        # The model should call the greeting tool
        self.assert_tool_called(response, "greeting")

    def test_the_description_matters(self):
        # The model uses the tool's description to decide WHEN to call it.
        # A vague description leads to uncertain tool usage.

        # This tool has a vague description — the model may not call it
        VAGUE_TOOL = {
            "type": "function",
            "function": {
                "name": "search",
                "description": "Search the web for information on a query",  # Write a CLEAR description: "Search the web for information on a query"
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            }
        }

        response = llm.ask(
            messages=[
                {"role": "user", "content": "Search for information about quantum computing."}
            ],
            tools=[VAGUE_TOOL]
        )
        # With a good description, the model should call search
        self.assert_tool_called(response, "search")