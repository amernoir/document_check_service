from dataclasses import dataclass

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".png"}
MAX_SIZE_KB = 20 * 1024  # 20 MB

REQUIRED_TYPES = {
    "federal": {"contract", "specification", "invoice", "act"},
    "regional": {"contract", "invoice", "act"},
}


@dataclass
class Issue:
    level: str  # "error" or "warning"
    message: str


def validate_package(
    documents: list[tuple[str, str | None, int | None]],
    program: str,
) -> list[Issue]:
    issues: list[Issue] = []
    detected_types: set[str] = set()

    for filename, detected_type, *rest in documents:
        size_kb = rest[0] if rest else None

        # Check file extension
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            issues.append(Issue(level="warning", message=f"Недопустимый формат файла: «{filename}»"))

        # Check file size
        if size_kb and size_kb > MAX_SIZE_KB:
            issues.append(Issue(level="warning", message=f"Файл «{filename}» превышает 20 МБ"))

        # Check unrecognized type
        if detected_type is None:
            issues.append(Issue(level="warning", message=f"Не удалось определить тип документа: «{filename}»"))
        else:
            detected_types.add(detected_type)

    # Check required types
    required = REQUIRED_TYPES.get(program, set())
    missing = required - detected_types
    type_names = {
        "contract": "договор",
        "specification": "спецификация",
        "invoice": "счёт",
        "act": "акт",
    }
    for t in sorted(missing):
        issues.append(Issue(level="error", message=f"Отсутствует обязательный документ: {type_names.get(t, t)}"))

    return issues
