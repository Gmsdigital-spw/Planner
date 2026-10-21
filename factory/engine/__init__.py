"""GM Factory engine — add-on Phase 3 (typed contracts, durable task records, state management).

See ARCHITECTURE.md for the map to the add-on and the conflicts resolved. No third-party dependencies.
"""
__version__ = "0.3.0"

from .contracts import (AgentContract, AgentRole, Approval, ApprovalStatus, AuditEvent, Budget, Capability, Channel,  # noqa: F401
                        DistributionPlan, ErrorPolicy, FileRef, IntegrationHealth, IntegrationState, ModelUsage,
                        ProductManifest, Run, Task, TaskSpec, TaskStatus, fmt_num, idempotency_key, scrub)
from .engine import EngineError, NeedsApproval, PermanentError, RateLimited, RunContext, TaskEngine, TransientError  # noqa: F401
from .store import Store  # noqa: F401
