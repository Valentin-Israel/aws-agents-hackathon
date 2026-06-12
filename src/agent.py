"""Minimal Strands agent – doubles as Bedrock access test."""
from strands import Agent, tool
from strands.models import BedrockModel

MODEL_ID = "us.anthropic.claude-sonnet-4-6-20250514-v1:0"

@tool
def ping(name: str) -> str:
    """Returns a greeting – proves tool calling works."""
    return f"pong, {name}!"

agent = Agent(
    model=BedrockModel(model_id=MODEL_ID, region_name="us-west-2"),
    tools=[ping],
    system_prompt="You are a concise, helpful agent.",
)

if __name__ == "__main__":
    print(agent("Call the ping tool with the name 'Valentin' and report the result."))
