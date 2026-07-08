import pytest
from app.services.validator import validate_package, Issue


class TestValidatePackage:
    def test_federal_complete(self):
        docs = [("contract.pdf", "contract"), ("spec.pdf", "specification"), ("invoice.pdf", "invoice"), ("act.pdf", "act")]
        issues = validate_package(docs, "federal")
        assert len([i for i in issues if i.level == "error"]) == 0

    def test_federal_missing_specification(self):
        docs = [("contract.pdf", "contract"), ("invoice.pdf", "invoice"), ("act.pdf", "act")]
        issues = validate_package(docs, "federal")
        error_msgs = [i.message for i in issues if i.level == "error"]
        assert any("спецификация" in msg.lower() for msg in error_msgs)

    def test_regional_complete(self):
        docs = [("contract.pdf", "contract"), ("invoice.pdf", "invoice"), ("act.pdf", "act")]
        issues = validate_package(docs, "regional")
        assert len([i for i in issues if i.level == "error"]) == 0

    def test_regional_missing_act(self):
        docs = [("contract.pdf", "contract"), ("invoice.pdf", "invoice")]
        issues = validate_package(docs, "regional")
        error_msgs = [i.message for i in issues if i.level == "error"]
        assert any("акт" in msg.lower() for msg in error_msgs)

    def test_unknown_format_warning(self):
        docs = [("report.exe", None)]
        issues = validate_package(docs, "federal")
        warnings = [i.message for i in issues if i.level == "warning"]
        assert any("формат" in msg.lower() for msg in warnings)

    def test_oversized_file_warning(self):
        docs = [("big.pdf", "contract", 25000)]
        issues = validate_package(docs, "federal")
        warnings = [i.message for i in issues if i.level == "warning"]
        assert any("20 мб" in msg.lower() or "20 mb" in msg.lower() for msg in warnings)

    def test_unrecognized_filename_warning(self):
        docs = [("random_name.jpg", None)]
        issues = validate_package(docs, "federal")
        warnings = [i.message for i in issues if i.level == "warning"]
        assert any("нераспознан" in msg.lower() or "определить тип" in msg.lower() for msg in warnings)
