from __future__ import annotations

from sys import path
from typing import Any, Callable, Protocol, TypeVar

from flywheel.fn.base import Fn
from flywheel.fn.compose import FnCompose
from flywheel.fn.endpoint import FnCollectEndpoint
from flywheel.fn.record import FnRecord
from flywheel.globals import global_collect
from flywheel.overloads import SimpleOverload, TypeOverload

T = TypeVar("T")


@Fn
class test(FnCompose):
    type = TypeOverload("type")
    sim = SimpleOverload("sim")

    def call(self, records, value: type[T]) -> T:
        entities = self.collect(records).use(self.sim, value)

        return entities.first(value)

    @FnCollectEndpoint
    @classmethod
    def collect(cls, type: type[T]):
        yield cls.sim.hold(type)

        def shape(value: type[T]) -> T: ...

        return shape


# @global_collect
# @test.implements(type=str)
def test_impl_str(value: type[str]):
    return "11"


def t(value: type[Any]) -> Any: ...


global_collect(test._.collect(type=str)(test_impl_str))


@global_collect
@test._.collect(type=int)
def test_impl_int(value: type[int]):
    return 11


# reveal_type(test)
import timeit

from viztracer import VizTracer

tracer = VizTracer()
tracer.start()

num = 100000
delta_a = timeit.timeit("test_impl_str('11')", globals=globals(), number=num)
delta_b = timeit.timeit("test(str)", globals=globals(), number=num)

print(f"test_impl_int: {delta_a}, call: {delta_b}, {delta_b/delta_a}, {num/delta_a}o/s, {num/delta_b}o/s")

tracer.stop()
tracer.save()  # also takes output_file as an optional argument
