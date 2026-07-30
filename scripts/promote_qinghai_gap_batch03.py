from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

CATALOG = {
    "CHEM-CONCEPT-AMOUNT": ("化学基本概念", "物质的量与化学计量"),
    "CHEM-CONCEPT-ION": ("化学基本概念", "离子反应与离子方程式"),
    "CHEM-CONCEPT-REDOX": ("化学基本概念", "氧化还原反应"),
    "CHEM-EXPERIMENT-DESIGN": ("化学实验", "实验方案设计与评价"),
    "CHEM-EXPERIMENT-OPERATION": ("化学实验", "实验基本操作与安全"),
    "CHEM-INORGANIC-NONMETAL": ("无机元素及其化合物", "非金属及其化合物"),
    "CHEM-INORGANIC-TRANSFORMATION": ("无机元素及其化合物", "无机物转化与推断"),
    "CHEM-ORGANIC-REACTION": ("有机化学基础", "有机反应类型"),
    "CHEM-REACTION-AQUEOUS": ("化学反应原理", "水溶液中的离子平衡"),
    "CHEM-REACTION-ENERGY": ("化学反应原理", "化学反应与能量"),
    "CHEM-REACTION-RATE-EQUILIBRIUM": ("化学反应原理", "反应速率与化学平衡"),
    "CHEM-STRUCTURE-ATOM": ("物质结构与性质", "原子结构与元素周期律"),
    "CHEM-STRUCTURE-BOND": ("物质结构与性质", "化学键与分子结构"),
    "BIO-CELL-LIFE-CYCLE": ("分子与细胞", "细胞生命历程"),
    "BIO-CELL-MOLECULE": ("分子与细胞", "组成细胞的分子"),
    "BIO-CELL-STRUCTURE": ("分子与细胞", "细胞结构与功能"),
    "BIO-ECOLOGY-ECOSYSTEM": ("生物与环境", "生态系统结构与功能"),
    "BIO-ECOLOGY-POPULATION-COMMUNITY": ("生物与环境", "种群与群落"),
    "BIO-GENETICS-LAWS": ("遗传与进化", "遗传基本规律"),
    "BIO-GENETICS-MOLECULAR": ("遗传与进化", "遗传的分子基础"),
    "BIO-HOMEOSTASIS-IMMUNE": ("稳态与调节", "免疫调节"),
    "BIO-HOMEOSTASIS-NEURAL-HUMORAL": ("稳态与调节", "神经调节与体液调节"),
    "BIO-HOMEOSTASIS-PLANT": ("稳态与调节", "植物生命活动调节"),
    "BIO-METABOLISM-ENZYME-ATP": ("细胞代谢", "酶与ATP"),
    "BIO-METABOLISM-PHOTOSYNTHESIS": ("细胞代谢", "光合作用"),
    "BIO-METABOLISM-RESPIRATION": ("细胞代谢", "细胞呼吸"),
}

# One-based draft ordinal -> (decision, canonical code, reviewed difficulty, reason).
REVIEW = {
    1: ("REVISE", "CHEM-REACTION-RATE-EQUILIBRIUM", 3, "考查平衡移动"),
    2: ("PASS", "CHEM-CONCEPT-REDOX", 3, "氧化数与电子守恒"),
    3: ("REJECT", None, None, "正式题库已存在相同题目"),
    4: ("REVISE", "CHEM-CONCEPT-REDOX", 3, "电化学本质为氧化还原"),
    5: ("REJECT", None, None, "正式题库已存在相同题目"),
    6: ("PASS", "CHEM-REACTION-AQUEOUS", 2, "溶液中性判据"),
    7: ("REJECT", None, None, "跨多个无关考点，无法诊断单一薄弱点"),
    8: ("PASS", "CHEM-REACTION-AQUEOUS", 2, "盐类水解"),
    9: ("REVISE", "CHEM-ORGANIC-REACTION", 2, "有机加成反应"),
    10: ("REVISE", "CHEM-CONCEPT-AMOUNT", 2, "阿伏加德罗常数"),
    11: ("REVISE", "CHEM-REACTION-ENERGY", 3, "盖斯定律"),
    12: ("PASS", "CHEM-REACTION-AQUEOUS", 3, "溶度积计算"),
    13: ("PASS", "CHEM-REACTION-RATE-EQUILIBRIUM", 3, "反应机理与速率"),
    14: ("REVISE", "CHEM-EXPERIMENT-OPERATION", 2, "实验仪器与基本操作"),
    15: ("REJECT", None, None, "关键化学品名称OCR损坏，无法可靠恢复"),
    16: ("REVISE", "CHEM-STRUCTURE-ATOM", 3, "元素推断与周期律"),
    17: ("REVISE", "CHEM-CONCEPT-AMOUNT", 2, "微粒数计算"),
    18: ("REVISE", "CHEM-EXPERIMENT-DESIGN", 3, "实验方案可行性评价"),
    19: ("REVISE", "CHEM-ORGANIC-REACTION", 2, "加成反应判断"),
    20: ("REVISE", "CHEM-STRUCTURE-ATOM", 3, "元素推断与周期律"),
    21: ("REVISE", "CHEM-INORGANIC-TRANSFORMATION", 3, "混合物性质推断"),
    22: ("REVISE", "CHEM-CONCEPT-AMOUNT", 2, "微粒组成与计量"),
    23: ("REVISE", "CHEM-EXPERIMENT-OPERATION", 3, "实验操作与滴定指示剂"),
    24: ("PASS", "CHEM-STRUCTURE-BOND", 3, "元素推断与化学键"),
    25: ("REVISE", "BIO-CELL-STRUCTURE", 1, "细胞结构与生物膜"),
    26: ("PASS", "BIO-METABOLISM-RESPIRATION", 2, "细胞呼吸过程"),
    27: ("REVISE", "BIO-CELL-STRUCTURE", 2, "显微观察与细胞材料选择"),
    28: ("REVISE", "BIO-GENETICS-MOLECULAR", 2, "基因突变的分子本质"),
    29: ("PASS", "BIO-METABOLISM-PHOTOSYNTHESIS", 2, "镁对光合作用的影响"),
    30: ("REJECT", None, None, "原答案B与解析结论BD冲突，存在多答案风险"),
    31: ("PASS", "BIO-GENETICS-MOLECULAR", 2, "翻译模板与蛋白质序列"),
    32: ("REVISE", "BIO-GENETICS-MOLECULAR", 2, "遗传信息表达"),
    33: ("REVISE", "BIO-CELL-LIFE-CYCLE", 3, "有丝分裂与减数分裂比较"),
    34: ("PASS", "BIO-ECOLOGY-POPULATION-COMMUNITY", 3, "种群密度调查"),
    35: ("PASS", "BIO-GENETICS-LAWS", 3, "分离定律实验设计"),
    36: ("REVISE", "BIO-CELL-MOLECULE", 2, "核酸分布与结构"),
    37: ("PASS", "BIO-METABOLISM-PHOTOSYNTHESIS", 1, "叶绿素吸收光谱"),
    38: ("REVISE", "BIO-METABOLISM-RESPIRATION", 2, "微生物呼吸"),
    39: ("PASS", "BIO-HOMEOSTASIS-IMMUNE", 1, "免疫细胞分类"),
    40: ("REVISE", "BIO-GENETICS-MOLECULAR", 2, "DNA是遗传物质的证据"),
    41: ("PASS", "BIO-METABOLISM-ENZYME-ATP", 2, "酶的特性"),
    42: ("REVISE", "BIO-HOMEOSTASIS-NEURAL-HUMORAL", 2, "内环境稳态"),
    43: ("REVISE", "BIO-CELL-STRUCTURE", 2, "质壁分离实验"),
    44: ("PASS", "BIO-HOMEOSTASIS-PLANT", 2, "生长素"),
    45: ("PASS", "BIO-ECOLOGY-POPULATION-COMMUNITY", 2, "群落演替"),
    46: ("REVISE", "BIO-CELL-MOLECULE", 2, "蛋白质结构与功能"),
    47: ("REVISE", "BIO-CELL-STRUCTURE", 1, "胞吐与跨核孔运输"),
    48: ("PASS", "BIO-ECOLOGY-ECOSYSTEM", 1, "生态系统稳定性"),
    49: ("PASS", "BIO-ECOLOGY-ECOSYSTEM", 1, "能量流动"),
}

