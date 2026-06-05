from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import gradio as gr
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()
console = Console()



#Step 1: Define the State object

class State(BaseModel):
    messages: Annotated[list,add_messages]

#Step 2: Start the Graph Builder with this State class
graph_builder = StateGraph(State)

#Step 3: Create a node
llm = ChatOpenAI(model="gpt-4o-mini")
def chatbot_node(old_state:State) -> State:
    response=llm.invoke(old_state.messages)
    new_state = State(messages=response)
    return new_state

graph_builder.add_node("chatbot",chatbot_node)

#Step 4: Create edges
graph_builder.add_edge(START,"chatbot")
graph_builder.add_edge("chatbot",END)

#Step 5: Compile the graph
graph = graph_builder.compile()
console.print(Markdown(graph.get_graph().draw_mermaid()))

def chat(user_input: str, history):
    state = State(messages=[{"role":"user","content":user_input}])
    result = graph.invoke(state)
    print(result)
    return result["messages"][-1].content

gr.ChatInterface(chat).launch()