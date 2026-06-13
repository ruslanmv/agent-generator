"""Shared Matrix contracts.

This package is the single source of truth for the data shapes exchanged across the
Matrix ecosystem boundary:

* ``agent-generator`` (this engine) produces them,
* ``matrix-builder`` consumes them in SDK mode (its ``app.schemas`` mirror these),
* ``matrix-definitions`` defines the canonical signed schemas they project onto.

Import the public contracts from here rather than from submodules.
"""

from __future__ import annotations

from agent_generator.contracts.batch import (
    BatchChangeType,
    BatchExecutionRequest,
    BatchPlan,
)
from agent_generator.contracts.blueprint import (
    DEFINITIONS_SCHEMA_VERSION,
    BlueprintCandidate,
    BlueprintCandidateResponse,
    BlueprintGenerationRequest,
    BlueprintResult,
    BlueprintSpec,
    BlueprintStack,
    BlueprintTask,
    TaskSpec,
)
from agent_generator.contracts.bundle import BundleManifest, BundleTreeNode, MatrixBundle
from agent_generator.contracts.commit import CommitManifest
from agent_generator.contracts.common import (
    ApiRoute,
    BuildType,
    BundleFile,
    BundleStatus,
    CoderId,
    ContractFileRef,
    Goal,
    JsonDict,
    QualityLevel,
    StrictModel,
    ValidationStatus,
)
from agent_generator.contracts.idea import (
    IdeaConstraints,
    IdeaIntent,
    IdeaMetadata,
    IdeaRequest,
)
from agent_generator.contracts.prompt_pack import (
    CoderHandoff,
    PromptItem,
    PromptPack,
    PromptResponse,
)
from agent_generator.contracts.publication import (
    PublicationRequest,
    PublicationResponse,
)
from agent_generator.contracts.standards import DefinitionsPackRef, StandardsLock
from agent_generator.contracts.validation import (
    ChangedFile,
    DependencyChange,
    ValidationArtifact,
    ValidationCheck,
    ValidationReport,
    ValidationRequest,
    ValidationViolation,
)
from agent_generator.contracts.versioning import (
    ChangeType,
    RegenerationRequest,
    RegenerationResult,
)

#: The contract surface version. Bump on any breaking change to a shared shape.
CONTRACTS_VERSION = "1.0"

__all__ = [
    "CONTRACTS_VERSION",
    "DEFINITIONS_SCHEMA_VERSION",
    # common
    "StrictModel",
    "ApiRoute",
    "BundleFile",
    "BundleStatus",
    "BuildType",
    "CoderId",
    "ContractFileRef",
    "Goal",
    "JsonDict",
    "QualityLevel",
    "ValidationStatus",
    # idea
    "IdeaConstraints",
    "IdeaIntent",
    "IdeaMetadata",
    "IdeaRequest",
    # blueprint
    "BlueprintCandidate",
    "BlueprintCandidateResponse",
    "BlueprintGenerationRequest",
    "BlueprintResult",
    "BlueprintSpec",
    "BlueprintStack",
    "BlueprintTask",
    "TaskSpec",
    # bundle
    "BundleManifest",
    "BundleTreeNode",
    "MatrixBundle",
    # prompt
    "CoderHandoff",
    "PromptItem",
    "PromptPack",
    "PromptResponse",
    # publication
    "PublicationRequest",
    "PublicationResponse",
    # standards
    "DefinitionsPackRef",
    "StandardsLock",
    # validation
    "ChangedFile",
    "DependencyChange",
    "ValidationArtifact",
    "ValidationCheck",
    "ValidationReport",
    "ValidationRequest",
    "ValidationViolation",
    # versioning
    "ChangeType",
    "RegenerationRequest",
    "RegenerationResult",
    # batches
    "BatchChangeType",
    "BatchExecutionRequest",
    "BatchPlan",
    # commits
    "CommitManifest",
]
