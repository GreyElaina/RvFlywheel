from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from ..context import CollectContext
from ..entity import BaseEntity
from ..typing import CR, P
from .record import FnRecord

if TYPE_CHECKING:
    from .endpoint import FnCollectEndpoint


class FnImplementEntity(Generic[CR], BaseEntity):
    targets: list[tuple[FnCollectEndpoint, type, tuple[Any, ...], dict[str, Any]]]
    impl: CR

    def __init__(self, impl: CR):
        self.targets = []
        self.impl = impl

    def add_target(self, endpoint: FnCollectEndpoint[P, Any], cls: type, *args: P.args, **kwargs: P.kwargs):
        self.targets.append((endpoint, cls, args, kwargs))

    def collect(self, collector: CollectContext):
        super().collect(collector)

        for endpoint, cls, args, kwargs in self.targets:
            record_signature = endpoint.fn.compose.signature()

            if record_signature in collector.fn_implements:
                records = collector.fn_implements[record_signature]
            else:
                records = collector.fn_implements[record_signature] = {}

            if endpoint in records:
                record = records[endpoint]
            else:
                record = records[endpoint] = FnRecord()

            for signal in endpoint.target(cls, *args, **kwargs):  # type: ignore
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
