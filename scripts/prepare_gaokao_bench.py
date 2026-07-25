from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


SELECTIONS = {
    "math": {
        "file": "Data/Objective_Questions/2010-2022_Math_I_MCQs.json",
        "subject": "数学",
        "items": {
            2: ("导数", "MATH-DERIVATIVE-ELEMENTARY", "基本初等函数的导数"),
            5: ("函数", "MATH-FUNCTION-PARITY", "函数的奇偶性"),
            9: ("复数", "MATH-COMPLEX-ARITHMETIC", "复数的四则运算"),
            10: ("函数", "MATH-FUNCTION-PARITY", "函数的奇偶性"),
            11: ("概率", "MATH-PROBABILITY-CLASSICAL", "古典概型"),
            12: ("三角函数", "MATH-TRIG-FUNDAMENTAL-IDENTITY", "同角三角函数的基本关系"),
            17: ("集合", "MATH-SET-OPERATIONS", "集合的基本运算"),
            20: ("数列", "MATH-SEQUENCE-GEOMETRIC-GENERAL", "等比数列的通项公式"),
            24: ("复数", "MATH-COMPLEX-ARITHMETIC", "复数的四则运算"),
            27: ("数列", "MATH-SEQUENCE-ARITHMETIC-GENERAL", "等差数列的通项公式"),
            31: ("集合", "MATH-SET-INTERSECTION", "集合的基本运算（交集）"),
            32: ("复数", "MATH-COMPLEX-ARITHMETIC", "复数的四则运算"),
            39: ("函数", "MATH-FUNCTION-PARITY", "函数的奇偶性"),
            41: ("概率", "MATH-PROBABILITY-CLASSICAL", "古典概型"),
            45: ("集合", "MATH-SET-INTERSECTION", "集合的基本运算（交集）"),
            46: ("复数", "MATH-COMPLEX-ARITHMETIC", "复数的四则运算"),
            47: ("平面向量", "MATH-VECTOR-COORDINATE", "平面向量的坐标运算"),
            50: ("导数", "MATH-DERIVATIVE-ELEMENTARY", "基本初等函数的导数"),
            61: ("数列", "MATH-SEQUENCE-GEOMETRIC-GENERAL", "等比数列的通项公式"),
            67: ("数列", "MATH-SEQUENCE-ARITHMETIC-GENERAL", "等差数列的通项公式"),
        },
    },
    "physics": {
        "file": "Data/Objective_Questions/2010-2022_Physics_MCQs.json",
        "subject": "物理",
        "items": {
            9: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律"),
            16: ("平抛运动", "PHY-PROJECTILE-HORIZONTAL", "平抛运动规律"),
            17: ("牛顿运动定律", "PHY-NEWTON-SECOND-LAW", "牛顿第二定律"),
            18: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律"),
            29: ("运动学", "PHY-KINEMATICS-UNIFORM-ACCELERATION", "匀变速直线运动规律"),
            30: ("动量", "PHY-MOMENTUM-BASIC", "动量概念与计算"),
            37: ("功和能", "PHY-WORK-ENERGY-KINETIC", "动能概念与计算"),
            40: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律"),
            43: ("动量", "PHY-MOMENTUM-BASIC", "动量概念与计算"),
            45: ("牛顿运动定律", "PHY-NEWTON-SECOND-LAW", "牛顿第二定律"),
            48: ("圆周运动", "PHY-CIRCULAR-CENTRIPETAL-ACCELERATION", "向心加速度"),
            49: ("动量", "PHY-MOMENTUM-BASIC", "动量概念与计算"),
            55: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律"),
            57: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律"),
            60: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律"),
        },
    },
    "english": {
        "file": "Data/Objective_Questions/2010-2013_English_MCQs.json",
        "subject": "英语",
        "items": {
            0: ("时态", "ENG-GRAMMAR-TENSE-PAST-CONTINUOUS", "过去进行时"),
            1: ("词汇", "ENG-VOCAB-CONTEXT-VERB", "动词语境辨析"),
            3: ("定语从句", "ENG-CLAUSE-RELATIVE-WORD-SELECTION", "定语从句关系词的选择"),
            5: ("形容词", "ENG-GRAMMAR-ADJECTIVE-COMPARATIVE", "形容词比较级"),
            7: ("时态", "ENG-GRAMMAR-TENSE-PRESENT-PERFECT", "现在完成时"),
            8: ("情态动词", "ENG-GRAMMAR-MODAL-BASIC", "情态动词的基本用法"),
            9: ("状语从句", "ENG-CLAUSE-ADVERBIAL-CONDITION", "条件状语从句"),
            10: ("非谓语动词", "ENG-NONFINITE-INFINITIVE", "动词不定式"),
            13: ("非谓语动词", "ENG-NONFINITE-INFINITIVE", "动词不定式"),
            17: ("词汇", "ENG-VOCAB-COLLOCATION", "固定搭配"),
            18: ("主谓一致", "ENG-GRAMMAR-TENSE-PRESENT-SIMPLE", "一般现在时"),
            22: ("形容词", "ENG-GRAMMAR-ADJECTIVE-COMPARATIVE", "形容词比较级"),
            24: ("被动语态", "ENG-GRAMMAR-VOICE-PRESENT-PASSIVE", "一般现在时被动语态"),
            25: ("定语从句", "ENG-CLAUSE-RELATIVE-THAT", "关系代词 that 的用法"),
            26: ("情态动词", "ENG-GRAMMAR-MODAL-BASIC", "情态动词的基本用法"),
        },
    },
}


