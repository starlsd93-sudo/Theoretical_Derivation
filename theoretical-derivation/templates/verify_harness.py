# -*- coding: utf-8 -*-
"""R4 验证脚本骨架（领域无关）—— 模块独立验证 → 接缝四查 → 系统级验证

配 references/verification.md 使用。三段结构：
  ① 模块注册表：每个子结构一个 @module 函数，自带独立锚点 + 容差 + 五类判据，返回 verdict。
     单子结构任务只保留一个模块即可（等价于单脚本）。未 PASS 的模块不进合并。
  ② 接缝四查 seam_checks()：共享参数同一性 / 约定一致性 / 量纲链 / 合成 = 独立整算。
  ③ 系统 runner：跑接缝 + 系统级判据 → 打印并落盘 PASS/FAIL 矩阵。
H1：本脚本单会话直接跑。H2：每个模块改由独立 subagent 跑并回传同 schema 的 verdict。
H3：同一结构由流水线编排（并行模块 + barrier 接缝 + 循环至全过）。

约定：检查名以五类判据名开头（如 "external_anchor_closed_form"），verdict 据此自动汇总；
某类判据未覆盖 → 该模块判 FAIL（严格/标准模式缺一不可）。轻量模式可把 REQUIRED 改为前三类。
强制：判据 3 外部锚点不可省；随机性验证固定种子；退出码 0 = 全过、1 = 有 FAIL。

下方 cantilever_tip 是可运行示例（悬臂梁端部挠度），用于演示写法，使用时替换为本任务的子结构。
用法：python verify_harness.py [输出目录]
"""
import json
import os
import sys

import numpy as np
from scipy import integrate

SEED = 20261029
rng = np.random.default_rng(SEED)

# 参数冻结块（R3.5 冻结值；每项注明出处）。跨模块共享量只在这里定义一次。
PARAMS = dict(
    E=200e9,     # 弹性模量 Pa（示例值）
    I=8.0e-9,    # 截面惯性矩 m^4（示例值）
    L=0.5,       # 梁长 m（示例值）
    P=100.0,     # 端部集中力 N（示例值）
)

CRITERIA = ("analytic_vs_numeric", "structural", "external_anchor", "library_xcheck", "random_sampling")
REQUIRED = CRITERIA


def make_checker():
    rec = {"pass": [], "fail": []}

    def check(name: str, cond, detail: str = "") -> bool:
        ok = bool(cond)
        (rec["pass"] if ok else rec["fail"]).append(name)
        print(f"    [{'PASS' if ok else 'FAIL'}] {name}" + (f" | {detail}" if detail else ""))
        return ok
    return rec, check


def make_verdict(name, anchor_type, rec, key_values=None, tolerance="", notes=""):
    """按 verification.md §4.2 的 schema 组装 verdict。"""
    criteria = {}
    for c in CRITERIA:
        hit = [n for n in rec["pass"] + rec["fail"] if n.startswith(c)]
        criteria[c] = bool(hit) and not any(n.startswith(c) for n in rec["fail"])
    ok = not rec["fail"] and all(criteria[c] for c in REQUIRED)
    return {"module": name, "status": "PASS" if ok else "FAIL", "anchor_type": anchor_type,
            "criteria": criteria, "key_values": key_values or {},
            "tolerance": tolerance, "notes": notes}


def rel(a, b):
    return abs(a - b) / max(abs(b), 1e-300)


# ① 模块注册表
MODULES = {}


def module(name):
    def deco(fn):
        MODULES[name] = fn
        return fn
    return deco


# ---- 被验证的推导结果（来自 R3 选定推导）----
def tip_deflection(P, L, E, I):
    """推导所得：悬臂梁端部挠度 δ = P L^3 / (3 E I)"""
    return P * L**3 / (3 * E * I)


def deflection_curve(x, P, L, E, I):
    """推导所得挠曲线：EI·y = P(L x^2/2 − x^3/6)（C1 = C2 = 0）"""
    return P * (L * x**2 / 2 - x**3 / 6) / (E * I)


