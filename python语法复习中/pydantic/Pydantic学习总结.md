# Pydantic 学习总结

这三份示例代码从基础到进阶，串起来展示了 Pydantic 的核心用途：用类型注解定义数据结构，并在实例化时自动完成数据校验、类型转换和序列化。

## 1. Pydantic 的核心作用

Pydantic 最常见的用途是：

- 定义结构化数据模型
- 在创建对象时自动校验数据是否合法
- 根据字段类型自动做一部分类型转换
- 把模型和 `dict`、JSON 之间互相转换

最基础的写法通常是继承 `BaseModel`：

```python
from pydantic import BaseModel

class UserProfile(BaseModel):
    username: str
    age: int
    email: str | None = None
```

这里可以直接看出几个规则：

- 有类型注解但没有默认值的字段，通常是必填字段
- 有默认值的字段，通常可以省略
- `str | None = None` 表示该字段可以是字符串，也可以是 `None`

## 2. 基础模型与自动类型转换

在 `1-PyDantic HelloWorld.py` 中，最重要的入门点有两个：

### 必填字段和可选字段

```python
user = UserProfile(username="alice", age=18)
```

这说明：

- `username` 和 `age` 必须传
- `email` 因为有默认值 `None`，所以可以不传

### 自动类型转换

```python
user2 = UserProfile(username="alice", age="18")
```

虽然 `age` 传入的是字符串 `"18"`，但 Pydantic 会尝试把它转换成 `int`。这也是它很适合处理接口参数、表单数据、配置数据的原因。

但要注意：

- 只有“可安全转换”的值才会成功
- 如果传入 `"abc"` 给 `int` 字段，就会报错

## 3. 校验失败与异常处理

当字段缺失、类型不对、格式不合法时，Pydantic 会抛出 `ValidationError`。

例如：

```python
try:
    UserProfile(username=123)
except ValidationError as e:
    print(e.errors())
```

这里体现了两个重点：

- 缺少必填字段会报错
- 类型不匹配也会报错

`e.errors()` 会返回结构化错误信息，适合调试，也适合接口里直接整理成错误响应。

## 4. `Field` 的作用

在 `2-advance.py` 中，重点展示了 `Field` 的作用。`Field` 用来给字段增加更多约束和元信息。

### 必填字段

```python
name: str = Field(..., title="Name of the user")
```

这里的 `...` 表示这个字段是必填的。

### 默认值

```python
name: str = Field("laowang", title="Name of the user")
```

表示字段有默认值，实例化时可以不传。

### 数值范围约束

```python
price: float = Field(..., gt=0)
stock: int = Field(..., ge=0)
```

常见约束含义：

- `gt=0`：大于 0
- `ge=0`：大于等于 0
- `min_length=1`：最小长度为 1

这些约束非常适合做：

- 商品价格校验
- 库存校验
- 用户输入长度校验
- 配置项合法性校验

## 5. 嵌套模型

`2-advance.py` 还展示了模型嵌套模型的写法：

```python
class Address(BaseModel):
    city: str = Field(..., min_length=1)
    country: str

class User(BaseModel):
    name: str
    address: Address
```

这说明一个模型字段本身也可以是另一个模型。

这种写法特别适合描述复杂数据结构，比如：

- 用户包含地址
- 订单包含商品列表
- 接口响应包含分页信息和数据列表

好处是：

- 结构清晰
- 校验可以递归进行
- 复杂 JSON 更容易映射成 Python 对象

## 6. 特殊类型校验

在 `1-PyDantic HelloWorld.py` 中还用了 `HttpUrl`：

```python
from pydantic import HttpUrl

class WebSite(BaseModel):
    url: HttpUrl
```

这表示 `url` 不只是字符串，还必须是合法的 URL，并且示例里要求包含 `http://` 或 `https://`。

这类“特殊类型”是 Pydantic 很实用的地方，因为你不用自己手写一堆字符串判断逻辑。

## 7. JSON 反序列化与序列化

`1-PyDantic HelloWorld.py` 还演示了模型与 JSON 的转换：

