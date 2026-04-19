# Content disclaimer
Majority of this repo was created by an amazing Vlad Kuklev - my AI-bro. He deserves all the credit. 
I'll be doing minor incremental improvements over this repo, so you might need to occasioanlly check for updates

# Health OS for OpenClaw (GPT)

Drop-in Health OS workflow for a **single-machine OpenClaw** install, using **OpenAI (GPT) models**.

## Install (fast path)

From this repo folder:

```bash
./install.sh --workspace /path/to/openclaw/workspace --openai-api-key "$OPENAI_API_KEY"
# optionally:
#   --model openai/gpt-5.4
```

Then restart if needed:

```bash
openclaw gateway restart
```

## Docs

- `MANUAL.md`
- `INSTALL.md`
- `QUICKSTART.md`

