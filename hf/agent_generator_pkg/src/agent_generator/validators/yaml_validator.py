"""YAML file validation: parse checking and emptiness detection."""
from __future__ import annotations

import yaml

from agent_generator.validators.spec_validator import ValidationResult


class YamlValidator:
    """Validate YAML content for syntax correctness and non-emptiness."""

    def validate(self, filepath: str, content: str) -> ValidationResult:
        """Validate a YAML file's content.

        Args:
            filepath: Path to the file (used in error messages).
            content: The raw YAML string to validate.

        Returns:
            A ValidationResult indicating validity, errors, and warnings.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not content or not content.strip():
            errors.append(f"{filepath}: File is empty")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        try:
            data = yaml.safe_load(content)
            if data is None:
                warnings.append(f"{filepath}: YAML parsed but is empty/null")
        except yaml.YAMLError as e:
            errors.append(f"{filepath}: YAML parse error: {e}")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )
