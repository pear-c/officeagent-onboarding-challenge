#!/usr/bin/env bash
# 샘플 문서를 API로 업로드하는 시드 스크립트
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"

echo "=== 샘플 문서 시드 ==="

for file in sample-docs/*; do
    filename=$(basename "$file")
    echo "업로드: $filename"
    curl -s -X POST "$API_URL/api/v1/documents" \
        -F "file=@$file" \
        | python3 -m json.tool
    echo ""
done

echo "=== 시드 완료 ==="
