"""Central validation service for specs and artifacts."""
from __future__ import annotations

from agent_generator.domain.project_spec import ProjectSpec
from agent_generator.domain.artifact_bundle import ArtifactBundle
from agent_generator.validators.spec_validator import SpecValidator, ValidationResult
from agent_generator.validators.security_validator import SecurityValidator

_spec_validator = SpecValidator()
_security_validator = SecurityValidator()


def validate_spec(spec: ProjectSpec) -> ValidationResult:
    """Validate a ProjectSpec. Returns ValidationResult with errors/warnings."""
    return _spec_validator.validate(spec)


def validate_artifact(artifact: ArtifactBundle) -> ArtifactBundle:
    """Run security validation on generated artifacts. Mutates and returns the bundle."""
    issues = _security_validator.validate(artifact)
    for issue in issues:
        if issue.level == "error":
            artifact.errors.append(issue)
        else:
            artifact.warnings.append(issue)
    return artifact
