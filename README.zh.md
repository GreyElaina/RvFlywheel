# Ryanvk Flywheel

Ryanvk Flywheel 是一个 Ryanvk-style 的 utility。

- ~~在单一入口点上的~~*几近完美*的自由重载；
- 简单灵活的重载机制；
- *前沿级*的类型支持 [^1] [^2]；
- 可切换上下文。

Available on PyPI: `elaina-flywheel`。

[^1]: 仅在 Pyright / Basedpyright 上可用。
[^2]: 仍存在无法彻底解决的问题，比如 `FnImplementEntity` 上的类型会因 check-and-narrowing 行为被迫丢失。

## 使用

Flywheel 着重于围绕 `Fn` 建设，以提供强大的重载功能为目的。

可以通过这种方法创建一个使用*简单重载*(`SimpleOverload`)的 `Fn`。

```python
from typing import Protocol

from flywheel import FnRecord, SimpleOverload, FnCollectEndpoint

class greet:
    name = SimpleOverload("name")

    @classmethod
    def call(cls, name: str) -> str:
        for selection in self.someone.select():
            if not selection.harvest(self.name, name):
                continue

            selection.complete()
        
        return selection(name)

    @FnCollectEndpoint
    @classmethod
    def someone(cls, *, name: str):
        yield cls.name.hold(name)

        # 可选的，你可以给出实现的类型，运行时中我们不关心这个，所以你可以放在 if TYPE_CHECKING 中。
        def shape(name: str) -> str: ...
        return shape
```

然后我们为 `greet` 提出两个实现：

- 当 `name` 是 `Teague` 的时候返回 `"Stargaztor, but in name only."`；
- 当 `name` 是 `Grey` 的时候返回 `"Symbol, the Founder."`：

当提出实现后，我们还得将其收集起来，这样 Flywheel 的内部系统才能调用的到这些实现。
在这里，我们使用 `global_collect` 函数，将实现收集到全局上下文中。

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

然后我们调用。

```python
>>> greet.call("Teague")
'Stargaztor, but in name only.'
>>> greet.call("Grey")
'Symbol, the Founder.'
```

看上去很不错，按照预期的调度到了相应的实现上；如果我们输入一个*未实现*的字段会怎么样呢？

```python
>>> greet.call("Hizuki")
NotImplementedError: cannot lookup any implementation with given arguments
```

显然，我们并没有面向 `"Hizuki"` 实现一个 `greet`。为了使我们的程序能处理这种情况，我们可以这样修改 `greet` 的声明：

```python
class greet:
    name = SimpleOverload("name")  # 指定 name 是必要的。

    @classmethod
    def call(cls, name: str) -> str:
        for selection in cls.collect.select(False):
            if not selection.harvest(cls.name, name):
                continue

            selection.complete()

        if not entities:  # 判断是否存在符合条件的实现
            return f"Ordinary, {name}."

        return selection(name)
```

这种方法可以提供一种极其灵活的默认实现机制：于是现在我们可以调用 `greet` 了。

```python
>>> greet.call("Hizuki")
'Ordinary, Hizuki.'
```

如果你感觉完全没有必要造个类出来放这些东西，你也可以直接这样写，Flywheel 现在只有 `FnCollectEndpoint` 是特殊的，
其他的都和一般的方法或函数是一样的。

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

`FnCollectEndpoint` 和具体的调用实现可以放在各个不同的地方 —— 他们都是独立存在的，也就是说，你可以同时写一个面向扩展开发者的 `ExtensionTrait`，
和一个面向用户的 `Userspace` 类或模块，并在 `Userspace` 中调用 `ExtensionTrait` 中声明的 `FnCollectEndpoint`。

基于语义性上的考虑，你最好别只写 `@FnCollectEndpoint def collect()`，而是类似 `@FnCollectEndpoint def implement_greet()` 这样。

## 重载机制

Flywheel 的重载机制是基于 `FnOverload` 的实现，其包含了以下 4 个主要功能：

- `digest`: 将收集实现时提供的参数 (`Fn.impl` 方法) 转换为可保存的签名对象；
- `collect`: 利用签名所蕴含的参数，在自己的命名空间中配置用于存放实现引用的集合；
- `harvest`: 根据传入的值，在命名空间中匹配相应的集合；
- `access`: 根据传入的签名，从命名空间中匹配相应的集合。

