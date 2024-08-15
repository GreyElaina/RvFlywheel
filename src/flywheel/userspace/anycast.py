from __future__ import annotations

from typing import Callable, Generic

from flywheel.overloads import SimpleOverload

from ..fn.endpoint import FnCollectEndpoint
from ..typing import CR, P, R

ANYCAST_OVERLOAD = SimpleOverload("flywheel.userspace.anycast")

class Anycast(Generic[CR]):
    endpoint: FnCollectEndpoint[[], CR]
    prototype: CR
    
    def __init__(self, prototype: CR):
        self.endpoint = FnCollectEndpoint(self._prototype_collect)
        self.prototype = prototype
    
    @staticmethod
    def _prototype_collect():
        yield ANYCAST_OVERLOAD.hold(None)

    def __call__(self: Anycast[Callable[P, R]], *args: P.args, **kwargs: P.kwargs) -> R:
        for selection in self.endpoint.select(False):
            if selection.harvest(ANYCAST_OVERLOAD, None):
                selection.complete()
                break
        else:
            return self.prototype(*args, **kwargs)
        
        return selection(*args, **kwargs)

    @property
    def override(self):
        return self.endpoint()


def wrap_anycast(entity: CR) -> Anycast[CR]:
    return Anycast(entity)
