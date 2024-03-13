from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, overload
from typing_extensions import Concatenate, Self

from flywheel.fn.record import FnRecord

from ..collector import Collector
from ..entity import BaseEntity
from ..typing import OutP, P, R, inRC

if TYPE_CHECKING:
    from .base import Fn
    from .overload import FnOverload


class FnImplementEntity(Generic[inRC, OutP], BaseEntity):
    fn: Fn[Callable[Concatenate[Any, OutP], Any], Any]
    impl: inRC

    def __init__(
        self,
        fn: Fn[Callable[Concatenate[Any, OutP], Any], Any],
        impl: inRC,
        *args: OutP.args,
        **kwargs: OutP.kwargs,
    ):
        self.fn = fn
        self.impl = impl

        self._collect_args = args
        self._collect_kwargs = kwargs

    def collect(self, collector: Collector):
        super().collect(collector)

        record_signature = self.fn.desc.signature()
        if record_signature in collector.fn_implements:
            record = collector.fn_implements[record_signature]
        else:
            record = collector.fn_implements[record_signature] = FnRecord(self.fn)

        overload_scopes = record.scopes
        segments: set[tuple[str, FnOverload, Any]] = set()

        for harvest_info in self.fn.desc.collect(self.impl, *self._collect_args, **self._collect_kwargs):
            sign = harvest_info.overload.digest(harvest_info.value)
            scope = overload_scopes.setdefault(harvest_info.name, {})
            target_set = harvest_info.overload.collect(scope, sign)
            target_set[self.impl] = None
            segments.add((harvest_info.name, harvest_info.overload, sign))

        record.entities[frozenset(segments)] = self.impl
        return self

    if TYPE_CHECKING:
        @property
        def __call__(self) -> inRC:
            return self.impl
    else:
        def __call__(self, *args, **kwargs):
            return self.impl(*args, **kwargs)

    @overload
    def __get__(self, instance: FnImplementEntityAgent, owner: type) -> Self:
        ...

    @overload
    def __get__(
        self: FnImplementEntity[Callable[Concatenate[Any, P], R], Any],
        instance: Any,
        owner: type,
    ) -> FnImplementEntityAgent[Callable[P, R]]:
        ...

    @overload
    def __get__(self, instance: Any, owner: type) -> Self:
        ...

    def __get__(self, instance: Any, owner: type):
        if instance is None or isinstance(instance, FnImplementEntityAgent):
            return self

        return FnImplementEntityAgent(instance, self)


class FnImplementEntityAgent(Generic[inRC]):
    instance: Any
    entity: FnImplementEntity[inRC, ...]

    def __init__(self, instance: Any, entity: FnImplementEntity) -> None:
        self.instance = instance
        self.entity = entity

    @property
    def __call__(self) -> inRC:
        def wrapper(*args, **kwargs):
            return self.entity.impl(*args, **kwargs)

        return wrapper  # type: ignore

    @property
    def super(self) -> inRC:
        return self.entity.fn.call  # type: ignore
