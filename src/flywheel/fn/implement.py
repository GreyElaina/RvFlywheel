from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic

from ..context import CollectContext
from ..entity import BaseEntity
from ..globals import COLLECTING_IMPLEMENT_ENTITY, COLLECTING_TARGET_RECORD
from ..typing import CR, P, R, cvar
from .record import FnRecord

if TYPE_CHECKING:
    from .endpoint import CollectEndpointTarget, FnCollectEndpoint


class FnImplementEntity(Generic[CR], BaseEntity):
    targets: list[tuple[FnCollectEndpoint, CollectEndpointTarget]]
    impl: CR

    def __init__(self, impl: CR):
        self.targets = []
        self.impl = impl

    def add_target(self, endpoint: FnCollectEndpoint[P, Any], generator: CollectEndpointTarget):
        self.targets.append((endpoint, generator))

    def collect(self, collector: CollectContext):
        super().collect(collector)

        with cvar(COLLECTING_IMPLEMENT_ENTITY, self):
            for endpoint, generator in self.targets:
                record_signature = endpoint.signature

                if record_signature in collector.fn_implements:
                    record = collector.fn_implements[record_signature]
                else:
                    record = collector.fn_implements[record_signature] = FnRecord()

                with cvar(COLLECTING_TARGET_RECORD, record):
                    for signal in generator:
                        signal.overload.lay(record, signal.value, self.impl)

        return self

    def __call__(self: FnImplementEntity[Callable[P, R]], *args: P.args, **kwargs: P.kwargs):
        return self.impl(*args, **kwargs)

    @property
    def super(self) -> CR:
        return self.targets[0][0].fn  # type: ignore

    @staticmethod
    def current():
        return COLLECTING_IMPLEMENT_ENTITY.get()


def wrap_entity(entity: CR) -> FnImplementEntity[CR]:
    return FnImplementEntity(entity)
