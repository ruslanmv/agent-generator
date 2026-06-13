"""Matrix engine HTTP facade (Batch 9).

A thin, **stateless** FastAPI app over ``AgentGenerator``: each endpoint is a direct wrapper
around an SDK method. Matrix Builder can call the engine over HTTP (when it doesn't want the
in-process SDK) by POSTing the inputs each method needs; the engine holds no state, so Matrix
Builder remains the system of record for bundles and versions.

Run standalone:  ``uvicorn agent_generator.http.app:app``
Mount in a backend:  ``backend_app.mount("/engine", create_app())``
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.responses import Response

from agent_generator import __version__
from agent_generator.contracts.batch import BatchPlan
from agent_generator.contracts.blueprint import BlueprintCandidateResponse
from agent_generator.contracts.bundle import MatrixBundle
from agent_generator.contracts.common import CoderId
from agent_generator.contracts.idea import IdeaIntent, IdeaRequest
from agent_generator.contracts.prompt_pack import CoderHandoff, PromptResponse
from agent_generator.contracts.validation import ValidationReport
from agent_generator.contracts.versioning import RegenerationResult
from agent_generator.control import Submission, diff_submissions
from agent_generator.engine import AgentGenerator
from agent_generator.http.models import (
    BatchPlanApiRequest,
    BatchPromptApiRequest,
    BundleRequest,
    CandidateSelection,
    DiffApiRequest,
    ExportRequest,
    PromptRequest,
    RegenerationApiRequest,
    ValidationApiRequest,
)


def get_engine(request: Request) -> AgentGenerator:
    return request.app.state.engine


def create_app(engine: AgentGenerator | None = None) -> FastAPI:
    app = FastAPI(title="agent-generator Matrix Engine API", version=__version__)
    app.state.engine = engine or AgentGenerator()

    @app.get("/health", tags=["health"])
    def health(eng: AgentGenerator = Depends(get_engine)) -> dict:
        return {
            "status": "ok",
            "engine": "agent-generator",
            "version": __version__,
            "sdk": eng.status(),
        }

    # --- standards ---------------------------------------------------------
    @app.get("/api/v1/standards/current", tags=["standards"])
    def standards_current(eng: AgentGenerator = Depends(get_engine)) -> dict:
        return eng.standards_metadata()

    # --- ideas -------------------------------------------------------------
    @app.post("/api/v1/ideas/parse", response_model=IdeaIntent, tags=["ideas"])
    def parse_idea(body: IdeaRequest, eng: AgentGenerator = Depends(get_engine)) -> IdeaIntent:
        return eng.parse_idea(body)

    # --- blueprints --------------------------------------------------------
    @app.post(
        "/api/v1/blueprints/candidates",
        response_model=BlueprintCandidateResponse,
        tags=["blueprints"],
    )
    def candidates(
        body: IdeaRequest, eng: AgentGenerator = Depends(get_engine)
    ) -> BlueprintCandidateResponse:
        return BlueprintCandidateResponse(candidates=eng.generate_blueprint_candidates(body))

    @app.post("/api/v1/blueprints", tags=["blueprints"])
    def blueprint(body: CandidateSelection, eng: AgentGenerator = Depends(get_engine)):
        return eng.generate_controlled_blueprint(body.idea_request, candidate_id=body.candidate_id)

    @app.post(
        "/api/v1/blueprints/regenerate", response_model=RegenerationResult, tags=["blueprints"]
    )
    def regenerate(
        body: RegenerationApiRequest, eng: AgentGenerator = Depends(get_engine)
    ) -> RegenerationResult:
        return eng.regenerate(
            body.base_blueprint,
            body.change_request,
            body.change_type,
            current_version=body.current_version,
        )

    # --- batches + commits (Continue build) --------------------------------
    @app.post("/api/v1/batches/plan", response_model=BatchPlan, tags=["batches"])
    def plan_batch(
        body: BatchPlanApiRequest, eng: AgentGenerator = Depends(get_engine)
    ) -> BatchPlan:
        return eng.plan_batch(
            body.blueprint,
            body.goal_md,
            body.change_type,
            ordinal=body.ordinal,
            parent_commit=body.parent_commit,
        )

    @app.post("/api/v1/batches/prompt-packs", tags=["batches"])
    def batch_prompt_packs(
        body: BatchPromptApiRequest, eng: AgentGenerator = Depends(get_engine)
    ) -> dict:
        coders = body.coders or list(CoderId)
        handoffs: list[CoderHandoff] = [
            eng.coder_handoff(
                body.blueprint,
                coder,
                batch=body.batch,
                bundle_id=body.bundle_id,
                bundle_url=body.bundle_url,
            )
            for coder in coders
        ]
        return {"handoffs": [h.model_dump() for h in handoffs]}

    @app.post("/api/v1/commits/diff", tags=["commits"])
    def commits_diff(body: DiffApiRequest) -> dict:
        base = Submission(
            files=body.base_files, changed_paths=tuple(sorted(body.base_files)), has_full_tree=True
        )
        head = Submission(
            files=body.head_files, changed_paths=tuple(sorted(body.head_files)), has_full_tree=True
        )
        diff = diff_submissions(base, head)
        return {
            "added": diff.added,
            "changed": diff.changed,
            "deleted": diff.deleted,
            "patch": diff.patch,
        }

    # --- bundles + prompts -------------------------------------------------
    @app.post("/api/v1/bundles", response_model=MatrixBundle, tags=["bundles"])
    def bundle(body: BundleRequest, eng: AgentGenerator = Depends(get_engine)) -> MatrixBundle:
        return eng.generate_matrix_bundle(body.blueprint, preferred_coder=body.preferred_coder)

    @app.post("/api/v1/prompts", response_model=PromptResponse, tags=["bundles"])
    def prompt(body: PromptRequest, eng: AgentGenerator = Depends(get_engine)) -> PromptResponse:
        return eng.generate_coder_prompt_pack(
            body.bundle_id or "bundle", body.coder, body.bundle_url, blueprint=body.blueprint
        )

    # --- validations -------------------------------------------------------
    @app.post("/api/v1/validations", response_model=ValidationReport, tags=["validations"])
    def validate(
        body: ValidationApiRequest, eng: AgentGenerator = Depends(get_engine)
    ) -> ValidationReport:
        return eng.validate_ai_coder_patch(
            body.bundle_id,
            request=body.request,
            blueprint=body.blueprint,
            patch=body.patch,
            current_version=body.current_version,
        )

    # --- artifacts ---------------------------------------------------------
    @app.post("/api/v1/exports", tags=["artifacts"])
    def export(body: ExportRequest, eng: AgentGenerator = Depends(get_engine)) -> Response:
        from agent_generator.artifacts import zip_bytes

        compiled = eng.compile_bundle(
            body.blueprint, version=body.version, preferred_coder=body.preferred_coder
        )
        data = zip_bytes(compiled.file_map())
        filename = f"{body.blueprint.slug}-{body.version}.zip"
        return Response(
            content=data,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Matrix-Contract-Hash": compiled.contract_hash,
            },
        )

    return app


#: Module-level app for ``uvicorn agent_generator.http.app:app``.
app = create_app()

__all__ = ["create_app", "get_engine", "app"]
