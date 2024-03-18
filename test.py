from __future__ import annotations

from sys import path
from typing import Callable, Protocol, TypeVar, reveal_type

from flywheel.fn.base import Fn
from flywheel.fn.compose import FnCompose
from flywheel.fn.implement import OverloadRecorder
from flywheel.fn.record import FnRecord
from flywheel.globals import global_collect
from flywheel.overloads import SimpleOverload, TypeOverload

T = TypeVar("T")


@Fn.declare
class test(FnCompose):
    type = TypeOverload("type")
    sim = SimpleOverload("sim")

    def call(self, record: FnRecord, value: type[T]) -> T:
        entities = self.load(self.sim.dig(record, value))

        return entities.first(value)

    def collect(self, recorder: OverloadRecorder, *, type: type[T]):
        recorder.use(self.sim, type)


# @global_collect
# @test.implements(type=str)
def test_impl_str(value: type[str]):
    return "11"

reveal_type(test)
reveal_type(test.impl(type=str))
global_collect(test.impl(type=str)(test_impl_str))


@global_collect
@test.impl(type=int)
def test_impl_int(value: type[str]):
    return 11
#reveal_type(test)
import timeit

from viztracer import VizTracer

#tracer = VizTracer()
#tracer.start()

num = 100000
delta_a = timeit.timeit("test_impl_str('11')", globals=globals(), number=num)
delta_b = timeit.timeit("test(str)", globals=globals(), number=num)

print(f"test_impl_int: {delta_a}, call: {delta_b}, {delta_b/delta_a}, {num/delta_a}o/s, {num/delta_b}o/s")

#tracer.stop()
#tracer.save()  # also takes output_file as an optional argument
