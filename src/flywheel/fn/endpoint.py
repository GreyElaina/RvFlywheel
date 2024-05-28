from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generator, Generic, Protocol, TypeVar, Union, overload

from typing_extensions import Concatenate, ParamSpec

from ..typing import RecordsT
from .compose import FnCompose
from .harvest import FnHarvestControl
from .implement import FnImplementEntity
from .record import FnOverloadSignal

T = TypeVar("T")
T_contra = TypeVar("T_contra", contravariant=True)
C = TypeVar("C", bound=Callable)
C_contra = TypeVar("C_contra", contravariant=True, bound=Callable)
CNR = TypeVar("CNR", covariant=True, bound=Union[Callable, None])
CN_contra = TypeVar("CN_contra", contravariant=True, bound=Union[Callable, None])
P = ParamSpec("P")
K = TypeVar("K")

P1 = ParamSpec("P1")
R = TypeVar("R", covariant=True)
P2 = ParamSpec("P2")

CollectEndpointTarget = Generator[FnOverloadSignal, None, T]


class EndpointCollectReceiver(Protocol[CNR]):
    @overload
    def __call__(self: EndpointCollectReceiver[None], value: C) -> FnImplementEntity[C]: ...
    @overload
    def __call__(self: EndpointCollectReceiver[C], value: FnImplementEntity[C]) -> FnImplementEntity[C]: ...
    @overload
    def __call__(self: EndpointCollectReceiver[C], value: C) -> FnImplementEntity[C]: ...


@dataclass(init=False, eq=True, unsafe_hash=True)
class FnCollectEndpoint(Generic[P, CN_contra]):
    @overload
    def __init__(
        self: FnCollectEndpoint[P1, Callable[P2, R]],
        target: Callable[Concatenate[Any, P1], CollectEndpointTarget[Callable[P2, R]]],
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
    def __get__(self: FnCollectEndpoint[P1, None], instance: None, owner: type[K]) -> Callable[P1, EndpointCollectReceiver[Callable]]:
        ...

    @overload
    def __get__(self: FnCollectEndpoint[P1, C_contra], instance: None, owner: type[K]) -> Callable[P1, EndpointCollectReceiver[C_contra]]:
        ...

    @overload
    def __get__(
        self: FnCollectEndpoint[..., None], instance: FnCompose, owner: Any
    ) -> Callable[[RecordsT], FnHarvestControl[Callable]]: ...

    @overload
    def __get__(
        self: FnCollectEndpoint[..., C_contra], instance: FnCompose, owner: Any
    ) -> Callable[[RecordsT], FnHarvestControl[C_contra]]: ...

    def __get__(self, instance, owner) -> Any:
        if instance is None:
            return self.get_collect_receiver

        def harvest_wrapper(records: RecordsT):
            return self.get_harvest_control(instance, records)

        return harvest_wrapper

    def get_harvest_control(self, instance: FnCompose, records: RecordsT) -> FnHarvestControl:
        return FnHarvestControl(self, instance, records)
    
    def get_collect_receiver(self, *args: P.args, **kwargs: P.kwargs):
        def receiver(entity: C | FnImplementEntity[C]) -> FnImplementEntity[C]:
            if not isinstance(entity, FnImplementEntity):
                entity = FnImplementEntity(entity)

            entity.add_target(self, self.compose, *args, **kwargs)
            return entity
        return receiver