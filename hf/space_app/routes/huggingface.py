"""POST /api/hf/* — publish a generated agent to Hugging Face Spaces.

Mirrors the official integration paths from huggingface.co/docs/hub:

* **Human-facing Space** — a Gradio (or Docker / Streamlit / static)
  app callable from a browser.
* **API-callable Space** — Gradio's ``/gradio_api/call/*`` surface.
* **Coding-agent compatible** — exposes ``agents.md`` so any coding
  agent can discover the Space.
* **MCP-compatible tool** — registers the Space as a callable tool
  for any MCP client.

The Space is created with `huggingface_hub.HfApi`. The Python SDK is
optional in the import below so the Space backend keeps booting even
if the dependency isn't installed yet (the route 503s with a
descriptive error instead).

Endpoints
---------

* ``POST /api/hf/connect``       store the user's HF token (in-memory).
* ``GET  /api/hf/status``        is the demo connected? whose account?
* ``POST /api/hf/disconnect``    forget the token.
* ``POST /api/hf/validate-space`` check name + warn on missing secrets.
* ``POST /api/hf/publish``       create-or-update Space and push files.
"""

from __future__ import annotations

import json
import os
import re
import textwrap
import threading
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..config import SpaceSettings, get_settings
from ..dependencies import ProjectStore, get_project_store

router = APIRouter(prefix="/api/hf", tags=["huggingface"])


# ── Session store ───────────────────────────────────────────────────


