# Static reviewed question text is intentionally kept intact.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

EXPECTED_COMMIT = "6dbb24f8d8439041e5431c4c184a582182a6ce9c"

QUESTIONS = [
    {
        "chapter": "生态系统",
        "code": "BIO-ECOLOGY-ENVIRONMENT",
        "name": "生态环境保护",
        "difficulty": 2,
        "question": "【2011高考真题材料改编】生活污水经过“厌氧沉淀池—曝气池—兼氧池—植物池”净化。生态工程的主要任务是（ ）",
        "options": [
            "只增加生产者数量",
            "修复受损生态系统并改善污染性生产方式",
            "彻底消灭分解者",
            "阻断生态系统物质循环",
        ],
        "answer": "B",
        "solution": "生态工程强调修复已被破坏的生态环境，改善造成污染和破坏的生产方式，并提高生态系统生产力。因此答案为 B。",
        "index": 5,
    },
    {
        "chapter": "生物技术与工程",
        "code": "BIO-TECHNOLOGY-FERMENTATION",
        "name": "发酵工程",
        "difficulty": 2,
        "question": "【2013高考真题材料改编】制作泡菜时，在冷却后的盐水中加入少量陈泡菜液，其主要目的是什么？",
        "options": [
            "提高食盐浓度",
            "接入乳酸菌并缩短发酵启动时间",
            "增加氧气含量",
            "直接除去亚硝酸盐",
        ],
        "answer": "B",
        "solution": "陈泡菜液中含有适应发酵环境的乳酸菌，相当于接种，可使乳酸菌数量较快增加并缩短发酵启动时间。因此答案为 B。",
        "index": 12,
    },
    {
        "chapter": "生物技术与工程",
        "code": "BIO-TECHNOLOGY-CELL-GENE",
        "name": "细胞工程与基因工程",
        "difficulty": 3,
        "question": "【2017高考真题材料改编】将几丁质酶目的基因与质粒载体连接时，DNA连接酶催化形成的化学键是（ ）",
        "options": ["氢键", "肽键", "磷酸二酯键", "二硫键"],
        "answer": "C",
        "solution": "DNA连接酶连接相邻脱氧核苷酸的脱氧核糖与磷酸基团，形成DNA骨架中的磷酸二酯键。因此答案为 C。",
        "index": 57,
    },
]


def build(root: Path) -> dict[str, object]:
    commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"source commit mismatch: {commit}")
    result = []
    for item in QUESTIONS:
        result.append(
            {
                "subject": "生物",
                "chapter": item["chapter"],
                "knowledge_points": [item["name"]],
                "difficulty": item["difficulty"],
                "type": "single_choice",
                "question": item["question"],
                "options": item["options"],
                "answer": item["answer"],
                "solution": item["solution"],
                "source": f"GAOKAO-Bench|adapted:true|biology-subjective|index:{item['index']}|commit:{commit[:12]}",
                "title": f"高考真题材料改编·生物·{item['index']}",
                "tags": [
                    f"kp:{item['code']}",
                    "origin:external-adapted",
                    "region-fit:qinghai-curriculum",
                    "batch:biology-adapted-09",
                    "review:independent-answer-passed",
                ],
            }
        )
    return {
        "schema_version": "shiguang-question-candidate-v1",
        "batch": "biology-adapted-09",
        "questions": result,
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


if __name__ == "__main__":
    main()
