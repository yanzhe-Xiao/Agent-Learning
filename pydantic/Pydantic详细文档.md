# Pydantic 详细文档

这份文档用于长期知识积累，重点覆盖 Pydantic v2 的核心概念、常用 API、设计思路和实战建议。

## 0. 版本说明

先记录一个当前环境里的重要事实：

- 你 IDE 打开的 `langchain` 环境中，Pydantic 版本是 `2.12.5`
- 当前终端默认 `python` 对应的是 `C:\ProgramData\anaconda3\python.exe`
- 这个默认解释器中的 Pydantic 版本是 `1.10.8`

这意味着：

- 你现在示例代码里用到的 `field_validator`、`model_dump`、`model_validate_json` 是 **Pydantic v2 风格**
- 如果你在终端里直接用默认 `python` 运行这些代码，可能会因为版本不一致报错

所以这份文档默认以 **Pydantic v2.12.x** 为主。

## 1. Pydantic 是做什么的

Pydantic 的核心定位是：

**用 Python 类型注解描述数据结构，并在运行时完成校验、转换、序列化。**

它适合处理这几类问题：

- 接口请求参数校验
- 配置文件校验
- 第三方接口返回值解析
- 数据库结果对象化
- 程序内部结构化数据约束

一句话理解：

**先声明“数据应该长什么样”，再让 Pydantic 帮你检查传进来的数据是不是这样。**

## 2. Pydantic 的核心价值

Pydantic 常被使用，不是因为“它能定义类”，而是因为它把几件经常一起出现的事情合并了：

- 类型声明
- 数据校验
- 数据转换
- 错误信息整理
- 字典和 JSON 输出

例如：

```python
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    age: int
```

当你写下这个模型时，你同时得到了：

- 一个清晰的数据结构
- 运行时类型校验能力
- 错误报告能力
- 序列化能力

## 3. 基础模型定义

### 3.1 继承 `BaseModel`

最常见的入口是继承 `BaseModel`：

```python
from pydantic import BaseModel


class UserProfile(BaseModel):
    username: str
    age: int
    email: str | None = None
```

规则非常重要：

- 只有类型注解、没有默认值，通常表示必填字段
- 有默认值，通常表示可省略字段
- `str | None` 或 `Optional[str]` 表示值允许为 `None`

### 3.2 实例化时自动校验

```python
user = UserProfile(username="alice", age=18)
```

实例化时会自动检查：

- 是否缺少必填字段
- 类型是否匹配
- 默认值是否需要补上

### 3.3 自动类型转换

Pydantic 默认是“宽松校验”风格，会做一些合理转换：

```python
user = UserProfile(username="alice", age="18")
print(user.age)  # 18
```

这里字符串 `"18"` 会被转换成整数 `18`。

这种行为适合处理：

- 表单输入
- URL 参数
- JSON 数据
- 环境变量

但这也意味着：

- Pydantic 不等于静态类型检查器
- 它不是“只接受完全同类型值”
- 它默认更偏“数据清洗 + 校验”

## 4. 校验失败与错误处理

校验失败时，Pydantic 会抛出 `ValidationError`。

```python
from pydantic import BaseModel, ValidationError


class User(BaseModel):
    name: str
    age: int


try:
    User(name="Alice", age="abc")
except ValidationError as e:
    print(e)
    print(e.errors())
```

常用观察方式：

- `print(e)`：适合人直接看
- `e.errors()`：适合程序处理

`e.errors()` 返回的是结构化错误列表，通常包含：

- 错误字段位置
- 错误类型
- 原始输入值
- 错误描述

这也是为什么 FastAPI 很适合和 Pydantic 一起用。

## 5. 常用数据入口

除了直接实例化，v2 还有几种很重要的入口方法。

### 5.1 `model_validate`

适合从字典或任意 Python 对象校验生成模型：

```python
data = {"username": "alice", "age": "18"}
user = UserProfile.model_validate(data)
```

它比直接写 `UserProfile(**data)` 更显式，语义也更清楚。

### 5.2 `model_validate_json`

适合直接从 JSON 字符串生成模型：

```python
json_data = '{"username":"alice","age":18}'
user = UserProfile.model_validate_json(json_data)
```

这一步会同时做：

- JSON 解析
- 字段校验
- 类型转换

### 5.3 `TypeAdapter`

如果你不是要验证一个完整模型，而是想验证“某个类型本身”，`TypeAdapter` 很有用。

```python
from pydantic import TypeAdapter


adapter = TypeAdapter(list[int])
result = adapter.validate_python(["1", 2, 3])
print(result)  # [1, 2, 3]
```

适合场景：

