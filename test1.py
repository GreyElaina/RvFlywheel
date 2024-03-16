from typing import Protocol

from flywheel.fn.base import Fn
from flywheel.fn.compose import FnCompose
from flywheel.fn.implement import OverloadRecorder
from flywheel.fn.record import FnRecord
from flywheel.overloads import SimpleOverload


@Fn.declare
class greet(FnCompose):
    name = SimpleOverload("name")

    def call(self, record: FnRecord, name: str) -> str:
        entities = self.load(self.name.dig(record, name))
        # entities 会自动读取到 collect 中对于 implement 参数的类型并返回。

        if not entities:
            return f"Ordinary, {name}."

        return entities.first(name)

    # 定义 Fn 实现的类型并在 collect 方法中引用。
    class ShapeCall(Protocol):
        def __call__(self, name: str) -> str:
            ...

    def collect(self, recorder: OverloadRecorder[ShapeCall], *, name: str):
        recorder.use(self.name, name)


from flywheel.context import CollectContext, InstanceContext
from flywheel.globals import global_collect
from flywheel.instance_of import InstanceOf
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
