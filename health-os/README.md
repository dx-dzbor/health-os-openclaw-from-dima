# Health OS v3.0

Two-layer Health Operating System for Claude Code.

Evidence-based: Medicine 3.0 (Peter Attia) + Training Science (Layne Norton, Mike Israetel, Andy Galpin).

## What's Inside

**5 specialized agents:**
- **CMO** — strategic risk assessment, generates directives
- **Analyst** — parses lab results into structured biomarkers
- **Strategist** — builds training/nutrition/sleep strategy from directives
- **Coach** — daily operations: meals, workouts, logging, substitutions
- **Behaviorist** — crisis support for binges, cravings, skipped workouts (zero judgment)

**14 skills:** metabolic calculations, biomarker parsing, exercise navigation, program building, training science, protocol enforcement, and more.

**WHOOP integration** (optional): auto-syncs sleep, recovery, and workout data.

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- Claude Pro / Max / API key

## Quick Start

```bash
# 1. Clone or copy this folder
cd health-os

# 2. Open Claude Code
claude

# 3. Run setup
/health-setup
```

The setup command creates the data directory structure, copies clean templates, and tells you what to do next.

## Commands

| Command | What it does |
|---------|-------------|
| `/health-setup` | Initial setup (run once) |
| `/health-daily` | Daily check-in: log meals, workouts, get substitutions |
| `/health-review` | Create/update strategy, weekly review |
| `/health-labs` | Parse lab results into structured biomarkers |
| `/health-strategy` | CMO risk assessment, generate directives |
| `/health-crisis` | Support for binges, cravings, skipped workouts |
| `/ask` | Evidence-based Q&A |

## How It Works

```
You fill: user_profile.yaml (age, weight, goals, training access)
           |
/health-labs -> biomarkers.yaml (your lab results + Attia optimal ranges)
           |
/health-strategy -> directives.yaml (CMO constraints: what you must/can't do)
           |
/health-review -> strategy.md (personalized plan: nutrition, training, sleep)
           |
/health-daily -> daily operations (meals, workouts, logging, adjustments)
```

The key insight: **directives.yaml** is the contract between strategy and execution. The CMO sets hard limits based on your health data. Tactical agents optimize within those limits.

## Knowledge Base (Optional)

The system can use a knowledge base for evidence-based answers. Place markdown files in:

```
data/knowledge/
├── cardio/      # Zone 2, VO2max, endurance
├── muscle/      # Hypertrophy, strength, protein
├── sleep/       # Sleep stages, optimization
├── metabolism/  # Fat loss, fasting, insulin
├── biomarkers/  # Lab interpretation, CVD risk
├── sauna/       # Heat therapy
└── dopamine/    # Motivation, addiction
```

Good sources: Huberman Lab transcripts, Peter Attia (The Drive) show notes, research summaries.

## WHOOP Integration (Optional)

If you have a WHOOP band, the integration auto-syncs sleep, recovery, and workout data.

```bash
# Setup
cd integrations/whoop
python3 -m venv ../../.venv
../../.venv/bin/pip install -r requirements.txt

# Auth (opens browser for OAuth)
../../.venv/bin/python auth.py

# Sync
../../.venv/bin/python sync.py --dry-run --days 3
```

See `integrations/whoop/README.md` for cron setup and details.

## MCP Servers (Optional)

Health OS can use MCP tools for extra capabilities. Configure in `.mcp.json`:

- **scheduler** — automated reminders (e.g., "log dinner at 8pm")
- **exa / serper** — web search for latest research

## Data Privacy

All your data lives in `data/` which is gitignored. Templates in `data/templates/` are the only data files tracked by git. Your personal health data never leaves your machine unless you explicitly push it.

## License

MIT
