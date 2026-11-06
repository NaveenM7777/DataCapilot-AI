from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from api.schemas import FileQueryResponse, SQLQueryRequest, SQLQueryResponse
from api.services import ask_excel_agent, ask_pdf_agent, ask_sql_agent

app = FastAPI(title="DataCapilot-AI API", version="0.1.0")

EXCEL_TYPES = (".xlsx", ".xls", ".csv")
PDF_TYPES = (".pdf",)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sql/query", response_model=SQLQueryResponse)
def sql_query(request: SQLQueryRequest):
    try:
        result = ask_sql_agent(request.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return SQLQueryResponse(question=request.question, **result)


def _check_extension(filename: str, allowed: tuple):
    if not filename.lower().endswith(allowed):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed)}",
        )


@app.post("/excel/analyze", response_model=FileQueryResponse)
def excel_analyze(file: UploadFile = File(...), question: str = Form(...)):
    _check_extension(file.filename, EXCEL_TYPES)
    content = file.file.read()
    try:
        result = ask_excel_agent(content, file.filename, question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return FileQueryResponse(filename=file.filename, question=question, **result)


@app.post("/pdf/ask", response_model=FileQueryResponse)
def pdf_ask(file: UploadFile = File(...), question: str = Form(...)):
    _check_extension(file.filename, PDF_TYPES)
    content = file.file.read()
    try:
        result = ask_pdf_agent(content, file.filename, question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return FileQueryResponse(filename=file.filename, question=question, **result)