OPTION_PATTERN = re.compile(r"(?:^|\s)([A-D])\.\s*", re.MULTILINE)


def split_question(raw: str) -> tuple[str, list[str]]:
    text = raw.strip()
    matches = list(OPTION_PATTERN.finditer(text))
    if len(matches) != 4 or [match.group(1) for match in matches] != list("ABCD"):
        raise ValueError("题目不能稳定拆分为A-D四个选项")
    stem = re.sub(r"^\s*\d+\.\s*", "", text[: matches[0].start()]).strip()
    options = [
        text[match.end() : matches[index + 1].start()].strip()
        if index < 3
        else text[match.end() :].strip()
        for index, match in enumerate(matches)
    ]
    if not stem or any(not option for option in options):
        raise ValueError("题干或选项为空")
    return stem, options


def repository_commit(source_root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def build(source_root: Path) -> dict[str, list[dict[str, object]]]:
    commit = repository_commit(source_root)
    result: list[dict[str, object]] = []
    for spec in SELECTIONS.values():
        payload = json.loads((source_root / spec["file"]).read_text(encoding="utf-8"))
        by_index = {int(item["index"]): item for item in payload["example"]}
        for index, (chapter, code, name) in spec["items"].items():
            item = by_index[index]
            answers = item["answer"]
            if len(answers) != 1 or len(answers[0]) != 1:
                raise ValueError(f"{spec['subject']} index={index} 不是单选题")
            stem, options = split_question(item["question"])
            result.append(
                {
                    "subject": spec["subject"],
                    "chapter": chapter,
                    "knowledge_points": [name],
                    "difficulty": 3,
                    "type": "single_choice",
                    "question": stem,
                    "options": options,
                    "answer": answers[0],
                    "solution": item["analysis"].strip(),
                    "source": (
                        f"GAOKAO-Bench|year:{item['year']}|index:{index}|"
                        f"commit:{commit[:12]}"
                    ),
                    "title": f"高考真题·{spec['subject']}·{item['year']}·{index}",
                    "tags": [
                        f"kp:{code}",
                        "origin:external",
                        "grade:high-school",
                        "review:required",
                    ],
                }
            )
    if len(result) != 50:
        raise ValueError(f"预期50题，实际{len(result)}题")
    return {"questions": result}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = build(args.source_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"generated={len(payload['questions'])} output={args.output}")


if __name__ == "__main__":
    main()
