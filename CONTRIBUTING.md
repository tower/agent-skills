# Contributing

## Adding a skill

1. Create `skills/<skill-name>/SKILL.md`. The directory name, lowercase and hyphen-separated, must match the `name` in the frontmatter.
2. Write frontmatter:

   ```yaml
   ---
   name: tower-example
   description: What the skill does, and the situations/phrases that should trigger it.
   ---
   ```

3. Write the skill body in markdown: imperative instructions to the agent, concrete commands over prose, a troubleshooting table, and a "what this skill is not for" section pointing at sibling skills.
4. Add the skill to the table in `README.md`.
5. Run the validation suite: `uv run pytest` (add `-m integration` to also verify discovery against the real skills CLI). CI runs both on every PR.

## Guidelines

- New skills must uphold the [design principles for data skills](AGENTS.md#design-principles-for-data-skills) in AGENTS.md — in particular, pick a side of the read/write credential boundary and end with Troubleshooting and "What this skill is not for" sections (the test suite enforces the latter two).

- Keep each skill self-contained; cross-reference sibling skills by name rather than duplicating content.
- Descriptions should cover trigger phrases a user might say without Tower terminology ("get our Stripe data in", "what data do we have?").
- Never include credential values or instructions that would put secrets into code, config files, or chat.
