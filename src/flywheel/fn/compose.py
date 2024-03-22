from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING, Any, Callable, Final, TypeVar

from ..overloads import SINGLETON_OVERLOAD
from .record import FnImplement, FnRecord

if TYPE_CHECKING:
    from .base import Fn
    from .implement import OverloadRecorder

FC = TypeVar("FC", bound="FnCompose")


class FnCompose:
    singleton: Final = SINGLETON_OVERLOAD
    fn: Fn

    def __init__(self, fn: Fn):
        self.fn = fn

    def call(self, record: FnRecord, *args, **kwargs) -> Any:
        return next(iter(SINGLETON_OVERLOAD.dig(record, None).keys()))(*args, **kwargs)

    def collect(self, recorder: OverloadRecorder) -> None:
        recorder.use(self.singleton, None)

    def signature(self):
        return FnImplement(self.fn)

    def load(self, *collections: dict[Callable, None]):  # type: ignore
        if not collections:
            raise TypeError("at least one collection is required")

        col = list(collections)
        init = col.pop(0)

        if not col:
            return HarvestWrapper(init)

        return HarvestWrapper(reduce(lambda x, y: {i: None for i in x if i in y}, col, init))


class HarvestWrapper:
    harvest: dict[Callable, None]

    def __init__(self, harvest: dict[Callable, None]):
        self.harvest = harvest

    @property
    def first(self) -> Callable:
        if not self.harvest:
            raise NotImplementedError("cannot lookup any implementation with given arguments")

        return next(iter(self.harvest))

    @property
    def __call__(self):
        return self.first

    def __iter__(self):
        if not self.harvest:
            raise NotImplementedError("cannot lookup any implementation with given arguments")

        return iter(self.harvest)

    def __bool__(self):
        return bool(self.harvest)
