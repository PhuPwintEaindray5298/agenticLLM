from dotenv import load_dotenv
import os
from agents import Agent, Runner, trace, function_tool, gen_trace_id, WebSearchTool
from agents.model_settings import ModelSettings
import sendgrid
import asyncio
from sendgrid.helpers.mail import Email, Mail, To, Content
from pydantic import BaseModel
from typing import Dict
from IPython.display import display, Markdown
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()
console = Console()
instructions = """ You are a research assistant. Given a search term, you search the web for the term and produce
a concise summary of the results. The summary must 2-3 paragraphs and less than 300 words. Capture the main points. 
Write succintly, no need to have complete sentences or good grammar. This will be consumed by someone synthesizing
a report, so it's vital you capture the essence and ignore fluff. Do not include any additional commentary other
than summary itself.
"""

search_agent = Agent(
    name="Search agent",
    instructions=instructions,
    tools = [WebSearchTool(search_context_size="low")],
    model = "gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required")
)

async def main1():
    with trace("Search"):
        results = await Runner.run(search_agent,"Latest AI Agent frameworks in 2026")
    console.print(Markdown(results.final_output))

#asyncio.run(main1())

NUM_OF_SEARCH = 3

instructions = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {NUM_OF_SEARCH} terms to query for."

class WebSearchItem(BaseModel):
    reason:str
    "Your reasoning for why this search is important to the query."

    query:str
    "The search term to use for the web search."

class WebSearchPlan(BaseModel):
    searches : list[WebSearchItem]
    """A list of web searches to perform to best answer the query."""

planner_agent = Agent(
    name="Planner Agent",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=WebSearchPlan
)

async def main2():
    with trace("Search"):
        results = await Runner.run(planner_agent,"Latest AI Agent frameworks in 2026")
    print(results.final_output)

#asyncio.run(main2())

@function_tool
def send_html_email(subject:str,html_body:str) -> Dict[str,str]:
    """Send out an email with the given subject and HTML body """
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("phupwint.eaindray@nhs.net")
    to_email = To("eaindrayphoopwint5@gmail.com")
    content = Content("text/html",html_body)
    mail = Mail(from_email,to_email,subject,content).get()
    response = sg.client.mail.send.post(request_body=mail)
    return {"status":"success"}

instructions = """You are able to send a nicely formatted HTML email based on a detailed report. You will be provided
with a detailed report. You should use your tool to send one email, providing the report converted into clean,
well presented HTML with appropriate subject line."""

email_agent = Agent(
    name="Email Agent",
    instructions=instructions,
    tools=[send_html_email],
    model="gpt-4o-mini"
)

instructions = (
    "You are a senior research tasked with writing a cohensive report for a research query."
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)

class ReportData(BaseModel):
    short_summary:str
    """A short 2-3 sentence summary of the findings"""

    markdown_report:str
    """The final report"""

    follow_up_questions:list[str]
    """Suggested topics to research further"""

writer_agent = Agent(
    name="WriterAgent",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=ReportData
)

async def plan_searches(query:str):
    """Use the planner agent to plan which searches to run for the query"""
    print("Planning searches...")
    result = await Runner.run(planner_agent,f"Query: {query}")
    print(f"Will perform {len(result.final_output.searches)} searches")
    return result.final_output

async def perform_searches(search_plan:WebSearchPlan):
    """Call search() for each item in the search plan"""
    print("Searching...")
    num_completed = 0
    tasks = [asyncio.create_task(search(item)) for item in search_plan.searches]
    results = await asyncio.gather(*tasks)
    print("Finished Searching")
    return results

async def search(item:WebSearchItem):
    """Use the search agent to run a web search for each item in the search plan """
    input = f"Search term: {item.query}\nReason for searching: {item.reason}"
    result = await Runner.run(search_agent,input)
    return result.final_output

async def write_report(query:str, search_result:list[str]):
    """Use the writer agent to write a report based on the search results"""
    print("Thinking about report...")
    input = f"Original query: {query}\nSummarized search results: {search_result}"
    result = await Runner.run(writer_agent,input)
    print("Finished writing report")
    return result.final_output

async def send_email(report:ReportData):
    """Use the email agent to send an email with the report"""
    print("Writing email...")
    result = await Runner.run(email_agent, report.markdown_report)
    print("Email sent")
    return report

async def main3():
    with trace("Research Trace"):
        search_plan = await plan_searches(query="Latest AI Agent frameworks in 2026")
        search_results = await perform_searches(search_plan=search_plan)
        report = await write_report(query="Latest AI Agent frameworks in 2026",search_result=search_results)
        await send_email(report=report)
        print("Done!!!")

asyncio.run(main3())