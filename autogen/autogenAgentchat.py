from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
import asyncio
import os
import sqlite3
load_dotenv()

#Model 
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

#Message
message = TextMessage(content="I'd like to work in Europe",source="user")

print(message)

#Agent
agent = AssistantAgent(
    name="airline_agent",
    model_client=model_client,
    system_message="You are a helpful assistant for an airline. You give short, humorous answers.",
    model_client_stream=True
)

#put it all together
async def main():
    response = await agent.on_messages(
        [message],
        cancellation_token=CancellationToken()
    )

    print(response.chat_message.content)

#asyncio.run(main())

if os.path.exists("jobs.db"):
    os.remove("jobs.db")

conn = sqlite3.connect("jobs.db")
c = conn.cursor()
c.execute("CREATE TABLE jobs (job_name TEXT PRIMARY KEY,salary REAL)")
conn.commit()
conn.close()

#Populate database
def save_job_price(job_name,salary_price):
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute("REPLACE INTO jobs (job_name,salary) VALUES (?,?)",(job_name.upper(),salary_price))
    conn.commit()
    conn.close()

save_job_price("Data Science",450000)
save_job_price("ML Engineer",480000)
save_job_price("GenAI Engineer",500000)
save_job_price("Data Engineer",400000)
save_job_price("Data Analyst",380000)

def get_job_price(job_name:str) -> float | None:
    """Get the salary for the jobs"""
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute("SELECT salary FROM jobs WHERE job_name = ?", (job_name.upper(),))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

print(get_job_price("GenAI Engineer"))

smart_agent = AssistantAgent(
    name="smart_job_agent",
    model_client=model_client,
    system_message="You are a helpful assistant for a job. You give short, humorous answers, including the salary of job.",
    model_client_stream=True,
    tools=[get_job_price],
    reflect_on_tool_use=True
)

async def main1():
    response = await smart_agent.on_messages(
        [message],
        cancellation_token=CancellationToken()
    )
    for inner in response.inner_messages:
        print(inner.chat_message)
    print(response.chat_message.content)

asyncio.run(main1())