class _HFSession:
    """Process-local HF auth state. Demo only — production should wire
    this through a real secret vault."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._token: str | None = None
        self._username: str | None = None

    def set(self, token: str, username: str | None) -> None:
        with self._lock:
            self._token = token
            self._username = username

    def clear(self) -> None:
        with self._lock:
            self._token = None
            self._username = None

    @property
    def token(self) -> str | None:
        with self._lock:
            return self._token

    @property
    def username(self) -> str | None:
        with self._lock:
            return self._username


_session = _HFSession()


def get_hf_session() -> _HFSession:
    return _session


# ── Schemas ─────────────────────────────────────────────────────────


SDK = Literal["gradio", "docker", "streamlit", "static"]
Visibility = Literal["public", "private"]


class ConnectIn(BaseModel):
    token: str = Field(..., min_length=8, max_length=200)


class ConnectOut(BaseModel):
    connected: bool
    username: str | None
    namespaces: list[str] = []


class ValidateIn(BaseModel):
    namespace: str = Field(..., pattern=r"^[A-Za-z0-9_-]+$", max_length=64)
    space_name: str = Field(..., pattern=r"^[A-Za-z0-9._-]+$", max_length=80)
    sdk: SDK = "gradio"
    visibility: Visibility = "public"
    required_tools: list[str] = Field(default_factory=list)


class ValidateOut(BaseModel):
    available: bool
    warnings: list[str]
    required_secrets: list[str]


class PublishIn(BaseModel):
    project_id: str
    namespace: str = Field(..., pattern=r"^[A-Za-z0-9_-]+$")
    space_name: str = Field(..., pattern=r"^[A-Za-z0-9._-]+$")
    sdk: SDK = "gradio"
    visibility: Visibility = "public"
    enable_agents_md: bool = True
    enable_mcp: bool = True
    require_hf_token: bool = False
    secrets: dict[str, str] = Field(default_factory=dict)
    dry_run: bool = False


class PublishOut(BaseModel):
    status: Literal["published", "would-publish"]
    space_url: str
    agents_url: str
    api_info_url: str
    files_pushed: int
    repo_id: str
    dry_run: bool


# ── Tool → required secret mapping ──────────────────────────────────
TOOL_SECRETS: dict[str, list[str]] = {
    "web_search": ["SERPER_API_KEY"],
    "search": ["SERPER_API_KEY"],
    "email_send": ["SMTP_API_KEY"],
    "email": ["SMTP_API_KEY"],
    "sql_query": ["DATABASE_URL"],
    "sql": ["DATABASE_URL"],
}

PROVIDER_SECRETS: dict[str, list[str]] = {
    "anthropic": ["ANTHROPIC_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "watsonx": ["WATSONX_API_KEY", "WATSONX_PROJECT_ID"],
    "ollabridge": [],
    "ollama": [],
}


def _required_secrets(tools: list[str], provider: str | None) -> list[str]:
    out: list[str] = list(PROVIDER_SECRETS.get(provider or "", [])) or [
        "ANTHROPIC_API_KEY"
    ]
    for t in tools:
        out.extend(TOOL_SECRETS.get(t, []))
    out.append("HF_TOKEN")
    # Stable order, no dupes.
    seen: set[str] = set()
    return [x for x in out if not (x in seen or seen.add(x))]


# ── HF SDK adapter (optional dependency) ────────────────────────────


def _load_hf_api() -> Any:
    try:
        from huggingface_hub import HfApi  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The huggingface_hub package isn't installed in this image. "
                "Add `huggingface_hub` to requirements.txt to enable HF "
                "publishing."
            ),
        ) from exc
    return HfApi


# ── Generated-files helpers ─────────────────────────────────────────


def _render_app_py(name: str, prompt: str, framework: str) -> str:
    """Tiny Gradio app that wraps the generated agent into a Space."""
    safe_prompt = (prompt or "").strip().replace('"""', "'''")
    return textwrap.dedent(
        f'''\
        # Auto-generated by agent-generator for Hugging Face Spaces.
        # Built on top of the {framework} project bundled here.

        from __future__ import annotations

        import os

        import gradio as gr

        TITLE = "{name}"
        DEFAULT_PROMPT = """{safe_prompt}"""


        def run_agent(prompt: str) -> str:
            """Entry point exposed to humans and coding agents alike.

            Replace this body with a real call into your generated
            agent. The default implementation is intentionally trivial
            so the Space boots green out of the box.
            """
            if not prompt.strip():
                prompt = DEFAULT_PROMPT
            return (
                f"agent-generator stub: planned a {{prompt!r}} run.\\n"
                "Wire `src/agent.py` into this function to enable real inference."
            )


        with gr.Blocks(title=TITLE) as demo:
            gr.Markdown(f"# {{TITLE}}\\n\\nAuto-generated agent. POST to "
                        "`/gradio_api/call/run` from any MCP-compatible client.")
            with gr.Row():
                inp = gr.Textbox(label="Prompt", lines=4, value=DEFAULT_PROMPT)
            with gr.Row():
                out = gr.Textbox(label="Result", lines=10)
            btn = gr.Button("Run", variant="primary")
            btn.click(run_agent, inputs=inp, outputs=out, api_name="run")


        if __name__ == "__main__":
            demo.queue().launch(
                server_name="0.0.0.0",
                server_port=int(os.environ.get("PORT", 7860)),
            )
        '''
    )


def _render_requirements_txt(framework: str) -> str:
    base = ["gradio>=4.44,<6", "huggingface_hub>=0.23"]
    fw_map = {
        "crewai": ["crewai>=1.12,<2"],
        "crewflow": ["crewai>=1.12,<2"],
        "langgraph": ["langgraph>=1.1,<2", "langchain-core>=0.1"],
        "react": [],
        "wxo": [],
        "watsonx_orchestrate": [],
        "autogen": ["autogen-agentchat>=0.4"],
        "llamaidx": ["llama-index>=0.12"],
    }
    return "\n".join(base + fw_map.get(framework, []))


def _render_agents_md(name: str, repo_id: str, prompt: str) -> str:
    """Plain-text agent discovery doc per HF's spaces-agents contract."""
    space_subdomain = repo_id.replace("/", "-")
    return textwrap.dedent(
        f"""\
        # {name}

        Auto-generated by agent-generator. Description from the source
        prompt:

        > {prompt or 'No prompt available.'}

        ## API schema
        https://{space_subdomain}.hf.space/gradio_api/info

        ## Call template
        POST /gradio_api/call/run
        Content-Type: application/json

        {{"data": ["<prompt>"]}}

        ## Poll template
        GET  /gradio_api/call/run/<event_id>

        ## Auth
        none
        """
    )


