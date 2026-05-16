"""AST-based Python code validation: syntax, security, and import extraction."""

from __future__ import annotations

import ast
import re

from agent_generator.validators.spec_validator import ValidationResult

_DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r"\beval\(", "eval() -- potential code injection"),
    (r"\bexec\(", "exec() -- potential code injection"),
    (r"os\.system\(", "os.system() -- use subprocess instead"),
    (r"__import__\(", "__import__() -- use regular imports"),
]

_SECRET_PATTERNS: list[tuple[str, str]] = [
    (
        r'(?:token|key|secret|password)\s*=\s*["\'][^"\']{10,}["\']',
        "Possible hardcoded secret",
    ),
]


def extract_imports(code: str) -> list[str]:
    """Extract all imported module names from Python source code.

    Uses AST parsing to reliably find both `import X` and `from X import Y`
    statements.

    Args:
        code: Python source code string.

    Returns:
        Sorted list of unique top-level module names.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level = alias.name.split(".")[0]
                modules.add(top_level)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top_level = node.module.split(".")[0]
                modules.add(top_level)

    return sorted(modules)


class PythonValidator:
    """Validate Python source code for syntax errors, security issues, and style.

    Performs three passes:
    1. AST-based syntax check.
    2. Regex-based security scan for dangerous function calls.
    3. Regex-based scan for hardcoded secrets.
    """

    def validate(self, filepath: str, code: str) -> ValidationResult:
        """Validate a Python source file.

        Args:
            filepath: Path to the file (used in error messages).
            code: The Python source code to validate.

        Returns:
            A ValidationResult indicating validity, errors, and warnings.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not code or not code.strip():
            errors.append(f"{filepath}: File is empty")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # 1. Syntax check via AST parsing
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"{filepath}: Syntax error at line {e.lineno}: {e.msg}")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # 2. Security scan for dangerous patterns
        for pattern, msg in _DANGEROUS_PATTERNS:
            if re.search(pattern, code):
                warnings.append(f"{filepath}: {msg}")

        # 3. Hardcoded secret detection
        for pattern, msg in _SECRET_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                warnings.append(f"{filepath}: {msg}")

        # 4. Import presence check
        imports = extract_imports(code)
        if not imports:
            warnings.append(f"{filepath}: No imports found")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