这里使用集合来在命名空间中保存实现的引用，是将一项 Overload 当成标记在引用上的*标签*使用，这样我们就能对不同的参数使用灵活的重载配置，并最终通过交集来找到对应的实现。
甚至，我们也可以籍由构造具有复杂逻辑的 `if / load` 链，实现一些难以想象的逻辑。

> [!NOTE]  
> Flywheel 使用 `dict[Callable, None]` 充当有序集合的内部实现。

以 `SimpleOverload` 为例：

```python
@dataclass(eq=True, frozen=True)
class SimpleOverloadSignature:
    value: Any


class SimpleOverload(FnOverload[SimpleOverloadSignature, Any, Any]):
    def digest(self, collect_value: Any) -> SimpleOverloadSignature:
        # 将收集实现时提供的参数转换为可保存的签名对象
        return SimpleOverloadSignature(collect_value)

    def collect(self, scope: dict, signature: SimpleOverloadSignature) -> dict[Callable, None]:
        if signature.value not in scope:
            # 在命名空间中配置用于存放实现引用的集合，如果没有就开辟，否则复用。
            # 这里会用 dict[Callable, None]，原因是我们需要有序 +　唯一。
            target = scope[signature.value] = {}
        else:
            target = scope[signature.value]

        return target

    def harvest(self, scope: dict, call_value: Any) -> dict[Callable, None]:
        # 对于 Flywheel，"匹配" 是更准确的说法。
        # 这允许我们对调用值实现泛匹配。

        if call_value in scope:
            return scope[call_value]

        return {}

    def access(self, scope: dict, signature: SimpleOverloadSignature) -> dict[Callable, None] | None:
        # 根据传入的签名，从命名空间中匹配相应的集合。
        # 从 Ryanvk 原实现继承来的，Flywheel 里似乎不要求必须实现。

        if signature.value in scope:
            return scope[signature.value]
```

你可以尝试借由这个例子来实现一个依据调用时值 (`call_value`) 的类型来找到对应的实现的 `TypeOverload`，作为参考答案，你可以在 `flywheel.overloads` 模块中找到同名的实现。

对于 `FnOverload` 来说，他不一定要搜索尽可能多的实现 —— 这根据实际情况来决定：如果你希望你的 Fn 表现的像是个事件系统，这种情况下你最好找到尽可能多的实现 —— 不幸的，我们没有提供什么 `greed` 参数，因此你需要自己实现。

你可以添加构造器参数，并继承现有的其他重载实现。

```python
class SomeMaybeGreedOverload(FnOverload):
    def __init__(self, name: str, greed: bool):
        self.name = name
        self.greed = greed

    ...  # 你的实际逻辑
```

## 上下文

Flywheel 提供了一个 `global_collect` 函数，用于将实现收集到全局上下文中。自然，上下文不会只有一个，Flywheel 允许你创建自己的上下文，并在你期望的时候应用。

相应的，全局上下文存储在 `flywheel.globals.GLOBAL_COLLECT_CONTEXT`，如果你知道你在做什么有所必要的事情，这一信息可能对你有用。但我想大多数情况下你都不会使用到这一技巧。

```python
from flywheel.context import CollectContext

local_cx = CollectContext()

with local_cx.collect_scope():
    # do some collect stuff;;
    # 现在收集一些东西...
    ...

# 你刚才收集到的东西现在并不能使用...

with local_cx.lookup_scope():
    # ...现在没问题啦！
    ...

# 或者有时你全部要？

with local_cx.scope():
    # 好的，只是这可能导致不在预期中对 local_cx 的写入。
    ...
```

需要注意的是，`global_collect` 函数的行为并不会因为上下文的存在而改变，为此，你需要考虑使用 `local_collect` 来将实现收集到你的上下文中。

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

如果你在这之前并没有使用过 `collect_scope`，`local_collect` 会采用默认行为，将实现收集到全局上下文中。

但我们不建议在所有情况下都使用 `local_collect`，而是尽可能的使用 `global_collect`，
除非你确定你的实现会因为你应用中蕴含的某种上下文而有必要发生改变（比如 Avilla 需要根据上下文中采用的协议实现切换）。

## scoped_collect

::: warning
`scoped_collect` 可能会在未来的版本中被移除 —— 毕竟处理实例的各种情况实在是太麻烦。但我现在没有太好的办法。
:::


如果你希望你的模块保持命名空间的整洁，采用 `scoped_collect` 或许是不错的主意。只是他还有其他更重要的应用，且听我娓娓道来。

