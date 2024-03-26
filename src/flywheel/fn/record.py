from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import Fn


@dataclass(eq=True, frozen=True)
class FnRecord:
    spec: Fn
    scopes: dict[str, dict[Any, Any]] = field(default_factory=dict)


@dataclass(eq=True, frozen=True)
class FnImplement:
    fn: Fn
