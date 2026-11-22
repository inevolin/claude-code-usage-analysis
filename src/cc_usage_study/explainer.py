"""Write the README's animated explainer: four screens a 15-year-old can follow.

    python -m cc_usage_study.explainer          # writes outputs/figures/explainer.svg

One short sentence per slide, huge text, one picture each. A slide timer along
the bottom fills one segment per slide.
  1. Claude saves your chat for a short time, so each new message is cheap:
     two equal cards, 1 hour on a plan and 5 minutes on an API key.
  2. Come back after the timer runs out, and your next message costs about 10x.
  3. Taking a break? Shrink the chat first (/compact).
  4. Back from a break? Start a new chat (/clear): the old chat's 9.8x price
     tag is crossed out next to a 1x new chat with a 3-line note.
  5. A short closing slide: found this useful? Star the repo on GitHub.

Every number is a measured README finding (see ``FACTS``). Plain CSS
animation, no script and no web fonts, so it plays inside a GitHub <img>.
Light and dark colors follow prefers-color-scheme. With reduced motion a
static summary of the two fixes shows instead.
"""

from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "figures" / "explainer.svg"

W, H = 1200, 675
LOOP = 26.5  # seconds: four content slides of 5.75 s, then a 3.5 s closing slide
FADE = 0.45
SCENES = [(0.0, 5.75), (5.75, 11.5), (11.5, 17.25), (17.25, 23.0), (23.0, 26.5)]

# Measured live, Opus 5.5, 5-minute cache, a chat of about 97,000 tokens.
# README "Cache expiry after a break" and "Compact before or after the break".
FACTS = {
    "warm": 1.5,  # back within 2 to 4 minutes, mean 1.51x, n=5
    "stale": 9.8,  # back after 6 to 13 minutes, mean 9.83x, n=5
    "compact_before": 2.5,  # /compact before the break, n=3
    "runs": 13,  # 3 new sessions + 5 warm + 5 stale
}

STYLE_COLORS = (
    ".bg{fill:#FAF9F5}.card{fill:#FFFFFF;stroke:#E8E6DC}.ink{fill:#141413}.muted{fill:#5E5D59}"
    ".acc{fill:#C2603F}.good{fill:#2F7A55}.warm{fill:#BFC9C2}.cold{fill:#D97757}.track{fill:#E8E6DC}"
    ".goodbar{fill:#3E9A6C}.seg{fill:#CFCCC1}.segfill{fill:#D97757}"
    "@media (prefers-color-scheme:dark){"
    ".bg{fill:#1F1E1D}.card{fill:#262624;stroke:#3D3929}.ink{fill:#F0EEE6}.muted{fill:#A6A39A}"
    ".acc{fill:#E8906F}.good{fill:#7FC29E}.warm{fill:#55605A}.cold{fill:#D97757}.track{fill:#353432}"
    ".goodbar{fill:#5DB487}.seg{fill:#4A4845}.segfill{fill:#E8906F}}"
)

FONT = "system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

ALT = (
    "Animated explainer in five slides, with a slide timer along the bottom. "
    "1. Claude saves your chat for a short time, so each new message is cheap: 1 hour on a Pro, Max or Ultra plan, "
    "5 minutes on an API key. Every message restarts the timer. "
    "2. Come back after the timer runs out, and your next message costs about 10x: new chat 1x, "
    f"back before the timer ends {FACTS['warm']}x, back after it ends {FACTS['stale']}x. Claude has to save the whole "
    f"chat again. Measured {FACTS['runs']} times on an API key. "
    f"3. Taking a break? Shrink the chat first. Type /compact. About {FACTS['compact_before']}x instead of 10x. "
    f"4. Back from a break? Start a new chat. Keeping going in the old chat costs {FACTS['stale']}x (crossed out). "
    "A new chat with a 3-line note (Goal, Done, Next) costs 1x. Type /clear, then write Goal, Done and Next. "
    "5. Found this useful? Star the repo on GitHub: github.com/inevolin/claude-code-usage-analysis."
)


def _pct(t: float) -> str:
    return f"{100.0 * t / LOOP:.3f}%"


