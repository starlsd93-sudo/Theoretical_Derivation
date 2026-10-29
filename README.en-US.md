[简体中文](README.md) | **English**

# theoretical-derivation

A Claude Skill that makes Claude's **theoretical derivations and modeling** both correct and actually verified.

When an LLM derives something, the usual failure is not that it can't solve the problem. It silently assumes a symmetry you never stated, drops a term it "knows" will vanish, states a count without saying why, treats a closed-form result as valid everywhere, or hides a sign error inside an otherwise self-consistent derivation. This skill turns each of those failures into a mandatory step, and backs them up with **multi-party verification**:

- **Modeling rigor**: structural assumptions are fixed by the human (P1), full general solution before applying conditions (P2), every count and choice is justified (P3), validity-domain review (P4), plus a four-question gate at the end.
- **Multi-party verification**: two independent derivation paths compared → five numerical criteria (including a mandatory **independent external anchor** and a mandatory **standard-library cross-check**) → independent recomputation in another session or by another model in strict mode.

The skill text is written in Chinese; Claude reads it fine and will answer in your language.

---

## Install

1. Download **[`theoretical-derivation_v1.0_20261029.skill`](theoretical-derivation_v1.0_20261029.skill)**
2. Upload it in your Claude client (**Settings → Capabilities → Skills**)

A `.skill` file is a ZIP. If your client can't upload it, copy the `theoretical-derivation/` folder into `~/.claude/skills/` and restart Claude Code.

R4 verification scripts need Python 3 with `numpy` and `scipy` (plus `sympy` etc. as the task requires).

---

## Workflow

```
R0 formulate ─N0─► R1 independent derivation ──┐
                                               ├─► R3 compare & select ─N3─► R3.5 freeze params ─► R4 numerical verification ─N4─► R5 handover package
                   R2 literature-based derivation ┘
```

| Stage | What | Key constraint |
|:--|:--|:--|
| R0 | Reduce the problem to math, lock conventions, plan decomposition and verification criteria | Ask about missing structural assumptions; never default them |
| R1 | Derive without looking at literature | Full general solution, justify every count, four self-checks |
| R2 | Derive against textbooks/papers, strengthen R1 | Every citation traceable; no fabrication |
| R3 | Compare both paths and select | Validity domain: premises / failure conditions / generalization path |
| R3.5 | Freeze all numerical parameters | Shared across all parties |
| R4 | Full numerical verification | Five criteria + four-question gate |
| R5 | Package results in a structured handover | Package only; no new derivation |

N0, N3 and N4 are mandatory human review points.

### Five R4 criteria

1. Analytic vs numeric agreement
2. Structural properties (symmetry, definiteness, homogeneity, conservation, units)
3. ★ **Independent external anchor**: known closed form / independent second derivation / analytically solvable special case (mandatory)
4. ★ **Standard-library cross-check** with numpy/scipy/sympy/OpenCV etc. (mandatory)
5. Random sampling (Monte Carlo or parameter-space sweep)

`templates/verify_harness.py` ships with a runnable example (cantilever tip deflection, using the unit-load method as the independent anchor).

---

## Modes

| Mode | Flow | Use for |
|:--|:--|:--|
| **Lite** | R0 → R1 → reduced R4 (criteria 1–3) | Exploratory or short derivations |
| **Standard** (default) | Full R0→R5 | Formal modeling |
| **Strict** | Standard + cross-session / cross-model recomputation | Core results, anything published or used for design decisions |
| **Review** | Run the rules and criteria on an existing derivation, output an issue list | Reviewing someone's (or your own) derivation |

Execution environments are orthogonal to modes: **A** an environment with local Python (Claude Code; primary and final arbiter), **B** web chat (literature cross-checking), **C** an external AI (the skill generates a self-contained delegation prompt for an independent second opinion).

---

## Quick start

In Claude Code:

```
Use the theoretical-derivation skill on this problem.
Working root: D:\my-project
Problem: axial equivalent stiffness of n offset parallel elastic rods connecting two rigid plates.
```

Claude first completes R0, asks you about any structural element you didn't specify, then recommends a mode.

To review an existing derivation:

```
Use theoretical-derivation in review mode on D:\my-project\inputs\derivation.md
```

More prompts in `references/prompts.md`.

## License

[Apache-2.0](LICENSE)