TEXT_REPLACEMENTS = {
    2: {"solution": [("末发生变化", "未发生变化")]},
    4: {"question": [("\\mathrm{Fe}^{+} \\mathrm{Ni}", "\\mathrm{Fe}+\\mathrm{Ni}")]},
    10: {"options": [("\\square", "")]},
    14: {
        "question": [("（（）", "（ ）")],
        "options": [("雉形瓶", "锥形瓶"), ("雉型瓶", "锥形瓶")],
        "solution": [("雉形瓶", "锥形瓶"), ("雉型瓶", "锥形瓶")],
    },
    23: {
        "options": [("酚唒", "酚酞"), ("加人液体", "加入液体")],
        "solution": [("酚唒", "酚酞"), ("酚䣭", "酚酞")],
    },
    29: {"solution": [("缺鎂", "缺镁")]},
}


def _replace(value: Any, replacements: list[tuple[str, str]]) -> Any:
    if isinstance(value, str):
        for old, new in replacements:
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [_replace(item, replacements) for item in value]
    return value


def promote(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    questions = payload.get("questions", [])
    if len(questions) != len(REVIEW):
        raise ValueError(f"expected {len(REVIEW)} questions, got {len(questions)}")

    promoted: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    distribution: Counter[str] = Counter()
    for ordinal, original in enumerate(questions, 1):
        decision, code, difficulty, reason = REVIEW[ordinal]
        record = {
            "ordinal": ordinal,
            "source": original["source"],
            "decision": decision,
            "reason": reason,
        }
        if decision == "REJECT":
            records.append(record)
            continue
        assert code is not None and difficulty is not None
        chapter, name = CATALOG[code]
        question = dict(original)
        question["chapter"] = chapter
        question["knowledge_points"] = [name]
        question["difficulty"] = difficulty
        question["tags"] = [
            tag for tag in question.get("tags", []) if not tag.startswith(("kp:", "review:"))
        ] + [f"kp:{code}", f"review:{decision.lower()}-semantic"]
        for field, replacements in TEXT_REPLACEMENTS.get(ordinal, {}).items():
            question[field] = _replace(question[field], replacements)
        promoted.append(question)
        distribution[code] += 1
        record.update({"knowledge_point_code": code, "difficulty": difficulty})
        records.append(record)

    candidate = {
        "schema_version": "shiguang-question-candidate-v1",
        "batch": "qinghai-gap-03-semantic-reviewed",
        "source_commit": payload.get("source_commit"),
        "distribution": dict(sorted(distribution.items())),
        "questions": promoted,
    }
    report = {
        "schema_version": "shiguang-semantic-review-v1",
        "input_questions": len(questions),
        "release_questions": len(promoted),
        "passed": sum(item["decision"] == "PASS" for item in records),
        "revised": sum(item["decision"] == "REVISE" for item in records),
        "rejected": sum(item["decision"] == "REJECT" for item in records),
        "records": records,
    }
    return candidate, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote the reviewed Qinghai gap batch.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    candidate, report = promote(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in report if key != "records"}))


if __name__ == "__main__":
    main()
