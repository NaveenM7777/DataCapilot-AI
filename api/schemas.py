from pydantic import BaseModel, Field


class SQLQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)


class SQLQueryResponse(BaseModel):
    question: str
    sql: str
    answer: str


class FileQueryResponse(BaseModel):
    filename: str
    question: str
    answer: str