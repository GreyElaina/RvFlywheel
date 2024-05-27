from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generator, Generic, Protocol, TypeVar, overload

from typing_extensions import Concatenate, ParamSpec

from .compose import FnCompose
from .harvest import FnHarvestControl
from .implement import FnImplementEntity
from .record import FnOverloadSignal, FnRecord

T = TypeVar("T")
T_contra = TypeVar("T_contra", contravariant=True)
C = TypeVar("C", bound=Callable)
C_contra = TypeVar("C_contra", contravariant=True, bound=Callable)
P = ParamSpec("P")
K = TypeVar("K")

K1 = TypeVar("K1")
P1 = ParamSpec("P1")
R = TypeVar("R", covariant=True)
P2 = ParamSpec("P2")


class EndpointCollectReceiver(Protocol[P, C]):
    @overload
    def __call__(self, value: FnImplementEntity[C]) -> FnImplementEntity[C]: ...
    @overload
    def __call__(self, value: C) -> FnImplementEntity[C]: ...


@dataclass(init=False, eq=True, unsafe_hash=True)
class FnCollectEndpoint(Generic[P, C_contra]):  # FIXME: should <: classmethod.
    @overload
    def __init__(
        self: FnCollectEndpoint[P1, Callable],
        target: Callable[Concatenate[Any, P1], Generator[FnOverloadSignal, None, None]],
    ): ...

    @overload
    def __init__(
        self: FnCollectEndpoint[P1, Callable[P2, R]],
        target: Callable[Concatenate[Any, P1], Generator[FnOverloadSignal, None, Callable[P2, R] | Any]],
    ) -> None: ...

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
    def __get__(self, instance: None, owner: type[K]) -> Callable[P, EndpointCollectReceiver[P, C_contra]]:
        # 这段类型理论上会让 FnImplementEntity 上的类型被保留。
        # 但我不确定 Unknown 并上去会不会被 Pyright 识别为 Any，从而 pass check。
        ...

    @overload
    def __get__(
        self, instance: FnCompose, owner: Any
    ) -> Callable[[dict[FnCollectEndpoint, FnRecord]], FnHarvestControl[C_contra]]: ...

    def __get__(self, instance, owner) -> Any:
        if instance is None:

            def wrapper(*args: P.args, **kwargs: P.kwargs):
                def receive(entity: C | FnImplementEntity) -> FnImplementEntity[C]:
                    if not isinstance(entity, FnImplementEntity):
                        entity = FnImplementEntity(entity)

                    entity.add_target(self, owner, *args, **kwargs)
                    return entity

                return receive

            return wrapper

        def harvest_wrapper(records: dict[FnCollectEndpoint, FnRecord]):
            return FnHarvestControl(self, instance, records)

        return harvest_wrapper
