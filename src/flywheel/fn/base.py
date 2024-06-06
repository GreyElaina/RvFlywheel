from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, Protocol, TypeVar

from typing_extensions import Concatenate

from ..globals import iter_layout
from ..typing import CR, P, R
from .record import FnImplement

if TYPE_CHECKING:
    from .compose import FnCompose

FC = TypeVar("FC", bound="FnCompose", covariant=True)


class ExtractCall(Protocol[CR]):
    @property
    def call(self) -> CR: ...


class Fn(Generic[FC]):
    def __init__(self, compose: type[FC]):
        self.compose = compose(self)

    # def entity(self, impl: C) -> FnImplementEntity[C]:
    #     return FnImplementEntity(impl)

    @property
    def _(self):
        return type(self.compose)

    def __call__(self: Fn[ExtractCall[Callable[Concatenate[Any, P], R]]], *args: P.args, **kwargs: P.kwargs) -> R:  # type: ignore
        sign = FnImplement(self)

        for layout in iter_layout(self):
            if sign in layout.fn_implements:
                records = layout.fn_implements[sign]

            return self.compose.call(records, *args, **kwargs)
        else:
            raise NotImplementedError("cannot lookup any implementation with given arguments")
