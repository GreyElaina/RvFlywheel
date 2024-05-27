# Ryanvk Flywheel

Ryanvk Flywheel is a utility designed in the Ryanvk style.

[中文说明](./README.zh.md)

- Near-perfect free overload at a single entry point;
- Simple and flexible overload mechanism;
- Cutting-edge type support [^1] [^2];
- Switchable contexts.

Available on PyPI: `elaina-flywheel`.

[^1]: Only available on Pyright / Basedpyright.
[^2]: Some issues remain unresolved, such as unexpected type information loss in `FnImplementEntity` due to check-and-narrowing behavior.

## Usage

Flywheel focuses on constructing around `Fn` to provide powerful overloading functionality.

You can create an `Fn` with simple overloading (`SimpleOverload`) like this:

```python
from typing import Protocol

from flywheel import Fn, FnCompose, FnRecord, SimpleOverload, FnCollectEndpoint

@Fn
class greet(FnCompose):
    name = SimpleOverload("name")

    def call(self, records, name: str) -> str:
        # We don't care about the type of records.
        # If you do, it is dict[FnCollectEndpoint, FnImplementEntity]

        entities = self.someone(records).use(self.name, name)
        return entities.first(name)

    @FnCollectEndpoint
    @classmethod
    def someone(cls, *, name: str):
        yield cls.name.hold(name)

        # Optionally, you can provide the implementation type; we don't care about it at runtime, so you can place it in if TYPE_CHECKING.
        def shape(name: str) -> str: ...
        return shape
```

Then, we propose two implementations for `greet`:

- Return `"Stargaztor, but in name only."` when `name` is `Teague`;
- Return `"Symbol, the Founder."` when `name` is `Grey`.

After proposing implementations, we need to collect them so that Flywheel's internal system can see, and call these implementations. Here, we use the `global_collect` function to collect implementations into the global context.

```python
from flywheel import global_collect

@global_collect
@greet._.someone(name="Teague")
def greet_teague(name: str) -> str:
    return "Stargaztor, but in name only."

@global_collect
@greet._.someone(name="Grey")
def greet_grey(name: str) -> str:
    return "Symbol, the Founder."
```

Then we call.

```python
>>> greet("Teague")
'Stargaztor, but in name only.'
>>> greet("Grey")
'Symbol, the Founder.'
```

It looks good, dispatching to the appropriate implementation as expected. What happens if we input an unimplemented field?

```python
>>> greet("Hizuki")
NotImplementedError: cannot lookup any implementation with given arguments
```

Clearly, we haven't implemented a `greet` for `"Hizuki"`. To handle such situations, we can modify the declaration of `greet`:

```python
@Fn.declare
class greet(FnCompose):
    name = SimpleOverload("name")  # Specify that name is required.

    def call(self, records, name: str) -> str:
        # We don't care about the type of records.
        # If you do, it is dict[FnCollectEndpoint, FnImplementEntity]

        entities = self.someone(records).use(self.name, name)

        if not entities:  # Check if there are any matching implementations
            return f"Ordinary, {name}."

        return entities.first(name)
```

This method provides an extremely flexible default implementation mechanism: now we can call `greet`.

```python
>>> greet("Hizuki")
'Ordinary, Hizuki.'
```

## Overloading Mechanism

Flywheel's overloading mechanism is implemented based on `FnOverload`, which includes the following four main functions:

- `digest`: Converts parameters provided during implementation collection (`Fn.impl` method) into storable signature objects;
- `collect`: Configures collections in its namespace for storing implementation references using the parameters in the signature;
- `harvest`: Matches collections in its namespace based on the provided values;
- `access`: Matches collections in its namespace based on the provided signature.

Here, collections are used to store references to implementations in the namespace, treating an Overload as a tag on references. This allows flexible overload configurations using different parameters and ultimately finding the corresponding implementation through intersections. Additionally, you can implement complex logic by constructing an `if/load` chain with complex logic.

> [!NOTE]  
> Flywheel uses `dict[Callable, None]` as the internal implementation of an ordered set.

For example, `SimpleOverload`:

