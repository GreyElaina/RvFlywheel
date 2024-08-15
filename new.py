from __future__ import annotations

from typing import TypeVar

from flywheel.fn.endpoint import FnCollectEndpoint
from flywheel.globals import global_collect, iter_layout
from flywheel.overloads import SimpleOverload
from flywheel.scoped import scoped_collect
from typing_extensions import reveal_type

T = TypeVar("T")

class test():
    sim = SimpleOverload("sim")

    @FnCollectEndpoint
    @classmethod
    def normal(cls, type: type[T]):
        yield cls.sim.hold(type)

        def shape(type: type[T]) -> T: ...
        return shape

    def call(self, type: type[T]) -> T:
        for selection in self.normal.select():
            if not selection.harvest(self.sim, type):
                continue

            selection.complete()

        return selection(type)

@FnCollectEndpoint
def normal_bare(type: type[T]):
    yield test.sim.hold(type)

    def shape(type: type[T]) -> T: ...
    return shape

reveal_type(test.normal)
reveal_type(test.normal(int))

reveal_type(normal_bare)
reveal_type(normal_bare(int))

@global_collect
@test.normal(type=int)
def s(type: type[int]):
    return 1


@global_collect
@test.normal(type=str)
def s1(type: type[str]):
    return "111"


a = test().call(int)
b = test().call(str)

print(a)
print(b)


class test1(m := scoped_collect.locals().target, static=True):
    @m.impl(test.normal(type=int))
    def s(self, type: type[int]):
        return 2

with test1.collector.lookup_scope():
    #print([i.fn_implements for i in iter_layout()])
    
    a = test().call(int)
    b = test().call(str)

    print(a)
    print(b)
