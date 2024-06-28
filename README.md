# Ryanvk Flywheel

Ryanvk Flywheel is a Ryanvk-style utility.

- **Near-perfect** free overloading at a single entry point;
- Simple and flexible overloading mechanism;
- **Cutting-edge** type support [^1] [^2];
- Switchable contexts.

Available on PyPI: `elaina-flywheel`.

[^1]: Available only on Pyright / Basedpyright.
[^2]: There are still unresolved issues, such as type loss on `FnImplementEntity` due to check-and-narrowing behavior.

## Usage

Flywheel focuses on building around `Fn` to provide powerful overloading capabilities.

You can create an `Fn` using *simple overload* (`SimpleOverload`) as follows:

```python
from typing import Protocol

from flywheel import FnRecord, SimpleOverload, FnCollectEndpoint

class greet:
    name = SimpleOverload("name")

    @classmethod
    def call(cls, name: str) -> str:
        entities = cls.someone.get_control().use(cls.name, name)
        return entities.first(name)

    @FnCollectEndpoint
    @classmethod
    def someone(cls, *, name: str):
        yield cls.name.hold(name)

        # Optionally, you can specify the implementation type, but we don't care about this at runtime, so you can put it in if TYPE_CHECKING.
        def shape(name: str) -> str: ...
        return shape
```

Then we provide two implementations for `greet`:

- When `name` is `Teague`, return `"Stargaztor, but in name only."`
- When `name` is `Grey`, return `"Symbol, the Founder."`

After providing the implementations, we need to collect them so that Flywheel's internal system can call these implementations.
Here, we use the `global_collect` function to collect the implementations into the global context.

```python
from flywheel import global_collect

@global_collect
@greet.someone(name="Teague")
def greet_teague(name: str) -> str:
    return "Stargaztor, but in name only."

@global_collect
@greet.someone(name="Grey")
def greet_grey(name: str) -> str:
    return "Symbol, the Founder."
```

Then we call it.

```python
>>> greet.call("Teague")
'Stargaztor, but in name only.'
>>> greet.call("Grey")
'Symbol, the Founder.'
```

It looks great, and it dispatches to the corresponding implementation as expected; what if we input an *unimplemented* field?

```python
>>> greet.call("Hizuki")
NotImplementedError: cannot lookup any implementation with given arguments
```

Obviously, we didn't implement `greet` for `"Hizuki"`. To make our program handle this situation, we can modify the `greet` declaration like this:

```python
class greet:
    name = SimpleOverload("name")  # Specify that name is required.

    @classmethod
    def call(cls, name: str) -> str:
        entities = cls.someone.get_control().use(cls.name, name)

        if not entities:  # Check if there are implementations matching the criteria
            return f"Ordinary, {name}."

        return entities.first(name)
```

This method provides an extremely flexible default implementation mechanism: now we can call `greet`.

```python
>>> greet.call("Hizuki")
'Ordinary, Hizuki.'
```

If you think it's unnecessary to create a class for these things, you can also write it directly like this, Flywheel now only treats `FnCollectEndpoint` specially,
and everything else is the same as regular methods or functions.

```python
NAME_OVERLOAD = SimpleOverload("name")

@FnCollectEndpoint
def implement_greet(name: str) -> str:
    yield NAME_OVERLOAD.hold(name)

    def shape(name: str) -> str: ...
    return shape

def greet(name: str) -> str:
    entities = implement_greet.get_control().use(NAME_OVERLOAD, name)

    if not entities:
        return f"Ordinary, {name}."

    return entities.first(name)

@global_collect
@implement_greet(name="Teague")
def greet_teague(name: str) -> str:
    return "Stargaztor, but in name only."
```

`FnCollectEndpoint` and the specific call implementations can be placed in different locations — they exist independently, meaning you can write an `ExtensionTrait` for extension developers,
and a `Userspace` class or module for users, and call `FnCollectEndpoint` declared in `ExtensionTrait` in `Userspace`.

For semantic reasons, you’d better not just write `@FnCollectEndpoint def collect()`, but something like `@FnCollectEndpoint def implement_greet()`.

