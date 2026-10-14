import csv
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark import astar, naive_cell_bfs
from maze_solver import (DOORS, KEYS, generate, load_grid_csv, mark_path, solve, validate,
                         write_csv)


def parse(text):
    return [list(row) for row in text.strip().split("\n")]


class SolverCases(unittest.TestCase):
    def test_start_adjacent_to_exit(self):
        g = parse("SE###\n#####\n#####\n#####\n#####")
        self.assertEqual(solve(g)[0], 1)

    def test_no_keys_plain_maze(self):
        g = parse("S.#..\n#.#.#\n..#..\n.##.#\n...#E")
        self.assertEqual(solve(g)[0], -1)          # E is walled off
        g = parse("S....\n####.\n.....\n.####\n....E")
        self.assertEqual(solve(g)[0], 16)

    def test_door_without_key_is_blocked(self):
        g = parse("#####\n#####\n..SAE\n#####\n#####")
        self.assertEqual(solve(g)[0], -1)

    def test_key_behind_its_own_door(self):
        g = parse("#####\n#####\nSAa.E\n#####\n#####")
        self.assertEqual(solve(g)[0], -1)

    def test_must_revisit_cells_to_fetch_key(self):
        g = parse("#####\n#####\na.SAE\n#####\n#####")
        length, path = solve(g)
        self.assertEqual(length, 6)
        self.assertEqual(len(path), 7)
        self.assertGreater(len(path), len(set(path)))   # S is visited twice

    def test_chain_of_keys(self):
        g = parse("######\n######\nSaAbBE\n######\n######\n######")
        self.assertEqual(solve(g)[0], 5)

    def test_wrong_order_of_keys_blocked(self):
        g = parse("######\n######\nSAaBbE\n######\n######\n######")
        self.assertEqual(solve(g)[0], -1)

    def test_extra_keys_and_duplicate_keys(self):
        g = parse("#####\n#####\nSaaAE\n#####\n#####")
        self.assertEqual(solve(g)[0], 4)

    def test_key_shortcut_beats_detour(self):
        # fetch key (1 step), come back, cross door A: 6 steps  <  12-step walk around
        g = parse("S.A.E\na###.\n.###.\n.###.\n.....")
        self.assertEqual(solve(g)[0], 6)

    def test_detour_beats_fetching_far_key(self):
        # the key is on the detour itself, so the 12-step open route wins
        g = parse("S.A.E\n.###.\n.###.\n.###.\n..a..")
        self.assertEqual(solve(g)[0], 12)

    def test_same_cell_different_masks_needed(self):
        # corridor cell next to the key is passed twice: once without, once with the key
        g = parse("#####\n#a###\n#.###\nS.AE#\n#####")
        self.assertEqual(solve(g)[0], 7)
        self.assertEqual(naive_cell_bfs(g), -1)         # cell-only BFS wrongly says "impossible"

    def test_e_is_exit_and_key_e_opens_G(self):
        g = parse("#######\n#######\nSeGE###\n#######\n#######\n#######\n#######")
        self.assertEqual(solve(g)[0], 3)
        g = parse("#######\n#######\nSGeE###\n#######\n#######\n#######\n#######")
        self.assertEqual(solve(g)[0], -1)

    def test_all_six_types(self):
        row = "S" + "".join(k + d for k, d in zip(KEYS, DOORS)) + "E"
        n = len(row)
        g = [["#"] * n for _ in range(n)]
        g[0] = list(row)
        self.assertEqual(solve(g)[0], n - 1)


class Validation(unittest.TestCase):
    def test_rejects_bad_grids(self):
        with self.assertRaises(ValueError):
            validate(parse("S.\n.E."))                              # not square
        with self.assertRaises(ValueError):
            validate(parse("S.\n.."))                              # no E
        with self.assertRaises(ValueError):
            validate(parse("SE\nE."))                              # two E
        with self.assertRaises(ValueError):
            validate(parse("S?\n.E"))                              # bad char
        with self.assertRaises(ValueError):
            validate(parse("SE\n.."), 7)                           # T out of range

    def test_warning_for_letters_beyond_T(self):
        g = parse("#####\n#####\nSbBE.\n#####\n#####")
        self.assertTrue(validate(g, 1))
        self.assertFalse(validate(g, 2))


class OutputCsv(unittest.TestCase):
    def test_path_marking_keeps_keys_and_doors_identifiable(self):
        g = parse("#####\n#####\na.SAE\n#####\n#####")
        length, path = solve(g)
        out = mark_path(g, path)
        self.assertEqual(out[2], ["xa", "x", "S", "xA", "E"])
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "o.csv")
            write_csv(out, p)
            with open(p, newline="") as f:
                self.assertEqual(list(csv.reader(f))[2], ["xa", "x", "S", "xA", "E"])

    def test_csv_roundtrip(self):
        g = parse("S.a#\n.#A.\n#..E\n....")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.csv")
            write_csv(g, p)
            self.assertEqual(load_grid_csv(p), g)


class Generator(unittest.TestCase):
    def test_generated_mazes_are_valid_and_solvable(self):
        for n, T in [(3, 1), (4, 2), (6, 3), (10, 4), (15, 5), (20, 6), (30, 6)]:
            for seed in range(5):
                g = generate(n, T, seed=seed)
                validate(g, T)
                flat = [ch for row in g for ch in row]
                for i in range(T):
                    self.assertEqual(flat.count(KEYS[i]), 1)
                    self.assertEqual(flat.count(DOORS[i]), 1)
                self.assertEqual(sum(ch in KEYS[T:] + DOORS[T:] for ch in flat), 0)
                self.assertNotEqual(solve(g)[0], -1, (n, T, seed))

    def test_too_small_grid_rejected(self):
        with self.assertRaises(ValueError):
            generate(2, 3)

    def test_same_seed_same_maze(self):
        self.assertEqual(generate(10, 3, seed=5), generate(10, 3, seed=5))


class CrossCheck(unittest.TestCase):
    def test_bfs_equals_dijkstra_and_astar_on_random_grids(self):
        rng = random.Random(2026)
        symbols = list("." * 10 + "#" * 4) + list(KEYS) + list(DOORS)
        for _ in range(300):
            n = rng.randint(2, 8)
            g = [[rng.choice(symbols) for _ in range(n)] for _ in range(n)]
            cells = [(r, c) for r in range(n) for c in range(n)]
            s, e = rng.sample(cells, 2)
            g[s[0]][s[1]], g[e[0]][e[1]] = "S", "E"
            a = solve(g)[0]
            self.assertEqual(a, astar(g, False)[0])
            self.assertEqual(a, astar(g, True)[0])

    def test_returned_path_is_a_legal_walk_of_that_length(self):
        for seed in range(20):
            g = generate(12, 4, seed=seed)
            length, path = solve(g)
            self.assertEqual(len(path) - 1, length)
            held = set()
            for (r0, c0), (r1, c1) in zip(path, path[1:]):
                self.assertEqual(abs(r0 - r1) + abs(c0 - c1), 1)
                ch = g[r1][c1]
                self.assertNotEqual(ch, "#")
                if ch in DOORS:
                    self.assertIn(KEYS[DOORS.index(ch)], held)
                if ch in KEYS:
                    held.add(ch)


if __name__ == "__main__":
    unittest.main()