- 验证 `list[int]`
- 验证 `dict[str, list[int]]`
- 验证 `Union`
- 验证没有必要单独建模型的临时结构

## 6. `Field` 的核心作用

`Field()` 用来给字段增加更详细的约束和元信息。

```python
from pydantic import BaseModel, Field


class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., gt=0)
    stock: int = Field(0, ge=0)
```

### 6.1 `Field(...)`

`...` 表示这个字段是必填的。

```python
name: str = Field(...)
```

### 6.2 常见约束

数值约束：

- `gt=0`：大于 0
- `ge=0`：大于等于 0
- `lt=10`：小于 10
- `le=10`：小于等于 10
- `multiple_of=2`：必须是 2 的倍数

字符串约束：

- `min_length=1`
- `max_length=100`
- `pattern=r"^\d+$"`

其他常见参数：

- `title`
- `description`
- `examples`
- `repr`
- `strict`
- `alias`

### 6.3 `default` 和 `default_factory`

对于可变类型，推荐使用 `default_factory`：

```python
from pydantic import BaseModel, Field


class Blog(BaseModel):
    tags: list[str] = Field(default_factory=list)
```

比下面这种更稳妥：

```python
tags: list[str] = []
```

虽然 Pydantic v2 对默认值处理更稳，但从习惯和可维护性上，`default_factory` 依然更推荐。

## 7. 推荐使用 `Annotated`

在 v2 里，很多约束更推荐和 `Annotated` 一起写。

```python
from typing import Annotated
from pydantic import BaseModel, Field


class User(BaseModel):
    age: Annotated[int, Field(ge=0, le=150)]
```

好处：

- 类型和约束更自然地绑在一起
- 在复杂嵌套类型里更清晰
- 和 v2 的设计方向更一致

尤其在这些场景里更有价值：

- `list[Annotated[int, Field(gt=0)]]`
- `str | None`
- 复杂联合类型

## 8. 特殊类型

Pydantic 不只是校验 `int`、`str`、`list`，还内置了很多实用类型。

常见例子：

- `HttpUrl`
- `EmailStr`
- `UUID`
- `AnyUrl`
- `SecretStr`
- `datetime`
- `date`
- `Decimal`

例如：

```python
from pydantic import BaseModel, HttpUrl, EmailStr, SecretStr


class Account(BaseModel):
    website: HttpUrl
    email: EmailStr
    password: SecretStr
```

这些类型的价值在于：

- 省去重复手写格式校验
- 错误信息统一
- 代码更表达业务含义

## 9. 嵌套模型

模型字段本身可以是另一个模型。

```python
from pydantic import BaseModel


class Address(BaseModel):
    city: str
    country: str


class User(BaseModel):
    name: str
    address: Address
```

这样做的好处：

- 复杂结构表达清楚
- 校验递归自动进行
- JSON 和 Python 对象的映射更自然

适用场景：

- 用户和地址
- 订单和商品
- API 响应和分页信息

## 10. 联合类型与多形态数据

很多时候同一个字段可能接受多种类型：

```python
class Demo(BaseModel):
    value: int | str
```

但更实用的是“带判别字段的联合类型”，也叫 **discriminated union**。

```python
from typing import Literal
from pydantic import BaseModel, Field


class Cat(BaseModel):
    pet_type: Literal["cat"]
    age: int


class Dog(BaseModel):
    pet_type: Literal["dog"]
    age: int


class Model(BaseModel):
    pet: Cat | Dog = Field(discriminator="pet_type")
```

这种写法适合：

- 多种事件结构
- 多种消息体结构
- 多态配置对象

## 11. 别名 `alias`

当外部字段名和 Python 内部字段名不一样时，用 `alias`。

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    user_name: str = Field(alias="userName")
```

这样外部传入：

```python
{"userName": "alice"}
```

也可以映射到：

```python
user.user_name
```

实际开发里常见原因：

- 前端是 camelCase
- Python 代码想保持 snake_case
- 第三方接口字段名无法控制

## 12. 序列化输出

Pydantic v2 的输出方法主要是：

- `model_dump()`
- `model_dump_json()`

### 12.1 `model_dump`

把模型转成 Python 字典：

```python
data = user.model_dump()
```

常用参数：

- `exclude_none=True`
- `exclude_unset=True`
- `exclude_defaults=True`
- `by_alias=True`

例如：

```python
user.model_dump(exclude_none=True, by_alias=True)
```

### 12.2 `model_dump_json`

把模型转成 JSON 字符串：

```python
json_text = user.model_dump_json()
```

适合：

- API 输出
- 写入文件
- 缓存
- 消息传输

## 13. 自定义校验器

### 13.1 `field_validator`

v2 里字段级自定义校验主要使用 `field_validator`。

```python
from pydantic import BaseModel, field_validator


