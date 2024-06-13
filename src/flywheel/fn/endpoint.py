from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generator, Generic, Protocol, overload

from typing_extensions import Concatenate, Self

from ..typing import CQ, P1, P2, C, Call, CnQ, CnR, P, R, RecordsT, T
from .compose import FnCompose
from .harvest import FnHarvestControl
from .implement import FnImplementEntity
from .record import FnOverloadSignal

CollectEndpointTarget = Generator[FnOverloadSignal, None, T]


class EndpointCollectReceiver(Protocol[CnR]):
    @overload
    def __call__(self: EndpointCollectReceiver[None], value: C) -> FnImplementEntity[C]: ...
    @overload
    def __call__(self: EndpointCollectReceiver[C], value: FnImplementEntity[C]) -> FnImplementEntity[C]: ...
    @overload
    def __call__(self: EndpointCollectReceiver[C], value: C) -> FnImplementEntity[C]: ...


@dataclass(init=False, eq=True, unsafe_hash=True)
class FnCollectEndpoint(Generic[P, CnQ]):
    @overload
    def __init__(
        self: FnCollectEndpoint[P1, Callable[P2, R]],
        target: Call[Concatenate[Any, P1], CollectEndpointTarget[Callable[P2, R]]],
    ) -> None: ...

    @overload
    def __init__(
        self: FnCollectEndpoint[P1, None],
        target: Callable[Concatenate[Any, P1], CollectEndpointTarget[T]],
    ): ...

    def __init__(self, target):
        if TYPE_CHECKING:
            self.target = target
        else:
            self.target = target.__func__

    def __set_name__(self, owner: type[FnCompose], name: str):
        self.compose = owner

    @property
    def fn(self):
        return self.compose.fn

    @overload
    def __get__(self: FnCollectEndpoint[P1, None], instance: None, owner: type) -> Callable[P1, EndpointCollectReceiver[Callable]]: ...

    @overload
    def __get__(self: FnCollectEndpoint[P1, CQ], instance: None, owner: type) -> Callable[P1, EndpointCollectReceiver[CQ]]: ...

    @overload
    def __get__(self, instance: Any, owner) -> Self: ...

    def __get__(self, instance, owner) -> Any:
        if instance is None:
            return self.get_collect_entity

        return self

    @overload
    def get_control(self: FnCollectEndpoint[..., C], records: RecordsT) -> FnHarvestControl[C]: ...
    @overload
    def get_control(self: FnCollectEndpoint[..., None], records: RecordsT) -> FnHarvestControl[Callable]: ...

    def get_control(self, records: RecordsT) -> FnHarvestControl:
        return FnHarvestControl(self, records)

    def get_collect_entity(self, *args: P.args, **kwargs: P.kwargs):
        def receiver(entity: C | FnImplementEntity[C]) -> FnImplementEntity[C]:
            if not isinstance(entity, FnImplementEntity):
                entity = FnImplementEntity(entity)

            entity.add_target(self, self.compose, *args, **kwargs)
            return entity

        return receiver
