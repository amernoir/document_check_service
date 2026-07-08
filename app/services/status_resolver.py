from dataclasses import dataclass

from app.services.validator import Issue


STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_IN_PROGRESS = "check_in_progress"


@dataclass
class StatusResult:
    status: str
    status_label: str
    reason: str | None


def resolve_status(issues: list[Issue]) -> StatusResult:
    has_errors = any(i.level == "error" for i in issues)

    if has_errors:
        error_messages = [i.message for i in issues if i.level == "error"]
        reason = "; ".join(error_messages)
        return StatusResult(
            status=STATUS_REJECTED,
            status_label="Нельзя заявлять в банк",
            reason=reason,
        )

    return StatusResult(
        status=STATUS_APPROVED,
        status_label="Можно заявлять в банк",
        reason=None,
    )
