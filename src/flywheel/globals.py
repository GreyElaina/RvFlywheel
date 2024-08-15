from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Tuple

from .context import CollectContext, InstanceContext
from .typing import TEntity

if TYPE_CHECKING:
    from .fn.endpoint import FnCollectEndpoint
    from .fn.implement import FnImplementEntity
    from .fn.record import FnRecord


GLOBAL_COLLECT_CONTEXT = CollectContext()
GLOBAL_INSTANCE_CONTEXT = InstanceContext()

COLLECTING_CONTEXT_VAR = ContextVar("CollectingContext", default=GLOBAL_COLLECT_CONTEXT)
COLLECTING_IMPLEMENT_ENTITY: ContextVar[FnImplementEntity] = ContextVar("CollectingImplementEntity")
COLLECTING_TARGET_RECORD: ContextVar[FnRecord] = ContextVar("CollectingTargetRecord")
LOOKUP_LAYOUT_VAR = ContextVar[Tuple[CollectContext, ...]]("LookupContext", default=(GLOBAL_COLLECT_CONTEXT,))
INSTANCE_CONTEXT_VAR = ContextVar("InstanceContext", default=GLOBAL_INSTANCE_CONTEXT)

CALLER_TOKENS: ContextVar[dict[FnCollectEndpoint, int]] = ContextVar("CallerTokens", default={})


def iter_layout(endpoint: FnCollectEndpoint):
    index = CALLER_TOKENS.get().get(endpoint, -1)
    contexts = LOOKUP_LAYOUT_VAR.get()

    for layer in contexts[index + 1 :]:
        yield layer


def global_collect(entity: TEntity) -> TEntity:
    return GLOBAL_COLLECT_CONTEXT.collect(entity)


def local_collect(entity: TEntity) -> TEntity:
    return COLLECTING_CONTEXT_VAR.get().collect(entity)


@contextmanager
def union_scope(*contexts: CollectContext):
    token = LOOKUP_LAYOUT_VAR.set((*contexts, *LOOKUP_LAYOUT_VAR.get()))

    try:
        yield
    finally:
        LOOKUP_LAYOUT_VAR.reset(token)
