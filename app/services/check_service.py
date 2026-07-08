from sqlalchemy.orm import Session

from app.core.storage import save_files
from app.repositories.check_repository import create_check
from app.services.classifier import classify_document
from app.services.validator import validate_package
from app.services.status_resolver import resolve_status


def process_check(
    db: Session,
    files: list[tuple[str, bytes]],
    program: str,
) -> dict:
    # 1. Save files to disk
    saved_files = save_files(files)

    # 2. Classify each document
    doc_infos = []
    for original_name, file_path, size_kb in saved_files:
        detected_type = classify_document(original_name)
        doc_infos.append({
            "filename": original_name,
            "detected_type": detected_type,
            "file_path": file_path,
            "size_kb": size_kb,
        })

    # 3. Validate package completeness
    validation_input = [
        (d["filename"], d["detected_type"], d["size_kb"])
        for d in doc_infos
    ]
    issues = validate_package(validation_input, program)

    # 4. Resolve status
    status_result = resolve_status(issues)

    # 5. Prepare extracted data (stub)
    extracted_data = {
        "contractor": "ООО «ТехАгро»",
        "amount": "1 250 000 ₽",
        "date": "01.03.2025",
        "subject": "Поставка минеральных удобрений",
    }

    # 6. Save to database
    check = create_check(
        db=db,
        program=program,
        status=status_result.status,
        status_label=status_result.status_label,
        reason=status_result.reason,
        document_count=len(doc_infos),
        extracted_data=extracted_data,
        documents=doc_infos,
        issues=[{"level": i.level, "message": i.message} for i in issues],
    )

    return {
        "check_id": check.id,
        "status": check.status,
        "status_label": check.status_label,
        "reason": check.reason,
        "issues": [{"level": i.level, "message": i.message} for i in issues],
        "documents": [
            {"name": d["filename"], "detected_type": d["detected_type"], "size_kb": d["size_kb"]}
            for d in doc_infos
        ],
        "extracted": extracted_data,
        "checked_at": check.created_at.isoformat() + "Z",
    }
