from __future__ import annotations

from flywheel.context import InstanceContext
from flywheel.fn.endpoint import FnCollectEndpoint
from flywheel.globals import global_collect
from flywheel.overloads import SimpleOverload
from typing_extensions import reveal_type


class greet():
    name = SimpleOverload("name")

    @classmethod
    def call(cls, name: str) -> str:
        for selection in cls.collect.select(False):
            if not selection.harvest(cls.name, name):
                continue

            selection.complete()

        if not selection:
            return f"Ordinary, {name}."

        return selection(name)

    @FnCollectEndpoint
    @classmethod
    def collect(cls, *, name: str):
        yield cls.name.hold(name)

        def shape(name: str) -> str:
           ...
        return shape




@global_collect
@greet.collect(name="Teague")
@greet.collect(name="Grey")
def greet_someone(name: str) -> str:
    return "Stargaztor"


reveal_type(greet_someone)

with InstanceContext().scope() as ins:
    ins.instances[str] = "test"

    print(greet.call("Teague"))
    print(greet.call("Grey"))
    print(greet.call("Hizuki"))
