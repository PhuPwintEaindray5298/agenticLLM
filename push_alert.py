from openai import OpenAI
from PyPDF2 import PdfReader
import gradio as gr
from pydantic import BaseModel
import requests
import json
from dotenv import load_dotenv
import os
load_dotenv()

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

def push(message):
    print("Push:{message}")
    payload = {"user":pushover_user,"token":pushover_token,"message":message}
    requests.post(pushover_url,data=payload)

push("Hi!!!")

def record_user_details(email,name="Name not provided",notes="not provided"):
    push(f"Recording interest from{name} with email {email} and notes {notes}")
    return {"recorded":"ok"}

def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    return {"recorded":"ok"}

record_user_details_json = {
    "name":"record_user_details",
    "description":"Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters":{
        "type":"object",
        "properties":{
            "email":{
                "type":"string",
                "description":"The email address of this user"
            },
            "name":{
                "type":"string",
                "description":"The user's name, if they provided it"
            },
            "notes":{
                "type":"string",
                "description":"Any additional information about the conversation that's worth recording to give context"
            },
        },
        "required":["email"],
        "additionalProperties":False
    }
}

record_unknown_question_json = {
    "name":"record_unknown_question",
    "description":"Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters":{
        "type":"object",
        "properties":{
            "question":{
                "type":"string",
                "description":"The question that couldn't be answered"
            },
        },
        "required":["question"],
        "additionalProperties":False
    }
}

tools = [{"type":"function","function":record_user_details_json},
         {"type":"function","function":record_unknown_question_json}]

""" def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool Called: {tool_name}",flush=True)

        if tool_name == "record_user_details":
            result = record_user_details(**arguments)
        elif tool_name == "record_unknown_question":
            result = record_unknown_question(**arguments)
        results.append({"role":"tool","content":json.dumps(result),"tool_call_id":tool_call.id})
    return results """

#globals()["record_unknown_question"]("This is a really hard question")

def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool Called: {tool_name}",flush=True)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append({"role":"tool","content":json.dumps(result),"tool_call_id":tool_call.id})
    return results

reader = PdfReader("linkedin.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text


with open("summary.txt","r",encoding="utf-8") as f:
    summary = f.read()

name = "Ed Donner"

system_prompt = f"""You are acting as {name}. You are answering questions on {name}'s website particularly questions related to {name}'s career, background, skills and experience. Your responsibility is to
represent {name} for interactions on the website as faithfully as possible. You are given a summary of {name}'s background and LinkedIn profile
which you can use to answer questions. Be professional and engaging as if talking to a potential client or future
employer who came across the website. If you don't know the answer, say so"""
system_prompt += f"\n\n##Summary:\n{summary}\n\n##LinkedIn Profile:\n{linkedin}\n\n"
system_prompt += f"With this context, please chat with the user, always staying in character as {name}"

def chat(message,history):
    messages = [{"role":"system","content":system_prompt}] + history + [{"role":"user","content":message}]
    done = False
    while not done:
        response = openai.chat.completions.create(model = "gpt-4", messages=messages,tools=tools)
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "tool_calls":
             message = response.choices[0].message
             tool_calls = message.tool_calls
             results = handle_tool_calls(tool_calls)
             messages.append(message)
             messages.append(results)
        else:
            done = True
        
    return response.choices[0].message.content

gr.ChatInterface(chat).launch()

