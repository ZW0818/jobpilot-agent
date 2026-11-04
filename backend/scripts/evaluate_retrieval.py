"""Offline regression benchmark; --vector explicitly opts into configured embeddings."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.rag_service import RAGService


def evaluate(cases: list[dict], rag: RAGService) -> dict:
    results, reciprocal_ranks, misses = [], [], []
    for case in cases:
        retrieved = rag.retrieve(case["question"])
        rank = next((i for i, c in enumerate(retrieved.chunks, 1)
                     if c.source == case["source"] and c.section == case.get("section")), None)
        passed = rank is not None if case["source"] else not retrieved.has_context
        if case["source"]:
            reciprocal_ranks.append(1 / rank if rank else 0)
        else:
            misses.append(not retrieved.has_context)
        results.append({"question": case["question"], "passed": passed, "relevant_rank": rank,
                        "sources": retrieved.sources, "status": retrieved.status})
    positive_count = len(reciprocal_ranks)
    return {
        "cases": len(cases), "passed": sum(r["passed"] for r in results), "top_k": rag.top_k,
        "hit_at_k": round(sum(value > 0 for value in reciprocal_ranks) / max(positive_count, 1), 4),
        "mrr_at_k": round(sum(reciprocal_ranks) / max(positive_count, 1), 4),
        "no_answer_accuracy": round(sum(misses) / max(len(misses), 1), 4),
        "note": "Small curated regression set; not an estimate of real-world answer accuracy.",
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path(__file__).resolve().parents[1] / "tests/fixtures/retrieval_cases.json")
    parser.add_argument("--vector", action="store_true", help="Use configured embedding service (may incur API usage).")
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    report = evaluate(cases, RAGService(enable_vector=args.vector))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] == report["cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
