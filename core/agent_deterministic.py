from langchain_openai import ChatOpenAI
from langchain.agents import create_agent


class DeterministicAgent:
    """
    Wrapper around LangChain agent to enforce single-tool execution.
    """

    def __init__(self, agent):
        self.agent = agent

    def invoke(self, payload: dict):
        result = self.agent.invoke(payload)

        # Extract tool calls from intermediate messages
        messages = result.get("messages", [])

        tool_calls = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend(msg.tool_calls)

        # Enforce single tool execution
        if len(tool_calls) > 1:
            return {
                "error": "Ambiguous request. Multiple structural actions detected. Please specify a single clear intention."
            }

        return result


def build_agent(tools):

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    base_agent = create_agent(
        model=llm,
        tools=tools,
    )

    return DeterministicAgent(base_agent)
