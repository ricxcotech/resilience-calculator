#!/usr/bin/env python3
"""Runs fixed cases through the JS model (index.html) and Resilience's Python projection(); they must match."""
import json, os, re, subprocess, sys, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/Users/patrickmugazambi/Claude/Projects/Resilience/scripts")
sys.dont_write_bytecode = True
import report as r

html = open(os.path.join(HERE, "..", "index.html")).read()
model = re.search(r"// ===== MODEL-START.*?// ===== MODEL-END =====", html, re.S).group(0)
CASES = [  # nPri nFull nHalf opening payout wBefore wAfter
    (7, 8, 28, 323820, 250000, 2500, 3500), (7, 8, 28, 323820, 200000, 2500, 3500),
    (7, 8, 28, 323820, 250000, 2500, 3000), (6, 39, 0, 217580, 220000, 2500, 3000),
    (6, 20, 19, 217580, 200000, 3000, 3600), (6, 4, 19, 217580, 200000, 3000, 3600),
    (0, 10, 5, 0, 150000, 2000, 2500), (3, 0, 0, 50000, 250000, 2500, 3500),
    (7, 8, 28, 323820, 130000, 4000, 5600), (1, 1, 1, 100000, 250000, 5000, 7000),
]
RUNS = 400
js = model + f"""
const cases={json.dumps(CASES)};
console.log(JSON.stringify(cases.map(c=>{{const p=projection({{nPri:c[0],nFull:c[1],nHalf:c[2],opening:c[3],payout:c[4],wBefore:c[5],wAfter:c[6]}},{RUNS});
 const cd=cadence(p,true);return {{t:p.weeks[true],f:p.weeks[false],gap:cd.gap}};}})));"""
out = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)

base = copy.deepcopy(r.RULES["slots"])
print(f"{'case (pri/full/half, payout, wk before/after)':50} {'JS end wk':>9} {'Py end wk':>9}  result")
bad = 0
for c, j in zip(CASES, out):
    npri, nf, nh, op, pay, wb, wa = c
    r.RULES["slots"] = copy.deepcopy(base)
    r.RULES["slots"]["full"].update(weekly=wb, weekly_after=wa)
    r.RULES["slots"]["half"].update(weekly=wb / 2, weekly_after=wa / 2)
    p = r.projection(npri, nf, nh, op, runs=RUNS, payout=pay)
    ok = p["weeks"][True] == j["t"] and p["weeks"][False] == j["f"]
    g = r.cadence(p)[0]
    ok = ok and (g is None or abs(g - j["gap"]) < 1e-9)
    bad += not ok
    print(f"{f'{npri}/{nf}/{nh}, R{pay:,}, R{wb:,}/R{wa:,}':50} {j['t'][-1]:>9} {p['weeks'][True][-1]:>9}  {'IDENTICAL' if ok else 'MISMATCH'}")
print("ALL IDENTICAL (every purchase week, with and without reserve)" if not bad else f"{bad} MISMATCHES")
sys.exit(bool(bad))
