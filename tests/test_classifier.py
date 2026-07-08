import pytest
from app.services.classifier import classify_document


class TestClassifyDocument:
    def test_contract_russian(self):
        assert classify_document("Договор_47.pdf") == "contract"

    def test_contract_english(self):
        assert classify_document("contract_agreement.docx") == "contract"

    def test_specification_russian(self):
        assert classify_document("спецификация_к_договору.pdf") == "specification"

    def test_specification_english(self):
        assert classify_document("specification_v2.docx") == "specification"

    def test_invoice_russian(self):
        assert classify_document("счёт_на_оплату.pdf") == "invoice"

    def test_invoice_transliteration(self):
        assert classify_document("schet_001.pdf") == "invoice"

    def test_act_russian(self):
        assert classify_document("акт_приемки.jpg") == "act"

    def test_act_upd(self):
        assert classify_document("УПД_акт.pdf") == "act"

    def test_unknown_file(self):
        assert classify_document("scan_0041.jpg") is None

    def test_case_insensitive(self):
        assert classify_document("ДОГОВОР_01.PDF") == "contract"

    def test_empty_filename(self):
        assert classify_document("") is None
