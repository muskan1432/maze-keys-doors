"""
Problem 1: Maze with Keys and Doors  (CSE Hackathon - DSA, CMRIT)

Core idea: BFS over the STATE (row, col, keyMask) instead of just (row, col).
keyMask is a T-bit integer (max 6 bits -> 64 masks); bit i set = key KEYS[i] held.

Usage examples
    echo 3 | python maze_solver.py --random 12 --seed 7 --viz
    echo 3 | python maze_solver.py --csv maze.csv --out solution.csv
    python maze_solver.py            # fully interactive (reads T and option from stdin)
"""
import argparse
import csv
import random
import sys
from collections import deque

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))   # up, down, left, right
# NOTE on the 'E' clash: the statement uses 'E' for the exit AND lists doors 'A'-'F'.
# We resolve it this way: 'E' is ALWAYS the exit. Key types are ordered so that
# T <= 5 uses only spec letters (a/A, b/B, c/C, d/D, f/F); the 6th type is the
# key 'e' which opens door 'G'.
KEYS = "abcdfe"                              # index in this string = bit number
DOORS = "ABCDFG"                             # DOORS[i] is opened by KEYS[i]
KEY_BIT = {k: i for i, k in enumerate(KEYS)}
DOOR_BIT = {d: i for i, d in enumerate(DOORS)}
MASKS = 1 << len(KEYS)                       # 64 states of the key inventory


