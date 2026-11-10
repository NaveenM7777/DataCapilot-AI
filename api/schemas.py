from pydantic import BaseModel, ConfigDict, Field


class QuestionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(..., min_length=1, max_length=1000)


class SQLQueryResponse(BaseModel):
    question: str
    sql: str
    answer: str


class ExcelQueryResponse(BaseModel):
    question: str
    code: str
    answer: str


class PDFQueryResponse(BaseModel):
    question: str
    answer: str
    pages: list[int]


class AgentQueryResponse(BaseModel):
    question: str
    answer: str
    tools_used: list[str]