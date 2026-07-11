from conftest import SKILL_FILES, SKILLS_DIR

JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def test_skills_dir_exists():
    assert SKILLS_DIR.is_dir()


def test_at_least_one_skill():
    assert SKILL_FILES, "no skills/<name>/SKILL.md files found"


def test_every_skill_dir_has_skill_md():
    for entry in SKILLS_DIR.iterdir():
        if entry.is_dir():
            assert (entry / "SKILL.md").is_file(), f"{entry} has no SKILL.md"


def test_no_loose_files_in_skills_dir():
    loose = [e.name for e in SKILLS_DIR.iterdir() if not e.is_dir()]
    assert not loose, f"unexpected files directly in skills/: {loose}"


def test_no_junk_files():
    junk = [p for p in SKILLS_DIR.rglob("*") if p.name in JUNK_NAMES]
    assert not junk, f"junk files found: {junk}"


def test_no_nested_skills():
    nested = [
        p for p in SKILLS_DIR.rglob("SKILL.md")
        if p.parent.parent != SKILLS_DIR
    ]
    assert not nested, f"SKILL.md files deeper than skills/<name>/: {nested}"
