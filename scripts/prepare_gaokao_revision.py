from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from scripts.apply_gaokao_review import DIFFICULTIES


def replace_kp(question: dict, code: str, name: str) -> None:
    question["knowledge_points"] = [name]
    question["tags"] = [
        tag for tag in question["tags"]
        if not tag.startswith("kp:") and not tag.startswith("review:")
    ] + [f"kp:{code}", "review:passed"]


def prepare(source: Path) -> dict:
    payload = json.loads(source.read_text(encoding="utf-8"))
    questions = copy.deepcopy(payload["questions"])
    if len(questions) != 50:
        raise ValueError("预期首批题库包含50题")

    for number, question in enumerate(questions, 1):
        question["difficulty"] = DIFFICULTIES[number]
        question["tags"] = [
            tag for tag in question["tags"] if not tag.startswith("review:")
        ] + ["review:passed"]

    questions[1]["solution"] = questions[1]["solution"].replace(
        "$=2^{|x|-4}$", "$=2^{|x|}-4$"
    )
    questions[12]["solution"] = questions[12]["solution"].replace(
        "$f(-x) \\cdot \\lg (-x)|=-f(x) \\cdot| g(x) \\mid$",
        "$f(-x) \\cdot |g(-x)|=-f(x) \\cdot |g(x)|$",
    )
    replace_kp(
        questions[16],
        "MATH-VECTOR-DOT-PRODUCT",
        "平面向量数量积",
    )
    questions[17]["solution"] = questions[17]["solution"].replace(
        "$y^{\\prime}=a \\frac{1}{x+1}$",
        "$y^{\\prime}=a-\\frac{1}{x+1}$",
    )
    questions[22]["question"] = questions[22]["question"].replace("粗䊁", "粗糙")
    replace_kp(
        questions[22],
        "PHY-WORK-ENERGY-WORK-CALCULATION",
        "功的计算",
    )
    questions[23]["options"][1] = (
        "$\\frac{3 \\pi g_{0}}{G T^{2}\\left(g_{0}-g\\right)}$"
    )
    questions[23]["solution"] = (
        "在两极有 $g_0=GM/R^2$。在赤道，万有引力与支持力之差提供"
        "向心力，因此 $g_0-g=4\\pi^2R/T^2$。又"
        "$\\rho=M/(4\\pi R^3/3)=3g_0/(4\\pi GR)$。消去 $R$ 得"
        "$\\rho=\\frac{3\\pi g_0}{GT^2(g_0-g)}$，故选B。"
    )
    questions[30]["question"] = (
        "(6分) 金星、地球和火星绕太阳的公转均可视为匀速圆周运动，"
        "它们的向心加速度大小分别为 $a_{金}$、$a_{地}$、$a_{火}$，"
        "沿轨道运行的速率分别为 $v_{金}$、$v_{地}$、$v_{火}$。已知轨道半径"
        "$R_{金}<R_{地}<R_{火}$，由此可以判定（ ）。"
    )
    questions[33]["question"] = questions[33]["question"].replace("进人", "进入")
    questions[33]["solution"] = (
        "忽略火星自转，在火星表面有 $GM=gR^2$。设与椭圆停泊轨道周期"
        "$T$ 相同的圆轨道半径为 $r$，由"
        "$GM/r^2=4\\pi^2r/T^2$ 得"
        "$r=\\sqrt[3]{GMT^2/(4\\pi^2)}$。椭圆半长轴等于该 $r$。"
        "近火点到火星中心的距离为 $R_1=R+d_1$，远火点距离"
        "$R_2=2r-R_1$，故最远离火星表面的距离"
        "$d_2=R_2-R\\approx6\\times10^7\\,\\mathrm{m}$，选C。"
    )
    questions[34]["question"] = questions[34]["question"].replace(
        "“天宫二号”空间站", "中国空间站"
    ).replace("“天宫二号”中", "中国空间站中")
    replace_kp(questions[38], "ENG-VOCAB-COLLOCATION", "固定搭配")
    replace_kp(
        questions[42],
        "ENG-VOCAB-SITUATIONAL-COMMUNICATION",
        "情景交际",
    )
    questions[45]["options"] = [
        option.replace("worm", "worn") for option in questions[45]["options"]
    ]
    questions[45]["tags"].append("capability:subject-verb-agreement")
    replace_kp(
        questions[46],
        "ENG-VOCAB-CONTEXT-ADVERB",
        "副词语境辨析",
    )
    return {"questions": questions}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = prepare(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"generated={len(payload['questions'])} output={args.output}")


if __name__ == "__main__":
    main()
