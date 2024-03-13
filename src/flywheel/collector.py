from __future__ import annotations

import functools
from typing import Any, Callable

from .context import CollectContext
from .globals import COLLECTING_CONTEXT_VAR, GLOBAL_INSTANCE_CONTEXT, INSTANCE_CONTEXT_VAR
from .typing import TYPE_CHECKING, P, R, TEntity

if TYPE_CHECKING:
    from typing_extensions import Concatenate

    from .fn.record import FnImplement, FnRecord


class Collector(CollectContext):
    fn_implements: dict[FnImplement, FnRecord]
    finalize_cbs: list[Callable[[Collector], Any]]
    cls: type | None = None

    def __init__(self) -> None:
        self.fn_implements = {}
        self.finalize_cbs = []

    @classmethod
    def env(cls):
        instance = cls()
        instance.fn_implements = COLLECTING_CONTEXT_VAR.get().fn_implements
        return instance

    def finalize(self):
        for cb in self.finalize_cbs:
            cb(self)

    def on_collected(self, func: Callable[[Collector], Any]):
        self.finalize_cbs.append(func)
        return func

    def remove_collected_callback(self, func: Callable[[Collector], Any]):
        self.finalize_cbs.remove(func)
        return func

    @property
    def entrypoint(self):
        class LocalEndpoint:
            collector = self

            def __init_subclass__(cls, *, static: bool = False) -> None:
                self.cls = cls
                self.finalize()

                if static:
                    GLOBAL_INSTANCE_CONTEXT.instances[cls] = cls()

            @staticmethod
            def collect(entity: TEntity) -> TEntity:  # type: ignore
                return entity.collect(self)

            @staticmethod
            def ensure_self(func: Callable[Concatenate[Any, P], R]):
                @functools.wraps(func)
                def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                    assert self.cls is not None

                    instance = INSTANCE_CONTEXT_VAR.get().instances[self.cls]
                    return func(instance, *args, **kwargs)

                return wrapper

        return LocalEndpoint
