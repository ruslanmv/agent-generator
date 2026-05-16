# Hello-world agent · OllaBridge Cloud

A two-file CrewAI starter that proves the end-to-end loop:

1. `agent-generator` scaffolds an agent (CLI flow).
2. `pair_ollabridge.py` exchanges a short-lived **pairing code** for a
   long-lived **device token**.
3. `hello_world.py` runs the agent with its LLM pointed at
   [OllaBridge Cloud](https://ruslanmv-ollabridge.hf.space) (an
   OpenAI-compatible `/v1` endpoint).

## 0. Install agent-generator

```sh
make install                 # runs `pip install -e .`
# or:
pip install -e .
```

## 1. (Already done) Generate the skeleton

The `hello_world.py` in this directory was generated with:

```sh
agent-generator \
  "A friendly hello-world agent that greets the user by name, then asks a question and prints the answer." \
  --framework crewai --provider watsonx --dry-run --output hello_world.py
```

Then patched to point CrewAI's `LLM` at OllaBridge instead of watsonx —
see the `LLM(...)` call near the top of the file.

## 2. Pair this device with OllaBridge

In the OllaBridge console:

> **Server URL** `https://ruslanmv-ollabridge.hf.space`
> **Pairing Code** `GKEV-8985` *(short-lived, ~10 minute TTL)*

```sh
cp .env.example .env
python pair_ollabridge.py GKEV-8985
```

The helper `POST`s the code to `/device/pair-simple` and writes the
returned `device_token` into `.env` as `OLLABRIDGE_TOKEN`. Get a fresh
code from the console if pairing fails with `Pairing code expired`.

## 3. Run

```sh
python hello_world.py
```

You should see CrewAI announce the agent, the task description, and the
LLM response streamed from OllaBridge.

## How the LLM is wired

CrewAI delegates LLM calls to LiteLLM. Anything prefixed with
`openai/...` is sent through the OpenAI-compatible client, which means
**any** `/v1/chat/completions` server (incl. OllaBridge and Ollama)
works without an extra adapter:

```python
from crewai import LLM
ollabridge_llm = LLM(
    model=f"openai/{OLLABRIDGE_MODEL}",     # e.g. "openai/qwen2.5:1.5b"
    base_url=f"{OLLABRIDGE_BASE_URL}/v1",   # e.g. "https://ruslanmv-ollabridge.hf.space/v1"
    api_key=OLLABRIDGE_TOKEN,               # the device token from pairing
)
```

Pass the `LLM` to each `Agent(..., llm=ollabridge_llm)` and CrewAI does
the rest.

## Files in this folder

| File | Purpose |
|------|---------|
| `hello_world.py` | The CrewAI agent + crew, wired to OllaBridge. |
| `pair_ollabridge.py` | One-shot helper that exchanges a pairing code for a device token and writes `.env`. |
| `.env.example` | Template — copy to `.env`. |
| `README.md` | This file. |
