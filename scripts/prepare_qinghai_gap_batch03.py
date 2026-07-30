from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.prepare_qinghai_six_subject_batch import repository_commit, split_question

SUBJECT_SPECS = {
    "chemistry": {
        "file": "2010-2022_Chemistry_MCQs.json",
        "subject": "化学",
        "limit": 24,
        "rules": [
            (r"氧化还原|化合价|电子转移", "化学基本概念", "CHEM-CONCEPT-REDOX", "氧化还原反应"),
            (
                r"反应速率|化学平衡|平衡移动|平衡常数",
                "化学反应原理",
                "CHEM-REACTION-RATE-EQUILIBRIUM",
                "反应速率与化学平衡",
            ),
            (
                r"pH|水解|电离平衡|溶度积|酸碱中和",
                "化学反应原理",
                "CHEM-REACTION-AQUEOUS",
                "水溶液中的离子平衡",
            ),
            (
                r"原子结构|电子排布|元素周期|周期表",
                "物质结构",
                "CHEM-STRUCTURE-ATOM",
                "原子结构与元素周期律",
            ),
            (
                r"化学键|分子结构|杂化|键角|极性分子",
                "物质结构",
                "CHEM-STRUCTURE-BOND",
                "化学键与分子结构",
            ),
            (
                r"合成路线|有机合成|合成有机物",
                "有机化学基础",
                "CHEM-ORGANIC-SYNTHESIS",
                "有机合成与推断",
            ),
            (
                r"实验|装置|操作|现象|检验",
                "化学实验",
                "CHEM-EXPERIMENT-ANALYSIS",
                "实验现象与数据分析",
            ),
            (
                r"金属|铁|铝|铜|钠|镁",
                "无机元素及其化合物",
                "CHEM-INORGANIC-METAL",
                "金属及其化合物",
            ),
            (
                r"氯|硫|氮|硅|非金属",
                "无机元素及其化合物",
                "CHEM-INORGANIC-NONMETAL",
                "非金属及其化合物",
            ),
        ],
    },
    "biology": {
        "file": "2010-2022_Biology_MCQs.json",
        "subject": "生物",
        "limit": 25,
        "rules": [
            (r"酶|ATP", "细胞代谢", "BIO-METABOLISM-ENZYME-ATP", "酶与ATP"),
            (r"光合作用|叶绿体|光合", "细胞代谢", "BIO-METABOLISM-PHOTOSYNTHESIS", "光合作用"),
            (r"细胞呼吸|有氧呼吸|无氧呼吸", "细胞代谢", "BIO-METABOLISM-RESPIRATION", "细胞呼吸"),
            (
                r"植物激素|生长素|赤霉素|脱落酸|乙烯",
                "稳态与调节",
                "BIO-HOMEOSTASIS-PLANT",
                "植物生命活动调节",
            ),
            (
                r"生态环境|环境保护|生物多样性|污染",
                "生物与环境",
                "BIO-ECOLOGY-ENVIRONMENT",
                "生态环境保护",
            ),
            (r"种群|群落|丰富度", "生物与环境", "BIO-ECOLOGY-POPULATION-COMMUNITY", "种群与群落"),
            (
                r"生态系统|食物链|能量流动|物质循环",
                "生物与环境",
                "BIO-ECOLOGY-ECOSYSTEM",
                "生态系统结构与功能",
            ),
            (
                r"基因工程|细胞工程|克隆|PCR|限制酶",
                "生物技术与工程",
                "BIO-TECHNOLOGY-CELL-GENE",
                "细胞工程与基因工程",
            ),
            (
                r"发酵|微生物培养|培养基",
                "生物技术与工程",
                "BIO-TECHNOLOGY-FERMENTATION",
                "发酵工程",
            ),
            (r"免疫|抗体|抗原|淋巴", "稳态与调节", "BIO-HOMEOSTASIS-IMMUNE", "免疫调节"),
            (r"遗传|基因型|表现型|孟德尔", "遗传与进化", "BIO-GENETICS-LAWS", "遗传基本规律"),
            (r"DNA|RNA|转录|翻译|复制", "遗传与进化", "BIO-GENETICS-MOLECULAR", "遗传的分子基础"),
        ],
    },
}

UNSAFE_MARKERS = ("![](", "\\begin{tabular}", "\\includegraphics", "如图", "下图")


def classify(text: str, rules: list[tuple[str, str, str, str]]) -> tuple[str, str, str] | None:
    for pattern, chapter, code, name in rules:
        if re.search(pattern, text):
            return chapter, code, name
    return None


def build(source_root: Path) -> dict[str, Any]:
    objective_root = source_root / "Data" / "Objective_Questions"
    commit = repository_commit(source_root)
    questions: list[dict[str, Any]] = []
    distribution: Counter[str] = Counter()

    for dataset, spec in SUBJECT_SPECS.items():
        payload = json.loads((objective_root / spec["file"]).read_text(encoding="utf-8"))
        selected = 0
        per_code: Counter[str] = Counter()
        for item in payload["example"]:
            if selected >= spec["limit"]:
                break
            answers = list("".join(item["answer"]))
            if not answers or any(answer not in "ABCD" for answer in answers):
                continue
            # Classification must use the stem only. Explanations mention many rejected
            # alternatives and caused unrelated knowledge-point matches in early drafts.
            raw_text = item["question"]
            if any(marker in raw_text for marker in UNSAFE_MARKERS):
                continue
            classification = classify(raw_text, spec["rules"])
            if not classification:
                continue
            chapter, code, name = classification
            if per_code[code] >= 4:
                continue
            try:
                stem, options = split_question(item["question"])
            except ValueError:
                continue
            if len(options) != 4 or len(set(options)) != 4:
                continue
            questions.append(
                {
                    "subject": spec["subject"],
                    "chapter": chapter,
                    "knowledge_points": [name],
                    "difficulty": 2 if int(item.get("score", 0)) <= 4 else 3,
                    "type": "single_choice" if len(answers) == 1 else "multiple_choice",
                    "question": stem,
                    "options": options,
                    "answer": answers[0] if len(answers) == 1 else answers,
                    "solution": " ".join(item["analysis"].split()),
                    "source": (
                        f"GAOKAO-Bench|dataset:{dataset}|year:{item['year']}|"
                        f"index:{item['index']}|commit:{commit[:12]}"
                    ),
                    "title": (f"高考真题候选03·{spec['subject']}·{item['year']}·{item['index']}"),
                    "tags": [
                        f"kp:{code}",
                        "origin:external",
                        "grade:high-school",
                        "region-fit:qinghai-curriculum",
                        "batch:qinghai-gap-03",
                        "review:required",
                    ],
                }
            )
            selected += 1
            per_code[code] += 1
            distribution[code] += 1
        if selected != spec["limit"]:
            raise ValueError(
                f"{spec['subject']} expected {spec['limit']} questions, selected {selected}"
            )

    return {
        "schema_version": "shiguang-question-draft-v1",
        "batch": "qinghai-gap-03",
        "source_commit": commit,
        "distribution": dict(sorted(distribution.items())),
        "questions": questions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = build(args.source_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "generated": len(payload["questions"]),
                "distribution": payload["distribution"],
                "output": str(args.output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
