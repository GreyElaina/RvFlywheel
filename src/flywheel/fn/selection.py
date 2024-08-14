from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterator

from flywheel.globals import iter_layout

from ..typing import C, P, R

if TYPE_CHECKING:
    from .endpoint import FnCollectEndpoint
    from .overload import FnOverload, TCallValue
    from .record import FnRecord


@dataclass
class Candidates(Generic[C]):
    endpoint: FnCollectEndpoint[..., C]
    expect_complete: bool = False

    def __iter__(self) -> Iterator[Selection[C]]:
        sig = self.endpoint.signature

        last_selection = None
        try:
            for layer in iter_layout(self.endpoint):
                if last_selection is not None and last_selection.completed:
                    break

                if sig in layer.fn_implements:
                    last_selection = Selection(layer.fn_implements[sig])
                    yield last_selection
        finally:
            if self.expect_complete and (last_selection is None or not last_selection.completed):
                raise NotImplementedError("cannot lookup any implementation with given arguments")


@dataclass
class Selection(Generic[C]):
    record: FnRecord
    result: dict[C, None] | None = None
    completed: bool = False

    def accept(self, collection: dict[Callable, None]):
        if self.result is None:
            self.result = collection  # type: ignore
        else:
            self.result = dict(self.result.items() & collection.items())

    def harvest(self, overload: FnOverload[Any, Any, TCallValue], value: TCallValue):
        digs = overload.dig(self.record, value)
        self.accept(digs)
        return digs

    def complete(self):
        self.completed = True

    def __iter__(self):
        if self.result is None:
            raise NotImplementedError("cannot lookup any implementation with given arguments")

        return iter(self.result)

    def __call__(self: Selection[Callable[P, R]], *args: P.args, **kwargs: P.kwargs) -> R:
        return next(iter(self))(*args, **kwargs)

    def __bool__(self):
        return bool(self.result)
