"""
Cross-check: Java MazeSolver vs Python solver on random mazes (needs Java 11+).
Run from the repo root:  python tests/cross_check_java.py
"""
import os
import random
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from maze_solver import DOORS, KEYS, generate, mark_path, solve, write_csv

rng = random.Random(99)
symbols = list("." * 10 + "#" * 4) + list(KEYS) + list(DOORS)
tmp = tempfile.mkdtemp()
mismatch = solvable = 0
N = 40
for i in range(N):
    if i % 2 == 0:
        g = generate(rng.randint(5, 25), rng.randint(1, 6), seed=i)
    else:                                   # fully random grid (often unsolvable)
        n = rng.randint(2, 9)
        g = [[rng.choice(symbols) for _ in range(n)] for _ in range(n)]
        s, e = rng.sample([(r, c) for r in range(n) for c in range(n)], 2)
        g[s[0]][s[1]], g[e[0]][e[1]] = "S", "E"
    csv_in, csv_out = os.path.join(tmp, f"m{i}.csv"), os.path.join(tmp, f"j{i}.csv")
    write_csv(g, csv_in)
    length, path = solve(g)
    run = subprocess.run(["java", os.path.join(ROOT, "MazeSolver.java"), csv_in, csv_out],
                         input="6\n", capture_output=True, text=True)
    if int(run.stdout.strip()) != length:
        mismatch += 1
        print("MISMATCH", i, length, run.stdout.strip(), run.stderr)
    elif length != -1:
        solvable += 1
        py_rows = [",".join(r) for r in mark_path(g, path)]
        assert py_rows == open(csv_out).read().split("\n")[:-1], f"CSV differs on maze {i}"
print(f"{N} mazes ({solvable} solvable): {mismatch} length mismatches, CSVs identical")
sys.exit(1 if mismatch else 0)
