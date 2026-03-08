# Suggested Repository Structure

## Goal

Keep runtime code, content bundles, and project docs clearly separated for maintainability and open-source onboarding.

## Recommended Layout

```text
.
├── app/                      # Application code (CLI, web, DB, importer, runner)
├── tests/                    # Automated tests
├── bundles/                  # Optional canonical location for problem bundles
│   ├── 9021/
│   └── final/
├── statements/               # Generated/checked-in statement markdown
├── docs/
│   ├── architecture.md
│   ├── repository-structure.md
│   └── screenshots/
├── .github/
│   └── ISSUE_TEMPLATE/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

## Practical Notes For This Repo

- Current bundle directories `9021/` and `final/` can stay as-is now; moving to `bundles/` is optional and can be done later.
- Keep `.practice/` ignored because it is runtime state (DB, runs, saved solutions).
- Keep `.env` ignored and maintain `.env.example` as the only committed template.
- If `statements/` is generated content, decide whether it should remain versioned; either strategy is valid if documented.

## Incremental Cleanup Plan (No Logic Changes)

1. Stabilize docs and contributor files (this PR scope).
2. Add `docs/screenshots/` assets for README.
3. Optionally migrate `9021/` and `final/` into `bundles/` with env defaults updated in docs.
4. Optionally split non-product planning files (`PLAN.md`, `TASKS.md`) into `docs/internal/` if desired.
