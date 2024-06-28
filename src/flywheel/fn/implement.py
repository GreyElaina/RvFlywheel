from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from ..context import CollectContext
from ..entity import BaseEntity
from ..typing import CR, P
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

        for endpoint, generator in self.targets:
            record_signature = endpoint.signature

            if record_signature in collector.fn_implements:
                record = collector.fn_implements[record_signature]
            else:
                record = collector.fn_implements[record_signature] = FnRecord()

            for signal in generator:
                signal.overload.lay(record, signal.value, self.impl)

        return self

    def _call(self, *args, **kwargs):
        return self.impl(*args, **kwargs)

    @property
    def __call__(self) -> CR:
        return self._call  # type: ignore

    @property
    def super(self) -> CR:
        return self.targets[0][0].fn  # type: ignore
