from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import Tool
from typing import TypedDict,Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph,START,END
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.checkpoint.memory import MemorySaver
import gradio as gr
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
import requests
import os
load_dotenv()

#Set up LangSmith
serper = GoogleSerperAPIWrapper()
serper.run("What is the capital of Norway?")

tool_search =Tool(
        name="search",
        func=serper.run,
        description="Useful for when you need more information from an online search"
    )

def push(text: str):
    """Send a push notification to the user"""
    requests.post(os.getenv("PUSHOVER_URL"), data = {"token": os.getenv("PUSHOVER_TOKEN"), "user": os.getenv("PUSHOVER_USER"), "message": text})

tool_push = Tool(
        name="send_push_notification",
        func=push,
        description="useful for when you want to send a push notification"
    )

tools = [tool_search,tool_push]
class State(TypedDict):
    messages: Annotated[list,add_messages]


#To add memory
memory = MemorySaver()

#step 1 and 2
graph_builder = StateGraph(State)

#Step 3

llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools=tools)

def chatbot(state:State):
    print(state)
    return {"messages":[llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot",chatbot)
graph_builder.add_node("tools",ToolNode(tools=tools))

#step 4
graph_builder.add_conditional_edges("chatbot",tools_condition,"tools")

graph_builder.add_edge("tools","chatbot")
graph_builder.add_edge(START,"chatbot")

#step 5
graph = graph_builder.compile(checkpointer=memory)
print(graph.get_graph().draw_mermaid())

config = {"configurable":{"thread_id":1}}

def chat(user_input:str,history):
    result = graph.invoke({"messages":[{"role":"user","content":user_input}]},config=config)
    return result["messages"][-1].content

#gr.ChatInterface(chat).launch()

#print(graph.get_state(config))

#list(graph.get_state_history[config])


#Store in SQL
db_path = "memory.db"

conn = sqlite3.connect(db_path,check_same_thread=False)
sql_memory = SqliteSaver(conn=conn)

#sqliteGraph
sql_graph = graph_builder.compile(checkpointer=sql_memory)

config = {"configurable":{"thread_id":3}}

def chat_sql(user_input:str,history):
    result = sql_graph.invoke({"messages":[{"role":"user","content":user_input}]},config=config)
    return result["messages"][-1].content

gr.ChatInterface(chat_sql).launch()