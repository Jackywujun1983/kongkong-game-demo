# Python 编码规范

本文档作为本项目及后续 Python 项目的默认编码规范。主要参考 PEP 8、PEP 257、类型标注实践，以及现代 Python 工程中常用的 `black`、`ruff`、`pytest` 等工具约定。

## 1. 基本原则

- 优先保证代码可读性和可维护性。
- 简单优于复杂，明确优于隐式。
- 遵循 PEP 8 风格规范。
- 公共函数、类、模块应具备清晰命名和必要文档。
- 新代码建议使用类型标注。
- 避免无意义抽象，只有在能降低复杂度或减少重复时才引入封装。

## 2. 命名规范

| 类型 | 命名方式 | 示例 |
| --- | --- | --- |
| 变量 | 小写 + 下划线 | `user_name` |
| 函数 | 小写 + 下划线 | `get_user_info()` |
| 类 | 大驼峰 | `UserService` |
| 常量 | 全大写 + 下划线 | `MAX_RETRY_COUNT` |
| 模块文件 | 小写 + 下划线 | `user_service.py` |
| 私有成员 | 单下划线开头 | `_cache` |

避免使用无意义命名：

```python
# 不推荐
x = get_data()

# 推荐
user_list = get_users()
```

布尔变量或函数建议使用表达状态的命名：

```python
is_active = True
has_permission = check_permission(user)
can_retry = retry_count < max_retry_count
```

## 3. 缩进与格式

- 使用 4 个空格缩进。
- 不使用 Tab。
- 每行建议不超过 88 个字符；如团队另有约定，可统一为 120。
- 运算符两侧保留空格。
- 函数、类、模块之间保持清晰空行。

```python
total_price = price * quantity
```

长参数或长表达式优先使用括号换行：

```python
result = create_order(
    user_id=user_id,
    product_id=product_id,
    quantity=quantity,
)
```

## 4. 导入规范

导入顺序：

1. 标准库
2. 第三方库
3. 本地模块

```python
import os
import sys

import requests

from app.services.user_service import UserService
```

避免使用通配符导入：

```python
# 不推荐
from module import *

# 推荐
from module import specific_function
```

## 5. 函数规范

函数应职责单一，命名应能表达行为。

```python
def calculate_total_price(price: float, quantity: int) -> float:
    return price * quantity
```

建议：

- 参数不宜过多。
- 避免函数过长。
- 有返回值时尽量标注返回类型。
- 布尔函数使用 `is_`、`has_`、`can_` 等前缀。
- 对外部可调用函数，应避免依赖隐式全局状态。

```python
def is_valid_email(email: str) -> bool:
    return "@" in email
```

## 6. 类规范

类名使用大驼峰命名。

```python
class UserService:
    def get_user_by_id(self, user_id: int) -> User:
        ...
```

建议：

- 类应表示清晰的业务概念或技术职责。
- 避免万能类。
- 私有方法使用 `_` 前缀。
- 优先组合，谨慎使用深层继承。

## 7. 注释规范

注释用于解释“为什么”，而不是重复代码“做了什么”。

```python
# 推荐：说明原因
# 使用缓存避免频繁请求外部接口
user = cache.get(user_id)
```

避免无意义注释：

```python
# 不推荐
# 给 x 加 1
x += 1
```

## 8. 文档字符串

公共模块、类、函数建议添加 docstring。

```python
def get_user(user_id: int) -> User:
    """根据用户 ID 获取用户信息。"""
    ...
```

复杂函数可说明参数和返回值：

```python
def create_order(user_id: int, product_id: int) -> Order:
    """
    创建订单。

    Args:
        user_id: 用户 ID。
        product_id: 商品 ID。

    Returns:
        创建成功的订单对象。
    """
    ...
```

## 9. 类型标注

推荐使用类型标注提升可维护性。

```python
def send_email(to: str, subject: str, content: str) -> bool:
    ...
```

常见类型：

```python
from typing import Optional


def find_user(user_id: int) -> Optional[User]:
    ...
```

Python 3.10+ 可使用：

```python
def find_user(user_id: int) -> User | None:
    ...
```

复杂结构建议使用 `TypedDict`、`dataclass` 或 Pydantic 模型表达。

## 10. 异常处理

只捕获明确知道如何处理的异常。

```python
try:
    user = get_user(user_id)
except UserNotFoundError:
    return None
```

避免裸 `except`：

```python
# 不推荐
try:
    ...
except:
    ...
```

记录异常时保留上下文：

```python
try:
    result = call_external_api()
except ExternalApiError:
    logger.exception("Failed to call external API")
    raise
```

## 11. 日志规范

生产代码中避免使用 `print`，应使用 `logging`。

```python
import logging

logger = logging.getLogger(__name__)

logger.info("User created: %s", user_id)
```

建议：

- 日志内容应包含排查问题所需的关键上下文。
- 不记录密码、Token、身份证号等敏感信息。
- 使用参数化日志，避免提前拼接字符串。

## 12. 代码组织

推荐项目结构：

```text
project/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── services/
│   ├── utils/
│   └── config.py
├── tests/
├── requirements.txt
└── README.md
```

建议：

- 业务逻辑放在清晰的模块中，避免集中在入口文件。
- 工具函数按职责拆分，不要堆积成大型 `utils.py`。
- 测试目录结构尽量对应业务代码结构。

## 13. 测试规范

- 测试文件以 `test_` 开头。
- 测试函数以 `test_` 开头。
- 推荐使用 `pytest`。
- 核心业务逻辑、边界条件、异常分支应有测试覆盖。

```python
def test_calculate_total_price():
    assert calculate_total_price(10, 2) == 20
```

## 14. 推荐工具

| 工具 | 用途 |
| --- | --- |
| `black` | 自动格式化 |
| `ruff` | 代码检查和自动修复 |
| `mypy` | 类型检查 |
| `pytest` | 单元测试 |
| `isort` | 导入排序，`ruff` 也可替代 |

推荐配置可放入 `pyproject.toml`：

```toml
[tool.black]
line-length = 88

[tool.ruff]
line-length = 88

[tool.mypy]
python_version = "3.10"
strict = true
```

## 15. 提交前检查

提交代码前建议执行：

```bash
ruff check .
black .
pytest
```

如项目启用了类型检查，额外执行：

```bash
mypy .
```

## 16. 总结

Python 代码应保持：

- 命名清晰
- 格式统一
- 函数简短
- 类型明确
- 异常可控
- 日志可追踪
- 测试覆盖核心逻辑

