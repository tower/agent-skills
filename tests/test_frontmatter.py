import re

from conftest import SKILL_FILES, parse_skill

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALLOWED_KEYS = {"name", "description", "metadata", "license", "allowed-tools"}
MAX_DESCRIPTION_LEN = 1024


def test_frontmatter_keys(skill):
    path, fm, _ = skill
    unknown = set(fm) - ALLOWED_KEYS
    assert not unknown, f"{path}: unknown frontmatter keys {unknown}"
    assert "name" in fm and "description" in fm, f"{path}: name and description are required"


def test_name_format(skill):
    path, fm, _ = skill
    assert NAME_RE.match(fm["name"]), f"{path}: name {fm['name']!r} must be lowercase-hyphenated"


def test_name_matches_directory(skill):
    path, fm, _ = skill
    assert fm["name"] == path.parent.name, (
        f"{path}: frontmatter name {fm['name']!r} != directory {path.parent.name!r}"
    )


def test_description_present_and_bounded(skill):
    path, fm, _ = skill
    description = fm["description"]
    assert isinstance(description, str) and description.strip(), f"{path}: empty description"
    assert len(description) <= MAX_DESCRIPTION_LEN, (
        f"{path}: description is {len(description)} chars (max {MAX_DESCRIPTION_LEN})"
    )


def test_names_unique_across_repo():
    names = [parse_skill(p)[0]["name"] for p in SKILL_FILES]
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes, f"duplicate skill names: {dupes}"
