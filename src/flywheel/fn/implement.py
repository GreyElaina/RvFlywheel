from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, overload

from typing_extensions import Concatenate, Self

from .record import FnRecord
from ..collector import Collector
from ..entity import BaseEntity
from ..typing import CR, P

if TYPE_CHECKING:
    from .base import Fn


class FnImplementEntity(Generic[CR, P], BaseEntity):
    fn: Fn[Callable[Concatenate[Any, P], Any], Any]
    impl: CR

    def __init__(self, fn: Fn[Callable[Concatenate[Any, P], Any], Any], impl: CR, *args: P.args, **kwargs: P.kwargs):
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

        self.fn.desc.collect(record, self.impl, *self._collect_args, **self._collect_kwargs)

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
    entity: FnImplementEntity[CR, ...]

    def __init__(self, entity: FnImplementEntity) -> None:
        self.entity = entity

    @property
    def __call__(self) -> CR:
        def wrapper(*args, **kwargs):
            return self.entity.impl(*args, **kwargs)

        return wrapper  # type: ignore

    @property
    def super(self) -> CR:
        return self.entity.fn.call
