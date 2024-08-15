from __future__ import annotations

from flywheel import wrap_anycast
from flywheel.globals import local_collect


@wrap_anycast
def test(s: str) -> str:
    return s

print(test("test"))

@local_collect
@test.override
def test_alter(s: str) -> str:
    return "test"

print(test("test1"))