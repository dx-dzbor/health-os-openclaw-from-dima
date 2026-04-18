# Health OS for OpenClaw (GPT) Manual

This package installs a Health OS skill plus an optional health knowledge base.

## Contents
- [Install](#install)
- [Quickstart](#quickstart)
- [Architecture](#architecture)
- [File layout and sources of truth](#file-layout-and-sources-of-truth)
- [Workflows](#workflows)
- [Knowledge base index](#knowledge-base-index)

## Install

## 0) Prereqs

- OpenClaw installed and running on the machine.
- OpenAI access, pick one:
  - **API key** (usage-based), or
  - **Codex subscription auth** (ChatGPT sign-in) via `openai-codex/*`.

## 1) Install the repo into the OpenClaw workspace

Clone (recommended):

```bash
cd /path/to/openclaw/workspace
# Either clone directly into the workspace root, or clone then copy the contents.
git clone <THIS_REPO_URL> .
# or: git clone <THIS_REPO_URL> health-os-openclaw && cp -R health-os-openclaw/* .
```

After install you should have:
- `skills/health-os/`
- `health-os/`

Restart OpenClaw (gateway) if your deployment requires it to pick up new skills.

## 2) Configure OpenAI in OpenClaw

### Option A (recommended): OpenAI API key

```bash
openclaw onboard --auth-choice openai-api-key
# or non-interactive
openclaw onboard --openai-api-key "$OPENAI_API_KEY"
```

Optional config snippet (example):

```json5
{
  env: { OPENAI_API_KEY: "sk-..." },
  agents: { defaults: { model: { primary: "openai/gpt-5.4" } } }
}
```

### Option B: Codex subscription auth (ChatGPT sign-in)

```bash
openclaw onboard --auth-choice openai-codex
# or:
openclaw models auth login --provider openai-codex
```

Then set your default model to an `openai-codex/*` route.

## 3) First run

1) Fill:
- `health-os/data/tactical/user_profile.yaml`

2) (Optional) Add labs:
- `health-os/data/strategic/biomarkers.yaml`

3) Generate risk constraints:
- `health-os/data/strategic/directives.yaml`


## Quickstart

1) Confirm the skill exists:
- `skills/health-os/SKILL.md`

2) Fill your user profile:
- `health-os/data/tactical/user_profile.yaml`

3) Start using the workflow:
- Create/update `health-os/data/strategic/directives.yaml`
- Create/update `health-os/data/tactical/strategy.md`
- Track training in `health-os/data/tactical/training/current_program.yaml`


## Architecture

Health OS is a two-layer system: Strategic (constraints) and Tactical (execution).

Primary contract file: `health-os/data/strategic/directives.yaml`.

Reference: [skills/health-os/references/CLAUDE.md](skills/health-os/references/CLAUDE.md)

## File layout and sources of truth

- Strategic
  - `health-os/data/strategic/biomarkers.yaml`
  - `health-os/data/strategic/genetics.yaml`
  - `health-os/data/strategic/directives.yaml`
- Tactical
  - `health-os/data/tactical/user_profile.yaml`
  - `health-os/data/tactical/strategy.md`
  - `health-os/data/tactical/training/current_program.yaml`

Templates: [health-os/data/templates/](health-os/data/templates/)

## Workflows

### Daily operations

- Update logs, meals, workouts, substitutions.
- Keep `current_program.yaml` as the single source of truth for training details.

### Labs → biomarkers → directives

- Put lab values into `biomarkers.yaml`
- Update `directives.yaml` with risk constraints

### Strategy + training plan

- Update `strategy.md` (nutrition, sleep, milestones)
- Update `current_program.yaml` (exercises, schedule, progression)

## Knowledge base index

Root: [skills/health-os/references/knowledge/](skills/health-os/references/knowledge/)

### cardio
- [201 - Deep dive back into Zone 2 Training](skills/health-os/references/knowledge/cardio/201 - Deep dive back into Zone 2 Training.md)
- [217 ‒ Exercise, VO2 max, and longevity](skills/health-os/references/knowledge/cardio/217 ‒ Exercise, VO2 max, and longevity.md)
- [261 ‒ Training for The Centenarian Decathlon — zone 2, VO2 max, stability, and strength](skills/health-os/references/knowledge/cardio/261 ‒ Training for The Centenarian Decathlon — zone 2, VO2 max, stability, and strength.md)
- [A guide to cardiorespiratory training at any fitness level to improve longevity](skills/health-os/references/knowledge/cardio/A guide to cardiorespiratory training at any fitness level to improve longevity.md)