### JSON 转模型

```python
item = Item.model_validate_json(data)
```

作用：

- 把 JSON 字符串解析成模型对象
- 同时完成字段校验和类型转换

### 模型转字典

```python
item.model_dump()
```

作用：

- 把模型转成 Python 字典
- 适合继续做程序内部处理

### 模型转 JSON

```python
item.model_dump_json()
```

作用：

- 把模型直接转成 JSON 字符串
- 适合接口返回、写文件、日志记录

这是 Pydantic 非常高频的用法，特别是在 FastAPI 这类框架里。

## 8. 自定义字段校验器 `field_validator`

`3-aadvance.py` 进入了更实用的进阶内容：自定义校验规则。

### 单字段自定义校验

比如邮箱格式：

```python
@field_validator("email")
def email_validator(cls, v):
    if "@" not in v:
        raise ValueError("邮箱格式错误")
    return v.lower()
```

这说明校验器不只是“检查”，还可以“顺手处理数据”，例如统一转成小写。

### 用户名业务规则校验

```python
@field_validator("name")
def name_validator(cls, v):
    if "admin" in v:
        raise ValueError("用户名错误")
    return v.lower()
```

说明 `field_validator` 很适合做业务规则限制，而不仅仅是类型检查。

### 密码复杂度校验

示例里还做了多条件校验：

```python
@field_validator("password")
def password_validator(cls, v):
    errors = []
    if len(v) < 8:
        errors.append("至少8个字符")
    if not any(c.isupper() for c in v):
        errors.append("至少1个大写字母")
    if errors:
        raise ValueError(";".join(errors))
    return v
```

这个例子很有代表性，说明你可以：

- 一次检查多个规则
- 收集多个错误后统一返回
- 把复杂业务校验集中写在模型里

这比把校验逻辑散落在业务代码里更清晰。

## 9. 这三份代码分别学到了什么

### `1-PyDantic HelloWorld.py`

重点是入门核心能力：

- `BaseModel` 基础模型
- 必填字段和可选字段
- 自动类型转换
- `ValidationError`
- `HttpUrl`
- `model_validate_json`
- `model_dump`
- `model_dump_json`

### `2-advance.py`

重点是字段约束和结构设计：

- `Field(...)` 必填声明
- 默认值
- 数值范围约束
- 字符串长度约束
- 嵌套模型
- `Optional` 可选字段

### `3-aadvance.py`

重点是业务规则校验：

- `field_validator`
- 单字段自定义校验
- 多条件组合校验
- 返回格式化后的值
- 多字段复用同一个校验逻辑

## 10. 学完之后应该形成的理解

可以把 Pydantic 理解成一句话：

“先定义数据应该长什么样，再让 Pydantic 帮你检查传进来的数据对不对。”

学习后应该掌握这条主线：

1. 用 `BaseModel` 定义数据结构
2. 用类型注解描述字段类型
3. 用 `Field` 增加约束
4. 用 `ValidationError` 处理错误
5. 用 `field_validator` 编写业务规则
6. 用 `model_dump` / `model_dump_json` 做数据输出

## 11. 实际开发中的典型应用

Pydantic 常用于：

- 校验前端传来的请求参数
- 校验配置文件内容
- 解析第三方接口返回的数据
- 约束数据库查询后的结构化结果
- 在 FastAPI 中定义请求体和响应体

## 12. 当前示例里的一个实践建议

示例里有这样的写法：

```python
tags: list[str] = []
```

虽然示例里问题不大，但从习惯上更推荐写成：

```python
from pydantic import Field

tags: list[str] = Field(default_factory=list)
```

这样更稳妥，也更符合“可变对象默认值”的最佳实践。

## 13. 一句话总结

这三份代码已经覆盖了 Pydantic 的一条完整学习路径：

从“定义模型和自动校验”，到“字段约束和嵌套结构”，再到“自定义业务校验规则”。

如果把这三部分掌握住，已经可以应对大多数日常开发里的数据校验场景。
