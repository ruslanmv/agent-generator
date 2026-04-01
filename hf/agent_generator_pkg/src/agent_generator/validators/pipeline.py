"""Full validation pipeline orchestrating spec and per-file validation.

Combines ProjectSpec validation with individual file validation (Python or YAML
based on file extension) into a single unified result.
"""
from __future__ import annotations

from agent_generator.domain.project_spec import ProjectSpec
from agent_generator.validators.python_validator import PythonValidator
from agent_generator.validators.spec_validator import SpecValidator, ValidationResult
from agent_generator.validators.yaml_validator import YamlValidator

_PYTHON_EXTENSIONS = frozenset({".py"})
_YAML_EXTENSIONS = frozenset({".yml", ".yaml"})


def _get_extension(path: str) -> str:
    """Extract the file extension from a path, lowercased."""
    dot_index = path.rfind(".")
    if dot_index == -1:
        return ""
    return path[dot_index:].lower()


class ValidationPipeline:
    """Orchestrate the full validation pipeline.

    Runs spec-level validation on the ProjectSpec, then validates each
    generated file using the appropriate validator based on its extension.
    """

    def __init__(self) -> None:
        self._spec_validator = SpecValidator()
        self._python_validator = PythonValidator()
        self._yaml_validator = YamlValidator()

    def validate_spec(self, spec: ProjectSpec) -> ValidationResult:
        """Validate only the ProjectSpec.

        Args:
            spec: The ProjectSpec to validate.

        Returns:
            A ValidationResult for the spec.
        """
        return self._spec_validator.validate(spec)

    def validate_file(self, filepath: str, content: str) -> ValidationResult:
        """Validate a single generated file based on its extension.

        Args:
            filepath: The file path (used to determine validator and in messages).
            content: The file content to validate.

        Returns:
            A ValidationResult for the file.
        """
        ext = _get_extension(filepath)
        if ext in _PYTHON_EXTENSIONS:
            return self._python_validator.validate(filepath, content)
        if ext in _YAML_EXTENSIONS:
            return self._yaml_validator.validate(filepath, content)
        return ValidationResult(valid=True)

    def validate_all(
        self,
        spec: ProjectSpec,
        files: dict[str, str],
    ) -> ValidationResult:
        """Run the full validation pipeline: spec + all generated files.

        Args:
            spec: The ProjectSpec to validate.
            files: Mapping of filepath to file content for all generated files.

        Returns:
            A combined ValidationResult aggregating all errors and warnings.
        """
        all_errors: list[str] = []
        all_warnings: list[str] = []

        # Validate the spec itself
        spec_result = self.validate_spec(spec)
        all_errors.extend(spec_result.errors)
        all_warnings.extend(spec_result.warnings)

        # Validate each generated file
        for filepath, content in files.items():
            file_result = self.validate_file(filepath, content)
            all_errors.extend(file_result.errors)
            all_warnings.extend(file_result.warnings)

        return ValidationResult(
            valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
        )
