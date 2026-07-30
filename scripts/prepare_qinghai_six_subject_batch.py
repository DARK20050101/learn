from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

SELECTIONS = {
    "chinese": {
        "file": "2010-2022_Chinese_Lang_and_Usage_MCQs.json",
        "subject": "语文",
        "items": {
            0: ("语言文字运用", "CHN-LANGUAGE-WORDS", "词语辨析与使用", 2),
            1: ("语言文字运用", "CHN-LANGUAGE-SENTENCE", "病句辨析与修改", 3),
            2: ("语言文字运用", "CHN-LANGUAGE-EXPRESSION", "语言表达与衔接", 3),
            4: ("语言文字运用", "CHN-LANGUAGE-SENTENCE", "病句辨析与修改", 3),
            5: ("语言文字运用", "CHN-LANGUAGE-EXPRESSION", "语言表达与衔接", 3),
            6: ("语言文字运用", "CHN-LANGUAGE-WORDS", "词语辨析与使用", 2),
            7: ("语言文字运用", "CHN-LANGUAGE-SENTENCE", "病句辨析与修改", 3),
            8: ("语言文字运用", "CHN-LANGUAGE-EXPRESSION", "语言表达与衔接", 3),
            37: ("语言文字运用", "CHN-LANGUAGE-EXPRESSION", "语言表达与衔接", 2),
            39: ("语言文字运用", "CHN-LANGUAGE-EXPRESSION", "语言表达与衔接", 3),
        },
    },
    "math": {
        "file": "2010-2022_Math_I_MCQs.json",
        "subject": "数学",
        "items": {
            173: ("集合与逻辑", "MATH-SET-OPERATIONS", "集合的基本运算", 2),
            174: ("三角函数", "MATH-TRIG-FUNDAMENTAL-IDENTITY", "同角三角函数的基本关系", 2),
            176: ("解析几何", "MATH-ANALYTIC-CIRCLE-STANDARD", "圆的标准方程", 3),
            177: ("数列", "MATH-SEQUENCE-GEOMETRIC-GENERAL", "等比数列的通项公式", 3),
            183: ("集合与逻辑", "MATH-SET-OPERATIONS", "集合的基本运算", 2),
            184: ("复数", "MATH-COMPLEX-ARITHMETIC", "复数的四则运算", 2),
            185: ("指数与对数", "MATH-LOGARITHM-OPERATION", "对数运算", 2),
            187: ("数列", "MATH-SEQUENCE-GEOMETRIC-GENERAL", "等比数列的通项公式", 3),
            189: ("概率", "MATH-PROBABILITY-CLASSICAL", "古典概型", 3),
            202: ("平面向量", "MATH-VECTOR-DOT-PRODUCT", "平面向量数量积", 2),
        },
    },
    "english": {
        "file": "2010-2013_English_MCQs.json",
        "subject": "英语",
        "items": {
            27: ("词汇", "ENG-VOCAB-SITUATIONAL-COMMUNICATION", "情景交际", 2),
            29: ("语法", "ENG-GRAMMAR-ADJECTIVE-COMPARATIVE", "形容词比较级", 2),
            30: ("词汇", "ENG-VOCAB-SITUATIONAL-COMMUNICATION", "情景交际", 2),
            32: ("语法", "ENG-GRAMMAR-MODAL-BASIC", "情态动词的基本用法", 2),
            34: ("词汇", "ENG-VOCAB-CONTEXT-VERB", "动词语境辨析", 2),
            38: ("词汇", "ENG-VOCAB-COLLOCATION", "固定搭配", 2),
            41: ("语法", "ENG-GRAMMAR-ADJECTIVE-COMPARATIVE", "形容词比较级", 2),
            50: ("词汇", "ENG-VOCAB-COLLOCATION", "固定搭配", 2),
            55: ("从句", "ENG-CLAUSE-RELATIVE-WORD-SELECTION", "定语从句关系词的选择", 3),
            66: ("词汇", "ENG-VOCAB-CONTEXT-VERB", "动词语境辨析", 2),
        },
    },
    "physics": {
        "file": "2010-2022_Physics_MCQs.json",
        "subject": "物理",
        "items": {
            14: ("电磁感应", "PHY-INDUCTION-CURRENT-CONDITION", "产生感应电流的条件", 2),
            16: ("曲线运动", "PHY-PROJECTILE-HORIZONTAL", "平抛运动规律", 3),
            22: ("磁场", "PHY-MAGNETIC-FIELD-DIRECTION", "磁场方向的判断", 2),
            29: ("直线运动", "PHY-KINEMATICS-VELOCITY-EQUATION", "匀变速直线运动公式", 3),
            31: ("曲线运动", "PHY-PROJECTILE-HORIZONTAL", "平抛运动规律", 2),
            38: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律", 3),
            39: ("动量", "PHY-MOMENTUM-BASIC", "动量概念与计算", 3),
            42: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律", 2),
            51: ("万有引力", "PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律", 3),
            53: ("恒定电流", "PHY-CIRCUIT-ELECTRIC-POWER", "电功率的计算", 3),
        },
    },
    "chemistry": {
        "file": "2010-2022_Chemistry_MCQs.json",
        "subject": "化学",
        "items": {
            89: ("物质结构与性质", "CHEM-STRUCTURE-CRYSTAL", "晶体结构与性质", 2),
            91: ("有机化学基础", "CHEM-ORGANIC-STRUCTURE", "有机物结构与性质", 2),
            92: ("化学基本概念", "CHEM-CONCEPT-AMOUNT", "物质的量与化学计量", 3),
            95: ("无机元素及其化合物", "CHEM-INORGANIC-NONMETAL", "非金属及其化合物", 2),
            100: ("有机化学基础", "CHEM-ORGANIC-STRUCTURE", "有机物结构与性质", 2),
            104: ("无机元素及其化合物", "CHEM-INORGANIC-METAL", "金属及其化合物", 2),
            105: ("化学实验", "CHEM-EXPERIMENT-ANALYSIS", "实验现象与数据分析", 3),
            110: ("化学反应原理", "CHEM-REACTION-ENERGY", "化学反应与能量", 2),
            111: ("化学基本概念", "CHEM-CONCEPT-ION", "离子反应与离子方程式", 3),
            116: ("化学基本概念", "CHEM-CONCEPT-ION", "离子反应与离子方程式", 2),
        },
    },
    "biology": {
        "file": "2010-2022_Biology_MCQs.json",
        "subject": "生物",
        "items": {
            95: ("分子与细胞", "BIO-CELL-LIFE-CYCLE", "细胞生命历程", 2),
            97: ("细胞代谢", "BIO-METABOLISM-PHOTOSYNTHESIS", "光合作用", 2),
            98: ("稳态与调节", "BIO-HOMEOSTASIS-NEURAL-HUMORAL", "神经调节与体液调节", 3),
            100: ("分子与细胞", "BIO-CELL-STRUCTURE", "细胞结构与功能", 2),
            101: ("细胞代谢", "BIO-METABOLISM-RESPIRATION", "细胞呼吸", 2),
            103: ("稳态与调节", "BIO-HOMEOSTASIS-NEURAL-HUMORAL", "神经调节与体液调节", 2),
            104: ("遗传与进化", "BIO-GENETICS-LAWS", "遗传基本规律", 3),
            105: ("生物与环境", "BIO-ECOLOGY-ECOSYSTEM", "生态系统结构与功能", 3),
            109: ("细胞代谢", "BIO-METABOLISM-RESPIRATION", "细胞呼吸", 2),
            112: ("分子与细胞", "BIO-CELL-MOLECULE", "组成细胞的分子", 2),
        },
    },
}

