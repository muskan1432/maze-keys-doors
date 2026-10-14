"""
Comparative analysis: BFS vs Dijkstra vs A* (all on the (r, c, mask) state space)
plus the classic WRONG approach (visited by cell only) to show why the mask matters.
Run:  python benchmark.py
"""
import heapq
import random
import time
from collections import deque

from maze_solver import DIRS, DOORS, DOOR_BIT, KEY_BIT, KEYS, MASKS, find, generate, solve


def astar(grid, use_heuristic=True):
    """A* (use_heuristic=False is exactly Dijkstra). Returns (length, expanded)."""
    n = len(grid)
    sr, sc = find(grid, "S")
    er, ec = find(grid, "E")
    h = (lambda r, c: abs(r - er) + abs(c - ec)) if use_heuristic else (lambda r, c: 0)
    best = {(sr, sc, 0): 0}
    heap = [(h(sr, sc), 0, sr, sc, 0)]
    expanded = 0
    while heap:
        f, g, r, c, m = heapq.heappop(heap)
        if best.get((r, c, m), 1 << 60) < g:
            continue
        expanded += 1
        if (r, c) == (er, ec):
            return g, expanded
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < n and 0 <= nc < n) or grid[nr][nc] == "#":
                continue
            ch, nm = grid[nr][nc], m
            if ch in DOOR_BIT and not (m >> DOOR_BIT[ch]) & 1:
                continue
            if ch in KEY_BIT:
                nm |= 1 << KEY_BIT[ch]
            if best.get((nr, nc, nm), 1 << 60) > g + 1:
                best[(nr, nc, nm)] = g + 1
                heapq.heappush(heap, (g + 1 + h(nr, nc), g + 1, nr, nc, nm))
    return -1, expanded


def naive_cell_bfs(grid):
    """WRONG on purpose: visited[r][c] ignores which keys we hold."""
    n = len(grid)
    s, e = find(grid, "S"), find(grid, "E")
    seen = {s}
    q = deque([(s, 0, 0)])
    while q:
        (r, c), d, m = q.popleft()
        if (r, c) == e:
            return d
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < n and 0 <= nc < n) or grid[nr][nc] == "#" or (nr, nc) in seen:
                continue
            ch, nm = grid[nr][nc], m
            if ch in DOOR_BIT and not (m >> DOOR_BIT[ch]) & 1:
                continue
            if ch in KEY_BIT:
                nm |= 1 << KEY_BIT[ch]
            seen.add((nr, nc))
            q.append(((nr, nc), d + 1, nm))
    return -1


def timed(fn, *a):
    t = time.perf_counter()
    out = fn(*a)
    return out, (time.perf_counter() - t) * 1000


if __name__ == "__main__":
    print(f"{'N':>4} {'T':>2} | {'answer':>6} | {'BFS exp / ms':>16} | {'Dijkstra exp / ms':>18} | {'A* exp / ms':>14} | naive(wrong)")
    wrong = 0
    for n, T in [(8, 2), (12, 3), (20, 4), (30, 5), (40, 6)]:
        for seed in range(3):
            g = generate(n, T, seed=seed)
            st = {}
            (ans, _), t_bfs = timed(solve, g, st)
            (d_ans, d_exp), t_d = timed(astar, g, False)
            (a_ans, a_exp), t_a = timed(astar, g, True)
            assert ans == d_ans == a_ans, (n, T, seed, ans, d_ans, a_ans)
            nv = naive_cell_bfs(g)
            wrong += nv != ans
            print(f"{n:>4} {T:>2} | {ans:>6} | {st['expanded']:>8}/{t_bfs:>6.1f} | {d_exp:>9}/{t_d:>7.1f} | {a_exp:>6}/{t_a:>6.1f} | {nv}{'  <-- WRONG' if nv != ans else ''}")
    print(f"\nBFS == Dijkstra == A* on every maze; naive visited[r][c] BFS was wrong on {wrong} of 15 mazes.")
