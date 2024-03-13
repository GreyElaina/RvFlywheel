from __future__ import annotations

from contextvars import ContextVar

from typing import TYPE_CHECKING, Any, Callable, ContextManager, Final, Generic, Iterable, overload
from typing_extensions import Concatenate

from ..builtins.overloads import SINGLETON_OVERLOAD
from ..typing import P1, CallGen, CollectGen, ExplictImplementShape, ImplementForCollect, P, R, inTC
from .record import FnImplement

if TYPE_CHECKING:
    from .base import Fn


class HarvestContextManager:
    def __enter__(self):
        harv = EntitiesHarvest()
        a = [None, harv]
        a[0] = EntitiesHarvest.slot.set(a)
        return harv

    def __exit__(self, exc_type, exc_val, exc_tb):
        tok, a = EntitiesHarvest.slot.get()
        a.finished = True
        EntitiesHarvest.slot.reset(tok)


HARVEST_CONTEXT_MANAGER = HarvestContextManager()


class FnCompose:
    singleton: Final = SINGLETON_OVERLOAD.as_agent()
    fn: Fn

    def __init__(self, fn: Fn):
        self.fn = fn

    @property
    def collector(self):
        return self.fn.collect_context

    def call(self) -> CallGen[Any]:
        ...

    def collect(self, implement) -> CollectGen:
        ...

    def signature(self):
        return FnImplement(self.fn)

    @overload
    def harvest(self: ExplictImplementShape[inTC]) -> ContextManager[EntitiesHarvest[[inTC]]]:
        ...

    @overload
    def harvest(self: ImplementForCollect[P1]) -> ContextManager[EntitiesHarvest[P1]]:
        ...

    def harvest(self):  # type: ignore
        return HARVEST_CONTEXT_MANAGER


class EntitiesHarvest(Generic[P1]):
    slot: Final[ContextVar[Any]] = ContextVar("EntitiesHarvest.slot")

    finished: bool = False
    _result: dict[Callable, None] | None = None

    def commit(self, inbound: dict[Callable, None]) -> None:
        if self._result is None:
            self._result = inbound
            return

        self._result = dict.fromkeys(self._result.keys() & inbound.keys())

    @property
    def ensured_result(self):
        if not self.finished or self._result is None:
            raise LookupError("attempts to read result before its mutations all finished")

        return list(self._result.keys())

    @property
    def first(self: EntitiesHarvest[Concatenate[Callable[P, R], ...]]) -> Callable[P, R]:
        result = self.ensured_result

        if not result:
            raise NotImplementedError("cannot lookup any implementation with given arguments")

        return result[0]  # type: ignore

    def iter_result(self: EntitiesHarvest[Concatenate[Callable[P, R], ...]]) -> Iterable[Callable[P, R]]:
        return self.ensured_result  # type: ignore