```python
@dataclass(eq=True, frozen=True)
class SimpleOverloadSignature:
    value: Any


class SimpleOverload(FnOverload[SimpleOverloadSignature, Any, Any]):
    def digest(self, collect_value: Any) -> SimpleOverloadSignature:
        # Converts parameters provided during implementation collection into storable signature objects
        return SimpleOverloadSignature(collect_value)

    def collect(self, scope: dict, signature: SimpleOverloadSignature) -> dict[Callable, None]:
        if signature.value not in scope:
            # Configures collections in its namespace for storing implementation references. If it doesn't exist, open a new one; otherwise, reuse.
            target = scope[signature.value] = {}  
        else:
            target = scope[signature.value]

        return target

    def harvest(self, scope: dict, call_value: Any) -> dict[Callable, None]:
        # For Flywheel, "matching" is a more accurate term.
        # This allows generic matching for call values.

        if call_value in scope:
            return scope[call_value]

        return {}

    def access(self, scope: dict, signature: SimpleOverloadSignature) -> dict[Callable, None] | None:
        # Matches collections in its namespace based on the provided signature.
        # Inherited from the original Ryanvk implementation; it seems Flywheel doesn't require this to be implemented.

        if signature.value in scope:
            return scope[signature.value]
```

You can try implementing a `TypeOverload` that finds the corresponding implementation based on the type of the call value (`call_value`). As a reference, you can find the implementation in the `flywheel.overloads` module.

For `FnOverload`, it doesn't necessarily need to search for as many implementations as possible — this depends on the actual situation: if you want your `Fn` to act like an event system, in which case you'd better find as many implementations as possible — unfortunately, we don't provide any `greed` parameter, so you need to implement it yourself.

You can add constructor parameters and inherit other existing overload implementations.

```python
class SomeMaybeGreedOverload(FnOverload):
    def __init__(self, name: str, greed: bool):
        self.name = name
        self.greed = greed

    ...  # Your actual logic
```

## Context

Flywheel provides a `global_collect` function to collect implementations into the global context. Naturally, there won't be just one context; Flywheel allows you to create your own contexts and apply them as you see fit.

Correspondingly, the global context is stored in `flywheel.globals.GLOBAL_COLLECT_CONTEXT`. If you know what you're doing and need to do something necessary, this information might be useful to you. But I think most of the time you won't need this trick.

```python
from flywheel.context import CollectContext

local_cx = CollectContext()

with local_cx.collect_scope():
    # do some collect stuff;
    # Now collecting some things...
    ...

# What you just collected can't be used now...

with local_cx.lookup_scope():
    # ...Now it's okay!
    ...
```

Note that the behavior of the `global_collect` function does not change due to the presence of contexts. Therefore, you need to consider using `local_collect` to collect implementations into your context.

```python
from flywheel import local_collect

@local_collect
@greet._.someone(name="Teague")
def greet_teague(name: str) -> str:
    return "Stargaztor, but in name only."

@local_collect
@greet._.someone(name="Grey")
def greet_grey(name: str) -> str:
    return "Symbol, the Founder."
```

If you haven't used `collect_scope` before, `local_collect` will adopt the default behavior of collecting implementations into the global context.

But we do not recommend using `local_collect` in all situations; instead, use `global_collect` as much as possible, unless you are certain that your implementation needs to change due to some context in your application (e.g., Avilla needs to switch implementations based on the protocol used in the context).

## scoped_collect

If you want to keep your module's namespace clean, using `scoped_collect` might be a good idea. However, it has other more important applications, as I'll explain.

```python
from flywheel import scoped_collect

class greet_implements(m := scoped_collect.globals().target, static=True):
    @m.collect
    @greet._.someone(name="Teague")
    @m.ensure_self
    def greet_teague(self, name: str) -> str:
        return "Stargaztor, but in name only."

    # The above method is too verbose; we are considering better ways.
```

This code achieves the same effect as our initial two `greet_xxx`.

```python
>>> greet("Teague")
'Stargaztor, but in name only.'
>>> greet("Grey")
'Symbol, the Founder.'
```

This code uses the `scoped_collect.globals()` method to connect to the global context

. If you don't want this, replace it with `scoped_collect.locals()`.

