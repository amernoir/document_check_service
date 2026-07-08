from pydantic import BaseModel


class IssueSchema(BaseModel):
    level: str
    message: str


class DocumentSchema(BaseModel):
    name: str
    detected_type: str | None
    size_kb: int


class ExtractedData(BaseModel):
    contractor: str | None = None
    amount: str | None = None
    date: str | None = None
    subject: str | None = None


class CheckResponse(BaseModel):
    check_id: str
    status: str
    status_label: str
    reason: str | None = None
    issues: list[IssueSchema]
    documents: list[DocumentSchema]
    extracted: ExtractedData | None = None
    checked_at: str


class CheckListItem(BaseModel):
    id: str
    created_at: str
    program: str
    status: str
    document_count: int
