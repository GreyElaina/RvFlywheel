from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, Protocol, TypeVar

from typing_extensions import Concatenate

from ..entity import BaseEntity
from ..globals import iter_layout
from ..typing import CR, CT, R1, Detour, InP, OutP, P, R, WrapCall
from .compose import FnCompose
from .implement import FnImplementEntity

if TYPE_CHECKING:
    from .record import FnRecord

K = TypeVar("K")

CCall = TypeVar("CCall", bound=Callable, covariant=True)
CCollect = TypeVar("CCollect", bound=Callable, covariant=True)


class ComposeShape(Protocol[CCollect, CCall]):
    @property
    def collect(self) -> CCollect:
        ...

    @property
    def call(self) -> CCall:
        ...


class SymCompose(Generic[CT], FnCompose):
    def call(self: SymCompose[Callable[P, R]], record: FnRecord, *args: P.args, **kwargs: P.kwargs) -> R:
        return next(iter(self.singleton.harvest(record, None)))(*args, **kwargs)

    def collect(self, record: FnRecord, implement: CT):
        with self.recording(record, implement) as recorder:
            recorder.use(self.singleton, None)


class Fn(Generic[CCollect, CCall], BaseEntity):
    desc: FnCompose

    def __init__(self, compose: type[FnCompose]):
        self.desc = compose(self)

    @classmethod
    def symmetric(cls: type[Fn[Callable[[CT], Any], CT]], entity: CT):
        return cls(SymCompose[CT])

    @classmethod
    def declare(
        cls: type[Fn[Callable[InP, R1], Callable[P, R]]],
        desc: type[ComposeShape[Callable[Concatenate[FnRecord, InP], R1], Callable[Concatenate[FnRecord, P], R]]],
    ):
        return cls(desc)  # type: ignore

    @classmethod
    def override(cls: type[Fn[CCollect, Callable[P, R]]], target: Fn):
        def wrapper(
            compose_cls: type[ComposeShape[CCollect, Callable[Concatenate[FnRecord, P], R]]],
        ) -> Fn[CCollect, Callable[P, R]]:
            comp = cls.declare(compose_cls)
            comp.desc.signature = target.desc.signature
            return comp  # type: ignore

        return wrapper

    @property
    def implements(self: Fn[Callable[Concatenate[CR, OutP], Any], Any]) -> Callable[OutP, Detour[WrapCall[..., CR], OutP]]:
        def wrapper(*args: OutP.args, **kwargs: OutP.kwargs):
            def inner(impl: Callable[P, R]):
                # TODO: FnImplementGroupEntity
                return FnImplementEntity(self, impl, *args, **kwargs)

            return inner

        return wrapper  # type: ignore

    def _call(self, *args, **kwargs):
        signature = self.desc.signature()

        for context in iter_layout(signature):
            if signature not in context.fn_implements:
                continue

            record = context.fn_implements[signature]
            return record.spec.desc.call(record, *args, **kwargs)
        else:
            raise NotImplementedError

    @property
    def call(self) -> CCall:
        return self._call  # type: ignore
