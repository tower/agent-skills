from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))


def parse_skill(path: Path) -> tuple[dict, str]:
    """Return (frontmatter, body) for a SKILL.md file."""
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path}: file must start with '---' frontmatter"
    parts = text.split("---\n", 2)
    assert len(parts) == 3, f"{path}: frontmatter is not closed with '---'"
    _, fm_text, body = parts
    frontmatter = yaml.safe_load(fm_text)
    assert isinstance(frontmatter, dict), f"{path}: frontmatter is not a YAML mapping"
    return frontmatter, body


@pytest.fixture(params=SKILL_FILES, ids=lambda p: p.parent.name)
def skill_file(request) -> Path:
    return request.param


@pytest.fixture
def skill(skill_file) -> tuple[Path, dict, str]:
    frontmatter, body = parse_skill(skill_file)
    return skill_file, frontmatter, body
