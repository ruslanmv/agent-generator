"""Compatibility matrix endpoint.

The frontend, the Marketplace, and the CLI all need to agree on which
framework / hyperscaler / orchestration-pattern / model / export-target
combinations are valid. To avoid two sources of truth, the backend
mirrors ``frontend/src/lib/{hyperscalers,frameworks,orchestration,models,
compatibility}.ts`` here and exposes the same diagnostics function over
HTTP.

Contract: if you change a rule in TypeScript, change it here too (and
add a parity test in ``backend/tests/test_compatibility.py`` — the
wider end-to-end parity check lands in Batch 30).
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/compatibility", tags=["compatibility"])

# ── enums (mirror lib/hyperscalers.ts + lib/frameworks.ts) ──────────────

HyperscalerId = Literal["azure", "aws", "gcp", "ibm", "on_prem"]
VendorId = Literal[
    "microsoft", "amazon", "google", "ibm", "langchain", "crewai", "community"
]
FrameworkId = Literal[
    "autogen", "strands", "langgraph", "crewai", "wxo", "crewflow", "react", "llamaidx"
]
PhilosophyId = Literal["brainstorm", "pipeline", "graph"]
OrchestrationPatternId = Literal["supervisor", "react"]
PatternSupport = Literal["native", "adapter", "unsupported"]
ExportTargetId = Literal[
    "azure-ai", "bedrock", "docker", "hf", "zip", "github", "watsonx"
]
DiagnosticSeverity = Literal["ok", "warn", "err"]


# ── catalogues ──────────────────────────────────────────────────────────


class Hyperscaler(BaseModel):
    id: HyperscalerId
    label: str
    short: str
    brand: str
    vendor: VendorId


HYPERSCALERS: list[Hyperscaler] = [
    Hyperscaler(id="azure",   label="Azure",   short="AZ",  brand="#0078d4", vendor="microsoft"),
    Hyperscaler(id="aws",     label="AWS",     short="AWS", brand="#ff9900", vendor="amazon"),
    Hyperscaler(id="gcp",     label="GCP",     short="GCP", brand="#34a853", vendor="google"),
    Hyperscaler(id="ibm",     label="IBM",     short="IBM", brand="#054ada", vendor="ibm"),
    Hyperscaler(id="on_prem", label="On-prem", short="OP",  brand="#161616", vendor="community"),
]

VENDOR_LABEL: dict[VendorId, str] = {
    "microsoft": "Microsoft",
    "amazon":    "AWS",
    "google":    "Google",
    "ibm":       "IBM",
    "langchain": "LangChain",
    "crewai":    "CrewAI",
    "community": "community",
}


class FrameworkPattern(BaseModel):
    summary: str
    risk: str
    glyph: PhilosophyId


class Framework(BaseModel):
    id: FrameworkId
    name: str
    vendor: VendorId
    philosophy: PhilosophyId
    pattern: FrameworkPattern
    hyperscalers: list[HyperscalerId]
    stage: Literal["core", "beta", "new"]


FRAMEWORKS: list[Framework] = [
    Framework(
        id="autogen", name="AutoGen", vendor="microsoft", philosophy="brainstorm",
        pattern=FrameworkPattern(
            summary="Free back-and-forth — write, critique, fix.",
            risk="May argue forever or drift off-topic if not monitored.",
            glyph="brainstorm",
        ),
        hyperscalers=["azure", "on_prem"], stage="beta",
    ),
    Framework(
        id="strands", name="Strands", vendor="amazon", philosophy="pipeline",
        pattern=FrameworkPattern(
            summary="Assembly line — output of one agent feeds the next.",
            risk="A bad step taints every downstream agent.",
            glyph="pipeline",
        ),
        hyperscalers=["aws", "on_prem"], stage="new",
    ),
    Framework(
        id="langgraph", name="LangGraph", vendor="langchain", philosophy="graph",
        pattern=FrameworkPattern(
            summary="Industrial process — explicit state machine with gated branches.",
            risk="Higher design cost; every transition must be modeled.",
            glyph="graph",
        ),
        hyperscalers=["azure", "aws", "gcp", "ibm", "on_prem"], stage="core",
    ),
    Framework(
        id="crewai", name="CrewAI", vendor="crewai", philosophy="pipeline",
        pattern=FrameworkPattern(
            summary="Role-based crews — supervisor delegates to specialists.",
            risk="Linear hand-offs; limited self-correction.",
            glyph="pipeline",
        ),
        hyperscalers=["azure", "aws", "gcp", "ibm", "on_prem"], stage="core",
    ),
    Framework(
        id="wxo", name="watsonx Orchestrate", vendor="ibm", philosophy="pipeline",
        pattern=FrameworkPattern(
            summary="Enterprise skills — supervisor routes to typed skills.",
            risk="IBM cloud-centric; limited multi-vendor reach.",
            glyph="pipeline",
        ),
        hyperscalers=["ibm"], stage="core",
    ),
    Framework(
        id="crewflow", name="CrewAI Flow", vendor="crewai", philosophy="graph",
        pattern=FrameworkPattern(
            summary="Event-driven flow with named transitions.",
            risk="Newer API; fewer community recipes.",
            glyph="graph",
        ),
        hyperscalers=["azure", "aws", "gcp", "on_prem"], stage="beta",
    ),
    Framework(
        id="react", name="ReAct", vendor="community", philosophy="brainstorm",
        pattern=FrameworkPattern(
            summary="Reason → Act → Observe loop.",
            risk="Loops may stall without explicit termination.",
            glyph="brainstorm",
        ),
        hyperscalers=["azure", "aws", "gcp", "ibm", "on_prem"], stage="core",
    ),
    Framework(
        id="llamaidx", name="LlamaIndex", vendor="community", philosophy="graph",
        pattern=FrameworkPattern(
            summary="Data-centric agents over RAG pipelines.",
            risk="Best for retrieval; limited multi-step tool use.",
            glyph="graph",
        ),
        hyperscalers=["azure", "aws", "gcp", "ibm", "on_prem"], stage="beta",
    ),
]

EXPORT_BY_FW: dict[FrameworkId, list[ExportTargetId] | Literal["*"]] = {
    "autogen":   ["azure-ai", "docker", "hf", "zip", "github"],
    "strands":   ["bedrock", "docker", "zip", "github"],
    "langgraph": "*",
    "crewai":    "*",
    "llamaidx":  "*",
    "react":     "*",
    "crewflow":  "*",
    "wxo":       ["watsonx", "docker", "github"],
}


class OrchestrationPattern(BaseModel):
    id: OrchestrationPatternId
    label: str
    glyph: str
    blurb: str
    steps: list[str]
    axes: dict[str, str]


ORCHESTRATION_PATTERNS: list[OrchestrationPattern] = [
    OrchestrationPattern(
        id="supervisor", label="Supervisor", glyph="⊕",
        blurb="One supervisor coordinates multiple workers.",
        steps=[
            "Receive the task from the user.",
            "Pick which specialised agent to call.",
            "Pass one agent's output as input to the next.",
            "Own the overall flow.",
        ],
        axes={
            "flow": "The chief agent",
            "communication": "Direct, top-down",
            "flexibility": "low",
            "predictability": "high",
            "cost": "low",
        },
    ),
    OrchestrationPattern(
        id="react", label="ReAct", glyph="◎",
        blurb="Reason → Act → Observe → Re-reason. Optionally over shared state.",
        steps=[
            "Reason about the problem.",
            "Act (call a tool or another agent).",
            "Observe the result.",
            "Re-reason and decide the next step.",
        ],
        axes={
            "flow": "State + each agent autonomously",
            "communication": "Via shared state (multi-agent)",
            "flexibility": "high",
            "predictability": "low",
            "cost": "high",
        },
    ),
]

PATTERN_BY_FW: dict[FrameworkId, dict[OrchestrationPatternId, PatternSupport]] = {
    "langgraph": {"supervisor": "native",      "react": "native"},
    "autogen":   {"supervisor": "native",      "react": "adapter"},
    "strands":   {"supervisor": "native",      "react": "unsupported"},
    "crewai":    {"supervisor": "native",      "react": "adapter"},
    "crewflow":  {"supervisor": "native",      "react": "adapter"},
    "react":     {"supervisor": "unsupported", "react": "native"},
    "wxo":       {"supervisor": "native",      "react": "unsupported"},
    "llamaidx":  {"supervisor": "adapter",     "react": "native"},
}


class Model(BaseModel):
    id: str
    label: str
    provider: Literal["openai", "anthropic", "watsonx", "ollama", "ollabridge"]
    hyperscalers: list[HyperscalerId]
    context_window: str = Field(alias="contextWindow")
    cost: Literal["free", "$", "$$", "$$$"]

    model_config = {"populate_by_name": True}


MODELS: list[Model] = [
    Model(
        id="gpt-5.1", label="GPT-5.1", provider="openai",
        hyperscalers=["azure"], contextWindow="256k", cost="$$$",
    ),
    Model(
        id="gpt-4o", label="GPT-4o", provider="openai",
        hyperscalers=["azure"], contextWindow="128k", cost="$$",
    ),
    Model(
        id="claude-opus-4", label="Claude Opus 4", provider="anthropic",
        hyperscalers=["azure", "aws", "on_prem"], contextWindow="500k", cost="$$$",
    ),
    Model(
        id="claude-haiku-4", label="Claude Haiku 4", provider="anthropic",
        hyperscalers=["azure", "aws", "on_prem"], contextWindow="200k", cost="$",
    ),
    Model(
        id="granite-3.1-70b", label="Granite 3.1 70B", provider="watsonx",
        hyperscalers=["ibm"], contextWindow="128k", cost="$$",
    ),
    Model(
        id="llama-3.1-70b", label="Llama 3.1 70B", provider="ollama",
        hyperscalers=["on_prem"], contextWindow="128k", cost="$",
    ),
    Model(
        id="qwen-2.5-1.5b", label="Qwen 2.5 1.5B", provider="ollabridge",
        hyperscalers=["on_prem"], contextWindow="32k", cost="free",
    ),
]


# ── diagnostics ─────────────────────────────────────────────────────────


class WizardCompatibilityState(BaseModel):
    framework: FrameworkId
    hyperscaler: HyperscalerId | None = None
    pattern: OrchestrationPatternId | None = None
    model: str | None = None
    tools: list[str] = Field(default_factory=list)


class Diagnostic(BaseModel):
    category: str
    value: str
    sub: str
    severity: DiagnosticSeverity
    step: int


_PATTERN_SEVERITY: dict[PatternSupport, DiagnosticSeverity] = {
    "native": "ok", "adapter": "warn", "unsupported": "err",
}

_ALL_EXPORTS: list[ExportTargetId] = ["azure-ai", "bedrock", "docker", "hf"]


def _framework(fw_id: FrameworkId) -> Framework:
    for f in FRAMEWORKS:
        if f.id == fw_id:
            return f
    return FRAMEWORKS[2]  # LangGraph fallback


def compatibility_for(state: WizardCompatibilityState) -> list[Diagnostic]:
    """Mirror of `frontend/src/lib/compatibility.ts::compatibilityFor`."""
    fw = _framework(state.framework)
    out: list[Diagnostic] = [
        Diagnostic(category="Framework", value=fw.name,
                   sub=VENDOR_LABEL[fw.vendor], severity="ok", step=2),
    ]

    if state.hyperscaler:
        native = state.hyperscaler in fw.hyperscalers
        h = next((x for x in HYPERSCALERS if x.id == state.hyperscaler), None)
        out.append(Diagnostic(
            category="Hyperscaler",
            value=h.label if h else state.hyperscaler,
            sub="native" if native else "via adapter",
            severity="ok" if native else "warn",
            step=2,
        ))

    if state.pattern:
        support = PATTERN_BY_FW.get(fw.id, {}).get(state.pattern, "unsupported")
        p = next((x for x in ORCHESTRATION_PATTERNS if x.id == state.pattern), None)
        out.append(Diagnostic(
            category="Orchestration",
            value=p.label if p else state.pattern,
            sub=support,
            severity=_PATTERN_SEVERITY[support],
            step=2,
        ))

    if state.model:
        m = next((x for x in MODELS if x.id == state.model), None)
        if m:
            native = (not state.hyperscaler) or (state.hyperscaler in m.hyperscalers)
            out.append(Diagnostic(
                category="Model",
                value=m.label,
                sub=f"{m.provider}{' · native' if native else ' · via adapter'}",
                severity="ok" if native else "warn",
                step=2,
            ))

    for t in (state.tools or [])[:3]:
        incompatible = fw.id == "strands" and t == "voice"
        out.append(Diagnostic(
            category="Tool", value=t,
            sub="requires Strands · adapter" if incompatible else "ok",
            severity="warn" if incompatible else "ok",
            step=3,
        ))

    allowed = EXPORT_BY_FW[fw.id]
    for target in _ALL_EXPORTS:
        ok = allowed == "*" or target in allowed
        if ok:
            out.append(Diagnostic(category="Export", value=target,
                                  sub="available", severity="ok", step=4))
        else:
            assert allowed != "*"
            preview = " / ".join(allowed[:2])
            out.append(Diagnostic(
                category="Export", value=target,
                sub=f"requires {preview}", severity="err", step=4,
            ))

    return out


# ── routes ──────────────────────────────────────────────────────────────


class Catalogue(BaseModel):
    hyperscalers: list[Hyperscaler]
    frameworks: list[Framework]
    orchestration_patterns: list[OrchestrationPattern]
    models: list[Model]
    export_by_framework: dict[FrameworkId, list[ExportTargetId] | Literal["*"]]
    pattern_by_framework: dict[FrameworkId, dict[OrchestrationPatternId, PatternSupport]]


@router.get("/catalogue", response_model=Catalogue)
def catalogue() -> Catalogue:
    """Single source of truth for the wizard / Marketplace facets."""
    return Catalogue(
        hyperscalers=HYPERSCALERS,
        frameworks=FRAMEWORKS,
        orchestration_patterns=ORCHESTRATION_PATTERNS,
        models=MODELS,
        export_by_framework=EXPORT_BY_FW,
        pattern_by_framework=PATTERN_BY_FW,
    )


@router.post("/diagnose", response_model=list[Diagnostic])
def diagnose(state: WizardCompatibilityState) -> list[Diagnostic]:
    """Run the diagnostics function the Review · Compatibility card uses."""
    return compatibility_for(state)
