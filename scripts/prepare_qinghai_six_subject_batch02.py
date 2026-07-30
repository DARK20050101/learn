from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.prepare_qinghai_six_subject_batch import (
    repository_commit,
    split_question,
)

SELECTIONS = {
    "chinese": {
        "file": "2010-2022_Chinese_Lang_and_Usage_MCQs.json",
        "subject": "语文",
        "items": {
            9: ("语言文字运用", "CHN-LANGUAGE-WORDS", "词语辨析与使用", 2),
            10: ("语言文字运用", "CHN-LANGUAGE-SENTENCE", "病句辨析与修改", 3),
            11: ("语言文字运用", "CHN-LANGUAGE-EXPRESSION", "语言表达与衔接", 3),
            15: ("语言文字运用", "CHN-LANGUAGE-WORDS", "词语辨析与使用", 2),
            16: ("语言文字运用", "CHN-LANGUAGE-SENTENCE", "病句辨析与修改", 3),
            17: ("语言文字运用", "CHN-LANGUAGE-EXPRESSION", "语言表达与衔接", 3),
            18: ("语言文字运用", "CHN-LANGUAGE-WORDS", "词语辨析与使用", 2),
            19: ("语言文字运用", "CHN-LANGUAGE-SENTENCE", "病句辨析与修改", 3),
            20: ("语言文字运用", "CHN-LANGUAGE-EXPRESSION", "语言表达与衔接", 3),
            23: ("语言文字运用", "CHN-LANGUAGE-EXPRESSION", "语言表达与衔接", 3),
        },
    },
    "math": {
        "file": "2010-2022_Math_I_MCQs.json",
        "subject": "数学",
        "items": {
            0: ("集合与逻辑", "MATH-SET-OPERATIONS", "集合的基本运算", 2),
            1: ("复数", "MATH-COMPLEX-ARITHMETIC", "复数的四则运算", 2),
            31: ("集合与逻辑", "MATH-SET-OPERATIONS", "集合的基本运算", 2),
            5: ("函数", "MATH-FUNCTION-PARITY", "函数的奇偶性", 3),
            6: ("三角函数", "MATH-TRIG-FUNDAMENTAL-IDENTITY", "同角三角函数的基本关系", 3),
            32: ("复数", "MATH-COMPLEX-ARITHMETIC", "复数的四则运算", 2),
            33: ("数列", "MATH-SEQUENCE-GEOMETRIC-GENERAL", "等比数列的通项公式", 3),
            44: ("导数", "MATH-DERIVATIVE-ELEMENTARY", "基本初等函数的导数", 3),
            41: ("概率", "MATH-PROBABILITY-CLASSICAL", "古典概型", 2),
            42: ("三角函数", "MATH-TRIG-FUNDAMENTAL-IDENTITY", "同角三角函数的基本关系", 3),
        },
    },
    "english": {
        "file": "2010-2013_English_MCQs.json",
        "subject": "英语",
        "items": {
            0: ("语法", "ENG-GRAMMAR-TENSE-PAST-CONTINUOUS", "过去进行时", 2),
            3: ("从句", "ENG-CLAUSE-RELATIVE-WORD-SELECTION", "定语从句关系词的选择", 2),
            7: ("语法", "ENG-GRAMMAR-TENSE-PRESENT-PERFECT", "现在完成时", 2),
            8: ("语法", "ENG-GRAMMAR-MODAL-BASIC", "情态动词的基本用法", 2),
            9: ("从句", "ENG-CLAUSE-ADVERBIAL-CONDITION", "条件状语从句", 2),
            47: ("语法", "ENG-GRAMMAR-TENSE-PRESENT-SIMPLE", "一般现在时", 2),
            16: ("从句", "ENG-CLAUSE-ADVERBIAL-CONDITION", "条件状语从句", 2),
            19: ("从句", "ENG-CLAUSE-RELATIVE-WHERE", "关系副词 where", 2),
            24: ("语法", "ENG-GRAMMAR-VOICE-PRESENT-PASSIVE", "一般现在时的被动语态", 2),
            25: ("从句", "ENG-CLAUSE-RELATIVE-THAT", "关系代词 that", 2),
        },
    },
    "physics": {
        "file": "2010-2022_Physics_MCQs.json",
        "subject": "物理",
        "items": {
            5: ("功和能", "PHY-WORK-ENERGY-KINETIC", "动能定理", 3),
            6: ("功和能", "PHY-WORK-ENERGY-WORK-CALCULATION", "功的计算", 3),
            48: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律", 3),
            13: ("圆周运动", "PHY-CIRCULAR-CENTRIPETAL-ACCELERATION", "向心加速度", 3),
            15: ("磁场", "PHY-MAGNETIC-FIELD-DIRECTION", "磁场方向的判断", 2),
            17: ("牛顿运动定律", "PHY-NEWTON-SECOND-LAW", "牛顿第二定律", 3),
            18: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律", 3),
            23: ("牛顿运动定律", "PHY-NEWTON-SECOND-LAW", "牛顿第二定律", 3),
            25: ("牛顿运动定律", "PHY-NEWTON-SECOND-LAW", "牛顿第二定律", 2),
            58: ("功和能", "PHY-WORK-ENERGY-KINETIC", "动能定理", 3),
        },
    },
    "chemistry": {
        "file": "2010-2022_Chemistry_MCQs.json",
        "subject": "化学",
        "items": {
            0: ("化学基本概念", "CHEM-CONCEPT-ION", "离子反应与离子方程式", 2),
            1: ("化学反应原理", "CHEM-REACTION-ENERGY", "化学反应与能量", 3),
            6: ("化学基本概念", "CHEM-CONCEPT-AMOUNT", "物质的量与化学计量", 2),
            7: ("有机化学基础", "CHEM-ORGANIC-STRUCTURE", "有机物结构与性质", 3),
            8: ("有机化学基础", "CHEM-ORGANIC-REACTION", "有机反应类型", 2),
            9: ("化学反应原理", "CHEM-REACTION-ENERGY", "化学反应与能量", 3),
            10: ("化学基本概念", "CHEM-CONCEPT-ION", "离子反应与离子方程式", 3),
            12: ("化学实验", "CHEM-EXPERIMENT-OPERATION", "实验基本操作与安全", 2),
            13: ("无机元素及其化合物", "CHEM-INORGANIC-NONMETAL", "非金属及其化合物", 2),
            22: ("化学实验", "CHEM-EXPERIMENT-DESIGN", "实验方案设计与评价", 3),
        },
    },
    "biology": {
        "file": "2010-2022_Biology_MCQs.json",
        "subject": "生物",
        "items": {
            113: ("细胞代谢", "BIO-METABOLISM-RESPIRATION", "细胞呼吸", 3),
            114: ("稳态与调节", "BIO-HOMEOSTASIS-NEURAL-HUMORAL", "神经调节与体液调节", 3),
            115: ("生物技术与实验", "BIO-TECHNOLOGY-EXPERIMENT", "教材基础实验", 2),
            116: ("遗传与进化", "BIO-GENETICS-LAWS", "遗传基本规律", 3),
            117: ("生物与环境", "BIO-ECOLOGY-POPULATION-COMMUNITY", "种群与群落", 2),
            118: ("分子与细胞", "BIO-CELL-MOLECULE", "组成细胞的分子", 2),
            119: ("稳态与调节", "BIO-HOMEOSTASIS-IMMUNE", "免疫调节", 2),
            121: ("遗传与进化", "BIO-GENETICS-VARIATION-EVOLUTION", "变异、育种与进化", 2),
            123: ("生物与环境", "BIO-ECOLOGY-POPULATION-COMMUNITY", "种群与群落", 2),
            124: ("遗传与进化", "BIO-GENETICS-MOLECULAR", "遗传的分子基础", 3),
        },
    },
}


