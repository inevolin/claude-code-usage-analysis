import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOLLAR = re.compile(r"\$[0-9]")


def _public_text_files(suffixes=(".md", ".py", ".toml")):
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".venv", "node_modules", ".git", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        if path.suffix.lower() in suffixes:
            yield path


def _user_facing():
    yield ROOT / "README.md"
    yield from sorted((ROOT / "docs").glob("*.md"))
    yield from sorted((ROOT / "benchmarks").glob("*.md"))
    yield from sorted((ROOT / "skills").rglob("*.md"))
    yield ROOT / "outputs" / "summary.json"


def test_no_em_dashes_anywhere():
    offenders = []
    for path in _public_text_files((".md", ".py", ".toml", ".json")):
        text = path.read_text(encoding="utf-8")
        if "\u2014" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_public_pages_do_not_mention_removed_claims():
    offenders = []
    for path in _public_text_files():
        text = path.read_text(encoding="utf-8").lower()
        banned = ("link" + "edin", "200" + "%")
        if any(needle in text for needle in banned):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_front_pages_drop_the_old_framing():
    for relative in ("README.md", "docs/article-draft.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        lowered = text.lower()
        assert "4x" not in lowered, relative
        assert ("link" + "edin") not in lowered, relative
        assert ("200" + "%") not in lowered, relative
        assert "\u2014" not in text, relative
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "250k" not in readme
    assert "25%" not in readme
    assert "3.9x" not in readme


def test_user_facing_text_has_no_dollar_amounts():
    offenders = []
    for path in _user_facing():
        text = path.read_text(encoding="utf-8")
        for match in DOLLAR.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            offenders.append(f"{path.relative_to(ROOT)}:{line}")
    assert offenders == []


def test_no_private_material_in_public_pages():
    needles = ("sk-" + "ant", ".claude_" + "study_key", "/home/", "/Users/", "/tmp/")
    offenders = []
    for path in _user_facing():
        text = path.read_text(encoding="utf-8")
        offenders.extend(f"{path.relative_to(ROOT)}: {needle}" for needle in needles if needle in text)
    assert offenders == []


def test_readme_leads_with_practices_and_embeds_the_charts():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# Claude Code usage anti-patterns and best-practices")
    hero = readme.index("outputs/figures/explainer.svg")
    practices = readme.index("## Best practices")
    check = readme.index("## Check your own habits: paste this into Claude Code")
    myths = readme.index("## Myths and unknowns")
    copy_paste = readme.index("## What to do about it")
    evidence = readme.index("## The evidence")
    assert hero < practices < check < myths < copy_paste < evidence
    # The dose-response chart belongs in the evidence section, not at the top.
    assert readme.index("outputs/figures/hero_cache_expiry.png") > evidence
    assert "## Anti-patterns" not in readme
    # Title, hero, and the paired practices list stay short; the self-check prompt follows.
    assert readme[:check].count("\n") < 25
    self_check = readme[check:myths]
    assert "cc_usage_study.analyze" in self_check
    assert "--summary" in self_check and "--sessions" in self_check
    assert "Everyone uses Claude Code differently" in self_check
    assert "~/.claude/skills" in self_check
    assert "/claude-code-usage-check" in self_check
    assert readme.index("### Cache expiry after a break") > evidence
    assert "### Does the model hold up?" in readme[evidence:]
    # Promote the CLI / T3 Code over Desktop, without inventing a chat-app number.
    top = readme[:evidence]
    assert "Use the Claude Code CLI" in top
    assert "T3 Code" in top
    assert "Desktop Code tab" in top
    assert "We did not test the Claude chat app." in top
    assert "1.19x the CLI" in top and "at least 1.80x" in top
    for figure in (
        "explainer.svg",
        "hero_cache_expiry.png",
        "hero_coffee_break.png",
        "ttl_price_of_a_pause.png",
        "resume_crossover.png",
        "cron_resume_vs_fresh.png",
        "live_compaction_arms.png",
        "live_clear_vs_warm.png",
        "live_client_comparison.png",
        "model_vs_measured.png",
        "scenario_comparison.png",
        "eoq_curve.png",
        "context_sawtooth.png",
    ):
        assert f"outputs/figures/{figure}" in readme, figure
        assert (ROOT / "outputs" / "figures" / figure).is_file(), figure
    assert "ttl_cliff" not in readme
    # Caveats move below the fold but must still be there.
    details = readme[evidence:]
    assert "cache-weighted" in details
    assert "1 / 1.25 / 2 / 0.05 / 5" in details
    assert "Honest limits" in details
    assert "n=1" in details
    assert "(estimate)" in readme[:evidence]


def _github_slug(title: str) -> str:
    text = title.replace("`", "").lower()
    cleaned = "".join(ch if ch.isalnum() or ch in " -_" else "" for ch in text)
    return re.sub(r"-+", "-", re.sub(r"\s+", "-", cleaned.strip()))


def test_readme_internal_anchors_resolve():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # Headings outside fenced code blocks.
    slugs: list[str] = []
    counts: dict[str, int] = {}
    in_fence = False
    for line in readme.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line.startswith("#"):
            continue
        title = line.lstrip("#").strip()
        if not title:
            continue
        base = _github_slug(title)
        n = counts.get(base, 0)
        slugs.append(base if n == 0 else f"{base}-{n}")
        counts[base] = n + 1
    missing = []
    for match in re.finditer(r"\]\((#[^)]+)\)", readme):
        anchor = match.group(1)[1:]
        if anchor not in slugs:
            missing.append(anchor)
    assert missing == []
    for required in (
        "best-practices",
        "check-your-own-habits-paste-this-into-claude-code",
        "myths-and-unknowns",
        "the-evidence",
        "cache-expiry-after-a-break",
        "compact-before-or-after-the-break",
        "does-this-apply-to-you",
        "does-the-model-hold-up",
        "compaction-measured-live",
        "clear-vs-a-warm-session",
        "three-clients-one-bugfix",
        "compaction-settings-and-sweet-spots",
        "honest-limits",
        "reproduce",
    ):
        assert required in slugs, required


def test_docs_reconcile_the_compound_trigger():
    for relative in ("docs/reference.md", "docs/examples.md", "benchmarks/protocol.md", "README.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "62,500" not in text, relative
    reference = (ROOT / "docs" / "reference.md").read_text(encoding="utf-8")
    assert "CLAUDE_CODE_IDLE_COMPACT_MIN_TOKENS" in reference
    assert "100,000" in reference
    client = (ROOT / "benchmarks" / "client_comparison.md").read_text(encoding="utf-8").lower()
    assert "cold start" not in client

def test_usage_check_skill_has_valid_frontmatter():
    path = ROOT / "skills" / "claude-code-usage-check" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    end = text.find("\n---", 3)
    assert end != -1
    meta = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        assert sep, line
        meta[key.strip()] = value.strip()
    assert meta.get("name") == "claude-code-usage-check"
    assert meta.get("description")
    assert "cc_usage_study.analyze" in text
    assert "--summary" in text and "--sessions" in text and "--calls" in text
    assert "Everyone uses Claude Code differently" in text
    assert "\u2014" not in text
    assert DOLLAR.search(text) is None
