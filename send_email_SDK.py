from dotenv import load_dotenv
import os
from agents import Agent, Runner, trace, function_tool
import asyncio
from openai.types.responses import ResponseTextDeltaEvent
from typing import Dict
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
load_dotenv()

instructions1 = """You are a sales agent working for ComplAI, a company that provides a SaaS tool for ensuring SOC2 compliance
and preparing for audits, powered by AI. You write professional, serious cold emails.
"""

instructions2 = """You are a humorous, engaging sales agent working for ComplAI, a companny that provides a SaaS
tool for ensuring SOC2 compliance and preparing for audits, powered by AI. You write witty, engaging cold emails
that are likely to get a response.
"""

instructions3 = """ You are a busy sales agent working for ComplAI, a company that provides a SaaS tool for ensuring
SOC2 compliance and preparing for audits, powered by AI. You write concise, to the point cold emails.
"""

sales_agent1 = Agent(
    name="Professional Sales Agent",
    instructions=instructions1,
    model="gpt-5"
)

sales_agent2 = Agent(
    name="Engaging Sales Agent",
    instructions=instructions2,
    model="gpt-5"
)

sales_agent3 = Agent(
    name="Busy Sales Agent",
    instructions=instructions3,
    model="gpt-5"
)

async def main():
    result = Runner.run_streamed(
        sales_agent1,
        input="Write a cold sales email"
    )

    async for event in result.stream_events():
        if (
            event.type == "raw_response_event"
            and isinstance(event.data, ResponseTextDeltaEvent)
        ):
            print(event.data.delta, end="", flush=True)

#asyncio.run(main())

async def main1():
    with trace("Parallel cold emails"):
        results = await asyncio.gather(
            Runner.run(sales_agent1,"Write a cold sales email"),
            Runner.run(sales_agent2,"Write a cold sales email"),
            Runner.run(sales_agent3,"Write a cold sales email")
        )
    outputs = [result.final_output for result in results]

    for output in outputs:
        print(output + "\n\n")

#asyncio.run(main1())

sales_picker = Agent(
    name="sales_picker",
    instructions="""You pick the best cold sales email from the given options.
    Imagine you are a customer and pick the one you are most likely to respond to.
    Do not give an explanation; reply with the selected email only."""
)

async def main2():
    with trace("Selection from sales people"):
        results = await asyncio.gather(
            Runner.run(sales_agent1,"Write a cold sales email"),
            Runner.run(sales_agent2,"Write a cold sales email"),
            Runner.run(sales_agent3,"Write a cold sales email")
        )
    outputs = [result.final_output for result in results]

    emails = "Cold sales emails:\n\n".join(outputs)

    best = await Runner.run(sales_picker,emails)

    print(f"Best sales emails:\n{best.final_output}")

#asyncio.run(main2())

@function_tool
def send_email(body:str):
    """Send out an email with the given body to all sales prospects"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("phupwint.eaindray@nhs.net")
    to_email = To("eaindrayphoopwint5@gmail.com")
    content = Content("text/plain",body)
    mail = Mail(from_email,to_email,"Sales email",content).get()
    response = sg.client.mail.send.post(request_body=mail)
    return {"status":"success"}

#convert agent as tool
tool1 = sales_agent1.as_tool(tool_name="sales_agent1",tool_description="Write a cold sales email")
tool2 = sales_agent2.as_tool(tool_name="sales_agent2",tool_description="Write a cold sales email")
tool3 = sales_agent3.as_tool(tool_name="sales_agent3",tool_description="Write a cold sales email")

tools = [tool1,tool2,tool3,send_email]

instructions = """You are a sales manager working for ComplAI. You use the tools given to you to generate cold
sales emails. You never generate sales emails yourself; you always use the tools. You try all 3 sales_agent tools once 
before choosing the best one. You pick the single best email and use the send_email tool to send the best email (and only the best email) 
to the user."""

sales_manager = Agent(name="Sales Manager",instructions=instructions,tools=tools,model="gpt-5")

message = "Send a cold sales email addressed to 'Dear CEO'"

async def main3():
    with trace("Sales manager"):
        results = await Runner.run(sales_manager,message)

#asyncio.run(main3())

subject_instructions = """You can write a subject for a cold sales email.
You are given a message and you need to write a subject for an email that is likely to get a response"""

html_instructions = """ You can convert a text email body to an HTML email body.
You are given a text email body which might have somoe markdown and you need to convert it to an HTML email
body with simple, clear, compelling layout and design.
"""

subject_writer = Agent(name="Email Subject Writer",instructions=subject_instructions,model="gpt-5.2")
subject_tool = subject_writer.as_tool(tool_name="subject_writer",tool_description="Write a subject for a cold sales email")

html_converter = Agent(name="HTML Email Body Converter",instructions=html_instructions,model="gpt-5.2")
html_tool = html_converter.as_tool(tool_name="html_converter",tool_description="Convert a text email body to an HTML email body")

@function_tool
def send_html_email(subject:str,html_body:str) -> Dict[str,str]:
    """Send out an email with the given subject and HTML body to all sales prospects"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("phupwint.eaindray@nhs.net")
    to_email = To("eaindrayphoopwint5@gmail.com")
    content = Content("text/html",html_body)
    mail = Mail(from_email,to_email,subject,content).get()
    response = sg.client.mail.send.post(request_body=mail)
    return {"status":"success"}

tools = [subject_tool, html_tool, send_html_email]

instructions = """You are an email formatter and sender. You receive the body of an email to be sent.
You firest use the subject_writer tool to write the subject for the email, then use the html_converter tool to 
convert the body to HTML. Finally you use send_html_email tool to send the email with the subject and HTML body."""

emailer_agent = Agent(
    name="Email Manager",
    instructions=instructions,
    tools=tools,
    model="gpt-5.2",
    handoff_description="Convert an email to HTML and send it"
)

tools = [tool1, tool2, tool3]
handsoffs = [emailer_agent]

#print(tools)
#print(handsoffs)

sales_manager_instructions = """You are a sales manager working for ComplAI. You use the tools given to you
to generate cold sales email. You never generate sales emails yourself; you always use the tools. You try all
3 sales agent tools at least once before choosing the best one. You can use the tools multiple times if you're not
satisfied with the results from the first try. You select the single best email using you own judgement of which
email will be most effective. After picking the email, you handoff to the Email Manager agent to format and send the email."""

sales_manager = Agent(
    name="Sales Manager",
    instructions=sales_manager_instructions,
    tools=tools,
    handoffs=handsoffs,
    model="gpt-5.2"
)

async def main4():
    with trace("Automated SDR"):
        results = await Runner.run(sales_manager,"Send out a cold sales email addressed to Dear CEO from Alice")

asyncio.run(main4())