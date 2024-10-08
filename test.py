from __future__ import annotations

from typing import Any, TypeVar

from flywheel.fn.endpoint import FnCollectEndpoint, wrap_endpoint
from flywheel.globals import global_collect
from flywheel.overloads import SimpleOverload, TypeOverload

T = TypeVar("T")


class test:
    type = TypeOverload("type")
    sim = SimpleOverload("sim")

    def call(self, value: type[T]) -> T:
        for selection in self.collect.select():
            if not selection.harvest(self.sim, value):
                continue

            selection.complete()

        return selection(value)

    @wrap_endpoint
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


global_collect(test.collect(type=str)(test_impl_str))


@global_collect
@test.collect(type=int)
def test_impl_int(value: type[int]):
    return 11


# reveal_type(test)
import timeit

from viztracer import VizTracer

tracer = VizTracer()
tracer.start()

num = 3000
delta_a = timeit.timeit("test_impl_str('11')", globals=globals(), number=num)
delta_b = timeit.timeit("test().call(str)", globals=globals(), number=num)

print(f"test_impl_int: {delta_a}, call: {delta_b}, {delta_b/delta_a}, {num/delta_a}o/s, {num/delta_b}o/s")

tracer.stop()
tracer.save()  # also takes output_file as an optional argument
