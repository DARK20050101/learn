from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED_DECISIONS = {"PASS", "REVISE", "REJECT"}
PROTECTED_FIELDS = {"source", "title", "subject", "chapter", "knowledge_points"}


class ReviewProcessingError(ValueError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def reviewed_tags(tags: list[str], decision: str) -> list[str]:
    result = [tag for tag in tags if not tag.startswith("review:")]
    result.append("review:passed" if decision == "PASS" else "review:revised")
    return result


def process(
    queue_path: Path,
    result_path: Path,
    revisions_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    queue_payload = load_json(queue_path)
    questions = (
        queue_payload if isinstance(queue_payload, list) else queue_payload["questions"]
    )
    result_payload = load_json(result_path)
    reviews = {
        item["source"]: item for item in result_payload.get("reviews", [])
    }
    revision_payload = load_json(revisions_path)
    revisions = revision_payload.get("revisions", {})

    sources = {question["source"] for question in questions}
    unknown_revisions = sorted(set(revisions) - sources)
    if unknown_revisions:
        raise ReviewProcessingError(
            f"revision manifest contains unknown sources: {unknown_revisions}"
        )

    release_questions: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for question in questions:
        source = question["source"]
        review = reviews.get(source)
        decision = review.get("decision", "") if review else ""
        if decision not in ALLOWED_DECISIONS:
            errors.append(f"{source}: review decision is incomplete")
            continue
        if decision == "REJECT":
            records.append({"source": source, "decision": decision, "action": "excluded"})
            continue

        clean_question = {
            key: value for key, value in question.items() if not key.startswith("_")
        }
        if decision == "REVISE":
            revision = revisions.get(source)
            if not revision:
                errors.append(f"{source}: REVISE requires a revision manifest entry")
                continue
            updates = revision.get("updates", {})
            protected = sorted(PROTECTED_FIELDS & set(updates))
            if protected:
                errors.append(f"{source}: protected fields cannot change: {protected}")
                continue
            clean_question.update(updates)
        clean_question["tags"] = reviewed_tags(
            list(clean_question.get("tags", [])), decision
        )
        release_questions.append(clean_question)
        records.append(
            {
                "source": source,
                "decision": decision,
                "action": "copied" if decision == "PASS" else "revised",
                "review_note": review.get("note", ""),
                "revision_reason": revisions.get(source, {}).get("reason", ""),
            }
        )

    if errors:
        raise ReviewProcessingError("; ".join(errors))

    report = {
        "schema_version": "shiguang-review-processing-v1",
        "queue": str(queue_path),
        "review_result": str(result_path),
        "revision_manifest": str(revisions_path),
        "input_questions": len(questions),
        "release_questions": len(release_questions),
        "pass": sum(item["decision"] == "PASS" for item in records),
        "revised": sum(item["decision"] == "REVISE" for item in records),
        "rejected": sum(item["decision"] == "REJECT" for item in records),
        "records": records,
    }
    return {"questions": release_questions}, report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a release candidate from a review queue and saved decisions."
    )
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--revisions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    candidate, report = process(args.queue, args.result, args.revisions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
