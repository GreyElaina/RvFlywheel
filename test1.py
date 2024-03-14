from typing import Protocol

from flywheel.builtins.overloads import SimpleOverload
from flywheel.fn.base import Fn
from flywheel.fn.compose import FnCompose, OverloadRecorder
from flywheel.fn.record import FnRecord


@Fn.declare
class greet(FnCompose):
    name = SimpleOverload().as_agent()

    def call(self, record: FnRecord, name: str) -> str:
        entities = self.harvest_from(self.name.harvest(record, name))
        # entities 会自动读取到 collect 中对于 implement 参数的类型并返回。

        if not entities:
            return f"Ordinary, {name}."

        return entities.first(name)

    # 定义 Fn 实现的类型并在 collect 方法中引用。
    class ShapeCall(Protocol):
        def __call__(self, name: str) -> str:
            ...

    # 使用 FnCompose.use_recorder 避免过于繁琐的调用。
    @FnCompose.use_recorder
    def collect(self, recorder: OverloadRecorder, implement: ShapeCall, *, name: str):
        recorder.use(self.name, name)


from flywheel.globals import global_collect
from flywheel.scoped import scoped_collect


class greet_implements(m := scoped_collect.globals().target, static=True):
    @m.collect
    @greet.implements(name="Teague")
    @m.ensure_self
    def greet_teague(self, name: str) -> str:
        return "Stargaztor, but in name only."

    @m.collect
    @greet.implements(name="Grey")
    @m.ensure_self
    def greet_grey(self, name: str) -> str:
        return "Symbol, the Founder."


print(greet.call("Teague"))
print(greet.call("Grey"))
print(greet.call("Hizuki"))