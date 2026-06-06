from io import BytesIO
import requests
from autogen_agentchat.messages import TextMessage, MultiModalMessage
from autogen_core import Image as AGImage
from PIL import Image
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from IPython.display import display, Markdown
from pydantic import BaseModel, Field
from typing import Literal
import asyncio
from autogen_ext.tools.langchain import LangChainToolAdapter
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_core.tools import Tool
from autogen_agentchat.conditions import TextMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
load_dotenv()

url = "https://edwarddonner.com/wp-content/uploads/2024/10/from-software-engineer-to-AI-DS.jpeg"
pil_image = Image.open(BytesIO(requests.get(url=url).content))
img = AGImage(pil_image)

multi_modal_message = MultiModalMessage(content=["Describe the content of this image in detail",img],source="User")

model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")


class ImageDescription(BaseModel):
    scene: str = Field(description="Briefly, the overall scene of the image")
    message: str = Field(description="The point that the image is trying to convery.")
    style: str = Field(description="The artistic style of the image")
    orientation: Literal["portrait","landscape","square"] = Field(description="The orientation of the image")

describer = AssistantAgent(
    name="description_agent",
    model_client=model_client,
    system_message="You are good at describing images",
    output_content_type=ImageDescription
)

async def main1():
    response = await describer.on_messages(
        [multi_modal_message],
        cancellation_token=CancellationToken()
    )
    
    print(response.chat_message.content)

#asyncio.run(main1())

#Using LangChain tools from AutoGen

prompt = """Your task is to find a one-way non-stop flight from JFK to LHR in June 2025.
First search online for promising deals.
Next, write all the deals to a file called flights.md with full details.
Finally, select the one you think is best and reply with a short summary.
Reply with the selected flight only, and only after you have written the details to the file."""

serper = GoogleSerperAPIWrapper()
langchain_serper = Tool(name="internet_search",func=serper.run,description="useful for when you need to search the internet")
autogen_serper = LangChainToolAdapter(langchain_serper)
autogen_tools = [autogen_serper]

langchain_file_management_tools = FileManagementToolkit(root_dir="sandbox").get_tools()
for tool in langchain_file_management_tools:
    autogen_tools.append(LangChainToolAdapter(tool))

for tool in autogen_tools:
    print(tool.name,tool.description)

agent = AssistantAgent(name="searcher",model_client=model_client,tools=autogen_tools,reflect_on_tool_use=True)
message = TextMessage(content=prompt,source="user")

async def main2():
    response = await agent.on_messages(
        [message],
        cancellation_token=CancellationToken()
    )
    for msg in response.inner_messages:
        print(msg.content)

#asyncio.run(main2())

#Team interaction

prompt = """Your task is to find a one-way non-stop flight from JFK to LHR in June 2026. 
First search online for promising deals.
Then reply with the best option you found.
Each time you are called, you should reply with another different option."""

primary_agent = AssistantAgent(
    "primary",
    model_client=model_client,
    tools=[autogen_serper],
    system_message="You are a helpful AI research assistant who looks for promising deals on flights. Respond only with one" \
    "option, strictly 1 option, do not mention others that you considered. Make sure it's different from any previous option mentioned."
)

evaluation_agent = AssistantAgent(
    "evaluator",
    model_client=model_client,
    system_message="Check whether it looks like the assistant has given a very promising recommendation for a flight." \
    "Respond with 'Approve' when you are satisfied that the recommendation is good." \
    "If you have only seem one reply from the assistant, then do not approve - you need to see more answers" \
    "from the assistant. Make sure you've seen at least answers before approving."
)

text_termination = TextMessageTermination("Approve")

team = RoundRobinGroupChat([primary_agent,evaluation_agent],termination_condition=text_termination)

async def main3():
    response = await team.run(task=prompt)
    for msg in response.messages:
        print(f"{msg.source}:\n{msg.content}\n\n")

#asyncio.run(main3())



