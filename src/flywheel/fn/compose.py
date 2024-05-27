from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, TypeVar

from ..overloads import SINGLETON_OVERLOAD
from .record import FnImplement, FnRecord

if TYPE_CHECKING:
    from .base import Fn
    from .endpoint import FnCollectEndpoint

FC = TypeVar("FC", bound="FnCompose")


class FnCompose:
    singleton: Final = SINGLETON_OVERLOAD
    fn: Fn

    def __init__(self, fn: Fn):
        type(self).fn = fn

    def call(self, records: dict[FnCollectEndpoint, FnRecord], *args, **kwargs) -> Any:
        raise NotImplementedError

    def signature(self):
        return FnImplement(self.fn)
