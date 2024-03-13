from __future__ import annotations

from sys import path

path.append("src")

from typing import Protocol, TypeVar

from flywheel.builtins.overloads import SimpleOverload, TypeOverload
from flywheel.fn.base import Fn
from flywheel.fn.compose import FnCompose
from flywheel.globals import global_collect
from flywheel.typing import CallGen

T = TypeVar("T")


@Fn.declare
class test(FnCompose):
    type = TypeOverload().as_agent()
    sim = SimpleOverload().as_agent()

    def call(self, value: type[T]) -> CallGen[T]:
        with self.harvest() as entities:
            yield self.sim.call(value)

        return entities.first(value)

    class ShapeCall(Protocol[T]):
        def __call__(self, value: type[T]) -> T:
            ...

    # TODO: 把这个 implement 扬了。
    def collect(self, implement: ShapeCall[T], *, type: type[T]):
        yield self.sim.collect(type)


@global_collect
@test.implements(type=str)
def test_impl_str(value: type[str]):
    return "11"


@global_collect
@test.implements(type=int)
def test_impl_int(value: type[int]) -> int:
    return 42


from viztracer import VizTracer

tracer = VizTracer()
tracer.start()

for _ in range(50):
    test_impl_int(int)

for _ in range(50):
    test.call(int)

tracer.stop()
tracer.save() # also takes output_file as an optional argument

