# Agentic AI & Multi-Agent Workflow Development


## Technologies: Python, OpenAI Agents SDK, LangGraph, AutoGen, LangChain, Pydantic, asyncio, SendGrid

* Developed a multi-agent research automation pipeline using the OpenAI Agents SDK, coordinating specialized planning, searching, report-writing, and email agents
* Implemented structured agent outputs using Pydantic models to generate search plans, research summaries, and detailed reports.
* Applied asynchronous programming with Python asyncio to execute multiple research tasks concurrently.
* Integrated web search tools and SendGrid email functionality to automate information retrieval report generation, and distribution.
* Explored multi-agent architectures for software engineering, coding assistance, and financial research using LangGraph and AutoGen


## Project overview

```mermaid
flowchart LR
    subgraph OpenAI["OpenAI"]
        A1["Career twin bot"]
        A2["Sales emails"]
        A3["Deep research"]
    end
    subgraph CrewAI["CrewAI"]
        B1["Stock picker"]
        B2["Coder"]
        B3["Engineering team"]
    end
    subgraph LangGraph["LangGraph"]
        C1["Basic chatbot"]
        C2["Search + memory"]
        C3["Browser agent"]
        C4["Sidekick"]
    end
    subgraph AutoGen["AutoGen"]
        D1["AgentChat + SQL"]
        D2["Multimodal team"]
        D3["Core runtime"]
    end
    OpenAI --> CrewAI --> LangGraph --> AutoGen
```

## Sales email system (OpenAI Agents SDK)

Three sales agents with different styles draft cold emails. The Sales Manager calls them as tools, picks the best draft, and hands off to the Email Manager, which writes a subject line, converts the email to HTML and sends it.

```mermaid
flowchart TD
    P["Professional<br/>sales agent tool"] --> M
    H["Humorous<br/>sales agent tool"] --> M
    C["Concise<br/>sales agent tool"] --> M
    M["Sales manager<br/>picks best draft"] -->|handoff| E["Email manager<br/>subject + HTML tools"]
    E --> S["Sent via SendGrid"]
```

## Deep research (OpenAI Agents SDK)

```mermaid
flowchart LR
    PL["Planner agent<br/>plans 3 queries"] --> SA["Search agents<br/>run in parallel"]
    SA --> W["Writer agent<br/>builds report"]
    W --> EM["Email agent<br/>HTML via SendGrid"]
```

## Stock picker (CrewAI, hierarchical process)

```mermaid
flowchart TD
    MG["Manager (GPT-4o)<br/>delegates tasks"] --> TF["Trend finder<br/>finds 2-3 companies"]
    MG --> FR["Researcher<br/>analyses each company"]
    MG --> SP["Stock picker<br/>picks best, sends push"]
    TF --> O1[("trending_companies.json")]
    FR --> O2[("research_report.json")]
    SP --> O3[("decision.md + push alert")]
    MEM["Memory: long-term, short-term, entity"] -.-> MG
```

## Engineering team (CrewAI, sequential process)

```mermaid
flowchart LR
    L["Engineering lead<br/>design (GPT-4o)"] --> B["Backend engineer<br/>accounts.py (Claude)"]
    B --> F["Frontend engineer<br/>Gradio app.py"]
    B --> T["Test engineer<br/>unit tests"]
```

## Sidekick (LangGraph)

A worker agent uses Playwright browser tools, and an evaluator agent checks the result against the user's success criteria, looping back with feedback until they are met. A `MemorySaver` checkpointer keeps each conversation thread.

```mermaid
flowchart TD
    U["User input<br/>request + success criteria"] --> WK["Worker agent<br/>GPT-4o-mini + tools"]
    WK <-->|tool calls| PW["Playwright tools<br/>browse, extract"]
    WK --> EV["Evaluator agent<br/>structured feedback"]
    EV -->|not met: retry with feedback| WK
    EV -->|criteria met or input needed| R["Return to user"]
```
