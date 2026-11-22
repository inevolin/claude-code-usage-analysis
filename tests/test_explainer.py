import re
from pathlib import Path

from cc_usage_study import explainer

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "outputs" / "figures" / "explainer.svg"


def test_committed_explainer_matches_generator():
    assert SVG.read_text(encoding="utf-8") == explainer.build()


def test_explainer_tells_four_plain_screens_and_ends_with_a_star():
    svg = explainer.build()
    for beat in (
        "Claude saves your chat for a short time,",
        "so each new message is cheap.",
        "Pro, Max or Ultra plan",
        "1 hour",
        "API key",
        "5 minutes",
        "Every message restarts the timer.",
        "Come back after the timer runs out,",
        "Back before the timer ends",
        "Back after it ends",
        "Claude has to save the whole chat again.",
        "Taking a break?",
        "Shrink the chat first.",
        "Back from a break?",
        "Start a new chat.",
        "Keep going in the old chat",
        "New chat with a 3-line note",
        "Found this useful?",
        "Star the repo on GitHub.",
        "github.com/inevolin/claude-code-usage-analysis",
    ):
        assert beat in svg, beat
    # Commands appear only as small secondary labels, never in the big headlines.
    assert "/compact" in svg and "/clear" in svg
    # The chat is never lost, it only gets expensive again. No wording that says otherwise.
    for misleading in ("is gone", "forgets", "deleted", "lost"):
        assert misleading not in svg, misleading
    for jargon in ("cache", "token", "TTL"):
        assert jargon.lower() not in re.sub(r"<style>.*?</style>", "", svg).lower(), jargon
    assert chr(0x2014) not in svg
    assert "<script" not in svg
    assert "prefers-color-scheme:dark" in svg and "prefers-reduced-motion" in svg


def test_subscription_and_api_limits_get_equal_weight():
    svg = explainer.build()
    sub = re.search(r'<text[^>]*font-size="(\d+)"[^>]*>1 hour</text>', svg)
    api = re.search(r'<text[^>]*font-size="(\d+)"[^>]*>5 minutes</text>', svg)
    assert sub and api and sub.group(1) == api.group(1)
    assert svg.index(">1 hour<") < svg.index(">5 minutes<")  # the subscription comes first


def test_slide_timer_has_one_segment_per_screen():
    svg = explainer.build()
    assert svg.count('class="seg"') == len(explainer.SCENES)
    assert svg.count('class="segfill ') == len(explainer.SCENES)


def test_explainer_numbers_match_the_published_findings():
    svg = explainer.build()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for shown, published in (("1.5x", "1.51x"), ("9.8x", "9.78x"), ("2.5x", "**2.5x"), ("about 10x", "about 10x"), ("1x instead of 9.8x", "**9.87x**")):
        assert shown in svg, shown
        assert published in readme, published
    assert f"Measured {explainer.FACTS['runs']} times on an API key" in svg


def test_explainer_is_short_and_github_img_safe():
    svg = explainer.build()
    # Four content slides of 5 to 6 seconds, then a 3 to 4 second closing slide.
    assert len(explainer.SCENES) == 5
    assert 24 <= explainer.LOOP <= 28
    for start, end in explainer.SCENES[:4]:
        assert 5 <= end - start <= 6
    start, end = explainer.SCENES[4]
    assert 3 <= end - start <= 4
    assert explainer.SCENES[-1][1] == explainer.LOOP
    assert "@import" not in svg and "@font-face" not in svg and "href=" not in svg
    assert len(svg.encode("utf-8")) < 60_000
    # Every animation runs on the one shared loop, so the whole thing loops cleanly.
    assert set(re.findall(r"animation:a\d+ ([\d.]+)s", svg)) == {f"{explainer.LOOP}"}
