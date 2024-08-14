from __future__ import annotations

from collections import ChainMap
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Mapping, MutableMapping

from .typing import TEntity, cvar

if TYPE_CHECKING:
    from .fn.record import FnRecord, FnRecordLabel


class CollectContext:
    fn_implements: dict[FnRecordLabel, FnRecord]

    def __init__(self):
        self.fn_implements = {}

    def collect(self, entity: TEntity) -> TEntity:
        return entity.collect(self)

    @contextmanager
    def collect_scope(self):
        from .globals import COLLECTING_CONTEXT_VAR

        with cvar(COLLECTING_CONTEXT_VAR, self):
            yield self

    @contextmanager
    def lookup_scope(self):
        from .globals import LOOKUP_LAYOUT_VAR

        with cvar(LOOKUP_LAYOUT_VAR, (self, *LOOKUP_LAYOUT_VAR.get())):
            yield self

    @contextmanager
    def scope(self):
        with self.collect_scope(), self.lookup_scope():
            yield self


class InstanceContext:
    instances: MutableMapping[type, Any]

    def __init__(self):
        self.instances = {}

    def store(self, *collection_or_target: Mapping[type, Any] | Any):
        for item in collection_or_target:
            if isinstance(item, Mapping):
                self.instances.update(item)
            else:
                self.instances[item.__class__] = item

    @contextmanager
    def scope(self, *, inherit: bool = True):
        from .globals import INSTANCE_CONTEXT_VAR

        if inherit:
            res = InstanceContext()
            res.instances = ChainMap({}, self.instances, INSTANCE_CONTEXT_VAR.get().instances)

            with res.scope(inherit=False):
                yield self
        else:
            with cvar(INSTANCE_CONTEXT_VAR, self):
                yield self
