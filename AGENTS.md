# Agent Skills for Tower

This repository is a catalog of agent skills for [Tower](https://tower.dev), installable with the [`skills`](https://github.com/vercel-labs/skills) CLI (`npx skills add tower/agent-skills`). There is no application code here — the deliverables are the `SKILL.md` files themselves.

## Repository layout

- `skills/<skill-name>/SKILL.md` — one directory per skill. The `skills` CLI discovers skills at exactly this depth.
- A skill directory may also contain supporting files (scripts, references) that the SKILL.md links to with relative paths.

## Skill conventions

- Frontmatter requires `name` (lowercase, hyphen-separated, must match the directory name and be unique across the repo) and `description`.
- The `description` is what an agent uses to decide when to load the skill: state what the skill does AND the trigger phrases/situations that should invoke it, including cases where the user doesn't use Tower terminology.
- Skill names are prefixed `tower-` (e.g. `tower-ingest`, `tower-data`).
- Write instructions imperatively, addressed to the agent. Prefer concrete commands and code snippets over prose. Include a troubleshooting section and a "what this skill is not for" section that points to sibling skills.
- Secrets handling is a hard rule in every skill: credential values never appear in code, config files, or conversation — they live in Tower secrets.

## Design principles for data skills

Every skill in this catalog gives an agent access to customer data. New skills must uphold these principles; they exist so a skill author doesn't accidentally relax a guarantee a sibling skill depends on.

1. **Read and write are separate skills with separate credential models.** `tower-data` vends short-lived read-only credentials; `tower-ingest` owns writes via scoped secrets. Never give an analytical skill write credentials or a write skill blanket admin credentials. A new skill must pick a side (or justify why it needs both, with explicit user confirmation before any write).
2. **Secrets never transit the conversation.** Skills instruct the user to create secrets themselves, verify by preview only, and never echo tokens — including into temp files that outlive the command. If a user pastes a credential, store it immediately, never repeat it, and advise rotation.
3. **Credentials resolve before code is written.** A skill must not have the agent write code that needs a credential that doesn't exist yet — that's how insecure workarounds (.env files, hardcoded fallbacks) get improvised.
4. **Writes are idempotent and stateless.** Safe to re-run (upsert/merge or explicit dedup); incremental cursors derived from the destination, never from local state — runners are ephemeral.
5. **Verify by reading the destination back.** Logs and exit codes are not proof that data landed or that an answer is right. Skills must end with a verification step against the actual data, and show the user auditable evidence (row counts, sample rows, the SQL that was run).
6. **Discover, don't assume.** List existing catalogs, tables, secrets, and apps before creating or querying anything; ask when ambiguous rather than guessing.
7. **Query results are the user's private data.** Use them to answer the question; don't republish them to external services.
8. **Fail with a diagnosis, not a rewrite.** Distinguish user-code failure, infrastructure failure, expired credentials (self-heal by re-vending), and cold-start — each has a different fix. Every skill carries a Troubleshooting table for this.
9. **Declare non-goals.** Every skill ends with a "What this skill is not for" section handing off to the sibling skill that owns the adjacent job — this is what keeps principle 1's boundary real.

## Making changes

- When adding a skill, also add a row to the Skills table in `README.md`.
- When renaming a skill, update the directory name, frontmatter `name`, the README table and layout diagram, and any cross-references from other skills.
- Verify the repo still lists cleanly: `npx skills add . --list` (or the repo slug once pushed).
