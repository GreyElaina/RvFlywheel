from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ..overloads import SINGLETON_OVERLOAD
from .record import FnImplement

if TYPE_CHECKING:
    from ..typing import RecordsT
    from .base import Fn


class FnCompose:
    singleton: Final = SINGLETON_OVERLOAD
    fn: Fn

    def __init__(self, fn: Fn):
        type(self).fn = fn

    def call(self, records: RecordsT, *args, **kwargs) -> Any:
        raise NotImplementedError

    def signature(self):
        return FnImplement(self.fn)