@module("cantilever_tip")
def verify_cantilever_tip():
    rec, check = make_checker()
    p = PARAMS
    delta = tip_deflection(p["P"], p["L"], p["E"], p["I"])

    # 1 解析 vs 数值：对弯矩方程 EI·y'' = P(L − x) 做两次数值积分
    def curvature(x):
        return p["P"] * (p["L"] - x) / (p["E"] * p["I"])
    slope = lambda s: integrate.quad(curvature, 0, s)[0]  # noqa: E731
    delta_num = integrate.quad(slope, 0, p["L"])[0]
    check("analytic_vs_numeric_double_integral", rel(delta, delta_num) < 1e-6, f"rel={rel(delta, delta_num):.2e}")

    # 2 结构性质：对 P 线性、对 L 三次齐次
    check("structural_linear_in_P", rel(tip_deflection(2 * p["P"], p["L"], p["E"], p["I"]), 2 * delta) < 1e-12)
    check("structural_cubic_in_L", rel(tip_deflection(p["P"], 2 * p["L"], p["E"], p["I"]), 8 * delta) < 1e-12)

    # 3 ★ 外部锚点（3b 独立第二推导）：单位载荷法 δ = ∫ M·m/(EI) dx，M = P(L−x)，m = (L−x)
    delta_unit = integrate.quad(lambda x: p["P"] * (p["L"] - x) ** 2 / (p["E"] * p["I"]), 0, p["L"])[0]
    check("external_anchor_unit_load", rel(delta, delta_unit) < 1e-6, f"rel={rel(delta, delta_unit):.2e}")
    #   挠曲线在 x = L 处应与端部挠度一致（推导内部自洽，非独立锚点，归入结构性质）
    check("structural_curve_at_tip", rel(deflection_curve(p["L"], p["P"], p["L"], p["E"], p["I"]), delta) < 1e-12)

    # 4 ★ 标准库实跑：EI·y'' = P(L−x) 写成一阶系统，用 scipy 做初值积分（y(0) = y'(0) = 0）
    sol = integrate.solve_ivp(lambda x, y: [y[1], p["P"] * (p["L"] - x) / (p["E"] * p["I"])],
                              (0, p["L"]), [0.0, 0.0], rtol=1e-12, atol=1e-15)
    check("library_xcheck_solve_ivp", rel(sol.y[0, -1], delta) < 1e-6, f"rel={rel(sol.y[0, -1], delta):.2e}")

    # 5 随机采样：参数空间随机抽样，逐点对外部锚点（数值积分）
    worst = 0.0
    for _ in range(50):
        P_, L_ = rng.uniform(10, 1000), rng.uniform(0.1, 2.0)
        num = integrate.quad(lambda s: integrate.quad(lambda x: P_ * (L_ - x) / (p["E"] * p["I"]), 0, s)[0], 0, L_)[0]
        worst = max(worst, rel(tip_deflection(P_, L_, p["E"], p["I"]), num))
    check("random_sampling_param_space", worst < 1e-6, f"worst rel={worst:.2e}, n=50")

    return make_verdict("cantilever_tip", "3b_second_derivation", rec,
                        key_values={"delta_m": f"{delta:.6e}"}, tolerance="rel < 1e-6")


# ② 接缝四查（多模块时填写；单模块可留空）
def seam_checks(verdicts):
    rec, check = make_checker()
    # 1 共享参数同一性：各模块所用共享量 == PARAMS 中唯一值
    # 2 约定一致性：正负号 / 参考系 / 参数化跨模块一致
    # 3 量纲链：上游出口单位 == 下游入口单位
    # 4 ★ 合成 = 独立整算：装配模型算例输出 == 独立整模型计算
    return rec


# 系统级判据（作用在装配后的整模型；单模块任务可留空）
def system_checks():
    rec, check = make_checker()
    return rec


def main(out_dir="."):
    os.makedirs(out_dir, exist_ok=True)
    verdicts = {}
    print("== 模块独立验证 ==")
    for name, fn in MODULES.items():
        print(f"  [{name}]")
        verdicts[name] = fn()
        with open(os.path.join(out_dir, f"{name}_verdict.json"), "w", encoding="utf-8") as f:
            json.dump(verdicts[name], f, ensure_ascii=False, indent=2)
    blocked = [k for k, v in verdicts.items() if v["status"] != "PASS"]
    if blocked:
        print(f"\n模块未通过：{blocked} → 修对应模块后重跑，不进合并。")
    print("\n== 接缝四查 ==")
    seam = seam_checks({k: v for k, v in verdicts.items() if v["status"] == "PASS"})
    print("\n== 系统级验证 ==")
    sysrec = system_checks()
    ok = bool(verdicts) and not blocked and not seam["fail"] and not sysrec["fail"]
    matrix = {"modules": {k: v["status"] for k, v in verdicts.items()},
              "seam_failed": seam["fail"], "system_failed": sysrec["fail"],
              "overall": "PASS" if ok else "FAIL", "seed": SEED}
    print("\n== PASS/FAIL 矩阵 ==")
    print(json.dumps(matrix, ensure_ascii=False, indent=2))
    with open(os.path.join(out_dir, "system_verdict.json"), "w", encoding="utf-8") as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)
    if not ok:
        print("→ 按失败回退路径处理（references/workflow.md）。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