### muscle
- [Build Muscle & Strength & Forge Your Life Path - Dorian Yates](skills/health-os/references/knowledge/muscle/Build Muscle & Strength & Forge Your Life Path - Dorian Yates.md)
- [Build Your Ideal Physique - Dr. Bret Contreras](skills/health-os/references/knowledge/muscle/Build Your Ideal Physique - Dr. Bret Contreras.md)
- [Dr. Andy Galpin - How to Build Strength, Muscle Size & Endurance](skills/health-os/references/knowledge/muscle/Dr. Andy Galpin - How to Build Strength, Muscle Size & Endurance.md)
- [Dr. Andy Galpin - Optimal Nutrition & Supplementation for Fitness](skills/health-os/references/knowledge/muscle/Dr. Andy Galpin - Optimal Nutrition & Supplementation for Fitness.md)
- [Dr. Duncan French - How to Exercise for Strength Gains & Hormone Optimization](skills/health-os/references/knowledge/muscle/Dr. Duncan French - How to Exercise for Strength Gains & Hormone Optimization.md)
- [Fitness Toolkit - Protocol & Tools to Optimize Physical Health](skills/health-os/references/knowledge/muscle/Fitness Toolkit - Protocol & Tools to Optimize Physical Health.md)
- [Guest Series - Dr. Andy Galpin - How to Build Physical Endurance & Lose Fat](skills/health-os/references/knowledge/muscle/Guest Series - Dr. Andy Galpin - How to Build Physical Endurance & Lose Fat.md)
- [Guest Series - Dr. Andy Galpin - Optimal Protocols to Build Strength & Grow Muscles](skills/health-os/references/knowledge/muscle/Guest Series - Dr. Andy Galpin - Optimal Protocols to Build Strength & Grow Muscles.md)
- [How to Use Exercise to Improve Your Brain’s Health, Longevity & Performance](skills/health-os/references/knowledge/muscle/How to Use Exercise to Improve Your Brain’s Health, Longevity & Performance.md)
- [Jeff Cavaliere - Optimize Your Exercise Program with Science-Based Tools](skills/health-os/references/knowledge/muscle/Jeff Cavaliere - Optimize Your Exercise Program with Science-Based Tools.md)
- [Science of Muscle Growth, Increasing Strength & Muscular Recovery](skills/health-os/references/knowledge/muscle/Science of Muscle Growth, Increasing Strength & Muscular Recovery.md)
- [Science-Supported Tools to Accelerate Your Fitness Goals](skills/health-os/references/knowledge/muscle/Science-Supported Tools to Accelerate Your Fitness Goals.md)

### sleep
- [Dr. Matt Walker - How to Structure Your Sleep, Use Naps & Time Caffeine](skills/health-os/references/knowledge/sleep/Dr. Matt Walker - How to Structure Your Sleep, Use Naps & Time Caffeine.md)
- [Dr. Matt Walker - Improve Sleep to Boost Mood & Emotional Regulation](skills/health-os/references/knowledge/sleep/Dr. Matt Walker - Improve Sleep to Boost Mood & Emotional Regulation.md)
- [Dr. Matt Walker - Protocols to Improve Your Sleep](skills/health-os/references/knowledge/sleep/Dr. Matt Walker - Protocols to Improve Your Sleep.md)
- [Dr. Matt Walker - The Biology of Sleep & Your Unique Sleep Needs](skills/health-os/references/knowledge/sleep/Dr. Matt Walker - The Biology of Sleep & Your Unique Sleep Needs.md)
- [Dr. Matt Walker - The Science of Dreams, Nightmares & Lucid Dreaming](skills/health-os/references/knowledge/sleep/Dr. Matt Walker - The Science of Dreams, Nightmares & Lucid Dreaming.md)
- [Dr. Matt Walker - Using Sleep to Improve Learning, Creativity & Memory](skills/health-os/references/knowledge/sleep/Dr. Matt Walker - Using Sleep to Improve Learning, Creativity & Memory.md)

