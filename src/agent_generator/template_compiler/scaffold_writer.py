"""Scaffold writer (Batch 5).

Emits a minimal, deterministic, stack-aware project skeleton the AI coder fills in per task:
config files plus a runnable health endpoint and its test. Intentionally small — the bundle
is a contract, not a finished app.
"""

from __future__ import annotations

from agent_generator.contracts.blueprint import BlueprintResult
from agent_generator.template_compiler.file_plan import CompiledFile

_ENV_EXAMPLE = """# Copy to .env and fill in. Never commit real secrets.
APP_ENV=development
LOG_LEVEL=info
"""

_GITIGNORE = """.env
__pycache__/
*.pyc
node_modules/
dist/
.next/
"""

_DOCKERIGNORE = """.git
.env
node_modules
__pycache__
dist
"""

_FASTAPI_MAIN = '''"""Application entrypoint. Implement routes per MATRIX_TASKS.md."""

from fastapi import FastAPI

app = FastAPI(title="{name}")


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {{"status": "ok"}}
'''

_FASTAPI_TEST = """from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
"""

_REQUIREMENTS = "fastapi\nuvicorn\npytest\nhttpx\n"

_NEXT_PAGE = """export default function Home() {
  return <main>Implement the UI per MATRIX_TASKS.md</main>;
}
"""


def _next_package_json(slug: str) -> str:
    return (
        "{\n"
        f'  "name": "{slug or "matrix-app"}",\n'
        '  "version": "0.1.0",\n'
        '  "private": true,\n'
        '  "scripts": { "dev": "next dev", "build": "next build", "start": "next start" }\n'
        "}\n"
    )


def build_scaffold(blueprint: BlueprintResult) -> list[CompiledFile]:
    """Return scaffold files for the blueprint's stack and services."""
    files: list[CompiledFile] = [
        CompiledFile(".env.example", _ENV_EXAMPLE, kind="config"),
        CompiledFile(".gitignore", _GITIGNORE, kind="config"),
        CompiledFile(".dockerignore", _DOCKERIGNORE, kind="config"),
    ]
    services = set(blueprint.services)
    stack = blueprint.stack

    if "api" in services and stack.backend == "fastapi":
        files += [
            CompiledFile("backend/app/__init__.py", "", kind="scaffold"),
            CompiledFile(
                "backend/app/main.py",
                _FASTAPI_MAIN.format(name=blueprint.name),
                kind="scaffold",
            ),
            CompiledFile("backend/requirements.txt", _REQUIREMENTS, kind="config"),
            CompiledFile("backend/tests/__init__.py", "", kind="test"),
            CompiledFile("backend/tests/test_health.py", _FASTAPI_TEST, kind="test"),
        ]
    elif "api" in services:
        files.append(
            CompiledFile(
                "backend/README.md",
                f"# Backend ({stack.backend})\n\nImplement per MATRIX_TASKS.md.\n",
                kind="scaffold",
            )
        )

    if "frontend" in services and stack.frontend == "nextjs":
        files += [
            CompiledFile(
                "frontend/package.json", _next_package_json(blueprint.slug), kind="config"
            ),
            CompiledFile("frontend/app/page.tsx", _NEXT_PAGE, kind="scaffold"),
        ]

    if "worker" in services:
        files.append(CompiledFile("worker/app/__init__.py", "", kind="scaffold"))

    return files


__all__ = ["build_scaffold"]
