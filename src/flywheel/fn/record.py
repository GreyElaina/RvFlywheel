from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .endpoint import FnCollectEndpoint
    from .overload import FnOverload


@dataclass(eq=True, frozen=True)
class FnRecordLabel:
    endpoint: FnCollectEndpoint


@dataclass(eq=True, frozen=True)
class FnRecord:
    scopes: dict[str, dict[Any, Any]] = field(default_factory=dict)
    entities: dict[frozenset[tuple[str, "FnOverload", Any]], Callable] = field(default_factory=dict)


@dataclass(eq=True, frozen=True)
class CollectSignal:
    overload: FnOverload
    value: Any
