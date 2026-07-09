import io
import pytest


AUTH_HEADERS = {"Authorization": "Bearer test-token"}


class TestPostChecks:
    def test_create_check_success(self, client):
        files = [
            ("files", ("договор.pdf", b"fake pdf content", "application/pdf")),
            ("files", ("спецификация.pdf", b"fake pdf content", "application/pdf")),
            ("files", ("счёт.pdf", b"fake pdf content", "application/pdf")),
            ("files", ("акт.pdf", b"fake pdf content", "application/pdf")),
        ]
        response = client.post("/api/checks", files=files, data={"program": "federal"}, headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "check_id" in data
        assert data["status"] == "approved"
        assert len(data["documents"]) == 4

    def test_create_check_empty_files(self, client):
        response = client.post("/api/checks", files=[], data={"program": "federal"}, headers=AUTH_HEADERS)
        assert response.status_code == 422

    def test_create_check_invalid_program(self, client):
        files = [("files", ("test.pdf", b"content", "application/pdf"))]
        response = client.post("/api/checks", files=files, data={"program": "invalid"}, headers=AUTH_HEADERS)
        assert response.status_code == 400


class TestGetChecks:
    def test_list_checks(self, client):
        response = client.get("/api/checks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_check_not_found(self, client):
        response = client.get("/api/checks/nonexistent-id")
        assert response.status_code == 404

    def test_get_check_by_id(self, client):
        files = [("files", ("договор.pdf", b"content", "application/pdf"))]
        create_resp = client.post("/api/checks", files=files, data={"program": "regional"}, headers=AUTH_HEADERS)
        check_id = create_resp.json()["check_id"]

        response = client.get(f"/api/checks/{check_id}")
        assert response.status_code == 200
        assert response.json()["check_id"] == check_id
