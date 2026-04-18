---
name: health-os
description: Evidence-based health operating system (Medicine 3.0 + training science) ported for OpenClaw/OpenAI models. Use when setting up or running the Health OS workflow (daily check-in, labs, strategy, directives), organizing health data files under data/, or when you need to reference the bundled health knowledge-base markdown files.
---

# Health OS (OpenClaw, GPT)

## What you have in this workspace

Source repo cloned to `health-os/`.

This skill bundles the important docs and health markdown library under:
- `skills/health-os/references/` (agent setup docs)
- `skills/health-os/references/knowledge/` (health topic markdowns)

## How to use (recommended workflow)

1) Read:
- `skills/health-os/references/CLAUDE.md` (architecture + data structure)
- `skills/health-os/references/README.md` (overview)

2) Use these as sources of truth (create/update as needed):
- `health-os/data/tactical/user_profile.yaml`
- `health-os/data/strategic/biomarkers.yaml`
- `health-os/data/strategic/directives.yaml`
- `health-os/data/tactical/strategy.md`
- `health-os/data/tactical/training/current_program.yaml`

Templates are in `health-os/data/templates/` (also copied into `skills/health-os/references/data/`).

3) For evidence-based answers, pull relevant snippets from `skills/health-os/references/knowledge/**`.

## Notes

- This is a Claude Code project originally, but you can run the same workflow here with GPT models by following the same file contract (`directives.yaml` drives everything).
- Keep personal data in `health-os/data/` (it is intended to be gitignored upstream).
