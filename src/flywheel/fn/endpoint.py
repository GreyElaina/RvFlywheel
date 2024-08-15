from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generator, Generic, Protocol, TypeVar, overload

from typing_extensions import Concatenate, Self

from ..typing import CQ, K1, P1, P2, C, CnQ, CnR, P, R, T
from .implement import FnImplementEntity
from .record import CollectSignal, FnRecordLabel
from .selection import Candidates

CollectEndpointTarget = Generator[CollectSignal, None, T]

A = TypeVar("A")
B = TypeVar("B", contravariant=True)


class EndpointCollectReceiver(Protocol[CnR]):
    @overload
    def __call__(self: EndpointCollectReceiver[None], entity: C) -> FnImplementEntity[C]: ...
    @overload
    def __call__(self: EndpointCollectReceiver[C], entity: FnImplementEntity[C]) -> FnImplementEntity[C]: ...
    @overload
    def __call__(self: EndpointCollectReceiver[C], entity: C) -> FnImplementEntity[C]: ...


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
    def descriptor(self):
        return FnCollectDescriptor(self)

    @property
    def signature(self):
        return FnRecordLabel(self)

    def __call__(self: FnCollectEndpoint[P1, CQ], *args: P1.args, **kwargs: P1.kwargs) -> EndpointCollectReceiver[CQ]:
        def receiver(entity: C | FnImplementEntity[C]) -> FnImplementEntity[C]:
            if not isinstance(entity, FnImplementEntity):
                entity = FnImplementEntity(entity)

            entity.add_target(self, self.target(*args, **kwargs))
            return entity

        return receiver  # type: ignore

    def select(self: FnCollectEndpoint[..., C], expect_complete: bool = True) -> Candidates[C]:
        return Candidates(self, expect_complete)


@dataclass
class FnCollectDescriptor(Generic[P, CnQ]):
    endpoint: FnCollectEndpoint[P, CnQ]

    @overload
    def __get__(self, instance: FnCollectEndpointAgent, owner: Any) -> Self: ...

    @overload
    def __get__(self, instance: A, owner: type[B]) -> FnCollectEndpointAgent[P, CnQ, A, type[B]]: ...

    def __get__(self, instance, owner):
        if isinstance(instance, FnCollectEndpointAgent):
            return self

        return FnCollectEndpointAgent(self.endpoint, instance, owner)

    def __call__(self: FnCollectDescriptor[P1, CQ], *args: P1.args, **kwargs: P1.kwargs) -> EndpointCollectReceiver[CQ]:
        return self.endpoint.__call__(*args, **kwargs)


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

    def select(self: FnCollectEndpointAgent[..., C, Any, Any], expect_complete: bool = True) -> Candidates[C]:
        return self.endpoint.select(expect_complete)


@overload
def wrap_endpoint(
    target: Callable[P1, CollectEndpointTarget[Callable[P2, R]]],
) -> FnCollectDescriptor[P1, Callable[P2, R]]: ...
@overload
def wrap_endpoint(target: Callable[P1, CollectEndpointTarget[Any]]) -> FnCollectDescriptor[P1, Callable]: ...
def wrap_endpoint(target):
    return FnCollectEndpoint(target).descriptor
