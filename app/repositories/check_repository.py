from sqlalchemy.orm import Session

from app.models import Check, Document, CheckIssue


def create_check(
    db: Session,
    program: str,
    status: str,
    status_label: str,
    reason: str | None,
    document_count: int,
    extracted_data: dict | None,
    documents: list[dict],
    issues: list[dict],
) -> Check:
    check = Check(
        program=program,
        status=status,
        status_label=status_label,
        reason=reason,
        document_count=document_count,
        extracted_data=extracted_data,
    )
    db.add(check)
    db.flush()

    for doc in documents:
        db.add(Document(check_id=check.id, **doc))

    for issue in issues:
        db.add(CheckIssue(check_id=check.id, **issue))

    db.commit()
    db.refresh(check)
    return check


def get_check(db: Session, check_id: str) -> Check | None:
    return db.query(Check).filter(Check.id == check_id).first()


def list_checks(db: Session) -> list[Check]:
    return db.query(Check).order_by(Check.created_at.desc()).all()
