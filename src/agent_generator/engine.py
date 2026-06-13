"""Public engine facade — ``agent_generator.engine.AgentGenerator``.

This is the stable SDK surface Matrix Builder imports in SDK mode. Its method *names and
return shapes* are a cross-repo contract: Matrix Builder's
``services/api/app/integrations/agent_generator_adapter.py`` probes for and calls

* ``parse_idea``
* ``generate_blueprint_candidates``
* ``generate_controlled_blueprint``
* ``generate_matrix_bundle``
* ``generate_coder_prompt_pack``
* ``validate_ai_coder_patch``

Do not rename or change the signatures of those six without a coordinated update in
matrix-builder. The richer methods (``build_prompt_pack``, ``generate_repair_prompt``,
``compile_bundle``, ``export_zip``, ``regenerate``, ``status``, ``info``) are additive.

Scope note: generation is template-aware (Batch 4) with a keyword-planner fallback;
standards are loaded and pinned (Batch 3); blueprints compile to a full, hash-locked file
plan (Batch 5); and ``regenerate`` produces new versions without mutating the original.
Real SBOM/signing (Batch 6/10), per-coder adapters (Batch 7), and full drift detection
(Batch 8) deepen these methods without changing the surface.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from agent_generator import __version__
from agent_generator.artifacts import write_strict_zip
from agent_generator.blueprints.batch_planner import plan_batch, plan_repair_batch
from agent_generator.blueprints.candidate_generator import generate_candidates
from agent_generator.blueprints.idea_parser import parse_idea_request
from agent_generator.blueprints.regeneration import regenerate_blueprint
from agent_generator.coder_adapters import PromptContext, get_adapter, render_prompt
from agent_generator.contracts import (
    CONTRACTS_VERSION,
    ApiRoute,
    BlueprintCandidate,
    BlueprintResult,
    BlueprintStack,
    BlueprintTask,
    BundleFile,
    CoderHandoff,
    CoderId,
    IdeaIntent,
    IdeaRequest,
    MatrixBundle,
    PromptItem,
    PromptPack,
    PromptResponse,
    QualityLevel,
    ValidationCheck,
    ValidationReport,
    ValidationStatus,
)
from agent_generator.contracts.batch import BatchChangeType, BatchPlan
from agent_generator.contracts.commit import CommitManifest
from agent_generator.contracts.projectspec_adapter import (
    idea_to_project_spec,
    project_spec_to_stack,
    project_spec_to_tasks,
)
from agent_generator.contracts.publication import PublicationResponse
from agent_generator.contracts.standards import StandardsLock
from agent_generator.contracts.versioning import ChangeType, RegenerationResult
from agent_generator.control import (
    DiffResult,
    Submission,
    build_commit_manifest,
    build_contract_spec,
    build_repair_prompt,
    diff_submissions,
    from_patch,
    from_request,
    scan_repo,
    scan_zip,
    tree_hash,
    validate_submission,
)
from agent_generator.errors import CandidateNotFoundError, StandardsError
from agent_generator.frameworks import FRAMEWORKS
from agent_generator.publishing import build_publication
from agent_generator.release import add_release_evidence
from agent_generator.result import EngineInfo, EngineStatus
from agent_generator.runtime import EngineMode, EngineRuntime
from agent_generator.standards import (
    StandardsRegistry,
    build_standards_lock,
    render_lock_yaml,
)
from agent_generator.standards.models import StandardsPack
from agent_generator.template_compiler import CompiledBundle, compile_blueprint

#: Matrix control files emitted for every controlled blueprint, in canonical order.
CONTROL_FILES = (
    "MATRIX_BLUEPRINT.yaml",
    "MATRIX_STANDARDS.lock",
    "MATRIX_TASKS.md",
    "MATRIX_ALLOWED_CHANGES.md",
    "MATRIX_ACCEPTANCE_CRITERIA.md",
    "MATRIX_VALIDATION.md",
)

#: Files an AI coder must never modify (the immutable contract surface).
FORBIDDEN_CHANGES = (
    "MATRIX_BLUEPRINT.yaml",
    "MATRIX_STANDARDS.lock",
    ".github/workflows/",
)

_REQUIRED_FILES = (
    "README.md",
    *CONTROL_FILES,
    "docs/architecture.md",
    "docs/security.md",
    "docs/standards-report.md",
)

#: AI-coder-control rules (RMD-1xx) every controlled prompt cites when no lock is available.
_DEFAULT_CODER_RULES = ("RMD-101", "RMD-103", "RMD-105", "RMD-107", "RMD-108", "RMD-118", "RMD-119")
_RMD_1XX = re.compile(r"^RMD-1\d\d$")


class AgentGenerator:
    """Deterministic Matrix Builder engine facade.

    Construct with no arguments for the default deterministic mode (no credentials, no
    network). Pass ``mode=EngineMode.LLM`` to allow LLM-assisted planning when a provider
    is configured, or ``fixed_now=`` to pin timestamps for snapshot tests.
    """

    def __init__(
        self,
        *,
        mode: EngineMode | str = EngineMode.AUTO,
        fixed_now: Any | None = None,
        standards_root: str | Path | None = None,
        verify_standards: bool = True,
        signature_mode: str = "warn",
    ) -> None:
        self.runtime = EngineRuntime(mode, fixed_now=fixed_now)
        self.standards = StandardsRegistry(
            standards_root, verify=verify_standards, signature_mode=signature_mode
        )

    # ------------------------------------------------------------------ #
    # Introspection
    # ------------------------------------------------------------------ #
    def status(self) -> dict[str, str]:
        """Return the engine status payload (shape matches the Matrix Builder adapter)."""
        return EngineStatus(
            mode="sdk",
            status="ready",
            engine="agent-generator",
        ).as_dict()

    def info(self) -> EngineInfo:
        return EngineInfo(
            engine="agent-generator",
            package_version=__version__,
            api_version="1",
            contracts_version=CONTRACTS_VERSION,
            frameworks=sorted(FRAMEWORKS.keys()),
            capabilities=[
                "parse_idea",
                "generate_blueprint_candidates",
                "generate_controlled_blueprint",
                "generate_matrix_bundle",
                "generate_coder_prompt_pack",
                "generate_coder_prompt",
                "validate_ai_coder_patch",
                "validate_bundle",
                "build_prompt_pack",
                "coder_handoff",
                "generate_repair_prompt",
                "compile_bundle",
                "export_zip",
                "regenerate",
                "plan_batch",
                "plan_repair_batch",
                "bundle_tree_hash",
                "diff_bundles",
                "build_commit",
                "build_release_evidence",
                "prepare_matrixhub_publication",
                "load_standards_pack",
                "generate_standards_lock",
            ],
        )

    # ------------------------------------------------------------------ #
    # Standards (Batch 3)
    # ------------------------------------------------------------------ #
    def load_standards_pack(self) -> StandardsPack:
        """Load and verify the active matrix-definitions standards pack."""
        return self.standards.current()

    def standards_metadata(self) -> dict[str, Any]:
        """Return active-pack metadata (shape for ``/api/v1/standards/current``)."""
        return self.standards.metadata()

    def generate_standards_lock(
        self,
        quality_level: QualityLevel | str = QualityLevel.STANDARD,
        *,
        control_files: list[str] | None = None,
    ) -> StandardsLock:
        """Build a deterministic ``MATRIX_STANDARDS.lock`` for a quality level.

        Pins the pack id/version, the combined-pack digest, the applied rule ids from the
        quality profile, and the pack input digests. The signed-vs-warn posture and checksum
        verification are handled by the standards loader.
        """
        level = (
            quality_level
            if isinstance(quality_level, QualityLevel)
            else QualityLevel(quality_level)
        )
        pack = self.standards.current()
        profile = self.standards.profile(level)
        return build_standards_lock(
            pack,
            quality_level=level,
            profile=profile,
            generated_at=self.runtime.now_iso(),
            control_files=control_files,
        )

    # ------------------------------------------------------------------ #
    # 1. Idea parsing
    # ------------------------------------------------------------------ #
    def parse_idea(self, payload: IdeaRequest | dict[str, Any] | Any) -> IdeaIntent:
        idea = self._coerce_idea(payload)
        parsed = parse_idea_request(idea)
        return IdeaIntent(
            normalized_idea=parsed.normalized_idea,
            build_type=parsed.detected_build_type,
            goal=idea.goal,
            preferred_coder=idea.preferred_coder,
            quality_level=idea.quality_level,
            constraints=idea.constraints,
        )

    # ------------------------------------------------------------------ #
    # 2. Blueprint candidates  (template-aware, Batch 4)
    # ------------------------------------------------------------------ #
    def generate_blueprint_candidates(
        self, payload: IdeaRequest | dict[str, Any] | Any
    ) -> list[BlueprintCandidate]:
        idea = self._coerce_idea(payload)
        return generate_candidates(idea, self.runtime)

    # ------------------------------------------------------------------ #
    # 3. Controlled blueprint  (template-aware; planner fallback)
    # ------------------------------------------------------------------ #
    def generate_controlled_blueprint(
        self,
        payload: IdeaRequest | dict[str, Any] | Any,
        candidate_id: str | None = None,
    ) -> BlueprintResult:
        idea = self._coerce_idea(payload)
        parsed = parse_idea_request(idea)
        normalized = parsed.normalized_idea
        candidates = generate_candidates(idea, self.runtime, parsed=parsed)
        selected = self._select_candidate(candidates, candidate_id)
        template = parsed.template

        database = "sqlite" if selected.quality_level == QualityLevel.STARTER else "postgresql"
        auth = "session" if (idea.constraints.requires_auth or parsed.wants_auth) else "none"
        deploy = idea.constraints.deployment_target or "docker"

        if template.tasks:
            # Flagship template: a curated, deterministic plan.
            stack = BlueprintStack(
                frontend="nextjs",
                backend="fastapi",
                worker="python",
                database=database,
                auth=auth,
                deploy=deploy,
            )
            pages = list(template.pages)
            api_routes = [
                ApiRoute(method=method, path=path, summary=summary)
                for method, path, summary in template.api_routes
            ]
            tasks = [
                BlueprintTask(
                    task_id=f"TASK-{index:03d}",
                    title=task.title,
                    allowed_files=list(task.allowed_files),
                    acceptance_criteria=list(task.acceptance_criteria),
                )
                for index, task in enumerate(template.tasks, start=1)
            ]
            services = list(template.services)
        else:
            # Generic idea: derive the plan from the keyword planner.
            spec, _warnings = idea_to_project_spec(idea, use_llm=self.runtime.use_llm)
            stack = project_spec_to_stack(spec, database=database, auth=auth, deploy=deploy)
            pages = list(template.pages)
            api_routes = [
                ApiRoute(method=method, path=path, summary=summary)
                for method, path, summary in template.api_routes
            ]
            tasks = project_spec_to_tasks(spec)
            services = list(template.services)

        blueprint_id = self.runtime.stable_id("bp", normalized, selected.candidate_id)
        return BlueprintResult(
            blueprint_id=blueprint_id,
            candidate_id=selected.candidate_id,
            name=template.name if template.tasks else selected.title,
            slug=selected.slug,
            idea=normalized,
            quality_level=selected.quality_level,
            stack=stack,
            pages=pages,
            services=services,
            api_routes=api_routes,
            required_files=list(_REQUIRED_FILES),
            allowed_change_roots=["frontend/", "backend/", "worker/", "tests/"],
            forbidden_changes=list(FORBIDDEN_CHANGES),
            tasks=tasks,
            acceptance_commands=["pytest -q", "ruff check .", "npm run build"],
            standards_lock_ref="MATRIX_STANDARDS.lock",
        )

    # ------------------------------------------------------------------ #
    # 4. Matrix Bundle metadata
    # ------------------------------------------------------------------ #
    def generate_matrix_bundle(
        self,
        blueprint: BlueprintResult,
        preferred_coder: CoderId | str = CoderId.GENERIC_AI_CODER,
    ) -> MatrixBundle:
        coder = self._normalize_coder(preferred_coder)
        bundle_id = self.runtime.stable_id("bundle", blueprint.blueprint_id, coder.value)
        compiled = self._compile(blueprint, coder=coder)
        files = [
            BundleFile(path=f.path, kind=f.kind, required=f.immutable or f.kind == "control")
            for f in sorted(compiled.files, key=lambda f: f.path)
        ]
        return MatrixBundle(
            bundle_id=bundle_id,
            blueprint_id=blueprint.blueprint_id,
            title=f"{blueprint.name} Bundle",
            created_at=self.runtime.now(),
            expires_at=None,
            bundle_url=f"/api/v1/bundles/{bundle_id}",
            download_url=f"/api/v1/bundles/{bundle_id}/download",
            manifest_digest=compiled.contract_hash,
            file_count=len(files),
            files=files,
            prompts_available=list(CoderId),
            standards=["RMD-001", "RMD-002", "RMD-003", "RMD-107", "AGENT-001", "GHA-001"],
            validation=ValidationStatus.NOT_RUN,
            links={
                "self": f"/api/v1/bundles/{bundle_id}",
                "download": f"/api/v1/bundles/{bundle_id}/download",
                "prompt": f"/api/v1/bundles/{bundle_id}/prompt/{coder.value}",
            },
        )

    # ------------------------------------------------------------------ #
    # 5. Coder prompt (single)  +  prompt pack (multi)
    # ------------------------------------------------------------------ #
    def generate_coder_prompt_pack(
        self,
        bundle_id: str,
        coder: CoderId | str = CoderId.GENERIC_AI_CODER,
        bundle_url: str | None = None,
        *,
        blueprint: BlueprintResult | None = None,
        task: BlueprintTask | None = None,
    ) -> PromptResponse:
        """Return a single controlled prompt for one coder.

        Named ``generate_coder_prompt_pack`` because that is the method Matrix Builder's
        adapter probes for; it returns a ``PromptResponse`` (one coder). Use
        ``build_prompt_pack`` for the full multi-coder ``PromptPack``.
        """
        coder_id = self._normalize_coder(coder)
        item = self._prompt_item(
            coder_id, blueprint=blueprint, task=task, bundle_id=bundle_id, bundle_url=bundle_url
        )
        return PromptResponse(
            coder=coder_id,
            label=item.label,
            path=item.path,
            prompt=item.content,
            bundle_id=bundle_id,
            bundle_url=bundle_url or f"/api/v1/bundles/{bundle_id}",
            task_id=task.task_id if task else "TASK-001",
            contract_files=item.contract_files,
            allowed_files=item.allowed_files,
            validation_commands=item.validation_commands,
            hard_constraints=item.hard_constraints,
            handoff_mode=get_adapter(coder_id).handoff_mode,
        )

    def generate_coder_prompt(
        self,
        bundle_id: str,
        coder: CoderId | str = CoderId.GENERIC_AI_CODER,
        bundle_url: str | None = None,
        *,
        blueprint: BlueprintResult | None = None,
        task: BlueprintTask | None = None,
    ) -> PromptResponse:
        """Alias for ``generate_coder_prompt_pack``.

        Matches the public method name on Matrix Builder's ``AgentGeneratorAdapter``. The
        adapter probes the engine for ``generate_coder_prompt_pack``; this alias lets either
        name be called directly with identical behavior.
        """
        return self.generate_coder_prompt_pack(
            bundle_id, coder, bundle_url, blueprint=blueprint, task=task
        )

    def build_prompt_pack(
        self,
        blueprint: BlueprintResult,
        *,
        bundle_id: str | None = None,
        coders: list[CoderId] | None = None,
        default_coder: CoderId | str = CoderId.GENERIC_AI_CODER,
    ) -> PromptPack:
        coder_list = coders or list(CoderId)
        default = self._normalize_coder(default_coder)
        bundle = bundle_id or self.runtime.stable_id(
            "bundle", blueprint.blueprint_id, default.value
        )
        first_task = blueprint.tasks[0] if blueprint.tasks else None
        rule_ids = self._coder_rule_ids(blueprint)
        prompts = [
            self._prompt_item(
                coder, blueprint=blueprint, task=first_task, bundle_id=bundle, rule_ids=rule_ids
            )
            for coder in coder_list
        ]
        return PromptPack(
            prompt_pack_id=self.runtime.stable_id("pp", blueprint.blueprint_id),
            bundle_id=bundle,
            blueprint_id=blueprint.blueprint_id,
            default_coder=default,
            prompts=prompts,
        )

    def coder_handoff(
        self,
        blueprint: BlueprintResult | dict[str, Any] | Any,
        coder: CoderId | str = CoderId.GENERIC_AI_CODER,
        *,
        batch: BatchPlan | None = None,
        bundle_id: str | None = None,
        bundle_url: str | None = None,
    ) -> CoderHandoff:
        """Build a full handoff for one AI coder: a contract-bound prompt plus the tool-native
        helper file (``CLAUDE.md`` / ``AGENTS.md`` / ``MATRIX_INSTRUCTIONS.md``).

        When ``batch`` is supplied, the prompt and helper are scoped to that batch ("this batch
        only", parent commit) and target the batch's first task.
        """
        bp = self._coerce_blueprint(blueprint)
        coder_id = self._normalize_coder(coder)
        task = None
        if batch is not None and batch.tasks:
            task = batch.tasks[0]
        elif bp.tasks:
            task = bp.tasks[0]
        ctx = PromptContext(
            blueprint=bp,
            task=task,
            bundle_id=bundle_id,
            bundle_url=bundle_url,
            rule_ids=self._coder_rule_ids(bp),
            batch_label=f"Batch {batch.ordinal:02d}" if batch else None,
            parent_commit=batch.parent_commit_ref if batch else None,
        )
        adapter = get_adapter(coder_id)
        item = adapter.render(ctx)
        prompt = PromptResponse(
            coder=coder_id,
            label=item.label,
            path=item.path,
            prompt=item.content,
            bundle_id=bundle_id,
            bundle_url=bundle_url or (f"/api/v1/bundles/{bundle_id}" if bundle_id else None),
            task_id=task.task_id if task else "TASK-001",
            contract_files=item.contract_files,
            allowed_files=item.allowed_files,
            validation_commands=item.validation_commands,
            hard_constraints=item.hard_constraints,
            handoff_mode=adapter.handoff_mode,
        )
        return CoderHandoff(
            coder=coder_id,
            prompt=prompt,
            helper_files=adapter.helper_files(ctx),
            batch_id=batch.batch_id if batch else None,
        )

    # ------------------------------------------------------------------ #
    # 6. Validation + repair
    # ------------------------------------------------------------------ #
    def validate_ai_coder_patch(
        self,
        bundle_id: str | None = None,
        *,
        request: Any | None = None,
        blueprint: BlueprintResult | dict[str, Any] | Any | None = None,
        repo_path: str | Path | None = None,
        zip_path: str | Path | None = None,
        patch: str | None = None,
        base_repo_path: str | Path | None = None,
        base_zip_path: str | Path | None = None,
        current_version: str = "1.0.0",
    ) -> ValidationReport:
        """Validate AI-coder output against the Matrix contract (the single authority).

        Accepts the submission as a ``ValidationRequest`` (``request``), a repository
        directory (``repo_path``), a ZIP (``zip_path``), or a unified diff (``patch``). When a
        ``blueprint`` is supplied the full contract is enforced (forbidden/immutable files,
        allowlist scope, required files, dependency drift, secrets, architecture drift);
        without one, the universal checks (forbidden files, secrets) still run.

        Pass ``base_repo_path`` / ``base_zip_path`` (the parent commit) to scope the
        change-based checks to *this batch's delta* rather than the whole tree.

        Returns ``approved`` / ``needs-repair`` / ``rejected`` with a bounded repair prompt, or
        ``not-run`` when there is nothing to validate.
        """
        bid = bundle_id or "bundle_demo"
        report_id = self.runtime.stable_id("val", bundle_id or "unknown")
        submission = self._build_submission(request, repo_path, zip_path, patch)
        base_submission = None
        if base_repo_path is not None or base_zip_path is not None:
            base_submission = self._build_submission(None, base_repo_path, base_zip_path, None)

        if submission.is_empty and blueprint is None:
            return ValidationReport(
                report_id=report_id,
                bundle_id=bid,
                status=ValidationStatus.NOT_RUN,
                score=0,
                violations=[],
                repair_prompt=None,
                checks=[
                    ValidationCheck(
                        check_id="adapter_boundary",
                        status="passed",
                        message="Engine ready; supply a submission (request/repo/zip/patch) to validate.",
                    ),
                ],
                created_at=self.runtime.now(),
            )

        contract = None
        if blueprint is not None:
            bp = self._coerce_blueprint(blueprint)
            compiled = self._compile(bp, version=current_version)
            contract = build_contract_spec(compiled, bp)

        return validate_submission(
            submission,
            contract,
            base_submission=base_submission,
            report_id=report_id,
            bundle_id=bid,
            created_at=self.runtime.now(),
        )

    # ------------------------------------------------------------------ #
    # Commit snapshots and diffs (Batch E2)
    # ------------------------------------------------------------------ #
    def bundle_tree_hash(
        self,
        *,
        repo_path: str | Path | None = None,
        zip_path: str | Path | None = None,
    ) -> str:
        """Content-address a full bundle tree (LF-normalized, order-independent)."""
        return tree_hash(self._build_submission(None, repo_path, zip_path, None))

    def diff_bundles(
        self,
        *,
        base_repo_path: str | Path | None = None,
        base_zip_path: str | Path | None = None,
        head_repo_path: str | Path | None = None,
        head_zip_path: str | Path | None = None,
    ) -> DiffResult:
        """Diff two bundle states into added/changed/deleted paths and a unified ``diff.patch``."""
        base = self._build_submission(None, base_repo_path, base_zip_path, None)
        head = self._build_submission(None, head_repo_path, head_zip_path, None)
        return diff_submissions(base, head)

    def build_commit(
        self,
        *,
        commit_no: int,
        head_repo_path: str | Path | None = None,
        head_zip_path: str | Path | None = None,
        base_repo_path: str | Path | None = None,
        base_zip_path: str | Path | None = None,
        parent_commit_ref: str | None = None,
        batch_ref: str | None = None,
        validation_status: ValidationStatus | str = ValidationStatus.NOT_RUN,
        summary: str = "",
    ) -> CommitManifest:
        """Build an immutable commit manifest for a bundle state (optionally diffed vs a parent)."""
        head = self._build_submission(None, head_repo_path, head_zip_path, None)
        base = None
        if base_repo_path is not None or base_zip_path is not None:
            base = self._build_submission(None, base_repo_path, base_zip_path, None)
        status = (
            validation_status
            if isinstance(validation_status, ValidationStatus)
            else ValidationStatus(str(validation_status))
        )
        return build_commit_manifest(
            commit_no=commit_no,
            head=head,
            base=base,
            parent_commit_ref=parent_commit_ref,
            batch_ref=batch_ref,
            validation_status=status,
            summary=summary,
        )

    @staticmethod
    def _build_submission(
        request: Any | None,
        repo_path: str | Path | None,
        zip_path: str | Path | None,
        patch: str | None,
    ) -> Submission:
        if repo_path is not None:
            return scan_repo(repo_path)
        if zip_path is not None:
            return scan_zip(zip_path)
        if patch is not None:
            return from_patch(patch)
        if request is not None:
            return from_request(request)
        return Submission()

    def validate_bundle(
        self,
        bundle_id: str | None = None,
        *,
        request: Any | None = None,
        blueprint: BlueprintResult | dict[str, Any] | Any | None = None,
        repo_path: str | Path | None = None,
        zip_path: str | Path | None = None,
        patch: str | None = None,
        base_repo_path: str | Path | None = None,
        base_zip_path: str | Path | None = None,
        current_version: str = "1.0.0",
    ) -> ValidationReport:
        """Alias for ``validate_ai_coder_patch``.

        Matches the public method name on Matrix Builder's ``AgentGeneratorAdapter`` (which
        probes the engine for ``validate_ai_coder_patch``). Both names are callable directly.
        """
        return self.validate_ai_coder_patch(
            bundle_id,
            request=request,
            blueprint=blueprint,
            repo_path=repo_path,
            zip_path=zip_path,
            patch=patch,
            base_repo_path=base_repo_path,
            base_zip_path=base_zip_path,
            current_version=current_version,
        )

    def generate_repair_prompt(self, report: ValidationReport) -> str | None:
        """Render a minimal, bounded repair prompt from a report's violations (RMD-120)."""
        return build_repair_prompt(report)

    # ------------------------------------------------------------------ #
    # Compile + export + release evidence + publishing
    # ------------------------------------------------------------------ #
    def compile_bundle(
        self,
        blueprint: BlueprintResult,
        *,
        version: str = "1.0.0",
        preferred_coder: CoderId | str = CoderId.GENERIC_AI_CODER,
        release_evidence: bool = False,
    ) -> CompiledBundle:
        """Compile a blueprint into the full controlled file plan.

        With ``release_evidence=True`` the bundle also carries SLSA provenance and a cosign
        signature bundle (Batch 10), with the manifest and checksums covering them.
        """
        compiled = self._compile(
            blueprint, version=version, coder=self._normalize_coder(preferred_coder)
        )
        if release_evidence:
            compiled = add_release_evidence(
                compiled, blueprint, engine_version=__version__, timestamp=self.runtime.now_iso()
            )
        return compiled

    def build_release_evidence(
        self,
        blueprint: BlueprintResult,
        *,
        version: str = "1.0.0",
        preferred_coder: CoderId | str = CoderId.GENERIC_AI_CODER,
    ) -> CompiledBundle:
        """Compile a release-ready bundle: provenance + signature + manifest + checksums."""
        return self.compile_bundle(
            blueprint, version=version, preferred_coder=preferred_coder, release_evidence=True
        )

    def prepare_matrixhub_publication(
        self,
        blueprint: BlueprintResult,
        *,
        version: str = "1.0.0",
        validation_report: ValidationReport | None = None,
        slug: str | None = None,
        visibility: str = "public",
        dry_run: bool = True,
        preferred_coder: CoderId | str = CoderId.GENERIC_AI_CODER,
    ) -> PublicationResponse:
        """Evaluate the MatrixHub trust gate for a bundle (dry-run only in the MVP)."""
        compiled = self.build_release_evidence(
            blueprint, version=version, preferred_coder=preferred_coder
        )
        return build_publication(
            compiled,
            validation_report=validation_report,
            slug=slug,
            visibility=visibility,
            dry_run=dry_run,
        )

    def export_zip(
        self,
        blueprint: BlueprintResult,
        out_path: str | Path | None = None,
        *,
        version: str = "1.0.0",
        preferred_coder: CoderId | str = CoderId.GENERIC_AI_CODER,
        release_evidence: bool = False,
    ) -> Path:
        out = Path(out_path) if out_path else Path.cwd() / f"{blueprint.slug}.zip"
        compiled = self.compile_bundle(
            blueprint,
            version=version,
            preferred_coder=self._normalize_coder(preferred_coder),
            release_evidence=release_evidence,
        )
        return write_strict_zip(compiled.file_map(), out)

    # ------------------------------------------------------------------ #
    # Regeneration (versioning — behind Matrix Builder's "Update requirements")
    # ------------------------------------------------------------------ #
    def regenerate(
        self,
        base_blueprint: BlueprintResult | dict[str, Any] | Any,
        change_request: str,
        change_type: ChangeType | str = ChangeType.ADD_FEATURE,
        *,
        current_version: str = "1.0.0",
    ) -> RegenerationResult:
        """Create a new blueprint version from an existing one without mutating it.

        ``change_type`` is one of ``small-update`` / ``add-feature`` / ``change-architecture``
        and drives the semver bump (patch / minor / major). The returned result carries the
        new blueprint, the new and previous version strings, and a human-readable change
        summary. The caller persists the base version unchanged and stores the new one.
        """
        ct = change_type if isinstance(change_type, ChangeType) else ChangeType(str(change_type))
        base = self._coerce_blueprint(base_blueprint)
        return regenerate_blueprint(
            base,
            change_request,
            ct,
            current_version=current_version,
            runtime=self.runtime,
        )

    # ------------------------------------------------------------------ #
    # Batch planning (Continue build — incremental change within a version)
    # ------------------------------------------------------------------ #
    def plan_batch(
        self,
        blueprint: BlueprintResult | dict[str, Any] | Any,
        goal_md: str,
        change_type: BatchChangeType | str = BatchChangeType.ADD_FEATURE,
        *,
        ordinal: int = 1,
        parent_commit: str | None = None,
    ) -> BatchPlan:
        """Plan the next batch inside the current version.

        Appends scoped tasks (continuing the blueprint's ``TASK-NNN`` numbering) and emits the
        contract context to implement them. Does **not** mutate the blueprint or bump the
        version — that is ``regenerate``'s job. Deterministic ``bat-…`` id.
        """
        return plan_batch(
            self._coerce_blueprint(blueprint),
            goal_md,
            change_type,
            ordinal=ordinal,
            parent_commit=parent_commit,
            runtime=self.runtime,
        )

    def plan_repair_batch(
        self,
        report: ValidationReport,
        *,
        blueprint: BlueprintResult | dict[str, Any] | Any | None = None,
        ordinal: int = 1,
        parent_commit: str | None = None,
    ) -> BatchPlan:
        """Turn a failing validation report into a fix-issue batch scoped to the bad files."""
        bp = self._coerce_blueprint(blueprint) if blueprint is not None else None
        return plan_repair_batch(
            report,
            blueprint=bp,
            ordinal=ordinal,
            parent_commit=parent_commit,
            runtime=self.runtime,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _coerce_idea(self, payload: IdeaRequest | dict[str, Any] | Any) -> IdeaRequest:
        if isinstance(payload, IdeaRequest):
            return payload
        if isinstance(payload, dict):
            return IdeaRequest.model_validate(payload)
        # Structurally-compatible object (e.g. Matrix Builder's own IdeaRequest).
        return IdeaRequest.model_validate(payload, from_attributes=True)

    @staticmethod
    def _coerce_blueprint(payload: BlueprintResult | dict[str, Any] | Any) -> BlueprintResult:
        if isinstance(payload, BlueprintResult):
            return payload
        if isinstance(payload, dict):
            return BlueprintResult.model_validate(payload)
        return BlueprintResult.model_validate(payload, from_attributes=True)

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.strip().split())

    @staticmethod
    def _normalize_coder(coder: CoderId | str) -> CoderId:
        if isinstance(coder, CoderId):
            return coder
        try:
            return CoderId(str(coder))
        except ValueError:
            return CoderId.GENERIC_AI_CODER

    @staticmethod
    def _select_candidate(
        candidates: list[BlueprintCandidate], candidate_id: str | None
    ) -> BlueprintCandidate:
        if candidate_id:
            for candidate in candidates:
                if candidate.candidate_id == candidate_id:
                    return candidate
            raise CandidateNotFoundError(candidate_id)
        for candidate in candidates:
            if candidate.recommended:
                return candidate
        return candidates[0]

    def _coder_rule_ids(self, blueprint: BlueprintResult | None) -> tuple[str, ...]:
        """Return the AI-coder-control rules (RMD-1xx) pinned by the active standards lock."""
        if blueprint is not None:
            try:
                lock = self.generate_standards_lock(blueprint.quality_level)
                rmd1xx = tuple(r for r in lock.rules if _RMD_1XX.match(r))
                if rmd1xx:
                    return rmd1xx
            except StandardsError:
                pass
        return _DEFAULT_CODER_RULES

    def _prompt_item(
        self,
        coder: CoderId,
        *,
        blueprint: BlueprintResult | None,
        task: BlueprintTask | None,
        bundle_id: str | None = None,
        bundle_url: str | None = None,
        rule_ids: tuple[str, ...] | None = None,
    ) -> PromptItem:
        ctx = PromptContext(
            blueprint=blueprint,
            task=task,
            bundle_id=bundle_id,
            bundle_url=bundle_url,
            rule_ids=rule_ids if rule_ids is not None else self._coder_rule_ids(blueprint),
        )
        return render_prompt(coder, ctx)

    def _standards_lock_for(self, blueprint: BlueprintResult) -> tuple[StandardsLock | None, str]:
        """Return ``(lock, rendered_text)``, falling back if no pack is available."""
        try:
            lock = self.generate_standards_lock(blueprint.quality_level)
            return lock, render_lock_yaml(lock)
        except StandardsError as exc:
            text = (
                "# MATRIX_STANDARDS.lock\n"
                f"# Standards pack unavailable: {exc}\n"
                "# Set MATRIX_DEFINITIONS_DIR or reinstall the bundled snapshot.\n"
                f"standards_lock_ref: {blueprint.standards_lock_ref}\n"
            )
            return None, text

    def _compile(
        self,
        blueprint: BlueprintResult,
        *,
        version: str = "1.0.0",
        coder: CoderId = CoderId.GENERIC_AI_CODER,
    ) -> CompiledBundle:
        """Compile a blueprint into a full deterministic file plan (Batch 5)."""
        lock, lock_text = self._standards_lock_for(blueprint)
        pack = self.build_prompt_pack(blueprint, default_coder=coder)
        prompt_files = {item.path: item.content for item in pack.prompts}
        return compile_blueprint(
            blueprint,
            version=version,
            standards_lock=lock,
            standards_lock_text=lock_text,
            prompt_files=prompt_files,
        )


__all__ = ["AgentGenerator", "CONTROL_FILES", "FORBIDDEN_CHANGES"]
