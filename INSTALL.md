# Install: Health OS on a fresh OpenClaw (single machine, GPT)

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

