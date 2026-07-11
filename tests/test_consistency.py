import re
import shutil
import subprocess

import pytest

from conftest import REPO_ROOT, SKILL_FILES, parse_skill

SKILL_NAMES = {parse_skill(p)[0]["name"] for p in SKILL_FILES}

# Patterns that look like real credentials, not placeholders.
SECRET_PATTERNS = [
    re.compile(r"sk_live_[A-Za-z0-9]{8,}"),
    re.compile(r"sk-ant-[A-Za-z0-9-]{8,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def test_body_starts_with_h1(skill):
    path, _, body = skill
    first_line = body.strip().splitlines()[0] if body.strip() else ""
    assert first_line.startswith("# "), f"{path}: body must start with an H1 heading"


def test_cross_references_resolve(skill):
    path, _, body = skill
    referenced = set(re.findall(r"\*\*(tower-[a-z0-9-]+)\*\*", body))
    missing = referenced - SKILL_NAMES
    assert not missing, f"{path}: references skills that don't exist: {missing}"


def test_no_credential_looking_strings(skill):
    path, _, body = skill
    hits = [pat.pattern for pat in SECRET_PATTERNS if pat.search(body)]
    assert not hits, f"{path}: contains credential-looking strings matching {hits}"


def test_has_troubleshooting_section(skill):
    path, _, body = skill
    assert re.search(r"^## Troubleshooting", body, re.MULTILINE), (
        f"{path}: missing '## Troubleshooting' section (AGENTS.md principle 8)"
    )


def test_has_non_goals_section(skill):
    path, _, body = skill
    assert re.search(r"^## What this skill is not for", body, re.MULTILINE), (
        f"{path}: missing '## What this skill is not for' section (AGENTS.md principle 9)"
    )


def test_every_skill_listed_in_readme():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    missing = [n for n in SKILL_NAMES if f"skills/{n}/SKILL.md" not in readme]
    assert not missing, f"skills missing from README table: {missing}"


def test_readme_links_resolve():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    for target in re.findall(r"\]\((?!https?://)([^)#]+)\)", readme):
        assert (REPO_ROOT / target).exists(), f"README links to missing path: {target}"


@pytest.mark.integration
def test_skills_cli_discovers_all_skills():
    npx = shutil.which("npx")
    if npx is None:
        pytest.skip("npx not available")
    result = subprocess.run(
        [npx, "--yes", "skills", "add", ".", "--list"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, f"skills CLI failed: {result.stderr}"
    for name in SKILL_NAMES:
        assert name in result.stdout, f"{name} not discovered by skills CLI"
