from typing import Protocol

from flywheel.overloads import SimpleOverload
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
    def collect(self, recorder: OverloadRecorder[ShapeCall], *, name: str):
        recorder.use(self.name, name)


from flywheel.instance_of import InstanceOf
from flywheel.context import CollectContext, InstanceContext
from flywheel.globals import global_collect
from flywheel.scoped import scoped_collect


@global_collect
@greet.impl(name="Teague")
@greet.impl(name="Grey")
def greet_someone(name: str) -> str:
    return "Stargaztor"


with InstanceContext().scope() as ins:
    ins.instances[str] = "test"

    print(greet("Teague"))
    print(greet("Grey"))
    print(greet("Hizuki"))
