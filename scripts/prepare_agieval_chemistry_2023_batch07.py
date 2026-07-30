from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPECTED_COMMIT = "84ab72d94318290aad2e4ec820d535a95a1f7552"
DATASET = "gaokao-chemistry.jsonl"


@dataclass(frozen=True)
class Selection:
    row: int
    chapter: str
    code: str
    standard_name: str
    difficulty: int
    solution: str


SELECTIONS = (
    Selection(
        187,
        "化学实验",
        "CHEM-EXPERIMENT-OPERATION",
        "实验基本操作与安全",
        3,
        "粗盐提纯要称量、溶解、过滤和蒸发，需要天平、烧杯和酒精灯；配制一定物质的量"
        "浓度的溶液必须使用容量瓶。因此必需仪器组合为①⑤⑥⑧，正确答案为 D。",
    ),
    Selection(
        193,
        "无机元素及其化合物",
        "CHEM-INORGANIC-NONMETAL",
        "非金属及其化合物",
        2,
        "$SiO_2$ 能与碱反应生成盐和水，属于酸性氧化物，且熔点很高、耐高温。$CO_2$"
        "不耐高温，$MgO$ 和 $Na_2O$ 均为碱性氧化物。因此正确答案为 B。",
    ),
    Selection(
        194,
        "物质结构与性质",
        "CHEM-STRUCTURE-ATOM",
        "原子结构与元素周期律",
        2,
        "铜是 d 区元素，不位于 p 区，A 错误。硫酸铜是可溶性盐，属于强电解质；其"
        "溶液因铜离子水解呈酸性，重金属盐还能使蛋白质变性。因此正确答案为 A。",
    ),
    Selection(
        195,
        "无机元素及其化合物",
        "CHEM-INORGANIC-TRANSFORMATION",
        "无机物转化与推断",
        2,
        "$NaClO$ 用于消毒是因为 $ClO^-$ 具有氧化性，而不是因为溶液呈碱性。其余"
        "三项所列性质与用途之间存在直接对应关系。因此不正确的是 C。",
    ),
    Selection(
        196,
        "无机元素及其化合物",
        "CHEM-INORGANIC-METAL",
        "金属及其化合物",
        2,
        "常温下铁在浓硝酸中发生钝化，不能用该反应制备 $NO_2$，D 错误。钠可置换"
        "乙醇羟基中的氢；黄铁矿焙烧可制 $SO_2$；氨催化氧化可制 $NO$。正确答案为 D。",
    ),
    Selection(
        197,
        "化学基本概念",
        "CHEM-CONCEPT-REDOX",
        "氧化还原反应",
        3,
        "$NH_2OH$ 中氮为 $-1$ 价，$N_2O$ 中氮的平均价为 $+1$。生成 1 mol "
        "$N_2O$ 含 2 mol 氮，共失去 4 mol 电子，A 正确；$NH_2OH$ 是还原剂，"
        "$Fe^{2+}$ 是正极还原产物。因此正确答案为 A。",
    ),
    Selection(
        198,
        "化学基本概念",
        "CHEM-CONCEPT-ION",
        "离子反应与离子方程式",
        3,
        "$H_2SO_3$ 是弱酸，在离子方程式中不能拆写为大量 $SO_3^{2-}$，所以 D "
        "不能正确表示反应。其余三项的物质拆分、原子和电荷守恒均符合相应条件。"
        "正确答案为 D。",
    ),
    Selection(
        199,
        "有机化学基础",
        "CHEM-ORGANIC-STRUCTURE",
        "有机物结构与性质",
        2,
        "糖类通常定义为多羟基醛、多羟基酮以及能水解生成它们的物质，不能说都是"
        "多羟基醛及其缩合产物，A 错误。蛋白质的颜色反应、低级酯的香味以及两种"
        "聚合物的热塑性说法均正确。因此正确答案为 A。",
    ),
    Selection(
        200,
        "物质结构与性质",
        "CHEM-STRUCTURE-ATOM",
        "原子结构与元素周期律",
        3,
        "由电子排布和题设可确定 $X、Y、Z、M、Q$ 依次为 Be、C、N、O、Na。"
        "氧通常不讨论最高正价，故“Z 的最高正价小于 M”不正确；$Na_2O_2$ 含"
        "非极性 O—O 键，且硝酸酸性强于碳酸。因此正确答案为 B。",
    ),
    Selection(
        201,
        "化学反应原理",
        "CHEM-REACTION-AQUEOUS",
        "水溶液中的离子平衡",
        2,
        "重油转化为小分子烃属于裂化或裂解，不消耗水，与水解无关。纯碱去油脂涉及"
        "油脂水解；蛋白质生成氨基酸是水解；制备氢氧化铁胶体涉及铁离子水解。"
        "正确答案为 B。",
    ),
    Selection(
        202,
        "化学反应原理",
        "CHEM-REACTION-RATE-EQUILIBRIUM",
        "反应速率与化学平衡",
        2,
        "$2NO_2\\rightleftharpoons N_2O_4$ 的正反应放热，升温使平衡向 $NO_2$"
        "方向移动，气体颜色加深，可用平衡移动解释。A、D 是反应速率或原电池效应，"
        "C 涉及钝化被破坏。因此正确答案为 B。",
    ),
    Selection(
        203,
        "化学基本概念",
        "CHEM-CONCEPT-ION",
        "离子反应与离子方程式",
        2,
        "食醋中的醋酸是弱电解质，在离子方程式中应保留分子形式，不能写成 $H^+$，"
        "所以 B 与事实不相符。其余方程式均符合物质状态、反应条件及守恒要求。"
        "正确答案为 B。",
    ),
)


def _commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _row(path: Path, number: int) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return json.loads(lines[number - 1])


def build(source_root: Path) -> dict[str, object]:
    commit = _commit(source_root)
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"AGIEval commit mismatch: {commit}")
    source_file = source_root / "data" / "v1_1" / DATASET
    questions = []
    for selection in SELECTIONS:
        record = _row(source_file, selection.row)
        options = [
            re.sub(r"^\s*\([A-D]\)\s*", "", option).strip()
            for option in record.get("options", [])
        ]
        answer = record.get("label")
        if len(options) != 4 or answer not in "ABCD":
            raise ValueError(f"row {selection.row}: incomplete single-choice record")
        source_name = str(record["other"]["source"]).strip()
        questions.append(
            {
                "subject": "化学",
                "chapter": selection.chapter,
                "knowledge_points": [selection.standard_name],
                "difficulty": selection.difficulty,
                "type": "single_choice",
                "question": str(record["question"]).strip(),
                "options": options,
                "answer": answer,
                "solution": selection.solution,
                "source": (
                    f"AGIEval-v1.1|dataset:gaokao-chemistry|row:{selection.row}|"
                    f"original:{source_name}|commit:{commit[:12]}"
                ),
                "title": f"2023高考真题·化学·AGIEval-{selection.row}",
                "tags": [
                    f"kp:{selection.code}",
                    "origin:external",
                    "grade:high-school",
                    "region-fit:qinghai-curriculum",
                    "source-year:2023",
                    "batch:agieval-chemistry-2023-07",
                    "review:independent-answer-passed",
                    "review:semantic-passed",
                ],
            }
        )
    return {
        "schema_version": "shiguang-question-candidate-v1",
        "batch": "agieval-chemistry-2023-07",
        "source_commit": commit,
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
    print(json.dumps({"generated": len(payload["questions"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