def _render_readme(name: str, namespace: str, sdk: SDK) -> str:
    """README the Space frontmatter parser reads on push."""
    return textwrap.dedent(
        f"""\
        ---
        title: {name}
        emoji: 🤖
        colorFrom: blue
        colorTo: indigo
        sdk: {sdk}
        sdk_version: "4.44.1"
        app_file: app.py
        pinned: false
        license: apache-2.0
        ---

        # {name}

        Auto-generated agent published to `{namespace}/{name}` by
        [agent-generator](https://github.com/ruslanmv/agent-generator).

        ## Endpoints

        * Human UI: this Space's main URL.
        * API: `POST /gradio_api/call/run`
        * Coding-agent discovery: `agents.md`
        """
    )


def _build_publish_files(project: dict[str, Any], req: PublishIn, repo_id: str) -> dict[str, str]:
    """Compose the file dict that gets pushed to the Space.

    Starts from the project's saved artifact bundle, drops any local
    .env, and overlays HF-specific files (`app.py`, `requirements.txt`,
    `README.md`, optional `agents.md`).
    """
    src_files: dict[str, str] = dict(project.get("artifacts", {}).get("files") or {})
    src_files.pop(".env", None)
    src_files.pop(".env.local", None)

    spec = project.get("spec", {}) or {}
    framework = spec.get("framework") or "crewai"
    name = spec.get("name") or req.space_name
    prompt = project.get("prompt") or spec.get("description") or ""

    files: dict[str, str] = {}
    # Move generator-emitted source files under src/ so app.py is the
    # canonical Space entry-point.
    for path, body in src_files.items():
        if path in {"README.md", "Dockerfile", "app.py", "requirements.txt", "agents.md"}:
            continue
        files[f"src/{path}"] = body

    files["app.py"] = _render_app_py(name, prompt, framework)
    files["requirements.txt"] = _render_requirements_txt(framework)
    files["README.md"] = _render_readme(name, req.namespace, req.sdk)
    if req.enable_agents_md:
        files["agents.md"] = _render_agents_md(name, repo_id, prompt)
    # Always include a .env.example shape so users know what to set.
    files[".env.example"] = "\n".join(
        f"{k}=" for k in _required_secrets(_project_tools(project), _project_provider(project))
    )
    return files


def _project_tools(project: dict[str, Any]) -> list[str]:
    spec = project.get("spec") or {}
    out: list[str] = []
    seen: set[str] = set()
    for tool in spec.get("tools") or []:
        tid = tool.get("template") or tool.get("id")
        if tid and tid not in seen:
            seen.add(tid)
            out.append(tid)
    for agent in spec.get("agents") or []:
        for tid in agent.get("tools") or []:
            if tid not in seen:
                seen.add(tid)
                out.append(tid)
    return out


def _project_provider(project: dict[str, Any]) -> str | None:
    return (project.get("spec") or {}).get("llm", {}).get("provider")


# ── Routes ──────────────────────────────────────────────────────────


@router.post("/connect", response_model=ConnectOut)
async def connect(body: ConnectIn, session: Annotated[_HFSession, Depends(get_hf_session)]) -> ConnectOut:
    if not re.match(r"^hf_[A-Za-z0-9_]+$", body.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token doesn't look like a Hugging Face access token (expected `hf_…`).",
        )
    HfApi = _load_hf_api()
    api = HfApi(token=body.token)
    try:
        whoami = api.whoami()
    except Exception as exc:  # noqa: BLE001 — surface upstream error verbatim
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token rejected by Hugging Face: {exc}",
        ) from exc
    username = whoami.get("name") if isinstance(whoami, dict) else None
    session.set(body.token, username)
    namespaces = [username] if username else []
    # Add org memberships too so the picker can show them.
    if isinstance(whoami, dict):
        for o in whoami.get("orgs") or []:
            n = o.get("name") if isinstance(o, dict) else None
            if n and n not in namespaces:
                namespaces.append(n)
    return ConnectOut(connected=True, username=username, namespaces=namespaces)


