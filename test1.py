from __future__ import annotations

from flywheel.context import InstanceContext
from flywheel.fn.base import Fn
from flywheel.fn.compose import FnCompose
from flywheel.fn.endpoint import FnCollectEndpoint
from flywheel.globals import global_collect
from flywheel.overloads import SimpleOverload
from typing_extensions import reveal_type


@Fn
class greet(FnCompose):
    name = SimpleOverload("name")

    def call(self, records, name: str) -> str:
        entities = self.collect(records).use(self.name, name)

        if not entities:
            return f"Ordinary, {name}."

        return entities.first(name)

    @FnCollectEndpoint
    @classmethod
    def collect(cls, *, name: str):
        yield cls.name.hold(name)

        # def shape(name: str) -> str:
        #    ...
        # return shape


@global_collect
@greet._.collect(name="Teague")
@greet._.collect(name="Grey")
def greet_someone(name: str) -> str:
    return "Stargaztor"


reveal_type(greet_someone)

with InstanceContext().scope() as ins:
    ins.instances[str] = "test"

    print(greet("Teague"))
    print(greet("Grey"))
    print(greet("Hizuki"))