class _Anim:
    """Collects @keyframes. Every animation runs on the shared loop, so the whole SVG loops cleanly."""

    def __init__(self) -> None:
        self.rules: list[str] = []

    def _add(self, prop_frames: list[tuple[float, str]], base: str, extra: str = "") -> str:
        name = f"a{len(self.rules)}"
        frames = "".join(f"{_pct(t)}{{{v}}}" for t, v in prop_frames)
        self.rules.append(
            f"@keyframes {name}{{{frames}}}.{name}{{{base}{extra}animation:{name} {LOOP}s linear infinite both}}"
        )
        return name

    def window(self, start: float, end: float, fade: float = FADE) -> str:
        """Fade in at ``start``, out by ``end`` (seconds into the loop)."""
        steps = [(0.0, 0)]
        if start > 0:
            steps.append((start, 0))
        steps += [(start + fade, 1), (end - fade, 1), (end, 0)]
        if end < LOOP:
            steps.append((LOOP, 0))
        return self._add([(t, f"opacity:{o}") for t, o in steps], "opacity:0;")

    def hide(self, start: float, end: float, fade: float = 0.2) -> str:
        """The inverse of ``window``: visible all loop except between ``start`` and ``end``."""
        steps = [(0.0, 1 if start > 0 else 0)]
        if start > 0:
            steps += [(start, 1), (start + fade, 0)]
        steps += [(end - fade, 0), (end, 1 if end < LOOP else 0)]
        if end < LOOP:
            steps.append((LOOP, 1))
        return self._add([(t, f"opacity:{o}") for t, o in steps], "")

    def move_x(self, points: list[tuple[float, float]]) -> str:
        frames = [(t, f"transform:translateX({x:.1f}px)") for t, x in points]
        return self._add(frames, f"transform:translateX({points[0][1]:.1f}px);")

    def grow_x(self, start: float, dur: float, end: float) -> str:
        """Scale a bar from 0 to full width between ``start`` and ``start + dur``, reset at ``end``."""
        frames = [(0.0, "transform:scaleX(0)"), (start, "transform:scaleX(0)"), (start + dur, "transform:scaleX(1)")]
        frames += [(end, "transform:scaleX(1)")]
        if end < LOOP:
            frames += [(end + 0.01, "transform:scaleX(0)"), (LOOP, "transform:scaleX(0)")]
        return self._add(frames, "transform:scaleX(0);transform-box:fill-box;transform-origin:0 50%;")


def _text(x, y, s, size, cls="ink", weight=400, anchor="start", extra=""):
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'class="{cls}"{extra}>{escape(s)}</text>'
    )


def _rich(x, y, parts, size, weight=400, anchor="start"):
    """One line of text with differently styled runs: parts = [(text, cls, weight, mono)]."""
    spans = []
    for s, cls, w, mono in parts:
        fam = f' font-family="{MONO}"' if mono else ""
        spans.append(f'<tspan class="{cls}" font-weight="{w}"{fam}>{escape(s)}</tspan>')
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'xml:space="preserve">{"".join(spans)}</text>'
    )


def _label(n: int, s: str) -> str:
    return _text(80, 78, f"{n} · {s.upper()}", 20, "acc", 700, extra=' letter-spacing="3"')


def _stepper(anim: _Anim) -> str:
    """Four labelled progress bars along the bottom. The current step fills and lights up."""
    out = []
    width, gap = 245, 20
    x0 = (W - 4 * width - 3 * gap) / 2
    for i, (name, (start, end)) in enumerate(zip(STEPS, SCENES)):
        x = x0 + i * (width + gap)
        out.append(f'<rect x="{x:.1f}" y="612" width="{width}" height="6" rx="3" class="track"/>')
        fill = anim.grow_x(start, end - start, end)
        out.append(f'<rect x="{x:.1f}" y="612" width="{width}" height="6" rx="3" class="cold {fill}"/>')
        off = anim.hide(start, end)
        out.append(f'<g class="{off}">' + _text(x, 646, f"{i + 1}  {name}", 18, "muted", 500) + "</g>")
        on = anim.window(start, end, 0.2)
        out.append(f'<g class="{on}">' + _text(x, 646, f"{i + 1}  {name}", 18, "ink", 700) + "</g>")
    return '<g class="stepper">' + "".join(out) + "</g>"


def _big(y, parts, size=64):
    return _rich(80, y, [(t, c, 800, False) for t, c in parts], size)


def _timer(anim: _Anim) -> str:
    """A slide timer like story apps: one segment per screen. The current one fills over its
    screen's time; finished ones stay full until the loop restarts."""
    out = []
    gap, x0, x1 = 14, 80, W - 80
    width = (x1 - x0 - gap * (len(SCENES) - 1)) / len(SCENES)
    for i, (start, end) in enumerate(SCENES):
        x = x0 + i * (width + gap)
        out.append(f'<rect x="{x:.1f}" y="628" width="{width:.1f}" height="10" rx="5" class="seg"/>')
        fill = anim.grow_x(start, end - start, LOOP)
        out.append(f'<rect x="{x:.1f}" y="628" width="{width:.1f}" height="10" rx="5" class="segfill {fill}"/>')
    return '<g class="stepper">' + "".join(out) + "</g>"


HEAD = 50  # headline size: two lines that fit the 1040 px text width


def _headline(lines) -> str:
    """Two big lines. Each line is a list of (text, cls) runs."""
    return "".join(_big(130 + 72 * i, line, HEAD) for i, line in enumerate(lines))


