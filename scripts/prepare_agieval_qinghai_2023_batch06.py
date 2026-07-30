from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPECTED_COMMIT = "84ab72d94318290aad2e4ec820d535a95a1f7552"


@dataclass(frozen=True)
class Selection:
    dataset: str
    row: int
    subject: str
    chapter: str
    code: str
    standard_name: str
    difficulty: int
    solution: str


SELECTIONS = (
    Selection(
        "gaokao-physics.jsonl",
        155,
        "物理",
        "曲线运动",
        "PHY-PROJECTILE-HORIZONTAL",
        "平抛运动规律",
        2,
        "铅球离手后只受重力，机械能守恒；加速度始终为竖直向下的重力加速度 "
        "$g$。下落过程中竖直分速度增大，速度和动能也增大。因此正确答案为 B。",
    ),
    Selection(
        "gaokao-physics.jsonl",
        157,
        "物理",
        "曲线运动",
        "PHY-CIRCULAR-CENTRIPETAL-ACCELERATION",
        "向心加速度",
        3,
        "匀速圆周运动的合力 $F=m\\frac{4\\pi^2r}{T^2}$。由 $T\\propto r^{-1}$，"
        "可得 $T^2\\propto r^{-2}$，所以 $F\\propto r^3$，即 $n=3$。正确答案为 C。",
    ),
    Selection(
        "gaokao-physics.jsonl",
        160,
        "物理",
        "机械振动与机械波",
        "PHY-WAVE-SPEED-FREQUENCY-WAVELENGTH",
        "波速、波长与频率的关系",
        2,
        "同一声源发出的声波进入不同介质后，频率由声源决定，周期也不变；波速由介质"
        "决定而改变。由 $v=f\\lambda$，频率不变而波速改变，波长也改变。因此正确答案为 A。",
    ),
    Selection(
        "gaokao-physics.jsonl",
        161,
        "物理",
        "功和能",
        "PHY-WORK-ENERGY-KINETIC",
        "动能概念与计算",
        2,
        "雨滴做匀速直线运动，动能不变，合力做功为零。重力做正功 $mgh$，空气阻力"
        "做功为 $-mgh$，所以克服空气阻力做功为 $mgh$。正确答案为 B。",
    ),
    Selection(
        "gaokao-physics.jsonl",
        163,
        "物理",
        "万有引力",
        "PHY-GRAVITY-UNIVERSAL-LAW",
        "万有引力定律",
        3,
        "物资质量不随位置改变；轨道半径大于地球半径，所受地球引力小于同一物体在"
        "地面所受引力。空间站轨道低于同步轨道，由 $\\omega=\\sqrt{GM/r^3}$ 可知其"
        "角速度大于地球自转角速度。因此正确答案为 D。",
    ),
    Selection(
        "gaokao-chemistry.jsonl",
        188,
        "化学",
        "化学基本概念",
        "CHEM-CONCEPT-REDOX",
        "氧化还原反应",
        2,
        "暖贴中铁粉与空气中的氧气反应，铁元素和氧元素的化合价发生变化，属于氧化还原"
        "反应。明矾净水、撒盐融雪和受激发光均不以元素化合价变化为特征。因此正确答案为 C。",
    ),
    Selection(
        "gaokao-chemistry.jsonl",
        189,
        "化学",
        "物质结构与性质",
        "CHEM-STRUCTURE-ATOM",
        "原子结构与元素周期律",
        3,
        "矿物遇盐酸产生无色无味气体，可判断含碳酸根；结合短周期元素及 "
        "$X^{2-}$、$Y^{2+}$ 等电子，可确定 $W$、$X$、$Y$ 分别为 C、O、Mg。"
        "氧常见化合价有 $-1$ 和 $-2$；原子半径应为 Mg>C>O，$Mg(OH)_2$ 不具有"
        "两性，碳的同素异形体也不只四种。因此正确答案为 A。",
    ),
    Selection(
        "gaokao-chemistry.jsonl",
        190,
        "化学",
        "无机元素及其化合物",
        "CHEM-INORGANIC-TRANSFORMATION",
        "无机物转化与推断",
        3,
        "胆矾久置发生风化，结晶水逐渐失去，表面形成白色无水硫酸铜，D 可解释现象。"
        "A 中所列产物不能正确解释棕黄色沉淀；B 把硫化物完全氧化为无色硫酸盐，不能"
        "解释浑浊变深；C 所列溴的歧化方程式不正确。因此正确答案为 D。",
    ),
    Selection(
        "gaokao-biology.jsonl",
        216,
        "生物",
        "细胞代谢",
        "BIO-METABOLISM-PHOTOSYNTHESIS",
        "光合作用",
        2,
        "叶绿素含氮和镁，叶绿素与类胡萝卜素均位于类囊体薄膜，类胡萝卜素主要吸收"
        "蓝紫光。色素在层析液中的溶解度越高，随层析液扩散越快，而不是越慢。"
        "因此错误叙述为 D。",
    ),
    Selection(
        "gaokao-biology.jsonl",
        217,
        "生物",
        "稳态与调节",
        "BIO-HOMEOSTASIS-NEURAL-HUMORAL",
        "神经调节与体液调节",
        2,
        "细胞外液渗透压下降时，机体应减少抗利尿激素释放，降低肾小管和集合管对水的"
        "重吸收。B 把调节方向说反。其余三项符合甲状腺轴、胸腺功能和激素运输特点。"
        "因此错误叙述为 B。",
    ),
    Selection(
        "gaokao-biology.jsonl",
        218,
        "生物",
        "遗传与进化",
        "BIO-GENETICS-LAWS",
        "遗传基本规律",
        3,
        "两个自交实验的 2∶1 分离比分别说明 $AA$ 和 $BB$ 致死，因此宽叶高茎"
        "只能是 $AaBb$。其自交后，在存活子代中每个基因座的纯合隐性个体均占 "
        "$1/3$，两对独立时纯合子 $aabb$ 占 $1/9$，不是 $1/4$。因此错误叙述为 D。",
    ),
)


