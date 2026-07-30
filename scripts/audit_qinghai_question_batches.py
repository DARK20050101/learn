from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

ANSWER_PATTERN = re.compile(r"(?:故选|答案(?:为)?)[：:\s]*([A-D]{1,4})", re.IGNORECASE)
IMAGE_PATTERN = re.compile(r"如图|下图|图中|右图|示意图")
OCR_MARKERS = ("\\oint", "ð", "�")


def normalized_answer(value: str | list[str]) -> str:
    answer = "".join(value) if isinstance(value, list) else value
    return "".join(sorted(answer.upper()))


def audit_question(question: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    review_reasons: list[str] = []
    expected = normalized_answer(question["answer"])
    conclusions = ANSWER_PATTERN.findall(str(question.get("solution", "")))
    if conclusions and normalized_answer(conclusions[-1]) != expected:
        blockers.append(
            f"解析结论答案 {conclusions[-1]} 与标准答案 {expected} 不一致"
        )

    text = " ".join(
        [
            str(question.get("question", "")),
            *[str(option) for option in question.get("options", [])],
            str(question.get("solution", "")),
        ]
    )
    if IMAGE_PATTERN.search(text):
        review_reasons.append("可能依赖未收录图片")
    if "\\begin{tabular}" in text:
        review_reasons.append("包含复杂LaTeX表格，移动端展示需确认")
    if text.count("$") % 2:
        review_reasons.append("LaTeX分隔符数量异常")
    if any(marker in text for marker in OCR_MARKERS):
        review_reasons.append("存在已知OCR异常符号")
    if any(
        unicodedata.category(character) == "Cc"
        and character not in {"\n", "\r", "\t"}
        for character in text
    ):
        review_reasons.append("存在不可见控制字符")

    status = "BLOCK" if blockers else "REVIEW" if review_reasons else "AUTO_PASS"
    return status, blockers, review_reasons


def run(
    paths: list[Path],
    candidate_path: Path,
    report_path: Path,
    review_path: Path | None = None,
) -> dict[str, Any]:
    approved: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    seen_sources: set[tuple[str, str]] = set()
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        questions = payload if isinstance(payload, list) else payload["questions"]
        for index, question in enumerate(questions, 1):
            source = str(question.get("source", ""))
            source_key = (str(question.get("subject", "")), source)
            if source_key in seen_sources:
                status, blockers, review_reasons = (
                    "BLOCK",
                    ["多个输入文件包含重复source"],
                    [],
                )
            else:
                seen_sources.add(source_key)
                status, blockers, review_reasons = audit_question(question)
            records.append(
                {
                    "file": path.name,
                    "index": index,
                    "title": question.get("title", ""),
                    "subject": question.get("subject", ""),
                    "source": source,
                    "status": status,
                    "blockers": blockers,
                    "review_reasons": review_reasons,
                }
            )
            if status == "AUTO_PASS":
                approved.append(question)
            elif status == "REVIEW":
                review_question = dict(question)
                review_question["_audit"] = {
                    "reasons": review_reasons,
                    "source_file": path.name,
                    "source_index": index,
                }
                needs_review.append(review_question)

    counts = Counter(record["status"] for record in records)
    report = {
        "schema_version": "shiguang-question-audit-v1",
        "policy": {
            "auto_pass": "格式、答案解析一致性和已知OCR风险检查均未发现异常",
            "review": "不进入自动发布批次，需在审查页面确认",
            "block": "禁止发布",
            "accuracy_notice": (
                "AUTO_PASS不是官方答案二次认证；答案继承自GAOKAO-Bench Standard Answer，"
                "按Apache-2.0 AS IS条款提供"
            ),
        },
        "inputs": [str(path) for path in paths],
        "total": len(records),
        "auto_pass": counts["AUTO_PASS"],
        "review": counts["REVIEW"],
        "block": counts["BLOCK"],
        "candidate_file": str(candidate_path),
        "review_file": str(review_path) if review_path else None,
        "records": records,
    }
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(
        json.dumps({"questions": approved}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if review_path:
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(
            json.dumps({"questions": needs_review}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--review-queue", type=Path)
    args = parser.parse_args()
    report = run(args.files, args.candidate, args.report, args.review_queue)
    print(json.dumps({key: report[key] for key in ("total", "auto_pass", "review", "block")}))


if __name__ == "__main__":
    main()
