from dataclasses import dataclass
from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler
from autogen_core import SingleThreadedAgentRuntime
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
import asyncio
load_dotenv()

#define Message object

@dataclass
class MyMessage:
    content: str

# define Agent
class SimpleAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("Simple")

    @message_handler
    async def on_my_message( self, message: MyMessage, ctx: MessageContext ) -> MyMessage:
        return MyMessage( content=f"This is {self.id.type}-{self.id.key}. You said '{message.content}' and I disagree." )

# create a standalone runtime
runtime = SingleThreadedAgentRuntime()

async def main1():
    await SimpleAgent.register( runtime, "simple_agent", lambda: SimpleAgent() )

    runtime.start()

    response = await runtime.send_message( MyMessage(content="Well hi there!"), recipient=AgentId("simple_agent", "default") )

    print(">>>", response.content)

    await runtime.stop_when_idle()
    await runtime.close()

asyncio.run(main1())