def _small(y, parts, size=28) -> str:
    """The small secondary line. Commands are ("/cmd", True) runs in monospace."""
    runs = [(t, "ink" if mono else "muted", 700 if mono else 500, mono) for t, mono in parts]
    return _rich(80, y, runs, size)


def _scene_ready(anim: _Anim) -> str:
    """Both limits get the same weight: two equal cards, the subscription first."""
    start, end = SCENES[0]
    f = anim.window(start, end)
    fill = anim.grow_x(start + 0.8, 3.0, end)
    cards = []
    for x, who, limit in ((80, "Pro, Max or Ultra plan", "1 hour"), (620, "API key", "5 minutes")):
        cards.append(
            f'<rect x="{x}" y="250" width="500" height="250" rx="20" class="card" stroke-width="2"/>'
            + _text(x + 36, 306, who, 30, "muted", 700)
            + _text(x + 36, 396, limit, 72, "good", 800)
            + f'<rect x="{x + 36}" y="436" width="428" height="26" rx="13" class="track"/>'
            + f'<rect x="{x + 36}" y="436" width="428" height="26" rx="13" class="goodbar {fill}"/>'
        )
    return (
        f'<g class="sc {f}">'
        + _headline([[("Claude saves your chat for a short time,", "ink")], [("so each new message is cheap.", "good")]])
        + "".join(cards)
        + _small(560, [("Every message restarts the timer.", False)])
        + "</g>"
    )


def _scene_cost(anim: _Anim) -> str:
    start, end = SCENES[1]
    f = anim.window(start, end)
    rows = [
        ("New chat", 1.0, "1x", "warm", "ink"),
        ("Back before the timer ends", FACTS["warm"], f"{FACTS['warm']}x", "warm", "ink"),
        ("Back after it ends", FACTS["stale"], f"{FACTS['stale']}x", "cold", "acc"),
    ]
    x_bar, per_x = 500, 60
    out = []
    for i, (name, value, shown, bar_cls, num_cls) in enumerate(rows):
        y = 262 + i * 88
        t0 = start + 0.7 + i * 0.7
        dur = 1.5 if i == 2 else 0.5
        out.append(_text(80, y + 44, name, 28, "ink", 700))
        grow = anim.grow_x(t0, dur, end)
        out.append(f'<rect x="{x_bar}" y="{y}" width="{per_x * value:.1f}" height="64" rx="10" class="{bar_cls} {grow}"/>')
        num = anim.window(t0 + dur, end, 0.2)
        if i == 2:
            out.append(f'<g class="{num}">' + _text(x_bar + per_x * value - 20, y + 46, shown, 40, "bg", 800, "end") + "</g>")
        else:
            out.append(f'<g class="{num}">' + _text(x_bar + per_x * value + 16, y + 46, shown, 40, num_cls, 800) + "</g>")
    return (
        f'<g class="sc {f}">'
        + _headline([[("Come back after the timer runs out,", "ink")], [("and your next message costs ", "ink"), ("about 10x.", "acc")]])
        + "".join(out)
        + _small(566, [(f"Claude has to save the whole chat again. Measured {FACTS['runs']} times on an API key.", False)], 24)
        + "</g>"
    )


def _scene_shrink(anim: _Anim) -> str:
    start, end = SCENES[2]
    f = anim.window(start, end)
    # A long chat bar squeezes into a short summary.
    shrink = anim._add(
        [(0.0, "transform:scaleX(1)"), (start + 1.2, "transform:scaleX(1)"), (start + 2.6, "transform:scaleX(0.22)"),
         (end, "transform:scaleX(0.22)"), (end + 0.01, "transform:scaleX(1)"), (LOOP, "transform:scaleX(1)")],
        "transform-box:fill-box;transform-origin:0 50%;",
    )
    label = anim.window(start + 2.7, end, 0.3)
    return (
        f'<g class="sc {f}">'
        + _headline([[("Taking a break?", "ink")], [("Shrink the chat first.", "good")]])
        + '<rect x="80" y="300" width="1040" height="90" rx="14" class="track"/>'
        + _text(1100, 356, "your long chat", 28, "muted", 600, "end")
        + f'<rect x="80" y="300" width="1040" height="90" rx="14" class="warm {shrink}"/>'
        + f'<g class="{label}">' + _text(340, 356, "short summary", 32, "good", 800) + "</g>"
        + _small(520, [("Type ", False), ("/compact", True), (f". About {FACTS['compact_before']}x instead of 10x.", False)])
        + "</g>"
    )


