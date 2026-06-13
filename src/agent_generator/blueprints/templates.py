"""Template families — the flagship controlled-blueprint templates (Batch 4).

A template family captures what the engine knows how to build well: a slug, the signals
that detect it in an idea, per-quality-level stacks and size estimates, the page/route/
service plan, and task definitions with file allowlists. The three flagship families match
the templates showcased in the Matrix Builder UI; ``GENERIC`` is the fallback that derives
everything from the idea itself.

Detection is deterministic keyword scoring — no LLM, no network — so the same idea always
maps to the same template.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_generator.contracts.common import BuildType, QualityLevel

_LEVELS = (QualityLevel.STARTER, QualityLevel.STANDARD, QualityLevel.PRODUCTION)


@dataclass(frozen=True)
class TemplateTask:
    title: str
    allowed_files: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]


@dataclass(frozen=True)
class TemplateFamily:
    template_id: str
    name: str
    slug: str
    build_type: BuildType
    keywords: tuple[str, ...]
    summary: str
    pages: tuple[str, ...]
    api_routes: tuple[tuple[str, str, str], ...]  # (method, path, summary)
    services: tuple[str, ...] = ("frontend", "api", "worker")
    tasks: tuple[TemplateTask, ...] = ()
    stack_by_level: dict[QualityLevel, tuple[str, ...]] = field(default_factory=dict)
    estimated_files: dict[QualityLevel, int] = field(default_factory=dict)

    def stack_for(self, level: QualityLevel) -> list[str]:
        if level in self.stack_by_level:
            return list(self.stack_by_level[level])
        return list(_DEFAULT_STACKS[level])

    def files_for(self, level: QualityLevel) -> int:
        return self.estimated_files.get(level, _DEFAULT_FILES[level])

    def keyword_hits(self, normalized_idea: str) -> list[str]:
        text = normalized_idea.lower()
        return [kw for kw in self.keywords if kw in text]


_DEFAULT_STACKS: dict[QualityLevel, tuple[str, ...]] = {
    QualityLevel.STARTER: ("Next.js", "FastAPI", "SQLite"),
    QualityLevel.STANDARD: ("Next.js", "FastAPI", "PostgreSQL", "Docker"),
    QualityLevel.PRODUCTION: ("Next.js", "FastAPI", "PostgreSQL", "Redis", "Docker"),
}

_DEFAULT_FILES: dict[QualityLevel, int] = {
    QualityLevel.STARTER: 18,
    QualityLevel.STANDARD: 34,
    QualityLevel.PRODUCTION: 64,
}


GITHUB_REPO_INTELLIGENCE = TemplateFamily(
    template_id="github-repo-intelligence-agent",
    name="GitHub Repo Intelligence Agent",
    slug="github-repo-intelligence-agent",
    build_type=BuildType.AGENT,
    keywords=(
        "github",
        "repository",
        "repositories",
        "repo",
        "codebase",
        "commit",
        "pull request",
    ),
    summary="Analyzes GitHub repositories and produces architecture, risk, and improvement reports.",
    pages=("/", "/analyze", "/report/:id", "/about"),
    api_routes=(
        ("GET", "/api/v1/health", "Health check"),
        ("POST", "/api/v1/repos/analyze", "Queue a repository analysis"),
        ("GET", "/api/v1/reports/{report_id}", "Read an analysis report"),
    ),
    tasks=(
        TemplateTask(
            title="Implement POST /api/v1/repos/analyze",
            allowed_files=("backend/app/api/repos.py", "backend/tests/test_repos_api.py"),
            acceptance_criteria=(
                "Endpoint accepts a public repository URL and returns a report id",
                "Tests pass",
                "No Matrix control files changed",
            ),
        ),
        TemplateTask(
            title="Build the analyze page",
            allowed_files=("frontend/app/analyze/page.tsx", "frontend/components/repo-form.tsx"),
            acceptance_criteria=("Form submits to the analyze endpoint", "Responsive layout"),
        ),
        TemplateTask(
            title="Implement the report worker",
            allowed_files=("worker/app/analysis.py", "worker/tests/test_analysis.py"),
            acceptance_criteria=("Worker produces a structured report", "Tests pass"),
        ),
    ),
)


DOCUMENT_QA = TemplateFamily(
    template_id="document-qa-agent",
    name="Document Q&A Agent",
    slug="document-qa-agent",
    build_type=BuildType.AGENT,
    keywords=(
        "document",
        "documents",
        "pdf",
        "q&a",
        "question",
        "answers",
        "rag",
        "knowledge base",
    ),
    summary="Answers questions from your documents using retrieval with citations.",
    pages=("/", "/upload", "/ask", "/about"),
    api_routes=(
        ("GET", "/api/v1/health", "Health check"),
        ("POST", "/api/v1/documents", "Upload and index a document"),
        ("POST", "/api/v1/questions", "Ask a question over indexed documents"),
    ),
    tasks=(
        TemplateTask(
            title="Implement document upload and indexing",
            allowed_files=("backend/app/api/documents.py", "backend/tests/test_documents_api.py"),
            acceptance_criteria=("Upload stores and indexes a document", "Tests pass"),
        ),
        TemplateTask(
            title="Implement the question endpoint with citations",
            allowed_files=("backend/app/api/questions.py", "backend/tests/test_questions_api.py"),
            acceptance_criteria=("Answers include source citations", "Tests pass"),
        ),
        TemplateTask(
            title="Build the ask page",
            allowed_files=("frontend/app/ask/page.tsx", "frontend/components/question-box.tsx"),
            acceptance_criteria=("Question box streams the answer", "Responsive layout"),
        ),
    ),
)


PORTFOLIO_REVIEWER = TemplateFamily(
    template_id="developer-portfolio-reviewer",
    name="Developer Portfolio Reviewer",
    slug="developer-portfolio-reviewer",
    build_type=BuildType.AGENT,
    keywords=(
        "portfolio",
        "resume",
        "cv",
        "developer profile",
        "review",
        "feedback",
        "career",
    ),
    summary="Provides structured feedback on developer portfolios and projects.",
    pages=("/", "/review", "/result/:id", "/about"),
    api_routes=(
        ("GET", "/api/v1/health", "Health check"),
        ("POST", "/api/v1/reviews", "Submit a portfolio for review"),
        ("GET", "/api/v1/reviews/{review_id}", "Read a review result"),
    ),
    tasks=(
        TemplateTask(
            title="Implement POST /api/v1/reviews",
            allowed_files=("backend/app/api/reviews.py", "backend/tests/test_reviews_api.py"),
            acceptance_criteria=("Endpoint accepts a portfolio URL", "Tests pass"),
        ),
        TemplateTask(
            title="Build the review submission page",
            allowed_files=("frontend/app/review/page.tsx", "frontend/components/review-form.tsx"),
            acceptance_criteria=("Form validates the URL", "Responsive layout"),
        ),
    ),
)


GENERIC = TemplateFamily(
    template_id="generic",
    name="Controlled Application",
    slug="",  # derived from the idea at generation time
    build_type=BuildType.APP,
    keywords=(),
    summary="A controlled full-stack application generated from your idea.",
    pages=("/", "/dashboard", "/about"),
    api_routes=(
        ("GET", "/api/v1/health", "Health check"),
        ("POST", "/api/v1/run", "Run the primary workflow"),
    ),
    tasks=(),  # derived from the keyword planner at generation time
)


FLAGSHIP_TEMPLATES: tuple[TemplateFamily, ...] = (
    GITHUB_REPO_INTELLIGENCE,
    DOCUMENT_QA,
    PORTFOLIO_REVIEWER,
)

#: Minimum keyword hits for a flagship template to win over the generic fallback.
MIN_KEYWORD_HITS = 2


def detect_template(normalized_idea: str) -> tuple[TemplateFamily, list[str]]:
    """Deterministically pick the best template family for an idea.

    Returns ``(template, matched_keywords)``. Falls back to ``GENERIC`` when no flagship
    template reaches ``MIN_KEYWORD_HITS``. Ties break by declaration order, which is stable.
    """
    best = GENERIC
    best_hits: list[str] = []
    for template in FLAGSHIP_TEMPLATES:
        hits = template.keyword_hits(normalized_idea)
        if len(hits) > len(best_hits):
            best, best_hits = template, hits
    if len(best_hits) < MIN_KEYWORD_HITS:
        return GENERIC, []
    return best, best_hits


__all__ = [
    "TemplateFamily",
    "TemplateTask",
    "GITHUB_REPO_INTELLIGENCE",
    "DOCUMENT_QA",
    "PORTFOLIO_REVIEWER",
    "GENERIC",
    "FLAGSHIP_TEMPLATES",
    "MIN_KEYWORD_HITS",
    "detect_template",
]