@router.get("/status", response_model=ConnectOut)
async def conn_status(session: Annotated[_HFSession, Depends(get_hf_session)]) -> ConnectOut:
    if not session.token:
        return ConnectOut(connected=False, username=None, namespaces=[])
    return ConnectOut(
        connected=True,
        username=session.username,
        namespaces=[session.username] if session.username else [],
    )


@router.post("/disconnect", response_model=ConnectOut)
async def disconnect(session: Annotated[_HFSession, Depends(get_hf_session)]) -> ConnectOut:
    session.clear()
    return ConnectOut(connected=False, username=None, namespaces=[])


@router.post("/validate-space", response_model=ValidateOut)
async def validate_space(
    body: ValidateIn,
    session: Annotated[_HFSession, Depends(get_hf_session)],
) -> ValidateOut:
    warnings: list[str] = []
    available = True

    if session.token:
        HfApi = _load_hf_api()
        api = HfApi(token=session.token)
        repo_id = f"{body.namespace}/{body.space_name}"
        try:
            # If the repo already exists, publishing will update it.
            api.repo_info(repo_id=repo_id, repo_type="space")
            warnings.append(
                f"Space {repo_id} already exists — publish will update it in place."
            )
        except Exception:  # noqa: BLE001 — 404 / 401 both fall here
            available = True
    else:
        warnings.append(
            "Not connected — sign in or paste a Hugging Face token to enable availability checks."
        )

    return ValidateOut(
        available=available,
        warnings=warnings,
        required_secrets=_required_secrets(body.required_tools, None),
    )


@router.post("/publish", response_model=PublishOut)
async def publish(
    body: PublishIn,
    session: Annotated[_HFSession, Depends(get_hf_session)],
    store: Annotated[ProjectStore, Depends(get_project_store)],
    settings: Annotated[SpaceSettings, Depends(get_settings)],
) -> PublishOut:
    project = store.get(body.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "project not found — the demo store is volatile, "
                "regenerate the project before publishing."
            ),
        )

    repo_id = f"{body.namespace}/{body.space_name}"
    files = _build_publish_files(project, body, repo_id)
    space_url = f"https://huggingface.co/spaces/{repo_id}"
    api_info_url = f"https://{repo_id.replace('/', '-')}.hf.space/gradio_api/info"
    agents_url = f"{space_url}/raw/main/agents.md"

    if body.dry_run or not session.token:
        return PublishOut(
            status="would-publish",
            space_url=space_url,
            agents_url=agents_url,
            api_info_url=api_info_url,
            files_pushed=len(files),
            repo_id=repo_id,
            dry_run=True,
        )

    HfApi = _load_hf_api()
    api = HfApi(token=session.token)

    try:
        api.create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk=body.sdk,
            private=(body.visibility == "private"),
            exist_ok=True,
        )
        for path, contents in files.items():
            api.upload_file(
                path_or_fileobj=contents.encode("utf-8"),
                path_in_repo=path,
                repo_id=repo_id,
                repo_type="space",
                commit_message=f"agent-generator: publish {path}",
            )
        # Configure Space secrets — only the ones the user supplied.
        for name, value in (body.secrets or {}).items():
            if not value or value in {"********", ""}:
                continue
            try:
                api.add_space_secret(repo_id=repo_id, key=name, value=value)
            except Exception:  # noqa: BLE001 — best effort
                pass
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hugging Face publish failed: {exc}",
        ) from exc

    return PublishOut(
        status="published",
        space_url=space_url,
        agents_url=agents_url,
        api_info_url=api_info_url,
        files_pushed=len(files),
        repo_id=repo_id,
        dry_run=False,
    )