```python
from flywheel import scoped_collect

class greet_implements(m := scoped_collect.globals().target, static=True):
    @m.collect
    @greet.someone(name="Teague")
    @m.ensure_self
    def greet_teague(self, name: str) -> str:
        return "Stargaztor, but in name only."

    # 上面的写法未免过于冗长，我们正在考虑更好的办法。
```

这段代码使用 `scoped_collect` 实现了和我们最初给出的两个 `greet_xxx` 一样的效果。

```python
>>> greet("Teague")
'Stargaztor, but in name only.'
>>> greet("Grey")
'Symbol, the Founder.'
```

这段代码使用 `scoped_collect.globals()` 方法连接到了全局上下文。如果你不想这样，需要换成 `scoped_collect.locals()`。

```python
from flywheel import scoped_collect

class greet_implements(m := scoped_collect.locals().target, static=True):
    ...
```

`static=True` 时，`greet_implements` 会被实例化并保存到全局中的*实例上下文* (Instance Context) 中。  
如果你自定义了你的构造方法 (即 `__init__` 或 `__new__`)，则会在启动时报错，此时你需要自己实现对 `InstanceContext` 的生成与应用。

## 叠加

Flywheel 允许你这么做...：

```python
@global_collect
@greet.someone(name="Teague")
@greet.someone(name="Grey")
def greet_stargaztor(name: str) -> str:
    return f"Stargaztor"
```

他等同于分别调用 `FnCollectEntity`，但写的更简短，同时你依旧能获得 Flywheel 前沿级的类型支持。

如果需配合 `scoped_collect` 使用，注意将 `Fn.impl` 调用*夹*在 `m.collect` 与 `m.ensure_self` 中间：

```python
@m.collect
@greet.impl(name="Teague")
@greet.impl(name="Grey")
@m.ensure_self
def greet_teague(self, name: str) -> str:
    return f"Stargaztor."
```

或者你试试我们又新又好的 `m.impl`？

```python
@m.impl(greet.collect(name="Harlan"))
@m.impl(greet.collect(name="Sen"))
def greet_stargaztor(name: str) -> str:
    return f"Stargaztor, also couple, then parent, and then broken parent."
```

## 实例上下文

实例上下文 (`InstanceContext`) 是 Flywheel 访问局部命名空间中实例的桥梁，此外，你也可以透过这一特性，向 `scoped_collect` 中隐式传递参数，实现依赖注入。  
此外，全局实例上下文也在 `flywheel.globals` 模块中，可供君自由取用。

```python
from flywheel import InstanceContext

instance_cx = InstanceContext()

instance_cx.instances[str] = "EMPTY"

with instance_cx.scope() as scope_cx:  # 会返回上下文实例，对这里返回的上下文实例进行修改**不会**影响上文。
    instance_cx.instances[int] = 42  # 常规用法。

    scope_cx.store({str: "42"}, 1.14, None)
    # 相当于 `instance_cx.store({str: "42", float: 1.14, type(None): None｝)`

    ...  # do other stuffs
```

由于轻量化目的，目前我们尚未完成 Flywheel 中对于不同集合中实现记录的合并，所以这一方法目前只用于：

### 手动提供实例

对于 `static=False` 的 `scoped_collect`，需要这样做以使其正常工作。

```python
instance_cx = ...
collect_cx = ...

with collect_cx.collect_scope():
    ...  # collect

with instance_cx.scope(), collect_cx.lookup_scope():
    instance_cx.instances[cls] = cls(...)

    # then normally Fn
```

### 向内提供信息

我们提供了可以自动访问当前实例上下文的描述符 `InstanceOf`，通过这一措施，你可以方便的访问实例上下文中的内容。

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

从该示例中你也可以了解到 Flywheel 对异步的支持，理论上也能一并支持生成器，异步生成器甚至 `contextlib.contextmanager`，但如果出了问题，欢迎汇报至 issues.

### 重写 static 实例化行为

通过重写类方法 (classmethod) `build_static`，你可以自定义 `static` 参数的实例化行为。

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

### 全局上下文

Flywheel 同样提供了全局的实例上下文。

```python
from flywheel.globals import GLOBAL_INSTANCE_CONTEXT

GLOBAL_INSTANCE_CONTEXT.instances[...] = ...
```

事实上，标记为 `static` 的 `scoped_collect`，其自动实例化结果就存储在这里，`static` 参数仅影响这一行为，也就是说 —— 你完全可以自己根据你自己的应用情况，将 `scoped_collect` 的实例化结果保存到这里提到的全局上下文中。
