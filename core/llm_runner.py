import json
from openai import OpenAI
from core.execution_policy import ExecutionPolicy


class LLMRunner:

    def __init__(self, tools, tool_executor):
        self.client = OpenAI()
        self.tools = tools
        self.tool_executor = tool_executor

    def run(self, user_input: str) -> str:

        response = self.client.responses.create(
            model="gpt-4.1",
            input=user_input,
            tools=self.tools,
            parallel_tool_calls=False
        )

        output = response.output[0]

        if output.type == "function_call":
            tool_name = output.name
            arguments = json.loads(output.arguments)

            validation = ExecutionPolicy.validate(tool_name, arguments)

            if validation["valid"]:
                result = self.tool_executor.execute(tool_name, arguments)
                return result
            else:
                return validation["message"]

        return output.content[0].text
