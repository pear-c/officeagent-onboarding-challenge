"""평가 하네스 실행 스크립트.

사용법:
  python eval/run.py --provider claude
  python eval/run.py --provider codex
  python eval/run.py --compare eval/results/result1.json eval/results/result2.json
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.embedding.embedder import Embedder
from app.llm.claude_provider import ClaudeProvider
from app.llm.codex_provider import CodexProvider
from app.services.rag_service import RAGService
from app.vectorstore.chroma_store import ChromaStore
from eval.metrics import compute_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("eval")

GOLDEN_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_DIR = Path(__file__).parent / "results"


class NoOpCacheService:
    """평가용 — 캐시 항상 miss, 저장도 무시."""

    @staticmethod
    def hash_question(question: str) -> str:
        return ""

    async def get_exact(self, _question_hash: str):
        return None

    def get_similar(self, _embedding, **kwargs):
        return None

    async def save(self, **kwargs):
        pass

    async def invalidate_by_document(self, _filename: str) -> int:
        return 0


def load_golden(filter_source: str | None = None) -> list[dict]:
    """골든 데이터셋 로드. filter_source 지정 시 해당 파일명을 포함하는 케이스만 반환."""
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if filter_source:
        data = [
            d for d in data
            if filter_source in (d.get("expected_source") or "")
            or (not d.get("answerable") and not filter_source)
        ]
    return data


def create_provider(name: str):
    """LLM provider 생성."""
    if name == "claude":
        return ClaudeProvider()
    elif name == "codex":
        return CodexProvider()
    else:
        raise ValueError(f"지원하지 않는 provider: {name}")


def init_resources():
    """Embedder + ChromaStore 초기화."""
    logger.info("임베딩 모델 로딩 중...")
    embedder = Embedder(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
    )
    chroma = ChromaStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_name=settings.chroma_collection,
    )
    logger.info("리소스 초기화 완료 (벡터 %d개)", chroma.count())
    return embedder, chroma


async def run_eval(provider_name: str, filter_source: str | None = None) -> dict:
    """골든 데이터셋 순차 실행 + 메트릭 계산. filter_source로 특정 파일 케이스만 실행."""
    golden = load_golden(filter_source)
    if not golden:
        logger.error("필터 '%s'에 해당하는 케이스가 없습니다.", filter_source)
        sys.exit(1)
    embedder, chroma = init_resources()

    # 문서가 업로드되어 있는지 확인
    if chroma.count() == 0:
        logger.error("Chroma에 벡터가 없습니다. 먼저 문서를 업로드하세요.")
        sys.exit(1)

    provider = create_provider(provider_name)
    rag = RAGService(
        cache_service=NoOpCacheService(),
        chroma=chroma,
        embedder=embedder,
        answer_llm=provider,
    )

    logger.info("=== 평가 시작: %s (%d케이스) ===", provider_name, len(golden))
    case_results = []

    for i, gold in enumerate(golden):
        qid = gold["id"]
        question = gold["question"]
        logger.info("[%d/%d] %s: %s", i + 1, len(golden), qid, question)

        start = time.time()
        try:
            answer = await rag.answer(question)
            latency_ms = int((time.time() - start) * 1000)

            # JSON 파싱 성공 여부 (answer 객체가 정상 생성되었으면 성공)
            json_parsed = True

            result = {
                "id": qid,
                "question": question,
                "answer": answer.answer,
                "sources": [{"file": s.file, "chunk_id": s.chunk_id} for s in answer.sources],
                "answerable": answer.answerable,
                "latency_ms": latency_ms,
                "model": answer.model,
                "json_parsed": json_parsed,
            }
            logger.info("  → %dms, answerable=%s, sources=%d",
                        latency_ms, answer.answerable, len(answer.sources))

        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            logger.error("  → 오류: %s (%dms)", e, latency_ms)
            result = {
                "id": qid,
                "question": question,
                "answer": f"오류: {e}",
                "sources": [],
                "answerable": False,
                "latency_ms": latency_ms,
                "model": provider_name,
                "json_parsed": False,
            }

        case_results.append(result)

    # 메트릭 계산
    metrics = compute_all(case_results, golden)

    output = {
        "provider": provider_name,
        "model": provider.model_name,
        "timestamp": datetime.now().isoformat(),
        "total_cases": len(golden),
        "metrics": metrics,
        "cases": case_results,
    }

    # 결과 저장
    RESULTS_DIR.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    suffix = f"_{filter_source.replace('.', '')}" if filter_source else ""
    result_path = RESULTS_DIR / f"{date_str}_{provider_name}{suffix}.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 요약 출력
    print_summary(output)
    logger.info("결과 저장: %s", result_path)

    return output


def print_summary(result: dict) -> None:
    """터미널에 요약 출력."""
    m = result["metrics"]
    print("\n" + "=" * 50)
    print(f"  평가 결과: {result['provider']} ({result['model']})")
    print(f"  시간: {result['timestamp']}")
    print(f"  케이스: {result['total_cases']}개")
    print("=" * 50)
    print(f"  Retrieval Hit Rate : {m['retrieval_hit_rate']:.2%}")
    print(f"  Citation Accuracy  : {m['citation_accuracy']:.2%}")
    print(f"  Refusal Accuracy   : {m['refusal_accuracy']:.2%}")
    print(f"  Keyword Hit Rate   : {m['keyword_hit_rate']:.2%}")
    print(f"  JSON Parse Rate    : {m['json_parse_rate']:.2%}")
    print(f"  Latency p50        : {m['latency_p50_ms']}ms")
    print(f"  Latency p95        : {m['latency_p95_ms']}ms")
    print("=" * 50 + "\n")


def compare_results(path1: str, path2: str) -> None:
    """두 결과 파일 비교 표 출력."""
    with open(path1, encoding="utf-8") as f:
        r1 = json.load(f)
    with open(path2, encoding="utf-8") as f:
        r2 = json.load(f)

    m1, m2 = r1["metrics"], r2["metrics"]
    name1 = f"{r1['provider']} ({r1['model']})"
    name2 = f"{r2['provider']} ({r2['model']})"

    print("\n" + "=" * 65)
    print(f"  {'메트릭':<22} {name1:>18} {name2:>18}")
    print("-" * 65)

    for key in m1:
        v1, v2 = m1[key], m2[key]
        if "rate" in key or "accuracy" in key:
            s1, s2 = f"{v1:.2%}", f"{v2:.2%}"
        else:
            s1, s2 = f"{v1}ms", f"{v2}ms"

        # 승자 표시
        if "latency" in key:
            winner = " ◀" if v1 < v2 else ("   ▶" if v2 < v1 else "")
        else:
            winner = " ◀" if v1 > v2 else ("   ▶" if v2 > v1 else "")

        label = key.replace("_", " ").title()
        print(f"  {label:<22} {s1:>16} {s2:>16}  {winner}")

    print("=" * 65)

    # 케이스별 차이
    print(f"\n  케이스별 차이 (keyword hit 불일치):")
    for c1, c2 in zip(r1["cases"], r2["cases"]):
        g = next((g for g in load_golden() if g["id"] == c1["id"]), {})
        keywords = g.get("expected_keywords", [])
        if not keywords:
            continue
        hit1 = all(kw in c1.get("answer", "") for kw in keywords)
        hit2 = all(kw in c2.get("answer", "") for kw in keywords)
        if hit1 != hit2:
            w = r1["provider"] if hit1 else r2["provider"]
            print(f"    {c1['id']}: {w} 승 — {g['question']}")

    print()


def main():
    parser = argparse.ArgumentParser(description="RAG 평가 하네스")
    sub = parser.add_subparsers(dest="command")

    # run 서브커맨드
    run_parser = sub.add_parser("run", help="평가 실행")
    run_parser.add_argument("--provider", required=True, choices=["claude", "codex"])
    run_parser.add_argument("--filter", default=None, help="소스 파일명 필터 (예: .pdf, security, it-security)")

    # compare 서브커맨드
    cmp_parser = sub.add_parser("compare", help="결과 비교")
    cmp_parser.add_argument("files", nargs=2, help="비교할 결과 JSON 2개")

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(run_eval(args.provider, args.filter))
    elif args.command == "compare":
        compare_results(args.files[0], args.files[1])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