def build(source_root: Path) -> dict[str, list[dict[str, object]]]:
    objective_root = source_root / "Data" / "Objective_Questions"
    commit = repository_commit(source_root)
    questions: list[dict[str, object]] = []
    for spec in SELECTIONS.values():
        payload = json.loads((objective_root / spec["file"]).read_text(encoding="utf-8"))
        by_index = {int(item["index"]): item for item in payload["example"]}
        for index, (chapter, code, name, difficulty) in spec["items"].items():
            item = by_index[index]
            answers = list("".join(item["answer"]))
            if not answers or any(answer not in "ABCD" for answer in answers):
                raise ValueError(f"{spec['subject']} index={index}答案格式错误")
            try:
                stem, options = split_question(item["question"])
            except ValueError as exc:
                raise ValueError(f"{spec['subject']} index={index}: {exc}") from exc
            questions.append(
                {
                    "subject": spec["subject"],
                    "chapter": chapter,
                    "knowledge_points": [name],
                    "difficulty": difficulty,
                    "type": "single_choice" if len(answers) == 1 else "multiple_choice",
                    "question": stem,
                    "options": options,
                    "answer": answers[0] if len(answers) == 1 else answers,
                    "solution": " ".join(item["analysis"].split()),
                    "source": (
                        f"GAOKAO-Bench|year:{item['year']}|index:{index}|"
                        f"commit:{commit[:12]}"
                    ),
                    "title": f"高考真题候选02·{spec['subject']}·{item['year']}·{index}",
                    "tags": [
                        f"kp:{code}",
                        "origin:external",
                        "grade:high-school",
                        "region-fit:qinghai-curriculum",
                        "batch:qinghai-six-subject-history-02",
                        "review:required",
                    ],
                }
            )
    if len(questions) != 60:
        raise ValueError(f"预期60题，实际{len(questions)}题")
    return {"questions": questions}


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
