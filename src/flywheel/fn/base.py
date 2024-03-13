from __future__ import annotations

from typing import Any, Callable, Generator, Generic, Protocol, TypeVar
from typing_extensions import Concatenate

from ..entity import BaseEntity
from ..globals import iter_layout
from ..typing import R1, CallGen, CollectGen, Detour, InP, OutP, P, Q, R, WrapCall, inTC
from .compose import EntitiesHarvest, FnCompose
from .implement import FnImplementEntity

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


class SymCompose(Generic[inTC], FnCompose):
    def call(self: SymCompose[Callable[P, R]], *args: P.args, **kwargs: P.kwargs) -> CallGen[R]:
        with self.harvest() as entities:
            yield self.singleton.call(None)

        return entities.first(*args, **kwargs)

    def collect(self, implement: inTC) -> CollectGen:
        yield self.singleton.collect(None)


class _WrapGenerator(Generic[R, Q, R1]):
    value: R1

    def __init__(self, gen: Generator[R, Q, R1]):
        self.gen = gen

    def __iter__(self) -> Generator[R, Q, R1]:
        self.value = yield from self.gen
        return self.value


class Fn(Generic[CCollect, CCall], BaseEntity):
    desc: FnCompose

    def __init__(self, compose: type[FnCompose]):
        self.desc = compose(self)

    @classmethod
    def symmetric(cls: type[Fn[Callable[[inTC], Any], inTC]], entity: inTC):
        return cls(SymCompose[inTC])

    @classmethod
    def declare(
        cls: type[Fn[Callable[InP, R1], Callable[P, R]]],
        desc: type[ComposeShape[Callable[InP, R1], Callable[P, CallGen[R]]]],
    ):
        return cls(desc)  # type: ignore

    @classmethod
    def override(cls: type[Fn[CCollect, Callable[P, R]]], target: Fn):
        def wrapper(
            compose_cls: type[ComposeShape[CCollect, Callable[P, CallGen[R]]]],
        ) -> Fn[CCollect, Callable[P, R]]:
            comp = cls.declare(compose_cls)
            comp.desc.signature = target.desc.signature
            return comp  # type: ignore

        return wrapper

    @property
    def implements(self: Fn[Callable[Concatenate[inTC, OutP], Any], Any]) -> Callable[OutP, Detour[WrapCall[..., inTC], OutP]]:
        def wrapper(*args: OutP.args, **kwargs: OutP.kwargs):
            def inner(impl: Callable[P, R]):
                # TODO: FnImplementGroupEntity
                return FnImplementEntity(self, impl, *args, **kwargs)

            return inner

        return wrapper  # type: ignore

    def _call(self, *args, **kwargs):
        signature = self.desc.signature()

        for context in iter_layout(signature):
            record = context.fn_implements.get(signature)
            if record is None:
                 continue

            record = context.fn_implements[signature]
            
            spec = record.spec
            wrap = _WrapGenerator(spec.desc.call(*args, **kwargs))

            for harvest in wrap:
                scope = record.scopes[harvest.name]
                stage = harvest.overload.harvest(scope, harvest.value)
                endpoint = EntitiesHarvest.slot.get(None)
                if endpoint is not None:
                    endpoint[1].commit(stage)

            return wrap.value
        else:
            raise NotImplementedError

    @property
    def call(self) -> CCall:
        return self._call  # type: ignore
