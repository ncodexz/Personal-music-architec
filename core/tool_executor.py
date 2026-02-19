class ToolExecutor:

    def __init__(self, tool_registry: dict):
        self.tool_registry = tool_registry

    def execute(self, tool_name: str, arguments: dict):

        if tool_name not in self.tool_registry:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool_function = self.tool_registry[tool_name]

        return tool_function(**arguments)
