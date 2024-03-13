from __future__ import annotations

from dataclasses import dataclass, field
from itertools import cycle
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .base import Fn
    from .overload import FnOverload

@dataclass(slots=True)
class FnRecord:
    spec: Fn
    scopes: dict[str, dict[Any, Any]] = field(default_factory=dict)
    entities: dict[frozenset[tuple[str, "FnOverload", Any]], Callable] = field(default_factory=dict)


@dataclass(slots=True, unsafe_hash=True)
class FnImplement:
    fn: Fn

    @staticmethod
    def flatten_record(record: FnRecord, target: FnRecord) -> None:
        target.spec = record.spec

    @staticmethod
    def flatten_entity(
        record: FnRecord,
        signature: tuple[tuple[str, "FnOverload", Any], ...],
        entity: Callable,
        replacement: Callable | None,
    ) -> None:
        scopes = record.scopes
        for segment in signature:
            name, fn_overload, sign = segment
            if name not in scopes:
                scope = scopes[name] = {}
            else:
                scope = scopes[name]

            target_set = fn_overload.collect(scope, sign)
            if replacement is not None:
                if replacement in target_set:
                    del target_set[replacement]

                for k, v in record.entities.items():
                    if v == replacement:
                        record.entities[k] = replacement
                        break
                else:
                    raise TypeError

            target_set[entity] = None

        record.entities[frozenset(signature)] = entity

    def merge(self, inbound: list[FnRecord], outbound: list[dict[FnImplement, FnRecord]]) -> None:
        outbound_depth = len(outbound)

        grouped = {}
        record_update_tasks = []

        for record in inbound:
            for identity, entity in record.entities.items():
                if identity in grouped:
                    group = grouped[identity]
                else:
                    group = grouped[identity] = []

                group.append((record, entity))

        for identity, group in grouped.items():
            outbound_index = 0
            for group_index in cycle(range(len(group))):
                twin = group[group_index]

                if twin is None:
                    break

                record, entity = twin

                if outbound_index == outbound_depth:
                    v: dict[FnImplement, FnRecord] = {self: FnRecord(self.fn)}
                    outbound.insert(outbound_index, v)
                    outbound_depth += 1
                else:
                    v = outbound[outbound_index]

                if self in v:
                    target_record = v[self]
                else:
                    target_record = v[self] = FnRecord(self.fn)

                if identity in target_record.entities:
                    e = target_record.entities[identity]
                    group[group_index] = (target_record, e)
                    record_update_tasks.append((lambda x, y: lambda: self.flatten_record(x, y))(record, target_record))
                    self.flatten_entity(target_record, identity, entity, e)
                else:
                    group[group_index] = None
                    self.flatten_entity(target_record, identity, entity, None)

                outbound_index += 1

        for i in record_update_tasks[::-1]:
            i()


@dataclass(eq=True, frozen=True, slots=True)
class FnOverloadHarvest:
    name: str
    overload: FnOverload
    value: Any
