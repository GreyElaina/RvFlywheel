from __future__ import annotations

from flywheel.context import CollectContext, InstanceContext
from flywheel.fn.endpoint import FnCollectEndpoint, wrap_endpoint
from flywheel.globals import global_collect, local_collect
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
            break
        else:
            return f"Ordinary, {name}."

        return selection(name)

    @wrap_endpoint
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

with InstanceContext().scope() as ins, CollectContext().scope() as cs:
    ins.instances[str] = "test"

    @local_collect
    @greet.collect(name="Grey")
    def greey_grey(name: str) -> str:
        print("1111", greet.call(name))
        return "Grey"
    
    print(cs.fn_implements)    

    #print(greet.call("Teague"))
    print(greet.call("Grey"))
    #print(greet.call("Hizuki"))

