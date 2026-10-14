import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/**
 * Problem 1 - Maze with Keys and Doors (Java implementation, BFS on (row, col, keyMask)).
 *
 * Build/run:   javac MazeSolver.java
 *              echo 3 | java MazeSolver maze.csv solution_java.csv
 * Stdin line 1 = T. Arg 1 = input CSV. Arg 2 (optional) = output CSV with the path marked.
 * stdout = the shortest length (or -1).
 *
 * 'E' is ALWAYS the exit. Key types: a/A b/B c/C d/D f/F and (6th) e/G.
 */
public class MazeSolver {
    static final String KEYS = "abcdfe";   // index = bit number
    static final String DOORS = "ABCDFG";  // DOORS[i] is opened by KEYS[i]
    static final int MASKS = 1 << KEYS.length();
    static final int[] DR = {-1, 1, 0, 0};
    static final int[] DC = {0, 0, -1, 1};

    static String[][] readGrid(String file) throws IOException {
        List<String[]> rows = new ArrayList<>();
        for (String line : Files.readAllLines(Paths.get(file), StandardCharsets.UTF_8)) {
            if (line.startsWith("\uFEFF")) line = line.substring(1);
            if (line.trim().isEmpty()) continue;
            String[] cells = line.split(",", -1);
            for (int i = 0; i < cells.length; i++) cells[i] = cells[i].trim();
            rows.add(cells);
        }
        return rows.toArray(new String[0][]);
    }

    static void validate(String[][] g, int T) {
        int n = g.length;
        if (n == 0) throw new IllegalArgumentException("grid is empty");
        int s = 0, e = 0;
        String allowed = ".#SE" + KEYS + DOORS;
        for (int r = 0; r < n; r++) {
            if (g[r].length != n)
                throw new IllegalArgumentException("grid must be N x N (row " + (r + 1) + ")");
            for (int c = 0; c < n; c++) {
                String ch = g[r][c];
                if (ch.length() != 1 || allowed.indexOf(ch.charAt(0)) < 0)
                    throw new IllegalArgumentException("invalid cell '" + ch + "' at row " + (r + 1) + ", col " + (c + 1));
                if (ch.equals("S")) s++;
                if (ch.equals("E")) e++;
            }
        }
        if (s != 1) throw new IllegalArgumentException("need exactly one S, found " + s);
        if (e != 1) throw new IllegalArgumentException("need exactly one E, found " + e);
        if (T < 1 || T > 6) throw new IllegalArgumentException("T must be 1..6");
    }

    /** Returns the path as a list of {row, col}, or null when E is unreachable. */
    static List<int[]> solve(String[][] g) {
        int n = g.length, sr = -1, sc = -1, er = -1, ec = -1;
        for (int r = 0; r < n; r++)
            for (int c = 0; c < n; c++) {
                if (g[r][c].equals("S")) { sr = r; sc = c; }
                if (g[r][c].equals("E")) { er = r; ec = c; }
            }
        int total = n * n * MASKS;
        int[] parent = new int[total];
        Arrays.fill(parent, -2);                 // -2 = unvisited, -1 = root
        int[] queue = new int[total];            // each state is enqueued at most once
        int head = 0, tail = 0;
        int start = (sr * n + sc) * MASKS;
        parent[start] = -1;
        queue[tail++] = start;
        while (head < tail) {
            int cur = queue[head++];
            int mask = cur % MASKS, cell = cur / MASKS, r = cell / n, c = cell % n;
            if (r == er && c == ec) {
                LinkedList<int[]> path = new LinkedList<>();
                for (int x = cur; x != -1; x = parent[x]) {
                    int cl = x / MASKS;
                    path.addFirst(new int[]{cl / n, cl % n});
                }
                return path;
            }
            for (int d = 0; d < 4; d++) {
                int nr = r + DR[d], nc = c + DC[d];
                if (nr < 0 || nc < 0 || nr >= n || nc >= n) continue;
                char ch = g[nr][nc].charAt(0);
                if (ch == '#') continue;
                int nm = mask;
                int di = DOORS.indexOf(ch), ki = KEYS.indexOf(ch);
                if (di >= 0 && ((mask >> di) & 1) == 0) continue;   // door without key
                if (ki >= 0) nm |= 1 << ki;                          // auto pick-up
                int ni = (nr * n + nc) * MASKS + nm;
                if (parent[ni] != -2) continue;
                parent[ni] = cur;
                queue[tail++] = ni;
            }
        }
        return null;
    }

    static void writeMarked(String[][] g, List<int[]> path, String file) throws IOException {
        String[][] out = new String[g.length][];
        for (int r = 0; r < g.length; r++) out[r] = g[r].clone();
        for (int[] p : path) {
            String ch = g[p[0]][p[1]];
            if (ch.equals(".")) out[p[0]][p[1]] = "x";
            else if (KEYS.indexOf(ch.charAt(0)) >= 0 || DOORS.indexOf(ch.charAt(0)) >= 0)
                out[p[0]][p[1]] = "x" + ch;
        }
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(Paths.get(file), StandardCharsets.UTF_8))) {
            for (String[] row : out) w.print(String.join(",", row) + "\n");
        }
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.err.println("usage: echo T | java MazeSolver <maze.csv> [solution.csv]");
            System.exit(1);
        }
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        String line = in.readLine();
        if (line == null) { System.err.println("error: T missing on stdin"); System.exit(1); }
        int T = Integer.parseInt(line.trim());
        String[][] g = readGrid(args[0]);
        try {
            validate(g, T);
        } catch (IllegalArgumentException ex) {
            System.err.println("error: " + ex.getMessage());
            System.exit(1);
        }
        List<int[]> path = solve(g);
        if (path == null) {
            System.out.println(-1);
            System.err.println("no path exists; no solution CSV written");
        } else {
            System.out.println(path.size() - 1);
            if (args.length > 1) writeMarked(g, path, args[1]);
        }
    }
}
