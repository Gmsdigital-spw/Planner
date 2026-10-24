"""GM Factory agent learning (Phase 9): scoped memory, frozen-rubric evaluation with objective checks, bounded repair,
ideas / experiments / promotion with rollback, and the dashboard panel. Stdlib only; durable through the engine store
(factory/engine/state/journal.jsonl committed to git, SQLite index rebuilt on demand). No model calls, no background worker."""
from .brain import AgentBrain, BUSINESS_SCOPES, KINDS, MAX_CONTEXT_CHARS, MAX_CONTEXT_ITEMS  # noqa: F401
from .checks import check_post, check_product  # noqa: F401
from .improve import MAX_REPAIRS, improve, next_attempt, plan_repairs  # noqa: F401
from .rubric import FALLBACK_RUBRIC, RUBRICS, anchors_markdown, assess, from_legacy_score, legacy_caps, rubric_id_of  # noqa: F401

__version__ = "0.9.0"
