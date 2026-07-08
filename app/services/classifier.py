from pathlib import Path


TYPE_KEYWORDS: dict[str, list[str]] = {
    "contract": ["договор", "contract", "дог", "dog"],
    "specification": ["спецификация", "specification", "спец", "spec"],
    "invoice": ["счёт-фактура", "счёт", "счет", "invoice", "сч", "schet"],
    "act": ["акт_приемки", "акт", "act", "upd", "упд"],
}


def classify_document(filename: str) -> str | None:
    stem = Path(filename).stem.lower()
    if not stem:
        return None
    # Build flat list of (keyword, type) sorted by keyword length (longest first)
    all_keywords = []
    for doc_type, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            all_keywords.append((kw, doc_type))
    all_keywords.sort(key=lambda x: -len(x[0]))
    for kw, doc_type in all_keywords:
        if kw in stem:
            return doc_type
    return None
