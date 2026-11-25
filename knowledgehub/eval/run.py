import json
import time
from pathlib import Path

from knowledgehub.answer import respond
from knowledgehub.search import search
from knowledgehub.usage import begin

CASES_PATH = Path(__file__).with_name("cases.jsonl")
REPORT_PATH = Path(__file__).with_name("report.json")

# Standard OpenAI rates per 1M tokens: text-embedding-3-small, gpt-4.1-mini.
EMBEDDING_USD_PER_MILLION = 0.02
CHAT_INPUT_USD_PER_MILLION = 0.40
CHAT_OUTPUT_USD_PER_MILLION = 1.60


def main() -> None:
    cases = _load_cases(CASES_PATH)
    results = [_run_case(case) for case in cases]
    summary = _summarize(results)
    REPORT_PATH.write_text(json.dumps({"summary": summary, "cases": results}, indent=2))
    _print_summary(summary, results)


def _load_cases(path: Path) -> list[dict]:
    cases = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        case = json.loads(line)
        if "id" not in case or "question" not in case or "should_refuse" not in case:
            raise ValueError(f"case on line {line_number} is missing a field")
        if not case["should_refuse"] and not case.get("expected_text"):
            raise ValueError(f"case {case['id']} needs expected_text")
        cases.append(case)
    return cases


def _run_case(case: dict) -> dict:
    usage = begin()
    started = time.perf_counter()
    found = search(case["question"])
    answer = respond(case["question"], found)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    expected = case.get("expected_text", "").lower()
    retrieved = any(expected and expected in passage.text.lower() for passage in found.passages)
    return {
        "id": case["id"],
        "question": case["question"],
        "should_refuse": case["should_refuse"],
        "status": answer["status"],
        "retrieval_hit": (not case["should_refuse"]) and retrieved,
        "refusal_correct": (answer["status"] == "refused") == case["should_refuse"],
        "elapsed_ms": elapsed_ms,
        "embedding_tokens": usage.embedding_tokens,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "cost_usd": _cost(usage),
    }


def _summarize(results: list[dict]) -> dict:
    answerable = [result for result in results if not result["should_refuse"]]
    return {
        "cases": len(results),
        "retrieval_hits": sum(result["retrieval_hit"] for result in answerable),
        "answerable_cases": len(answerable),
        "refusal_correct": sum(result["refusal_correct"] for result in results),
        "total_elapsed_ms": sum(result["elapsed_ms"] for result in results),
        "total_cost_usd": round(sum(result["cost_usd"] for result in results), 6),
    }


def _cost(usage) -> float:
    return (
        usage.embedding_tokens * EMBEDDING_USD_PER_MILLION
        + usage.prompt_tokens * CHAT_INPUT_USD_PER_MILLION
        + usage.completion_tokens * CHAT_OUTPUT_USD_PER_MILLION
    ) / 1_000_000


def _print_summary(summary: dict, results: list[dict]) -> None:
    hits = summary["retrieval_hits"]
    answerable = summary["answerable_cases"]
    correct = summary["refusal_correct"]
    total = summary["cases"]
    print(f"retrieval hits: {hits}/{answerable}")
    print(f"refusal accuracy: {correct}/{total}")
    print(f"total time: {summary['total_elapsed_ms']} ms")
    print(f"total cost: ${summary['total_cost_usd']:.6f}")
    misses = [
        result["id"]
        for result in results
        if (not result["should_refuse"] and not result["retrieval_hit"])
        or not result["refusal_correct"]
    ]
    if misses:
        print("misses:", ", ".join(misses))


if __name__ == "__main__":
    main()
