from __future__ import annotations

from dataclasses import dataclass, field
from functools import reduce
from typing import TYPE_CHECKING, Any, Callable, Final, Generic, TypeVar, overload

from typing_extensions import Concatenate

from ..overloads import SINGLETON_OVERLOAD
from ..typing import CT, P1, Collectable, ImplementSample, P, R
from .overload import FnOverload, FnOverloadAgent, TCollectValue
from .record import FnImplement, FnRecord

if TYPE_CHECKING:
    from .base import Fn

FC = TypeVar("FC", bound="FnCompose")


class FnCompose:
    singleton: Final = SINGLETON_OVERLOAD.as_agent()
    fn: Fn

    def __init__(self, fn: Fn):
        self.fn = fn

    def call(self, record: FnRecord) -> Any:
        ...

    def collect(self, record: FnRecord, implement) -> None:
        ...

    def signature(self):
        return FnImplement(self.fn)

    @property
    def collector(self):
        return self.fn.collect_context

    @overload
    def harvest_from(self: ImplementSample[CT], *collections: dict[Callable, None]) -> HarvestWrapper[CT]:
        ...

    @overload
    def harvest_from(
        self: Collectable[Concatenate[Any, Callable[P, R], P1]], *collections: dict[Callable, None]
    ) -> HarvestWrapper[Callable[P, R]]:
        ...

    def harvest_from(self, *collections: dict[Callable, None]):  # type: ignore
        if not collections:
            raise TypeError("at least one collection is required")

        col = list(collections)
        init = col.pop(0)

        if not col:
            return HarvestWrapper(init)

        r = reduce(lambda x, y: {i: None for i in x if i in y}, col, init)
        return HarvestWrapper(r)

    def recording(self, record: FnRecord, implement: CT) -> OverloadRecorder[CT]:
        return OverloadRecorder(record, implement)

    @staticmethod
    def use_recorder(func: Callable[Concatenate[FC, OverloadRecorder[CT], P], R]):
        def wrapper(self: FC, record: FnRecord, implement: CT, *args: P.args, **kwargs: P.kwargs) -> R:
            with self.recording(record, implement) as recorder:
                return func(self, recorder, *args, **kwargs)

        return wrapper


@dataclass(slots=True)
class OverloadRecorder(Generic[CT]):
    target: FnRecord
    implement: CT
    operators: list[tuple[str, FnOverload, Any]] = field(default_factory=list)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.done()

    def done(self):
        for name, rule, value in self.operators:
            signature = rule.digest(value)
            scope = self.target.scopes.setdefault(name, {})
            target_set = rule.collect(scope, signature)
            target_set[self.implement] = None

        self.target.entities[frozenset(self.operators)] = self.implement

    @overload
    def use(self, target: FnOverload[Any, TCollectValue, Any], value: TCollectValue, *, name: str) -> OverloadRecorder:
        ...

    @overload
    def use(
        self,
        target: FnOverloadAgent[FnOverload[Any, TCollectValue, Any]],
        value: TCollectValue,
        *,
        name: str | None = None,
    ) -> OverloadRecorder:
        ...

    def use(self, target: ..., value: ..., *, name: str | None = None) -> OverloadRecorder:
        if isinstance(target, FnOverloadAgent):
            self.operators.append((name or target.name, target.fn_overload, value))
        elif name is None:
            raise ValueError("overload must be given a name if it is not an overload agent")
        else:
            self.operators.append((name, target, value))

        return self


class HarvestWrapper(Generic[CT]):
    harvest: dict[CT, None]

    def __init__(self, harvest: dict[CT, None]):
        self.harvest = harvest

    @property
    def first(self) -> CT:
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
