from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Final, Generic, Iterator, TypeVar, overload

from typing_extensions import Concatenate

from ..builtins.overloads import SINGLETON_OVERLOAD
from ..typing import CT, P1, ExplictImplementShape, ImplementForCollect, P, R
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

    @property
    def collector(self):
        return self.fn.collect_context

    def call(self, record: FnRecord) -> Any:
        ...

    def collect(self, record: FnRecord, implement) -> None:
        ...

    def signature(self):
        return FnImplement(self.fn)

    @overload
    def harvest(self: ExplictImplementShape[CT]) -> EntitiesHarvest[[CT]]:
        ...

    @overload
    def harvest(self: ImplementForCollect[P1]) -> EntitiesHarvest[P1]:
        ...

    def harvest(self):  # type: ignore
        return EntitiesHarvest()

    def recording(self, record: FnRecord, implement: Callable):
        return OverloadRecorder(record, implement)

    @staticmethod
    def use_recorder(func: Callable[Concatenate[FC, OverloadRecorder, CT, P], R]):
        def wrapper(self: FC, record: FnRecord, implement: CT, *args: P.args, **kwargs: P.kwargs) -> R:
            with self.recording(record, implement) as recorder:
                return func(self, recorder, implement, *args, **kwargs)

        return wrapper


@dataclass(slots=True)
class OverloadRecorder:
    target: FnRecord
    implement: Callable
    operators: list[tuple[str, FnOverload, Any]] = field(default_factory=list)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.done()

    def done(self):
        for scope_id, ov, collect_value in self.operators:
            signature = ov.digest(collect_value)
            scope = self.target.scopes.setdefault(scope_id, {})
            target_set = ov.collect(scope, signature)
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


@dataclass(init=True, slots=True)
class EntitiesHarvest(Generic[P1]):
    _result: dict[Callable, None] | None = None

    def commit(self, inbound: dict[Callable, None]) -> None:
        if self._result is None:
            self._result = inbound
            return

        self._result = dict.fromkeys(inbound.keys() & self._result)

    def iter_result(self: EntitiesHarvest[Concatenate[Callable[P, R], ...]]) -> Iterator[Callable[P, R]]:
        if self._result is None:
            raise LookupError("attempts to read result before its mutations all finished")

        return iter(self._result.keys())  # type: ignore

    @property
    def first(self: EntitiesHarvest[Concatenate[Any, Callable[P, R], ...]]) -> Callable[P, R]:
        res = self._result

        if res is None:
            raise LookupError("attempts to read result before its mutations all finished")

        for i in res:
            return i  # type: ignore
        else:
            raise NotImplementedError("cannot lookup any implementation with given arguments")
