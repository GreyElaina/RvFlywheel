from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from ..typing import C, RecordsT
from .overload import FnOverload, TCallValue

if TYPE_CHECKING:
    from .endpoint import FnCollectEndpoint


class FnHarvestControl(Generic[C]):
    def __init__(self, endpoint: FnCollectEndpoint, records: RecordsT) -> None:
        self.endpoint = endpoint
        self.records = records

    @property
    def record(self):
        if self.endpoint not in self.records:
            raise NotImplementedError(f"endpoint {self.endpoint} not found in records")

        return self.records[self.endpoint]

    def use(self: FnHarvestControl[C], overload: FnOverload[Any, Any, TCallValue], value: TCallValue):
        return FnHarvest(self).apply(overload, value)


class FnHarvest(Generic[C]):
    def __init__(self, control: FnHarvestControl[C]) -> None:
        self.control = control
        self.result = None

    def apply(self, overload: FnOverload[Any, Any, TCallValue], value: TCallValue):
        self.result = overload.dig(self.control.record, value)
        return self

    def use(self, overload: FnOverload[Any, Any, TCallValue], value: TCallValue):
        if self.result is None:
            raise NotImplementedError(f"result is None, cannot use overload {overload} with value {value}")

        self.result = dict(self.result.items() & overload.dig(self.control.record, value).items())
        return self

    @property
    def first(self) -> C:
        if self.result is None:
            raise NotImplementedError("result is None, cannot get first item")

        return next(iter(self.result))  # type: ignore

    def __iter__(self) -> list[C]:
        if self.result is None:
            raise NotImplementedError("result is None, cannot iterate")

        return list(self.result)  # type: ignore

    def __bool__(self):
        return bool(self.result)
