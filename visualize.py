"""
Animated visualization (matplotlib) for the Maze with Keys and Doors problem.

Colours : white = open, black = wall, green = start, red = exit,
          each key/door pair has its own colour.
Animation: path trail is highlighted, keys disappear when picked up and the
           inventory panel updates, doors turn white with an "unlocked" padlock.
"""
import matplotlib

from maze_solver import DOOR_BIT, KEYS

PAIR_COLORS = {      # none of these clash with white/black/green/red
    "a": "#1f77b4",  # blue
    "b": "#ff7f0e",  # orange
    "c": "#9467bd",  # purple
    "d": "#17becf",  # cyan
    "e": "#8c564b",  # brown
    "f": "#e377c2",  # pink
}
TRAIL = "#ffe066"
START_C, EXIT_C = "#2ca02c", "#d62728"


def _frames(grid, path):
    """Pre-compute (position, inventory, picked key cells, opened door cells) per step."""
    frames, inv, picked, opened = [], set(), set(), set()
    for i, (r, c) in enumerate(path):
        ch = grid[r][c]
        if ch in PAIR_COLORS:
            inv.add(ch)
            picked.add((r, c))
        elif ch in DOOR_BIT:
            opened.add((r, c))
        frames.append(((r, c), set(inv), set(picked), set(opened), i))
    return frames


def animate(grid, path, gif=None, png=None, show=True, interval=350):
    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.patches import Rectangle, Circle, Arc

    n = len(grid)
    letters = [k for k in KEYS if any(k in row for row in grid)]
    frames = _frames(grid, path)
    total = len(path) - 1
    fig, (ax, side) = plt.subplots(1, 2, figsize=(9.5, 7),
                                   gridspec_kw={"width_ratios": [5, 1.4]})

    def draw(k):
        (pos, inv, picked, opened, step) = frames[min(k, len(frames) - 1)]
        ax.clear()
        side.clear()
        ax.set_xlim(0, n)
        ax.set_ylim(n, 0)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        trail = set(path[: step + 1])
        for r in range(n):
            for c in range(n):
                ch = grid[r][c]
                face = "white"
                if ch == "#":
                    face = "black"
                elif ch == "S":
                    face = START_C
                elif ch == "E":
                    face = EXIT_C
                elif (r, c) in trail:
                    face = TRAIL
                ax.add_patch(Rectangle((c, r), 1, 1, facecolor=face, edgecolor="#cccccc", lw=0.5))
                cx, cy = c + 0.5, r + 0.5
                fs = max(6, 150 / n)
                if ch in "SE":
                    ax.text(cx, cy, ch, ha="center", va="center", color="white",
                            fontsize=fs, fontweight="bold")
                elif ch in PAIR_COLORS and (r, c) not in picked:        # key still on floor
                    ax.add_patch(Circle((cx, cy), 0.32, facecolor=PAIR_COLORS[ch], edgecolor="black", lw=0.8))
                    ax.text(cx, cy, ch, ha="center", va="center", color="white",
                            fontsize=fs, fontweight="bold")
                elif ch in DOOR_BIT:                                       # door
                    col = PAIR_COLORS[KEYS[DOOR_BIT[ch]]]
                    if (r, c) in opened:                                  # unlocked: white + open padlock
                        ax.add_patch(Rectangle((c + 0.06, r + 0.06), 0.88, 0.88, facecolor="white",
                                               edgecolor=col, lw=2, linestyle="--"))
                        # small OPEN padlock in the upper-right corner (stays visible under the player)
                        ax.add_patch(Rectangle((c + 0.62, r + 0.30), 0.26, 0.24, facecolor=col,
                                               edgecolor="black", lw=0.7, zorder=7))
                        ax.add_patch(Arc((c + 0.75, r + 0.22), 0.14, 0.2, theta1=180, theta2=360,
                                         color="black", lw=1.6, zorder=7))
                    else:
                        ax.add_patch(Rectangle((c + 0.06, r + 0.06), 0.88, 0.88, facecolor=col,
                                               edgecolor="black", lw=1))
                        ax.text(cx, cy, ch, ha="center", va="center", color="white",
                                fontsize=fs, fontweight="bold")
        ys = [p[0] + 0.5 for p in path[: step + 1]]
        xs = [p[1] + 0.5 for p in path[: step + 1]]
        ax.plot(xs, ys, color="#ff8c00", lw=2.2, alpha=0.9, zorder=5)
        ax.add_patch(Circle((pos[1] + 0.42, pos[0] + 0.55), 0.2, facecolor="white",
                            edgecolor="black", lw=2.5, zorder=6))
        ax.set_title(f"Maze with Keys & Doors - step {step} / {total}", fontsize=12)

        # inventory panel
        side.set_xlim(0, 3.2)
        side.set_ylim(max(len(letters), 1) + 1.0, 0)
        side.axis("off")
        side.text(1.6, 0.4, "Key inventory", ha="center", va="center", fontsize=11, fontweight="bold")
        for i, ch in enumerate(letters):
            y = i + 1.3
            held = ch in inv
            side.add_patch(Circle((0.6, y), 0.3, facecolor=PAIR_COLORS[ch] if held else "white",
                                  edgecolor=PAIR_COLORS[ch], lw=2, linestyle="-" if held else "--"))
            side.text(0.6, y, ch, ha="center", va="center", fontsize=11, fontweight="bold",
                      color="white" if held else PAIR_COLORS[ch])
            side.text(1.15, y, "collected" if held else "missing", va="center", fontsize=9,
                      color="black" if held else "#888888")
        side.set_aspect("equal")

    hold = 6                                    # extra frames at the end so the result stays visible
    count = len(frames) + hold
    ani = None
    if gif or show:
        ani = FuncAnimation(fig, draw, frames=count, interval=interval, repeat=False)
    if gif:
        ani.save(gif, writer=PillowWriter(fps=max(1, round(1000 / interval))))
    if png:
        draw(len(frames) - 1)
        fig.savefig(png, dpi=140, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    return ani
