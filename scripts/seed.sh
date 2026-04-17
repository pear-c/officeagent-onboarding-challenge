#!/usr/bin/env bash
# 샘플 문서 자동 업로드 스크립트
# 사용법: ./scripts/seed.sh [API_URL]
set -euo pipefail

API_URL="${1:-${API_URL:-http://localhost:8000}}"

echo "=== Document Q&A 샘플 문서 업로드 ==="
echo "API: $API_URL"
echo ""

# 서버 대기 (최대 120초 — 임베딩 모델 로딩 시간 고려)
echo "서버 준비 대기 중..."
for i in $(seq 1 60); do
    if curl -sf "$API_URL/health" > /dev/null 2>&1; then
        echo "서버 준비 완료!"
        break
    fi
    if [ "$i" -eq 60 ]; then
        echo "서버 응답 없음 (120초 초과). docker compose logs app 확인하세요."
        exit 1
    fi
    sleep 2
done

echo ""

# 샘플 문서 업로드 (평가자 제공 파일 2개)
SEED_FILES=("sample-docs/company-policy.txt" "sample-docs/development-guide.md")
for file in "${SEED_FILES[@]}"; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo -n "업로드: $filename ... "
        result=$(curl -sf -X POST "$API_URL/api/v1/documents" -F "file=@$file" 2>/dev/null || echo "")
        if [ -n "$result" ]; then
            chunks=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['chunk_count'])" 2>/dev/null || echo "?")
            echo "완료 (${chunks}개 청크)"
        else
            echo "실패"
        fi
    fi
done
echo ""
echo "추가 문서는 웹 UI 또는 API로 직접 업로드하세요."
echo "  curl -X POST $API_URL/api/v1/documents -F 'file=@sample-docs/파일명'"

echo ""
echo "=== 업로드 완료 ==="
echo "브라우저: $API_URL"
echo "API 문서: $API_URL/docs"
