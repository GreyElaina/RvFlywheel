from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, overload

from typing_extensions import Concatenate, Self

from ..entity import BaseEntity
from ..scoped import scoped_collect
from ..typing import CR, P
from .record import FnRecord

if TYPE_CHECKING:
    from .base import Fn


class FnImplementEntity(Generic[CR], BaseEntity):
    targets: list[tuple[Fn, tuple[Any, ...], dict[str, Any]]]
    impl: CR

    def __init__(self, impl: CR):
        self.targets = []
        self.impl = impl

    def add_target(self, fn: Fn[Callable[Concatenate[Any, P], Any], Any], *args: P.args, **kwargs: P.kwargs):
        self.targets.append((fn, args, kwargs))

    def collect(self, collector: scoped_collect):
        super().collect(collector)

        for fn, args, kwargs in self.targets:
            record_signature = fn.desc.signature()
            if record_signature in collector.fn_implements:
                record = collector.fn_implements[record_signature]
            else:
                record = collector.fn_implements[record_signature] = FnRecord(fn)

            fn.desc.collect(record, self.impl, *args, **kwargs)

        return self

    def _call(self, *args, **kwargs):
        return self.impl(*args, **kwargs)

    @property
    def agent(self):
        return FnImplementEntityAgent(self)

    @property
    def __call__(self) -> CR:
        return self._call  # type: ignore

    @overload
    def __get__(self, instance: None, owner: type) -> Self:
        ...

    @overload
    def __get__(self, instance: FnImplementEntityAgent, owner: type) -> Self:
        ...

    @overload
    def __get__(self, instance: Any, owner: type) -> FnImplementEntityAgent[CR]:
        ...

    def __get__(self, instance: Any, owner: type):
        if instance is None or isinstance(instance, FnImplementEntityAgent):
            return self

        return self.agent


class FnImplementEntityAgent(Generic[CR]):
    entity: FnImplementEntity[CR]

    def __init__(self, entity: FnImplementEntity) -> None:
        self.entity = entity

    @property
    def __call__(self) -> CR:
        def wrapper(*args, **kwargs):
            return self.entity.impl(*args, **kwargs)

        return wrapper  # type: ignore

    @property
    def super(self) -> CR:
        if len(self.entity.targets) != 1:
            # 这种情况下无法确认要 call 哪个 fn
            raise RuntimeError("super() is only available for single target.")

        return self.entity.targets[0][0].call
