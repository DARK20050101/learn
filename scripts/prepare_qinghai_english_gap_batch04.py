from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.prepare_qinghai_six_subject_batch import repository_commit, split_question

# Fixed, independently reviewed selections from GAOKAO-Bench English MCQs.
# index -> (chapter, code, standard name, difficulty)
SELECTIONS = {
    10: ("词汇", "ENG-VOCAB-SITUATIONAL-COMMUNICATION", "情景交际", 2),
    22: ("词汇", "ENG-VOCAB-CONTEXT-ADVERB", "副词语境辨析", 2),
    47: ("非谓语动词", "ENG-NONFINITE-GERUND-SUBJECT", "动名词短语作主语", 2),
    58: ("词汇", "ENG-VOCAB-CONTEXT-VERB", "动词语境辨析", 2),
    60: ("词汇", "ENG-VOCAB-SITUATIONAL-COMMUNICATION", "情景交际", 2),
    62: ("语法", "ENG-GRAMMAR-TENSE-PRESENT-SIMPLE", "一般现在时", 2),
    74: ("词汇", "ENG-VOCAB-CONTEXT-VERB", "动词语境辨析", 2),
    75: ("词汇", "ENG-VOCAB-SITUATIONAL-COMMUNICATION", "情景交际", 2),
    82: ("词汇", "ENG-VOCAB-CONTEXT-VERB", "动词语境辨析", 2),
    89: ("词汇", "ENG-VOCAB-SITUATIONAL-COMMUNICATION", "情景交际", 2),
    92: ("词汇", "ENG-VOCAB-CONTEXT-VERB", "动词语境辨析", 2),
    99: ("词汇", "ENG-VOCAB-CONTEXT-VERB", "动词语境辨析", 2),
}


def build(source_root: Path) -> dict[str, object]:
    source_file = source_root / "Data" / "Objective_Questions" / "2010-2013_English_MCQs.json"
    payload = json.loads(source_file.read_text(encoding="utf-8"))
    by_index = {int(item["index"]): item for item in payload["example"]}
    commit = repository_commit(source_root)
    questions = []
    for index, (chapter, code, name, difficulty) in SELECTIONS.items():
        item = by_index[index]
        answers = list("".join(item["answer"]))
        if len(answers) != 1 or answers[0] not in "ABCD":
            raise ValueError(f"index={index}: expected one A-D answer")
        stem, options = split_question(item["question"])
        questions.append(
            {
                "subject": "英语",
                "chapter": chapter,
                "knowledge_points": [name],
                "difficulty": difficulty,
                "type": "single_choice",
                "question": stem,
                "options": options,
                "answer": answers[0],
                "solution": " ".join(item["analysis"].split()),
                "source": (
                    f"GAOKAO-Bench|dataset:english-mcq|year:{item['year']}|"
                    f"index:{index}|commit:{commit[:12]}"
                ),
                "title": f"高考真题候选04·英语·{item['year']}·{index}",
                "tags": [
                    f"kp:{code}",
                    "origin:external",
                    "grade:high-school",
                    "region-fit:qinghai-curriculum",
                    "batch:qinghai-gap-04",
                    "review:semantic-passed",
                ],
            }
        )
    return {
        "schema_version": "shiguang-question-candidate-v1",
        "batch": "qinghai-gap-04",
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
