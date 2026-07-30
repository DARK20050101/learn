from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.prepare_qinghai_six_subject_batch import repository_commit, split_question

# Fixed no-image selections. Each item was independently matched to one primary
# knowledge point so the imported answer data can update mastery reliably.
SELECTIONS = {
    13: ("曲线运动", "PHY-CIRCULAR-CENTRIPETAL-ACCELERATION", "向心加速度", 3),
    26: ("牛顿运动定律", "PHY-NEWTON-SECOND-LAW", "牛顿第二定律", 3),
    59: ("功和能", "PHY-WORK-ENERGY-KINETIC", "动能概念与计算", 3),
}


def build(source_root: Path) -> dict[str, object]:
    source_file = source_root / "Data" / "Objective_Questions" / "2010-2022_Physics_MCQs.json"
    payload = json.loads(source_file.read_text(encoding="utf-8"))
    by_index = {int(item["index"]): item for item in payload["example"]}
    commit = repository_commit(source_root)
    questions = []
    for index, (chapter, code, name, difficulty) in SELECTIONS.items():
        item = by_index[index]
        answers = list("".join(item["answer"]))
        if not answers or any(answer not in "ABCD" for answer in answers):
            raise ValueError(f"index={index}: invalid answer")
        stem, options = split_question(item["question"])
        questions.append(
            {
                "subject": "物理",
                "chapter": chapter,
                "knowledge_points": [name],
                "difficulty": difficulty,
                "type": "single_choice" if len(answers) == 1 else "multiple_choice",
                "question": stem,
                "options": options,
                "answer": answers[0] if len(answers) == 1 else answers,
                "solution": " ".join(item["analysis"].split()),
                "source": (
                    f"GAOKAO-Bench|dataset:physics|year:{item['year']}|"
                    f"index:{index}|commit:{commit[:12]}"
                ),
                "title": f"高考真题候选05·物理·{item['year']}·{index}",
                "tags": [
                    f"kp:{code}",
                    "origin:external",
                    "grade:high-school",
                    "region-fit:qinghai-curriculum",
                    "batch:qinghai-gap-05",
                    "review:semantic-passed",
                ],
            }
        )
    return {
        "schema_version": "shiguang-question-candidate-v1",
        "batch": "qinghai-gap-05",
        "source_commit": commit,
        "questions": questions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.source_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"generated": len(result["questions"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
