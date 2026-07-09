import hashlib

from sqlalchemy.orm import Session

from app.core.storage import save_files
from app.repositories.check_repository import create_check
from app.services.classifier import classify_document
from app.services.validator import validate_package
from app.services.status_resolver import resolve_status

MOCK_CONTRACTORS = [
    "ООО «ТехАгро»",
    'АО "СтройМаш"',
    'ООО "ПромТехника"',
    'ПАО "АгроПром"',
    'ООО "ЭнергоСеть"',
]

MOCK_SUBJECTS = [
    "Поставка минеральных удобрений",
    "Строительство складского комплекса",
    "Ремонт дорожного покрытия",
    "Поставка сельскохозяйственной техники",
    "Модернизация электросети",
]

MOCK_AMOUNTS = [
    "1 250 000 ₽",
    "3 480 000 ₽",
    "875 500 ₽",
    "5 120 000 ₽",
    "2 340 000 ₽",
]

MOCK_DATES = [
    "01.03.2025",
    "15.06.2025",
    "22.01.2025",
    "10.09.2025",
    "30.04.2025",
]


def _mock_extracted(doc_infos: list[dict]) -> dict:
    doc_names = "+".join(d["filename"] for d in doc_infos)
    seed = int(hashlib.md5(doc_names.encode()).hexdigest()[:8], 16)
    return {
        "contractor": MOCK_CONTRACTORS[seed % len(MOCK_CONTRACTORS)],
        "amount": MOCK_AMOUNTS[(seed // 7) % len(MOCK_AMOUNTS)],
        "date": MOCK_DATES[(seed // 13) % len(MOCK_DATES)],
        "subject": MOCK_SUBJECTS[(seed // 19) % len(MOCK_SUBJECTS)],
    }


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

    # 5. Prepare extracted data (mock — varies by filenames)
    extracted_data = _mock_extracted(doc_infos)

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