class User(BaseModel):
    password: str

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码至少 8 位")
        return v
```

这类校验适合处理：

- 业务规则
- 格式补充校验
- 标准化输入值

### 13.2 校验器也可以改值

校验器不只是检查，还可以返回处理后的值：

```python
@field_validator("email")
def normalize_email(cls, v):
    return v.lower().strip()
```

这让模型同时承担了：

- 数据合法性检查
- 数据标准化处理

### 13.3 多条件错误合并

如果一个字段有多条规则，可以先收集错误再统一抛出：

```python
@field_validator("password")
def validate_password(cls, v):
    errors = []
    if len(v) < 8:
        errors.append("至少 8 个字符")
    if not any(c.isupper() for c in v):
        errors.append("至少 1 个大写字母")
    if errors:
        raise ValueError("; ".join(errors))
    return v
```

这类写法适合教学、表单校验和统一错误展示。

### 13.4 `model_validator`

当校验逻辑依赖多个字段一起判断时，应该考虑 `model_validator`。

```python
from pydantic import BaseModel, model_validator


class RegisterForm(BaseModel):
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self
```

适合：

- 字段间一致性校验
- 跨字段业务规则
- 构造后的整体合法性判断

## 14. 严格模式 `strict`

Pydantic 默认比较宽松，会尝试转换值。

如果你不希望 `"123"` 自动变成 `123`，可以开启严格模式。

### 14.1 单次校验时开启

```python
User.model_validate({"age": "18"}, strict=True)
```

### 14.2 字段级严格

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    age: int = Field(strict=True)
```

### 14.3 模型级严格

```python
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(strict=True)
    age: int
```

适用场景：

- 金额
- 风险控制规则
- 数据清洗之后的二次校验
- 不允许隐式转换的接口边界

## 15. 模型配置 `ConfigDict`

v2 里模型配置通常写在 `model_config` 中。

```python
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        frozen=False,
    )

    name: str
    age: int
```

常见配置项：

- `extra="ignore"`：忽略多余字段
- `extra="forbid"`：禁止多余字段
- `extra="allow"`：允许多余字段
- `validate_assignment=True`：字段赋值时再次校验
- `strict=True`：全模型严格模式
- `frozen=True`：实例不可修改

其中 `extra` 非常常用。

例如：

```python
class User(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
```

如果传入未声明字段，就会直接报错。

## 16. JSON Schema

Pydantic 模型可以生成 JSON Schema：

```python
schema = User.model_json_schema()
```

它的意义非常大：

- 接口文档生成
- OpenAPI 集成
- 前后端约定
- 第三方工具联动

这也是 FastAPI 能自动生成文档的重要基础之一。

## 17. `RootModel`

当你的数据“根本不是一个对象”，而是一个列表、字典或某个单值时，可以考虑 `RootModel`。

```python
from pydantic import RootModel


class Tags(RootModel[list[str]]):
    pass


tags = Tags.model_validate(["python", "pydantic"])
```

它适合：

- 直接表示 `list[str]`
- 直接表示 `dict[str, int]`
- 对根级数据做封装

## 18. `TypeAdapter` 和 `BaseModel` 的区别

可以这样理解：

- `BaseModel`：适合定义“命名明确、可复用”的结构化对象
- `TypeAdapter`：适合验证一个临时类型表达式

例如：

```python
TypeAdapter(list[dict[str, int]]).validate_python(data)
```

如果你只是想验证一段数据结构，而不是需要一个正式模型类，`TypeAdapter` 会更直接。

## 19. 计算字段

Pydantic v2 里还有 `computed_field`，适合把某些派生值纳入序列化输出。

```python
from pydantic import BaseModel, computed_field


class Rectangle(BaseModel):
    width: int
    height: int

    @computed_field
    @property
    def area(self) -> int:
        return self.width * self.height
```

适合：

- 金额汇总
- 页面展示字段
- 组合属性

但注意：

- 它是“派生值”
- 不适合替代真正的输入字段校验

## 20. 配置类与环境变量

在 v2 生态里，配置管理通常使用 `pydantic-settings` 包，而不是直接都放在 `pydantic` 主包里。

典型场景：

- 读取 `.env`
- 读取系统环境变量
- 管理数据库地址、密钥、开关项

基本思路是：

- 定义一个配置类
- 字段有类型
- 从环境变量中自动装载

如果你后面做 FastAPI、LangChain、AI 应用配置，这一块会很常见。

## 21. v1 和 v2 的关键差异

你当前环境里 v1 和 v2 同时存在，所以这部分必须记住。

