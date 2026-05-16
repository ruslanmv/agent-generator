"""AST-based security validator — blocks unsafe patterns in generated code."""

from __future__ import annotations

import ast

from agent_generator.domain.artifact_bundle import ArtifactBundle, ValidationIssue

FORBIDDEN_CALLS = {"eval", "exec", "__import__"}

FORBIDDEN_ATTR_CALLS = {
    ("os", "system"),
    ("subprocess", "Popen"),
    ("subprocess", "call"),
    ("subprocess", "run"),
}


class _SecurityVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.issues: list[ValidationIssue] = []

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            self.issues.append(
                ValidationIssue(
                    level="error",
                    message=f"{self.path}: forbidden call '{node.func.id}()' detected",
                )
            )
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            key = (node.func.value.id, node.func.attr)
            if key in FORBIDDEN_ATTR_CALLS:
                self.issues.append(
                    ValidationIssue(
                        level="error",
                        message=f"{self.path}: forbidden call '{key[0]}.{key[1]}()' detected",
                    )
                )
        self.generic_visit(node)


class SecurityValidator:
    """Scan generated artifacts for forbidden code patterns using AST analysis."""

    def validate(self, artifact: ArtifactBundle) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for file in artifact.files:
            if not file.path.endswith(".py"):
                continue
            try:
                tree = ast.parse(file.content)
            except SyntaxError as exc:
                issues.append(
                    ValidationIssue(
                        level="error",
                        message=f"{file.path}: syntax error during security scan: {exc.msg}",
                    )
                )
                continue

            visitor = _SecurityVisitor(file.path)
            visitor.visit(tree)
            issues.extend(visitor.issues)

            # Warn on requests calls without timeout
            if "requests." in file.content and "timeout=" not in file.content:
                issues.append(
                    ValidationIssue(
                        level="warning",
                        message=f"{file.path}: HTTP request may be missing timeout parameter",
                    )
                )
        return issues
