from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Protocol, TypeVar

from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from .entity import BaseEntity


R = TypeVar("R", covariant=True)
P = ParamSpec("P")
CR = TypeVar("CR", covariant=True, bound=Callable)
TEntity = TypeVar("TEntity", bound="BaseEntity")


class Collectable(Protocol[P]):
    def collect(self, *args: P.args, **kwargs: P.kwargs) -> Any: ...