## Overloading Mechanism

Flywheel's overloading mechanism is implemented based on `FnOverload`, which includes the following four main functions:

- `digest`: Convert the parameters provided when collecting implementations (`Fn.impl` method) into a savable signature object;
- `collect`: Use the parameters contained in the signature to configure a collection for storing implementation references in its namespace;
- `harvest`: Match the corresponding collection in the namespace based on the values passed in;
- `access`: Match the corresponding collection in the namespace based on the signature passed in.

Using collections to store implementation references in the namespace is like using an Overload as a tag on the reference, allowing us to use flexible overloading configurations for different parameters and finally find the corresponding implementation through intersections.
We can even construct complex `if / load` chains to implement some unimaginable logic.

> [!NOTE]  
> Flywheel uses `dict[Callable, None]` as the internal implementation of ordered collections.

For example, `SimpleOverload`:

```python
@dataclass(eq=True, frozen=True)
class SimpleOverloadSignature:
    value: Any


class SimpleOverload(FnOverload[SimpleOverloadSignature, Any, Any]):
    def digest(self, collect_value: Any) -> SimpleOverloadSignature:
        # Convert the parameters provided when collecting implementations into a savable signature object
        return SimpleOverloadSignature(collect_value)

    def collect(self, scope: dict, signature: SimpleOverloadSignature) -> dict[Callable, None]:
        if signature.value not in scope:
            # Configure a collection for storing implementation references in the namespace, create a new one if it doesn't exist, otherwise reuse it.
            # Here we use dict[Callable, None] because we need ordered and unique.
            target = scope[signature.value] = {}
        else:
            target = scope[signature.value]

        return target

    def harvest(self, scope: dict, call_value: Any) -> dict[Callable, None]:
        # For Flywheel, "matching" is a more accurate term.
        # This allows us to implement general matching for call values.

        if call_value in scope:
            return scope[call_value]

        return {}

    def access(self, scope: dict, signature: SimpleOverloadSignature) -> dict[Callable, None] | None:
        # Match the corresponding collection in the namespace based on the signature passed in.
        # Inherited from Ryanvk's original implementation, it doesn't seem required in Flywheel.

        if signature.value in scope:
            return scope[signature.value]
```

You can try to implement a `TypeOverload` that finds the corresponding implementation based on the type of the call value, as a reference, you can find the same name implementation in the `flywheel.overloads` module.

For `FnOverload`, it doesn't necessarily have to search for as many implementations as possible — it depends on the actual situation: if you want your Fn to behave like an event system, it's best to find as many implementations as possible — unfortunately, we don't provide any `greed` parameter, so you need to implement it yourself.

You can add constructor parameters and inherit other existing overload implementations.

```python
class SomeMaybeGreedOverload(FnOverload):
    def __init__(self, name: str, greed: bool):
        self.name = name
        self.greed = greed

    ...  # Your actual logic
```

## Contexts

Flywheel provides a `global_collect` function to collect implementations into the global context. Naturally, there won't be just one context, Flywheel allows you to create your own contexts and apply them when you expect.

Correspondingly, the global context is stored in `flywheel.globals.GLOBAL_COLLECT_CONTEXT`, if you know what you're doing and find it necessary, this information might be useful to you. But I guess most of the time you won't use this trick.

```python
from flywheel.context import CollectContext

local_cx = CollectContext()

with local_cx.collect_scope():
    # do some collect stuff;
    # now collect some stuff...
    ...

# The stuff you just collected cannot be used now...

with local_cx.lookup_scope():
    # ...now it's fine!
    ...
```

Note that the behavior of the `global_collect` function does not change because of the existence of contexts, for this reason, you need to consider using `local_collect` to collect implementations into your context.

```python
from flywheel import local_collect

@local_collect
@greet.someone(name="Teague")
def greet_teague(name: str) -> str:
    return "Stargaztor, but in name only."

@local_collect
@greet.someone(name="Grey")
def greet_grey(name: str) -> str:
    return "Symbol, the Founder."
```