### metabolism
- [Controlling Sugar Cravings & Metabolism with Science-Based Tools](skills/health-os/references/knowledge/metabolism/Controlling Sugar Cravings & Metabolism with Science-Based Tools.md)
- [Dr. Casey Means - Transform Your Health by Improving Metabolism, Hormone & Blood Sugar Regulation](skills/health-os/references/knowledge/metabolism/Dr. Casey Means - Transform Your Health by Improving Metabolism, Hormone & Blood Sugar Regulation.md)
- [Dr. Charles Zuker - The Biology of Taste Perception & Sugar Craving](skills/health-os/references/knowledge/metabolism/Dr. Charles Zuker - The Biology of Taste Perception & Sugar Craving.md)
- [Dr. Robert Lustig - How Sugar & Processed Foods Impact Your Health](skills/health-os/references/knowledge/metabolism/Dr. Robert Lustig - How Sugar & Processed Foods Impact Your Health.md)
- [Dr. Zachary Knight - The Science of Hunger & Medications to Combat Obesity](skills/health-os/references/knowledge/metabolism/Dr. Zachary Knight - The Science of Hunger & Medications to Combat Obesity.md)
- [Effects of Fasting & Time Restricted Eating on Fat Loss & Health](skills/health-os/references/knowledge/metabolism/Effects of Fasting & Time Restricted Eating on Fat Loss & Health.md)
- [Essentials - Effects of Fasting & Time Restricted Eating on Fat Loss & Health](skills/health-os/references/knowledge/metabolism/Essentials - Effects of Fasting & Time Restricted Eating on Fat Loss & Health.md)
- [Essentials - How to Control Hunger, Eating & Satiety](skills/health-os/references/knowledge/metabolism/Essentials - How to Control Hunger, Eating & Satiety.md)
- [How Different Diets Impact Your Health - Dr. Christopher Gardner](skills/health-os/references/knowledge/metabolism/How Different Diets Impact Your Health - Dr. Christopher Gardner.md)
- [How Our Hormones Control Our Hunger, Eating & Satiety](skills/health-os/references/knowledge/metabolism/How Our Hormones Control Our Hunger, Eating & Satiety.md)
- [How Sugar & Processed Foods Impact Your Health](skills/health-os/references/knowledge/metabolism/How Sugar & Processed Foods Impact Your Health.md)
- [How to Lose Fat & Gain Muscle With Nutrition | Alan Aragon](skills/health-os/references/knowledge/metabolism/How to Lose Fat & Gain Muscle With Nutrition | Alan Aragon.md)
- [How to Lose Fat with Science-Based Tools](skills/health-os/references/knowledge/metabolism/How to Lose Fat with Science-Based Tools.md)
- [Intermittent Fasting to Improve Health, Cognition & Longevity - Dr. Satchin Panda](skills/health-os/references/knowledge/metabolism/Intermittent Fasting to Improve Health, Cognition & Longevity - Dr. Satchin Panda.md)
- [Lose Fat With Science-Based Tools](skills/health-os/references/knowledge/metabolism/Lose Fat With Science-Based Tools.md)
- [The Science of Eating for Health, Fat Loss & Lean Muscle | Dr. Layne Norton](skills/health-os/references/knowledge/metabolism/The Science of Eating for Health, Fat Loss & Lean Muscle | Dr. Layne Norton.md)

### biomarkers
- [229 ‒ Understanding cardiovascular disease risk, cholesterol, and apoB](skills/health-os/references/knowledge/biomarkers/229 ‒ Understanding cardiovascular disease risk, cholesterol, and apoB.md)
- [337- Insulin resistance masterclass — The full body impact of metabolic dysfunction, treatment & more](skills/health-os/references/knowledge/biomarkers/337- Insulin resistance masterclass — The full body impact of metabolic dysfunction, treatment & more.md)
- [What a DEXA can show you about longevity](skills/health-os/references/knowledge/biomarkers/What a DEXA can show you about longevity.md)

### sauna
- [Sauna Benefits Deep Dive and Optimal Use with Dr. Rhonda Patrick & MedCram](skills/health-os/references/knowledge/sauna/Sauna Benefits Deep Dive and Optimal Use with Dr. Rhonda Patrick & MedCram.md)

### dopamine
- [Controlling Your Dopamine For Motivation, Focus & Satisfaction](skills/health-os/references/knowledge/dopamine/Controlling Your Dopamine For Motivation, Focus & Satisfaction.md)
- [Essentials - Understanding & Treating Addiction](skills/health-os/references/knowledge/dopamine/Essentials - Understanding & Treating Addiction.md)

### fitness
- [Dr. Gabrielle Lyon - How to Exercise & Eat for Optimal Health & Longevity](skills/health-os/references/knowledge/fitness/Dr. Gabrielle Lyon - How to Exercise & Eat for Optimal Health & Longevity.md)
- [Dr. Layne Norton - Tools for Nutrition & Fitness](skills/health-os/references/knowledge/fitness/Dr. Layne Norton - Tools for Nutrition & Fitness.md)

