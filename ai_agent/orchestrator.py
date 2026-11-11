import os
from dotenv import load_dotenv
from llm.config import MODEL

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

from ai_agent.tools import ALL_TOOLS, TOOL_EXECUTORS

load_dotenv()

# Switched from llama-3.3-70b-versatile: that model frequently emits
# malformed tool-call text on Groq (<function=name{...}> instead of a
# proper tool call), which Groq's API rejects outright. gpt-oss-120b
# is Groq's current recommendation for reliable tool/function calling.
llm = ChatGroq(
    model=MODEL,
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY"),
)

SYSTEM_PROMPT = (
    "You are an orchestrator agent with access to three tools: a SQL "
    "database, a company spreadsheet, and a company PDF. Decide which "
    "tool(s) are needed to answer the user's question, call them, and then "
    "give a clear final answer in plain English. If a question needs data "
    "from more than one source, call multiple tools. "
    "If a tool returns an empty or zero result, do NOT assume or invent a "
    "reason why (e.g. do not guess the data is incomplete) — state plainly "
    "that no matching data was found and suggest rephrasing the question."
)

agent = create_react_agent(
    model=llm,
    tools=ALL_TOOLS,
    prompt=SYSTEM_PROMPT,
)


def build_message_history(chat_history):

    messages = []

    if chat_history:
        for chat in chat_history[-3:]:
            messages.append(HumanMessage(content=chat["question"]))
            messages.append(AIMessage(content=chat["answer"]))

    return messages


def keyword_fallback_route(question):
    """
    Last-resort deterministic router, used only if the LLM's tool-calling
    fails outright (e.g. malformed function-call text). Guarantees the
    app always returns something instead of an error message.
    """

    q = question.lower()

    tools_to_try = []

    db_words = ["database", "sql", "track", "album", "artist", "invoice",
                "customer", "employee", "genre", "playlist", "media"]
    sheet_words = ["spreadsheet", "excel", "csv", "revenue", "rent", "store",
                   "sales", "month", "uptime", "department"]
    pdf_words = ["report", "pdf", "policy", "refund", "return", "governance",
                 "outlook", "forecast", "document"]

    if any(w in q for w in db_words):
        tools_to_try.append("query_database")
    if any(w in q for w in sheet_words):
        tools_to_try.append("query_spreadsheet")
    if any(w in q for w in pdf_words):
        tools_to_try.append("query_pdf")

    if not tools_to_try:
        tools_to_try = ["query_database", "query_spreadsheet", "query_pdf"]

    tools_used = []
    steps = []
    combined_content = []

    for tool_name in tools_to_try:
        executor = TOOL_EXECUTORS.get(tool_name)
        if not executor:
            continue

        result_text = executor.invoke({"question": question})

        tools_used.append(tool_name)
        steps.append({"tool": tool_name, "args": {"question": question}, "result": {"content": result_text}})
        combined_content.append(result_text)

    answer = "\n\n".join(combined_content) if combined_content else (
        "I couldn't confidently answer that. Try rephrasing, or ask about one source at a time."
    )

    return {"answer": answer, "tools_used": tools_used, "steps": steps}


def run_agent(question, chat_history=None):

    messages = build_message_history(chat_history)
    messages.append(HumanMessage(content=question))

    try:
        response = agent.invoke({"messages": messages})

    except Exception:
        # Model failed to produce a valid tool call at all — fall back
        # to keyword routing so the app never shows a raw error.
        return keyword_fallback_route(question)

    result_messages = response.get("messages", [])

    tools_used = []
    steps = []
    final_answer = "I couldn't generate an answer."

    for msg in result_messages:

        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tools_used.append(tc["name"])

        if msg.__class__.__name__ == "ToolMessage":
            tool_name = getattr(msg, "name", "unknown_tool")
            steps.append({
                "tool": tool_name,
                "args": {},
                "result": {"content": str(msg.content)}
            })

        if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
            final_answer = msg.content

    return {
        "answer": final_answer,
        "tools_used": tools_used,
        "steps": steps,
    }