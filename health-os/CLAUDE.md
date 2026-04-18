# Health OS v3.0

Two-layer Health Operating System: **Strategic (The Board)** + **Tactical (The Field)**.
Evidence-based: Medicine 3.0 (Attia) + Training Science (Norton, Israetel, Galpin).

## Quick Start

New user? Run `/health-setup` — it creates the data directory structure, copies clean templates, and walks you through onboarding.

## Architecture

```
STRATEGIC LAYER (The Board)
  CMO: Risk Assessment → directives.yaml
  Analyst: Labs → biomarkers.yaml
                    │
                    ▼ directives.yaml (The Interface)
TACTICAL LAYER (The Field)
  Strategist: Directives → strategy.md
  Coach: Plans → Daily Operations
  Behaviorist: Crisis Support
```

## Commands

| Command | Agent | Purpose |
|---------|-------|---------|
| `/health-daily` | Coach | Daily check-in, meals, exercise subs |
| `/health-review` | Strategist | Strategy, weekly review |
| `/health-labs` | Analyst | Lab results → biomarkers.yaml |
| `/health-strategy` | CMO | Risk assessment → directives.yaml |
| `/health-crisis` | Behaviorist | Binges, cravings, skips |
| `/ask` | ask | Evidence-based Q&A from knowledge base |

## Data Structure

```
data/
├── strategic/          # THE BOARD
│   ├── biomarkers.yaml, genetics.yaml, decathlon_goals.md
│   ├── directives.yaml  # INTERFACE → tactical
│   └── history/
├── tactical/           # THE FIELD
│   ├── user_profile.yaml, strategy.md, science_rules.md
│   ├── training/       # exercise_db.yaml, current_program.yaml
│   ├── nutrition/food_inventory/
│   ├── logs/{YYYY-MM-DD}.yaml, weekly/{YYYY-Www}.yaml
│   └── analytics/whoop/  # rolling.yaml, weekly/, monthly/
├── integrations/whoop/   # OAuth, sync metadata
└── knowledge/            # RAG: attia/, huberman/, etc.
```

## WHOOP Integration

Auto-sync sleep, recovery, workout every 12h.

```bash
.venv/bin/python integrations/whoop/sync.py --dry-run --days 3
```

Recovery zones: Red (0-32) skip | Yellow (33-65) 50% volume | Green (66-100) full.

Analytics: `data/tactical/analytics/whoop/` — rolling averages, weekly/monthly reports.

## The Interface: directives.yaml

Machine-readable contract from CMO to Tacticians.
**Hierarchy:** CMO Directives > User Preferences > Default Calculations.

## Agents & Skills

**Strategic:** CMO (opus), Analyst (sonnet)
**Tactical:** Strategist (sonnet), Coach (sonnet), Behaviorist (opus)

**Skills:** biomarker-engine, longevity-math, protocol-enforcer, metabolic-calc, log-manager, menu-navigator, exercise-navigator, program-builder, training-science, science-rules, whoop-analytics, ask

Full details: `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`

## Knowledge Base

| Folder | Topics |
|--------|--------|
| cardio | Zone 2, VO2max, endurance |
| muscle | Hypertrophy, strength, protein |
| sleep | Sleep stages, optimization |
| metabolism | Fat loss, fasting, insulin |
| biomarkers | Lab interpretation, CVD risk |

## Sources of Truth

| What | File | Notes |
|------|------|-------|
| Training program (exercises, weights, progression, deload, schedule) | `data/tactical/training/current_program.yaml` | **Single source** — strategy.md references it, never duplicates |
| Overall strategy (nutrition, sleep, modes, milestones) | `data/tactical/strategy.md` | No exercise details here |
| CMO directives | `data/strategic/directives.yaml` | Overrides everything |
| User profile | `data/tactical/user_profile.yaml` | Biometrics, preferences |

## Key Principles

- **Backcasting:** Plan from 90 years back
- **Optimal > Normal:** Lab "normal" = sick population average
- **Four Horsemen:** CVD, Cancer, Neuro, Metabolic
- **Volume landmarks:** MV < MEV < MAV < MRV. Deficit → MV-MEV
- **Zone 2:** Non-negotiable for metabolic health (180 min/week)

## Constraints

**Nutrition:** Never below 1200/1500 cal, deficit ≤25%, directives override defaults
**Training:** Never exceed MRV, respect banned patterns, Novice Protocol if gap >14d
**Sleep:** 7h minimum, regularity > duration, caffeine cutoff 10h
**Sauna:** 4 sessions/week, 20+ min, never with alcohol
**Behavior:** Zero judgment, redirect to specialist if red flags

## Movement Patterns

Squat | Hinge | Push H/V | Pull H/V — substitution ONLY within same pattern.
