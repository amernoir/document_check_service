import pytest
from app.services.status_resolver import resolve_status, StatusResult
from app.services.validator import Issue


class TestResolveStatus:
    def test_no_issues_approved(self):
        result = resolve_status([])
        assert result.status == "approved"
        assert result.status_label == "Можно заявлять в банк"

    def test_has_errors_rejected(self):
        issues = [Issue(level="error", message="Missing contract")]
        result = resolve_status(issues)
        assert result.status == "rejected"

    def test_only_warnings_approved(self):
        issues = [Issue(level="warning", message="Unknown file type")]
        result = resolve_status(issues)
        assert result.status == "approved"

    def test_mixed_errors_and_warnings_rejected(self):
        issues = [
            Issue(level="error", message="Missing specification"),
            Issue(level="warning", message="Large file"),
        ]
        result = resolve_status(issues)
        assert result.status == "rejected"

    def test_empty_list_approved(self):
        result = resolve_status([])
        assert result.status == "approved"
