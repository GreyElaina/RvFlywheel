from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar, overload
from typing_extensions import Self, final

if TYPE_CHECKING:
    from .compose import FnCompose
    from .record import FnRecord

TOverload = TypeVar("TOverload", bound="FnOverload", covariant=True)
TCallValue = TypeVar("TCallValue")
TCollectValue = TypeVar("TCollectValue")
TSignature = TypeVar("TSignature")


class FnOverload(Generic[TSignature, TCollectValue, TCallValue]):
    def __init__(self) -> None:
        ...

    @final
    def as_agent(self):
        return FnOverloadAgentDescriptor(self)

    def digest(self, collect_value: TCollectValue) -> TSignature:
        ...

    def collect(self, scope: dict, signature: TSignature) -> dict[Callable, None]:
        ...

    def harvest(self, scope: dict, value: TCallValue) -> dict[Callable, None]:
        ...

    def access(self, scope: dict, signature: TSignature) -> dict[Callable, None] | None:
        ...


@dataclass(slots=True)
class FnOverloadAgent(Generic[TOverload]):
    name: str
    compose: FnCompose
    fn_overload: TOverload

    def harvest(
        self: FnOverloadAgent[FnOverload[Any, Any, TCallValue]],
        record: FnRecord,
        value: TCallValue,
        *,
        name: str | None = None,
    ):
        return self.fn_overload.harvest(record.scopes[name or self.name], value)


class FnOverloadAgentDescriptor(Generic[TOverload]):
    name: str
    fn_overload: TOverload

    def __init__(self, fn_overload: TOverload) -> None:
        self.fn_overload = fn_overload

    def __set_name__(self, owner: type, name: str):
        self.name = name

    @overload
    def __get__(self, instance: None, owner: type) -> Self:
        ...

    @overload
    def __get__(self, instance: FnCompose, owner: type) -> FnOverloadAgent[TOverload]:
        ...

    def __get__(self, instance: FnCompose | None, owner: type):
        if instance is None:
            return self

        return FnOverloadAgent(self.name, instance, self.fn_overload)
