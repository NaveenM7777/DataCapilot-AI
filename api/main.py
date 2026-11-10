from fastapi import FastAPI, HTTPException

from api.schemas import (
    AgentQueryResponse,
    ExcelQueryResponse,
    PDFQueryResponse,
    QuestionRequest,
    SQLQueryResponse,
)
from api.services import (
    ask_ai_agent,
    ask_excel_agent,
    ask_pdf_agent,
    ask_sql_agent,
)

app = FastAPI(title="DataCapilot-AI API", version="0.2.0")


def _run(agent_function, question):
    """Runs an agent and turns any crash into a clean 500 JSON error."""
    try:
        return agent_function(question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sql/query", response_model=SQLQueryResponse)
def sql_query(request: QuestionRequest):
    result = _run(ask_sql_agent, request.question)
    return SQLQueryResponse(question=request.question, **result)


@app.post("/excel/query", response_model=ExcelQueryResponse)
def excel_query(request: QuestionRequest):
    result = _run(ask_excel_agent, request.question)
    return ExcelQueryResponse(question=request.question, **result)


@app.post("/pdf/query", response_model=PDFQueryResponse)
def pdf_query(request: QuestionRequest):
    result = _run(ask_pdf_agent, request.question)
    return PDFQueryResponse(question=request.question, **result)


@app.post("/agent/query", response_model=AgentQueryResponse)
def agent_query(request: QuestionRequest):
    result = _run(ask_ai_agent, request.question)
    return AgentQueryResponse(question=request.question, **result)