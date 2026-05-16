"""Tests for the security validator."""

from agent_generator.domain.artifact_bundle import ArtifactBundle, GeneratedFile
from agent_generator.validators.security_validator import SecurityValidator


def test_blocks_eval():
    artifact = ArtifactBundle(files=[GeneratedFile(path="bad.py", content="result = eval('1+1')")])
    issues = SecurityValidator().validate(artifact)
    assert any(i.level == "error" for i in issues)


def test_blocks_exec():
    artifact = ArtifactBundle(files=[GeneratedFile(path="bad.py", content="exec('print(1)')")])
    issues = SecurityValidator().validate(artifact)
    assert any(i.level == "error" for i in issues)


def test_allows_safe_code():
    artifact = ArtifactBundle(files=[GeneratedFile(path="safe.py", content="x = 1 + 2\nprint(x)")])
    issues = SecurityValidator().validate(artifact)
    assert not any(i.level == "error" for i in issues)


def test_flags_eval_substring_in_safe_eval():
    """AST-based validator correctly identifies _safe_eval as a non-forbidden call.

    Unlike substring matching, the AST visitor resolves the actual function name
    as '_safe_eval', which is NOT in FORBIDDEN_CALLS.  No error is expected.
    """
    artifact = ArtifactBundle(
        files=[GeneratedFile(path="calc.py", content="result = _safe_eval('1+1')")]
    )
    issues = SecurityValidator().validate(artifact)
    # AST analysis sees the call name as '_safe_eval', not 'eval' — no error.
    assert not any(i.level == "error" for i in issues)


def test_skips_non_python():
    artifact = ArtifactBundle(files=[GeneratedFile(path="config.yaml", content="eval: true")])
    issues = SecurityValidator().validate(artifact)
    assert len(issues) == 0
