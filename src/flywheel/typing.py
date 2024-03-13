from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generator, Protocol, TypeVar
from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from .entity import BaseEntity
    from .fn.implement import FnImplementEntity
    from .fn.record import FnOverloadHarvest


T = TypeVar("T")
R = TypeVar("R", covariant=True)
R1 = TypeVar("R1", covariant=True)
P = ParamSpec("P")
P1 = ParamSpec("P1")
Q = TypeVar("Q", contravariant=True)
InP = ParamSpec("InP")
OutP = ParamSpec("OutP")
inRC = TypeVar("inRC", covariant=True, bound=Callable)
inTC = TypeVar("inTC", bound=Callable)
TEntity = TypeVar("TEntity", bound="BaseEntity")
CollectGen = Generator["FnOverloadHarvest", Any, None]
CallGen = Generator["FnOverloadHarvest", None, R]


class ImplementForCollect(Protocol[InP]):
    def collect(self, *args: InP.args, **kwargs: InP.kwargs) -> Any:
        ...


class WrapCall(Protocol[P, R]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        ...


class Detour(Protocol[R, OutP]):
    def __call__(
        self: Detour[WrapCall[..., Callable[P1, R1]], OutP],
        implement: Callable[P1, R1],
    ) -> FnImplementEntity[Callable[P1, R1], OutP]:
        ...


class ExplictImplementShape(Protocol[inRC]):
    @property
    def implement_sample(self) -> inRC:
        ...