def _scene_fresh(anim: _Anim) -> str:
    """Before and after: the old chat's 9.8x price tag gets crossed out, a new chat with a note is 1x."""
    start, end = SCENES[3]
    f = anim.window(start, end)
    old = anim.window(start + 0.5, end, 0.3)
    strike = anim.grow_x(start + 1.6, 0.5, end)
    new = anim.window(start + 2.3, end, 0.4)
    stale = f"{FACTS['stale']}x"
    old_card = (
        '<rect x="80" y="250" width="440" height="270" rx="20" class="card" stroke-width="2"/>'
        + _text(110, 300, "Keep going in the old chat", 26, "muted", 700)
        # A price tag: body plus a hole.
        + '<path d="M150 340 h230 a16 16 0 0 1 16 16 v108 a16 16 0 0 1 -16 16 h-230 l-46 -70 z" class="cold"/>'
        + '<circle cx="138" cy="410" r="9" class="card"/>'
        + _text(278, 438, stale, 76, "bg", 800, "middle")
        + f'<g class="{strike}"><rect x="100" y="405" width="316" height="9" rx="4.5" class="ink" transform="rotate(-10 258 409)"/></g>'
    )
    lines = [("Goal:", "fix the rounding bug"), ("Done:", "a test shows the bug"), ("Next:", "patch money.py")]
    note = "".join(
        _rich(596, 364 + i * 44, [(k + " ", "ink", 800, False), (v, "muted", 500, False)], 25) for i, (k, v) in enumerate(lines)
    )
    new_card = (
        '<rect x="560" y="250" width="560" height="270" rx="20" class="card" stroke-width="2"/>'
        + _text(590, 300, "New chat with a 3-line note", 26, "muted", 700)
        + _text(1092, 486, "1x", 120, "good", 800, "end")
        + note
    )
    return (
        f'<g class="sc {f}">'
        + _headline([[("Back from a break?", "ink")], [("Start a new chat.", "good")]])
        + f'<g class="{old}">' + old_card + "</g>"
        + f'<g class="{new}">' + new_card + "</g>"
        + _small(570, [("Type ", False), ("/clear", True), (", then write Goal, Done and Next. About 1x instead of 9.8x.", False)], 24)
        + "</g>"
    )


def _scene_star(anim: _Anim) -> str:
    start, end = SCENES[4]
    f = anim.window(start, end, 0.35)
    # A five-point star, drawn around (600, 230).
    pts = []
    for k in range(10):
        r = 110 if k % 2 == 0 else 46
        a = math.pi / 2 + k * math.pi / 5
        pts.append(f"{600 + r * math.cos(a):.1f},{230 - r * math.sin(a):.1f}")
    return (
        f'<g class="sc {f}">'
        + f'<polygon points="{" ".join(pts)}" class="cold"/>'
        + _text(600, 420, "Found this useful?", 56, "ink", 800, "middle")
        + _text(600, 490, "Star the repo on GitHub.", 56, "good", 800, "middle")
        + _text(600, 560, "github.com/inevolin/claude-code-usage-analysis", 28, "muted", 600, "middle")
        + "</g>"
    )


def build() -> str:
    anim = _Anim()
    parts = [_scene_ready(anim), _scene_cost(anim), _scene_shrink(anim), _scene_fresh(anim), _scene_star(anim), _timer(anim)]
    # Reduced motion: one still summary.
    parts.append(
        '<g class="rm" opacity="0">'
        + _big(110, [("Claude saves your chat for a short time, so each new message is cheap:", "ink")], 26)
        + _big(148, [("1 hour on a Pro, Max or Ultra plan, 5 minutes on an API key.", "ink")], 26)
        + _big(220, [("Come back after that, and your next message costs ", "ink"), ("about 10x.", "acc")], 34)
        + _big(320, [("Taking a break? ", "ink"), ("Shrink the chat first.", "good")], 38)
        + _small(362, [("Type ", False), ("/compact", True), (". About 2.5x instead of 10x.", False)], 24)
        + _big(450, [("Back from a break? ", "ink"), ("Start a new chat.", "good")], 38)
        + _small(492, [("Type ", False), ("/clear", True), (", then write Goal, Done and Next. About 1x instead of 9.8x.", False)], 24)
        + _text(80, 590, "★ Found this useful? Star the repo on GitHub.", 24, "acc", 700)
        + "</g>"
    )
    style = (
        f"text{{font-family:{FONT}}}"
        + STYLE_COLORS
        + "".join(anim.rules)
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}"
        ".sc{opacity:0!important}.stepper{display:none}.rm{opacity:1}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(ALT, {chr(34): "&quot;"})}">'
        "<title>Claude saves your chat for a short time. Come back after the timer runs out, and your next message costs about 10x.</title>"
        f"<style>{style}</style>"
        f'<rect width="{W}" height="{H}" rx="24" class="bg"/>'
        + "".join(parts)
        + "</svg>\n"
    )


def main() -> int:
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
