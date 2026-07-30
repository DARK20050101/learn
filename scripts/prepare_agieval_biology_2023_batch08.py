from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPECTED_COMMIT = "84ab72d94318290aad2e4ec820d535a95a1f7552"
DATASET = "gaokao-biology.jsonl"


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
        211,
        "细胞的结构与功能",
        "BIO-CELL-STRUCTURE",
        "细胞结构与功能",
        2,
        "乙醇可通过自由扩散跨膜；抗体分泌的胞吐过程需要能量；葡萄糖既可能协助扩散，"
        "也可能主动运输。红细胞维持较高的胞内钾浓度需要载体并消耗 ATP，B 正确。",
    ),
    Selection(
        212,
        "稳态与调节",
        "BIO-HOMEOSTASIS-PLANT",
        "植物生命活动调节",
        2,
        "色氨酸可转变为生长素，生长素能运输到其他部位，并可与乙烯等激素共同调节"
        "生长发育。激素是信息分子，不是催化细胞代谢的酶，因此错误叙述为 D。",
    ),
    Selection(
        213,
        "稳态与调节",
        "BIO-HOMEOSTASIS-NEURAL-HUMORAL",
        "神经调节与体液调节",
        2,
        "膝跳反射的神经中枢位于脊髓，只要反射弧和脊髓相应部位完整，即使脑部受损仍"
        "可完成反射。大脑皮层的高级调节、脑和脊髓中的神经元以及高级中枢对低级中枢"
        "的调控均正确，因此错误叙述为 D。",
    ),
    Selection(
        214,
        "生态系统",
        "BIO-ECOLOGY-ECOSYSTEM",
        "生态系统的结构与能量流动",
        2,
        "生产者是第一营养级，初级消费者是第二营养级，次级消费者应属于第三营养级，"
        "所以 C 错误。同种动物可因食性不同处于不同营养级，生态系统能量沿营养级"
        "单向流动，其源头通常是太阳能。",
    ),
    Selection(
        215,
        "遗传与进化",
        "BIO-GENETICS-LAWS",
        "遗传基本规律",
        3,
        "全抗与抗性植株杂交时，全抗亲本至少含 $A_1$，抗性亲本不含 $A_1$，不能"
        "得到全抗∶抗性为 3∶1。$A_2a\\times aa$ 可得 1∶1；"
        "$A_1A_2\\times aa$ 可得全抗∶抗性 1∶1；$A_1a\\times A_2a$ 可得"
        "2∶1∶1。因此错误叙述为 A。",
    ),
    Selection(
        219,
        "细胞的结构与功能",
        "BIO-CELL-STRUCTURE",
        "细胞结构与功能",
        2,
        "葡萄糖是极性较强的分子，通常需要膜上转运蛋白协助，不能直接通过脂双层自由"
        "扩散。血糖受激素调节，进入肝细胞后可氧化或合成肝糖原，进入脂肪细胞后也可"
        "转化为甘油三酯。因此错误叙述为 B。",
    ),
    Selection(
        220,
        "稳态与调节",
        "BIO-HOMEOSTASIS-PLANT",
        "植物生命活动调节",
        3,
        "春化处理说明一定低温可促进某些植物开花，光周期处理说明昼夜长短影响开花，"
        "A 合理。风干主要抑制种子呼吸而合理密植主要提高光能利用；春化并非促进"
        "光合作用；光周期处理也不是以降低呼吸为主要目的。",
    ),
    Selection(
        221,
        "稳态与调节",
        "BIO-HOMEOSTASIS-IMMUNE",
        "免疫调节",
        3,
        "①免疫细胞受体能识别相应抗原；④两类特异性免疫均能形成相应记忆细胞；"
        "⑤某些细菌既可引发体液免疫也可引发细胞免疫。B 细胞也能呈递抗原，辅助性"
        "T 细胞也参与细胞免疫，所以②③错误。正确组合为①④⑤，即 B。",
    ),
    Selection(
        222,
        "生态系统",
        "BIO-ECOLOGY-POPULATION-COMMUNITY",
        "种群与群落",
        2,
        "红外相机能在干扰较小的情况下记录不同物种和个体，可据此估计物种丰富度及"
        "东北豹种群密度；影像也可记录幼年个体，并非只能调查成年个体。因此错误"
        "叙述为 D。",
    ),
    Selection(
        223,
        "遗传与进化",
        "BIO-GENETICS-LAWS",
        "遗传基本规律",
        3,
        "$AaBb$ 自交时，$A_B_、aaB_或A_bb、aabb$ 分别表现为高秆、矮秆、"
        "极矮秆，比例为 9∶6∶1。矮秆中的纯合子 $aaBB$ 和 $AAbb$ 占 $2/6=1/3$，"
        "而非 $1/2$；高秆中的纯合子 $AABB$ 占 $1/9$。因此错误叙述为 D。",
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
    return json.loads(path.read_text(encoding="utf-8").splitlines()[number - 1])


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
                "subject": "生物",
                "chapter": selection.chapter,
                "knowledge_points": [selection.standard_name],
                "difficulty": selection.difficulty,
                "type": "single_choice",
                "question": str(record["question"]).strip(),
                "options": options,
                "answer": answer,
                "solution": selection.solution,
                "source": (
                    f"AGIEval-v1.1|dataset:gaokao-biology|row:{selection.row}|"
                    f"original:{source_name}|commit:{commit[:12]}"
                ),
                "title": f"2023高考真题·生物·AGIEval-{selection.row}",
                "tags": [
                    f"kp:{selection.code}",
                    "origin:external",
                    "grade:high-school",
                    "region-fit:qinghai-curriculum",
                    "source-year:2023",
                    "batch:agieval-biology-2023-08",
                    "review:independent-answer-passed",
                    "review:semantic-passed",
                ],
            }
        )
    return {
        "schema_version": "shiguang-question-candidate-v1",
        "batch": "agieval-biology-2023-08",
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
