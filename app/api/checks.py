from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.check_repository import get_check, list_checks
from app.schemas.check import CheckResponse, CheckListItem
from app.services.check_service import process_check

router = APIRouter(prefix="/api/checks", tags=["checks"])


@router.post("", response_model=CheckResponse)
async def create_check(
    files: list[UploadFile] = File(...),
    program: str = Form(...),
    db: Session = Depends(get_db),
):
    if program not in ("federal", "regional"):
        raise HTTPException(status_code=400, detail="Program must be 'federal' or 'regional'")

    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    file_data = []
    for f in files:
        content = await f.read()
        file_data.append((f.filename, content))

    result = process_check(db, file_data, program)
    return result


@router.get("", response_model=list[CheckListItem])
def list_all_checks(db: Session = Depends(get_db)):
    checks = list_checks(db)
    return [
        CheckListItem(
            id=c.id,
            created_at=c.created_at.isoformat() + "Z",
            program=c.program,
            status=c.status,
            document_count=c.document_count,
        )
        for c in checks
    ]


@router.get("/{check_id}", response_model=CheckResponse)
def get_check_by_id(check_id: str, db: Session = Depends(get_db)):
    check = get_check(db, check_id)
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")

    issues = [{"level": i.level, "message": i.message} for i in check.issues]
    documents = [
        {"name": d.filename, "detected_type": d.detected_type, "size_kb": d.size_kb}
        for d in check.documents
    ]

    return CheckResponse(
        check_id=check.id,
        status=check.status,
        status_label=check.status_label,
        reason=check.reason,
        issues=issues,
        documents=documents,
        extracted=check.extracted_data,
        checked_at=check.created_at.isoformat() + "Z",
    )
