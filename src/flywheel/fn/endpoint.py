from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generator, Generic, Protocol, TypeVar, overload

from typing_extensions import Concatenate, Self

from flywheel.globals import iter_layout

from ..typing import CQ, K1, P1, P2, C, CnQ, CnR, P, R, T
from .harvest import FnHarvestControl
from .implement import FnImplementEntity
from .record import FnImplement, FnOverloadSignal

CollectEndpointTarget = Generator[FnOverloadSignal, None, T]

A = TypeVar("A")
B = TypeVar("B", contravariant=True)


class EndpointCollectReceiver(Protocol[CnR]):
    @overload
    def __call__(self: EndpointCollectReceiver[None], entity: C) -> FnImplementEntity[C]: ...
    @overload
    def __call__(self: EndpointCollectReceiver[C], entity: FnImplementEntity[C]) -> FnImplementEntity[C]: ...
    @overload
    def __call__(self: EndpointCollectReceiver[C], entity: C) -> FnImplementEntity[C]: ...


class FnCollectEndpointAgent(Generic[P, CnQ, A, B]):
    endpoint: FnCollectEndpoint[P, CnQ]
    referrer_instance: A
    referrer_owner: type[B]

    def __init__(self, endpoint: FnCollectEndpoint[P, CnQ], referrer_instance: A, referrer_owner: type[B]):
        self.endpoint = endpoint
        self.referrer_instance = referrer_instance
        self.referrer_owner = referrer_owner

    @overload
    def __call__(
        self: FnCollectEndpointAgent[Concatenate[type[K1], P1], CQ, None, type[K1]], *args: P1.args, **kwargs: P1.kwargs
    ) -> EndpointCollectReceiver[CQ]: ...

    @overload
    def __call__(
        self: FnCollectEndpointAgent[Concatenate[K1, P1], CQ, K1, type], *args: P1.args, **kwargs: P1.kwargs
    ) -> EndpointCollectReceiver[CQ]: ...

    def __call__(self, *args, **kwargs) -> EndpointCollectReceiver:
        def receiver(entity: C | FnImplementEntity[C]) -> FnImplementEntity[C]:
            if not isinstance(entity, FnImplementEntity):
                entity = FnImplementEntity(entity)

            entity.add_target(
                self.endpoint, self.endpoint.target.__get__(self.referrer_instance, self.referrer_owner)(*args, **kwargs)
            )
            return entity

        return receiver

    def get_control(self: FnCollectEndpointAgent[..., C, Any, Any]) -> FnHarvestControl[C]:
        sig = self.endpoint.signature

        for i in iter_layout(self.endpoint):
            if sig in i.fn_implements:
                record = i.fn_implements[sig]
                break
        else:
            raise NotImplementedError(f"Cannot find record for {sig!r} in {self.endpoint!r}")

        return FnHarvestControl(self.endpoint, record)


@dataclass(init=False, eq=True, unsafe_hash=True)
class FnCollectEndpoint(Generic[P, CnQ]):
    target: Callable[P, CollectEndpointTarget]

    @overload
    def __init__(self: FnCollectEndpoint[P1, Callable[P2, R]], target: Callable[P1, CollectEndpointTarget[Callable[P2, R]]]): ...

    @overload
    def __init__(self: FnCollectEndpoint[P1, Callable], target: Callable[P1, CollectEndpointTarget[Any]]): ...

    def __init__(self, target):
        self.target = target

    @property
    def signature(self):
        return FnImplement(self)

    @overload
    def __get__(self, instance: FnCollectEndpointAgent, owner: Any) -> Self: ...

    @overload
    def __get__(self, instance: A, owner: type[B]) -> FnCollectEndpointAgent[P, CnQ, A, type[B]]: ...

    def __get__(self, instance, owner):
        if isinstance(instance, FnCollectEndpointAgent):
            return self

        return FnCollectEndpointAgent(self, instance, owner)

    def __call__(self: FnCollectEndpoint[P1, CQ], *args: P1.args, **kwargs: P1.kwargs) -> EndpointCollectReceiver[CQ]:
        def receiver(entity: C | FnImplementEntity[C]) -> FnImplementEntity[C]:
            if not isinstance(entity, FnImplementEntity):
                entity = FnImplementEntity(entity)

            entity.add_target(self, self.target(*args, **kwargs))
            return entity

        return receiver

    def get_control(self: FnCollectEndpoint[..., C]) -> FnHarvestControl[C]:
        sig = self.signature

        for i in iter_layout(self):
            if sig in i.fn_implements:
                record = i.fn_implements[sig]
                break
        else:
            raise NotImplementedError  # TODO

        return FnHarvestControl(self, record)
