from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Protocol, TypeVar, Union

from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from .entity import BaseEntity


T = TypeVar("T")
R = TypeVar("R", covariant=True)
Q = TypeVar("Q", contravariant=True)
K = TypeVar("K")
K1 = TypeVar("K1")

C = TypeVar("C", bound=Callable)
CQ = TypeVar("CQ", contravariant=True, bound=Callable)
CR = TypeVar("CR", covariant=True, bound=Callable)
CnQ = TypeVar("CnQ", contravariant=True, bound=Union[Callable, None])
CnR = TypeVar("CnR", covariant=True, bound=Union[Callable, None])

P = ParamSpec("P")
P1 = ParamSpec("P1")
P2 = ParamSpec("P2")

TEntity = TypeVar("TEntity", bound="BaseEntity")


class Collectable(Protocol[P]):
    def collect(self, *args: P.args, **kwargs: P.kwargs) -> Any: ...
