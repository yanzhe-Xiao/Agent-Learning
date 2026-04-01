# ==================== 1. 函数装饰器（用了闭包） ====================
def timer(func):
    import time
    def wrapper(*args, **kwargs):      # ← 这里用了闭包！wrapper 记住了 func
        start = time.time()
        result = func(*args, **kwargs)
        print(f"[{func.__name__}] 耗时 {time.time()-start:.4f}s")
        return result
    return wrapper                     # 返回新函数

import time;   # 模拟耗时操作
@timer
def say_hello():
    time.sleep(1)
    print("hello")

# ==================== 2. 类装饰器（一般不用闭包） ====================
def add_timestamp(cls):                # 接收的是 class 对象
    """给类自动加上 created_at 属性"""
    original_init = cls.__init__

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        from datetime import datetime

# 当前日期和时间
        now = datetime.now()
        self.created_at = now   # 可以是 time.time()
        print(f"类 {cls.__name__} 被装饰了！")

    cls.__init__ = new_init            # 直接修改原类
    return cls                         # 返回修改后的类（或返回新类也行）

@add_timestamp
class User:
    def __init__(self, name):
        self.name = name

# ====================== 使用 ======================
say_hello()

u = User("张三")
print(u.created_at)   # 2026-04-01