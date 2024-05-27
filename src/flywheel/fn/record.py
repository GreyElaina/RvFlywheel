from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .base import Fn
    from .overload import FnOverload


# layout: FnImplement -> {FnCollectEndpoint -> FnRecord}


@dataclass(eq=True, frozen=True)
class FnImplement:
    fn: Fn


@dataclass(eq=True, frozen=True)
class FnRecord:
    scopes: dict[str, dict[Any, Any]] = field(default_factory=dict)
    entities: dict[frozenset[tuple[str, "FnOverload", Any]], Callable] = field(default_factory=dict)


@dataclass(eq=True, frozen=True)
class FnOverloadSignal:
    overload: FnOverload
    value: Any