OPTION_PATTERN = re.compile(r"(?<![A-Za-z])([A-D])[.．、]\s*", re.MULTILINE)


def split_question(raw: str) -> tuple[str, list[str]]:
    text = raw.strip()
    matches = list(OPTION_PATTERN.finditer(text))
    if len(matches) != 4 or [match.group(1) for match in matches] != list("ABCD"):
        raise ValueError("题目不能稳定拆分为A-D四个选项")
    stem = re.sub(r"^\s*\d+\s*[.．、]\s*(?:（[^）]*分）\s*)?", "", text[: matches[0].start()])
    stem = " ".join(stem.split()).strip()
    options = [
        " ".join(
            (
                text[match.end() : matches[index + 1].start()]
                if index < 3
                else text[match.end() :]
            ).split()
        )
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
    objective_root = source_root / "Data" / "Objective_Questions"
    commit = repository_commit(source_root)
    questions = []
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
            question_type = "single_choice" if len(answers) == 1 else "multiple_choice"
            questions.append(
                {
                    "subject": spec["subject"],
                    "chapter": chapter,
                    "knowledge_points": [name],
                    "difficulty": difficulty,
                    "type": question_type,
                    "question": stem,
                    "options": options,
                    "answer": answers[0] if len(answers) == 1 else answers,
                    "solution": " ".join(item["analysis"].split()),
                    "source": (
                        f"GAOKAO-Bench|year:{item['year']}|index:{index}|"
                        f"commit:{commit[:12]}"
                    ),
                    "title": f"高考真题候选·{spec['subject']}·{item['year']}·{index}",
                    "tags": [
                        f"kp:{code}",
                        "origin:external",
                        "grade:high-school",
                        "region-fit:qinghai-curriculum",
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
