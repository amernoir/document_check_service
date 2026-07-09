#!/bin/bash
# Test script for document_check_service
# Usage: bash test_files/test.sh [BASE_URL]

BASE_URL="${1:-http://localhost:8000}"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== 1. Health check ==="
curl -s "$BASE_URL/health" | python3 -m json.tool
echo -e "\n"

echo "=== 2. Federal — full package (should be approved) ==="
curl -s -X POST "$BASE_URL/api/checks" \
  -F "files=@$DIR/договор_001.pdf" \
  -F "files=@$DIR/спецификация_к_договору.pdf" \
  -F "files=@$DIR/счет-фактура_№123.pdf" \
  -F "files=@$DIR/акт_приемки_2025.pdf" \
  -F "program=federal" | python3 -m json.tool
echo -e "\n"

echo "=== 3. Federal — missing specification (should have error) ==="
curl -s -X POST "$BASE_URL/api/checks" \
  -F "files=@$DIR/договор_001.pdf" \
  -F "files=@$DIR/счет-фактура_№123.pdf" \
  -F "files=@$DIR/акт_приемки_2025.pdf" \
  -F "program=federal" | python3 -m json.tool
echo -e "\n"

echo "=== 4. Regional — full package (should be approved) ==="
curl -s -X POST "$BASE_URL/api/checks" \
  -F "files=@$DIR/договор_дополнительный.pdf" \
  -F "files=@$DIR/счёт_фактура_456.pdf" \
  -F "files=@$DIR/акт_сдачи_работ.pdf" \
  -F "program=regional" | python3 -m json.tool
echo -e "\n"

echo "=== 5. Regional — only contract (missing invoice+act) ==="
curl -s -X POST "$BASE_URL/api/checks" \
  -F "files=@$DIR/договор_001.pdf" \
  -F "program=regional" | python3 -m json.tool
echo -e "\n"

echo "=== 6. Wrong extension (.txt) — should warn ==="
curl -s -X POST "$BASE_URL/api/checks" \
  -F "files=@$DIR/договор_бракованный.txt" \
  -F "files=@$DIR/спецификация_к_договору.pdf" \
  -F "files=@$DIR/счет-фактура_№123.pdf" \
  -F "files=@$DIR/акт_приемки_2025.pdf" \
  -F "program=federal" | python3 -m json.tool
echo -e "\n"

echo "=== 7. Unrecognized filename — should warn about unknown type ==="
curl -s -X POST "$BASE_URL/api/checks" \
  -F "files=@$DIR/unknown_document.txt" \
  -F "program=federal" | python3 -m json.tool
echo -e "\n"

echo "=== 8. Invalid program value ==="
curl -s -X POST "$BASE_URL/api/checks" \
  -F "files=@$DIR/договор_001.pdf" \
  -F "program=local" | python3 -m json.tool
echo -e "\n"

echo "=== 9. No files ==="
curl -s -X POST "$BASE_URL/api/checks" \
  -F "program=federal" | python3 -m json.tool
echo -e "\n"

echo "=== 10. List all checks ==="
curl -s "$BASE_URL/api/checks" | python3 -m json.tool
echo -e "\n"

echo "=== Done ==="