```python
from flywheel import scoped_collect

class greet_implements(m := scoped_collect.locals().target, static=True):
    ...
```

When `static=True`, `greet_implements` will be instantiated and stored in the global *instance context*.  
If you have customized your constructor (i.e., `__init__` or `__new__`), an error will occur at startup. In this case, you need to implement the generation and application of the `InstanceContext` yourself.

## Stacking

Flywheel allows you to do this...:

```python
@global_collect
@greet._.someone(name="Teague")
@greet._.someone(name="Grey")
def greet_stargaztor(name: str) -> str:
    return f"Stargaztor"
```

It is equivalent to calling `FnCollectEntity` separately but written more concisely while still obtaining Flywheel's cutting-edge type support.

If you need to use it with `scoped_collect`, be sure to sandwich the `Fn.impl` call between `m.collect` and `m.ensure_self`:

```python
@m.collect
@greet._.impl(name="Teague")
@greet._.impl(name="Grey")
@m.ensure_self
def greet_teague(self, name: str) -> str:
    return f"Stargaztor."
```

## Instance Context

The instance context (`InstanceContext`) is a bridge for Flywheel to access instances in the local namespace. Moreover, you can use this feature to implicitly pass parameters to `scoped_collect`, achieving dependency injection.  
Additionally, the global instance context is also available in the `flywheel.globals` module for your free use.

```python
from flywheel import InstanceContext

instance_cx = InstanceContext()

instance_cx.instances[str] = "EMPTY"

with instance_cx.scope() as scope_cx:  # Returns the context instance; modifying the context instance returned here **will not** affect the above.
    instance_cx.instances[int] = 42  # Normal usage.

    scope_cx.store({str: "42"}, 1.14, None)
    # Equivalent to `instance_cx.store({str: "42", float: 1.14, type(None): None})`

    ...  # do other stuff
```

For lightweight purposes, we have not yet completed the merging of implementation records in different collections in Flywheel. Therefore, this method is currently only used for:

### Manually Providing Instances

For `scoped_collect` with `static=False`, you need to do this to make it work properly.

```python
instance_cx = ...
collect_cx = ...

with collect_cx.collect_scope():
    ...  # collect

with instance_cx.scope(), collect_cx.lookup_scope():
    instance_cx.instances[cls] = cls(...)

    # then normally Fn
```

### Providing Information Internally

We provide a descriptor `InstanceOf` that can automatically access the current instance context, making it convenient to access content in the instance context.

```python
from flywheel import InstanceOf

from aiohttp import ClientSession

class sth_implements(m := scoped_collect.locals().target, static=True):
    session = InstanceOf(ClientSession)

    @m.impl(...)
    async def something(self, num: int):
        await self.session.get(f"http://example.com/", params={"num": num})

# -----

with instance_cx.scope(), collect_cx.lookup_scope():
    instance_cx.instances[ClientSession] = self.aiohttp_session

    await fn(10)
```

From this example, you can also see Flywheel's support for asynchronous operations. Theoretically, it can also support generators, asynchronous generators, and even `contextlib.contextmanager`. If you encounter any issues, feel free to report them to the issues.

### Overriding Static Instantiation Behavior

By overriding the class method (classmethod) `build_static`, you can customize the instantiation behavior of the `static` parameter.

```python
class sth_implements(m := scoped_collect.locals().target, static=True):
    session = InstanceOf(ClientSession)

    def __init__(self, session: ClientSession):
        self.session = session

    @m.impl(...)
    async def something(self, num: int):
        await self.session.get(f"http://example.com/", params={"num": num})

    @classmethod
    def build_static(cls):
        return cls(GLOBAL_AIOHTTP_SESSION)
```

### Global Context

Flywheel also provides a global instance context.

```python
from flywheel.globals import GLOBAL_INSTANCE_CONTEXT

GLOBAL_INSTANCE_CONTEXT.instances[...] = ...
```

In fact, the automatically instantiated result of `scoped_collect` marked as `static` is stored in this global instance context. The `static` parameter only affects this behavior. This means you can freely save the instantiation result of `scoped_collect` into this global context based on your application's situation.