def repository_commit(source_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _read_row(source_file: Path, row: int) -> dict[str, Any]:
    lines = source_file.read_text(encoding="utf-8").splitlines()
    if row < 1 or row > len(lines):
        raise ValueError(f"{source_file.name}: row {row} does not exist")
    return json.loads(lines[row - 1])


def _clean_options(options: list[str]) -> list[str]:
    return [re.sub(r"^\s*\([A-D]\)\s*", "", option).strip() for option in options]


def build(source_root: Path) -> dict[str, object]:
    commit = repository_commit(source_root)
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"AGIEval commit mismatch: expected {EXPECTED_COMMIT}, got {commit}")

    data_root = source_root / "data" / "v1_1"
    questions: list[dict[str, object]] = []
    for item in SELECTIONS:
        record = _read_row(data_root / item.dataset, item.row)
        answer = record.get("label")
        options = _clean_options(record.get("options") or [])
        if answer not in "ABCD" or len(options) != 4:
            raise ValueError(f"{item.dataset}:{item.row}: expected one A-D answer and 4 options")

        source_name = str(record["other"]["source"]).strip()
        questions.append(
            {
                "subject": item.subject,
                "chapter": item.chapter,
                "knowledge_points": [item.standard_name],
                "difficulty": item.difficulty,
                "type": "single_choice",
                "question": str(record["question"]).strip(),
                "options": options,
                "answer": answer,
                "solution": item.solution,
                "source": (
                    f"AGIEval-v1.1|dataset:{item.dataset.removesuffix('.jsonl')}|"
                    f"row:{item.row}|original:{source_name}|commit:{commit[:12]}"
                ),
                "title": f"2023高考真题·{item.subject}·AGIEval-{item.row}",
                "tags": [
                    f"kp:{item.code}",
                    "origin:external",
                    "grade:high-school",
                    "region-fit:qinghai",
                    "source-year:2023",
                    "batch:agieval-qinghai-2023-06",
                    "review:independent-answer-passed",
                    "review:semantic-passed",
                ],
            }
        )

    return {
        "schema_version": "shiguang-question-candidate-v1",
        "batch": "agieval-qinghai-2023-06",
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
