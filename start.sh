#!/usr/bin/env bash
# Document Q&A API — 한 줄 실행 스크립트
# 사용법: ./start.sh
set -euo pipefail

echo "=== Document Q&A API 시작 ==="
echo ""

# 1. Chroma + Redis 실행
echo "[1/4] Chroma + Redis 시작..."
docker compose up -d chroma redis
echo "      DB 준비 완료"

# 2. Python 가상환경 + 의존성
echo "[2/4] Python 환경 구성..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -e . --quiet 2>/dev/null

# 3. .env 복사 (없으면)
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "      .env 생성 완료 (기본 설정)"
fi

# 4. 서버 실행 (백그라운드)
echo "[3/4] 서버 시작 (임베딩 모델 로딩 중, 최대 2~3분)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
APP_PID=$!

# 서버 준비 대기
for i in $(seq 1 90); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    if [ "$i" -eq 90 ]; then
        echo "서버 시작 실패. 로그를 확인하세요."
        exit 1
    fi
    sleep 2
done
echo "      서버 준비 완료"

# 5. 샘플 문서 업로드
echo "[4/4] 샘플 문서 업로드..."
for file in sample-docs/*; do
    filename=$(basename "$file")
    result=$(curl -sf -X POST http://localhost:8000/api/v1/documents -F "file=@$file" 2>/dev/null || echo "")
    if [ -n "$result" ]; then
        chunks=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['chunk_count'])" 2>/dev/null || echo "?")
        echo "      $filename (${chunks}개 청크)"
    fi
done

echo ""
echo "=== 준비 완료 ==="
echo ""
echo "  웹 UI:    http://localhost:8000"
echo "  API 문서: http://localhost:8000/docs"
echo "  서버 PID: $APP_PID"
echo ""
echo "  종료: kill $APP_PID && docker compose down"
echo ""

# 포그라운드로 전환 (Ctrl+C로 종료 가능)
wait $APP_PID