### v2 常见写法

- `field_validator`
- `model_validator`
- `model_dump`
- `model_dump_json`
- `model_validate`
- `model_validate_json`
- `ConfigDict`

### v1 常见写法

- `@validator`
- `@root_validator`
- `.dict()`
- `.json()`
- `class Config:`
- `parse_obj()`

### 一个最实用的判断方法

如果你看到这些名字，基本就是 v2：

- `field_validator`
- `model_dump`
- `model_validate`

如果你看到这些名字，基本是 v1 风格：

- `validator`
- `root_validator`
- `dict()`
- `parse_obj()`

## 22. 实战设计建议

### 22.1 模型职责要清晰

推荐让模型负责：

- 数据结构定义
- 基础校验
- 轻量标准化处理

不推荐让模型承担：

- 数据库访问
- 网络请求
- 复杂业务流程编排

### 22.2 约束尽量靠近字段

像长度、范围、正则这类规则，优先放在字段定义上，而不是散落在业务代码里。

### 22.3 跨字段规则再用 `model_validator`

不要把依赖多个字段的逻辑硬塞进单个字段校验器。

### 22.4 面向外部输入时考虑 `strict`

如果你的输入来自不可信来源，而你又不希望自动转换过于宽松，就应该认真评估严格模式。

### 22.5 优先使用有业务含义的类型

例如：

- `HttpUrl` 优于普通 `str`
- `EmailStr` 优于普通 `str`
- `SecretStr` 优于普通 `str`

这会让模型本身更像“业务规则声明”。

## 23. 常见使用模板

### 23.1 接口请求体

```python
from pydantic import BaseModel, Field, EmailStr


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)
```

### 23.2 分页响应

```python
from pydantic import BaseModel


class UserItem(BaseModel):
    id: int
    name: str


class PageResponse(BaseModel):
    total: int
    items: list[UserItem]
```

### 23.3 配置对象

```python
from pydantic import BaseModel, ConfigDict


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_name: str
    debug: bool = False
    timeout: int = 30
```

## 24. 学习路线建议

如果后续继续深入，建议按这个顺序学：

1. `BaseModel`、必填字段、默认值
2. `Field` 和常见约束
3. `ValidationError`
4. 嵌套模型
5. `model_dump` / `model_validate_json`
6. `field_validator`
7. `model_validator`
8. `ConfigDict`
9. `strict`、`TypeAdapter`、`RootModel`
10. `pydantic-settings`、JSON Schema、联合类型

## 25. 一份最小但完整的 v2 示例

```python
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, field_validator


class User(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: Annotated[str, Field(min_length=3, max_length=20)]
    age: Annotated[int, Field(ge=0, le=150)]
    website: HttpUrl | None = None
    tags: list[str] = Field(default_factory=list)
    password: str

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("password too short")
        return v


try:
    user = User.model_validate(
        {
            "username": "alice",
            "age": "18",
            "website": "https://example.com",
            "password": "Abc12345",
        }
    )
    print(user.model_dump(exclude_none=True))
except ValidationError as e:
    print(e.errors())
```

这个例子已经包含了：

- 模型定义
- 字段约束
- 自动类型转换
- 特殊类型
- 默认工厂
- 自定义校验
- 字典输出

## 26. 最后总结

Pydantic 的核心不是“写模型”本身，而是：

**把数据结构、数据约束、数据转换、错误反馈和输出格式统一到一个地方。**

对日常开发来说，真正最值得掌握的是这几块：

- `BaseModel`
- `Field`
- `ValidationError`
- `field_validator`
- `model_dump`
- `model_validate`
- `ConfigDict`
- `strict`

如果这几块掌握扎实，Pydantic 已经能解决你大部分实际项目里的数据校验问题。

## 27. 官方文档入口

建议后续优先查这些官方页面：

- 总览: https://docs.pydantic.dev/latest/
- Models: https://docs.pydantic.dev/latest/concepts/models/
- Fields: https://docs.pydantic.dev/latest/concepts/fields/
- Validators: https://docs.pydantic.dev/latest/concepts/validators/
- Serialization: https://docs.pydantic.dev/latest/concepts/serialization/
- Configuration: https://docs.pydantic.dev/latest/concepts/config/
- Types: https://docs.pydantic.dev/latest/concepts/types/
- TypeAdapter: https://docs.pydantic.dev/latest/concepts/type_adapter/
- Alias: https://docs.pydantic.dev/latest/concepts/alias/
- Strict Mode: https://docs.pydantic.dev/latest/concepts/strict_mode/
- RootModel: https://docs.pydantic.dev/latest/api/root_model/