# --------------------------------------------------------------------------- #
# Input / validation
# --------------------------------------------------------------------------- #
def load_grid_csv(path):
    """Read an N x N grid from a CSV file (one cell per field)."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        grid = [[c.strip() for c in row] for row in csv.reader(f)
                if any(c.strip() for c in row)]
    return grid


def validate(grid, T=None):
    """Raise ValueError for an invalid maze; return a list of warnings."""
    warnings = []
    n = len(grid)
    if n == 0:
        raise ValueError("grid is empty")
    for i, row in enumerate(grid):
        if len(row) != n:
            raise ValueError(f"grid must be N x N: row {i + 1} has {len(row)} cells, expected {n}")
    allowed = set(".#SE" + KEYS + DOORS)
    starts = ends = 0
    for r in range(n):
        for c in range(n):
            ch = grid[r][c]
            if len(ch) != 1 or ch not in allowed:
                raise ValueError(f"invalid cell {ch!r} at row {r + 1}, col {c + 1}")
            starts += ch == "S"
            ends += ch == "E"
    if starts != 1:
        raise ValueError(f"grid must contain exactly one 'S' (found {starts})")
    if ends != 1:
        raise ValueError(f"grid must contain exactly one 'E' (found {ends})")
    if T is not None:
        if not 1 <= T <= 6:
            raise ValueError("T must be between 1 and 6")
        allowed_letters = set(KEYS[:T] + DOORS[:T])
        extra = {ch for row in grid for ch in row if ch in KEYS + DOORS} - allowed_letters
        if extra:
            warnings.append(f"grid contains letters {sorted(extra)} outside the first T={T} types")
    return warnings


# --------------------------------------------------------------------------- #
# Solver: BFS on (row, col, mask)
# --------------------------------------------------------------------------- #
def find(grid, target):
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == target:
                return r, c
    raise ValueError(f"{target!r} not found")


def solve(grid, stats=None):
    """
    Return (length, path). path is the list of (r, c) cells from S to E
    (inclusive, may revisit cells). Returns (-1, []) if E is unreachable.
    """
    n = len(grid)
    sr, sc = find(grid, "S")
    er, ec = find(grid, "E")
    size = n * n * MASKS
    dist = [-1] * size
    parent = [-1] * size

    def idx(r, c, m):
        return (r * n + c) * MASKS + m

    start = idx(sr, sc, 0)
    dist[start] = 0
    queue = deque([(sr, sc, 0)])
    expanded = 0
    while queue:
        r, c, m = queue.popleft()
        expanded += 1
        cur = idx(r, c, m)
        if (r, c) == (er, ec):           # BFS pops states in non-decreasing distance
            path = []
            while cur != -1:
                cell = cur // MASKS
                path.append((cell // n, cell % n))
                cur = parent[cur]
            path.reverse()
            if stats is not None:
                stats["expanded"] = expanded
            return dist[idx(r, c, m)], path
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < n and 0 <= nc < n):
                continue
            ch = grid[nr][nc]
            if ch == "#":
                continue
            nm = m
            if ch in DOORS:
                if not (m >> DOOR_BIT[ch]) & 1:           # door without its key
                    continue
            elif ch in KEYS:
                nm |= 1 << KEY_BIT[ch]                    # auto pick-up
            ni = idx(nr, nc, nm)
            if dist[ni] != -1:
                continue
            dist[ni] = dist[cur] + 1
            parent[ni] = cur
            queue.append((nr, nc, nm))
    if stats is not None:
        stats["expanded"] = expanded
    return -1, []


# --------------------------------------------------------------------------- #
# Output 2: CSV with the path marked
# --------------------------------------------------------------------------- #
def mark_path(grid, path):
    """
    Copy of the grid with the path marked:
      '.'      -> 'x'
      key 'a'  -> 'xa'  (path crosses/picks up key a)
      door 'A' -> 'xA'  (path passes through door A; key 'e' / door 'G' likewise)
      S and E  stay 'S' and 'E'
    """
    out = [row[:] for row in grid]
    for r, c in path:
        ch = grid[r][c]
        if ch == ".":
            out[r][c] = "x"
        elif ch in KEYS or ch in DOORS:
            out[r][c] = "x" + ch
    return out


def write_csv(grid, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator="\n").writerows(grid)


# --------------------------------------------------------------------------- #
# Option 2: random maze generator (always solvable)
# --------------------------------------------------------------------------- #
def _plain_path(grid, s, e):
    """Shortest path S->E treating doors/keys as open (only '#' blocks)."""
    n = len(grid)
    prev = {s: None}
    q = deque([s])
    while q:
        cur = q.popleft()
        if cur == e:
            path = []
            while cur is not None:
                path.append(cur)
                cur = prev[cur]
            return path[::-1]
        for dr, dc in DIRS:
            nxt = (cur[0] + dr, cur[1] + dc)
            if 0 <= nxt[0] < n and 0 <= nxt[1] < n and nxt not in prev and grid[nxt[0]][nxt[1]] != "#":
                prev[nxt] = cur
                q.append(nxt)
    return None


def generate(n, T, seed=None, wall_p=0.25, tries=400):
    """
    Random N x N maze with exactly T keys, T doors, one S, one E and at least
    one solution. Doors are preferably placed on the key-less shortest route so
    that the keys really matter; mazes whose optimal route actually passes through a
    door are preferred. Solvability is always verified with solve().
    """
    if not 1 <= T <= 6:
        raise ValueError("T must be between 1 and 6")
    if n * n < 2 * T + 2:
        raise ValueError(f"N={n} is too small for T={T}: need at least {2 * T + 2} cells")
    rng = random.Random(seed)
    cells = [(r, c) for r in range(n) for c in range(n)]
    fallback = middling = None
    for attempt in range(tries):
        p = wall_p * (1 - attempt / tries)      # walls thin out if we keep failing
        g = [["#" if rng.random() < p else "." for _ in range(n)] for _ in range(n)]
        s, e = rng.sample(cells, 2)
        g[s[0]][s[1]] = "S"
        g[e[0]][e[1]] = "E"
        plain = _plain_path(g, s, e)
        if plain is None:
            continue
        letters = list(range(T))
        rng.shuffle(letters)
        interior = plain[1:-1]
        on_path = rng.sample(interior, min(T, len(interior)))
        used = set()
        for (r, c) in on_path:                  # doors on the direct route
            g[r][c] = DOORS[letters.pop()]
            used.add((r, c))
        free = [(r, c) for (r, c) in cells if g[r][c] == "." and (r, c) not in used]
        need = len(letters) + T                 # leftover doors + all T keys
        if len(free) < need:
            continue
        spots = rng.sample(free, need)
        for i in letters:                       # leftover doors
            r, c = spots.pop()
            g[r][c] = DOORS[i]
        for i in range(T):                      # keys
            r, c = spots.pop()
            g[r][c] = KEYS[i]
        length, path = solve(g)
        if length == -1:
            continue
        if any(g[r][c] in DOOR_BIT for r, c in path):
            return g                            # best: optimal route really uses a door (and its key)
        if length > len(plain) - 1 and middling is None:
            middling = g                        # keys/doors at least change the answer
        if fallback is None:
            fallback = g
    if middling is not None:
        return middling
    if fallback is not None:
        return fallback
    raise ValueError("could not generate a solvable maze; try a larger N or another seed")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _read_line(prompt):
    sys.stderr.write(prompt)
    sys.stderr.flush()
    line = sys.stdin.readline()
    if not line:
        raise SystemExit("unexpected end of input")
    return line.strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Maze with Keys and Doors - shortest path")
    ap.add_argument("--csv", help="Option 1: read the N x N grid from this CSV file")
    ap.add_argument("--random", type=int, metavar="N", help="Option 2: generate a random N x N maze")
    ap.add_argument("--T", type=int, help="number of key/door types (default: read from stdin)")
    ap.add_argument("--seed", type=int, help="random seed for --random")
    ap.add_argument("--out", default="solution.csv", help="Output 2 CSV (default solution.csv)")
    ap.add_argument("--grid-out", default="maze.csv", help="where to save a generated maze")
    ap.add_argument("--viz", action="store_true", help="show the animated visualization")
    ap.add_argument("--gif", help="save the animation as a GIF (implies --viz)")
    ap.add_argument("--png", help="save the final frame as a PNG (implies --viz)")
    ap.add_argument("--no-show", action="store_true", help="do not open a window (headless)")
    ap.add_argument("--verbose", action="store_true", help="extra info on stderr")
    args = ap.parse_args(argv)

    T = args.T if args.T is not None else int(_read_line("T (1-6): "))
    if not 1 <= T <= 6:
        raise SystemExit("T must be between 1 and 6")

    if args.csv is None and args.random is None:
        opt = _read_line("Option (1 = CSV file, 2 = random): ")
        if opt == "1":
            args.csv = _read_line("CSV path: ")
        elif opt == "2":
            args.random = int(_read_line("N: "))
        else:
            raise SystemExit("option must be 1 or 2")

    try:
        if args.csv is not None:
            grid = load_grid_csv(args.csv)
        else:
            grid = generate(args.random, T, seed=args.seed)
            write_csv(grid, args.grid_out)
            sys.stderr.write(f"generated maze saved to {args.grid_out}\n")
        for w in validate(grid, T):
            sys.stderr.write("warning: " + w + "\n")
    except (ValueError, OSError) as exc:
        raise SystemExit(f"error: {exc}")

    stats = {}
    length, path = solve(grid, stats)
    print(length)                                # Output 1: only the integer on stdout
    if args.verbose:
        sys.stderr.write(f"states expanded: {stats['expanded']}\n")

    if length == -1:
        sys.stderr.write("no path exists; no solution CSV written\n")
    else:
        write_csv(mark_path(grid, path), args.out)
        sys.stderr.write(f"solution CSV written to {args.out}\n")

    if args.viz or args.gif or args.png:
        if length == -1:
            sys.stderr.write("nothing to animate (no path)\n")
        else:
            from visualize import animate
            animate(grid, path, gif=args.gif, png=args.png,
                    show=args.viz and not args.no_show)


if __name__ == "__main__":
    main()
