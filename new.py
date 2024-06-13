from __future__ import annotations

from typing import TypeVar

from flywheel.fn.base import Fn
from flywheel.fn.compose import FnCompose
from flywheel.fn.endpoint import FnCollectEndpoint
from flywheel.globals import global_collect
from flywheel.overloads import SimpleOverload
from flywheel.typing import RecordsT
from typing_extensions import reveal_type

T = TypeVar("T")


@Fn
class test(FnCompose):
    sim = SimpleOverload("sim")

    @FnCollectEndpoint
    @classmethod
    def normal(cls, type: type[T]):
        yield cls.sim.hold(type)

        def shape(type: type[T]) -> T: ...
        return shape

    def call(self, records: RecordsT, type: type[T]) -> T:
        a = self.normal.get_control(records).use(self.sim, type).first
        return a(type)


reveal_type(test._.normal(int))


@global_collect
@test._.normal(type=int)
def s(type: type[int]):
    return 1


@global_collect
@test._.normal(type=str)
def s1(type: type[str]):
    return "111"


a = test(int)
b = test(str)

print(a)
print(b)