If you haven't used `collect_scope` before, `local_collect` will adopt the default behavior and collect implementations into the global context.

But we don't recommend using `local_collect` in all cases, instead, use `global_collect` whenever possible, unless you are sure your implementation needs to change because of some context contained in your application (for example,

 Avilla needs to switch implementations based on the protocol used in the context).

## scoped_collect

If you want your module to keep the namespace clean, using `scoped_collect` might be a good idea. It also has other more important applications, let me explain.

```python
from flywheel import scoped_collect

class greet_implements(m := scoped_collect.globals().target, static=True):
    @m.collect
    @greet.someone(name="Teague")
    @m.ensure_self
    def greet_teague(self, name: str) -> str:
        return "Stargaztor, but in name only."

    # The above method is too verbose, we are considering better ways.
```

This code uses `scoped_collect` to achieve the same effect as the two `greet_xxx` we initially provided.

```python
>>> greet("Teague")
'Stargaztor, but in name only.'
>>> greet("Grey")
'Symbol, the Founder.'
```

This code connects to the global context using the `scoped_collect.globals()` method. If you don't want this, you need to switch to `scoped_collect.locals()`.

```python
from flywheel import scoped_collect

class greet_implements(m := scoped_collect.locals().target, static=True):
    ...
```

When `static=True`, `greet_implements` will be instantiated and saved in the global *Instance Context*.  
If you have customized your constructor method (i.e., `__init__` or `__new__`), it will report an error at startup, in which case you need to implement the generation and application of `InstanceContext` yourself.

## Stacking

Flywheel allows you to do this:

```python
@global_collect
@greet.someone(name="Teague")
@greet.someone(name="Grey")
def greet_stargaztor(name: str) -> str:
    return f"Stargaztor"
```

This is equivalent to calling `FnCollectEntity` separately but written more concisely, while still getting Flywheel's cutting-edge type support.

If you need to use it with `scoped_collect`, note to *sandwich* the `Fn.impl` call between `m.collect` and `m.ensure_self`:

```python
@m.collect
@greet.impl(name="Teague")
@greet.impl(name="Grey")
@m.ensure_self
def greet_teague(self, name: str) -> str:
    return f"Stargaztor."
```

Or maybe you should try our new and awesome `m.impl`?

```python
@m.impl(greet.collect(name="Harlan"))
@m.impl(greet.collect(name="Sen"))
def greet_stargaztor(name: str) -> str:
    return f"Stargaztor, also couple, then parent, and then broken parent."
```

## Instance Context

Instance context (`InstanceContext`) is the bridge for Flywheel to access instances in the local namespace. Besides, you can implicitly pass parameters to `scoped_collect` through this feature to achieve dependency injection.  
Additionally, the global instance context is also available in the `flywheel.globals` module for your free use.

```python
from flywheel import InstanceContext

instance_cx = InstanceContext()

instance_cx.instances[str] = "EMPTY"

with instance_cx.scope() as scope_cx:  # Returns the context instance here, modifying the returned context instance **will not** affect the above context.
    instance_cx.instances[int] = 42  # Regular usage.

    scope_cx.store({str: "42"}, 1.14, None)
    # Equivalent to `instance_cx.store({str: "42", float: 1.14, type(None): None})`

    ...  # do other stuffs
```

For lightweight purposes, we have not completed the merging of implementation records in different collections in Flywheel, so this method is currently only used for:

### Manually Providing Instances

For `scoped_collect` with `static=False`, this is necessary to make it work correctly.

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

We provide a descriptor `InstanceOf` that can automatically access the current instance context. This measure allows you to easily access the content in the instance context.

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

From this example, you can also understand Flywheel's support for asynchronous operations. Theoretically, it can also support generators, asynchronous generators, and even `contextlib.contextmanager`. If there are any problems, please report to issues.

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

In fact, the automatic instantiation results of `scoped_collect` marked as `static` are stored in the global context mentioned here. The `static` parameter only affects this behavior, meaning — you can completely save the instantiation results of `scoped_collect` in the global context according to your own application situation.