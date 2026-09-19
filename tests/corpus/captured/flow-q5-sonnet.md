A decorator is a function that takes a function and returns a replacement, and `@decorator` is shorthand for `func = decorator(func)`.

```
 @timer
 def work(): ...
        │
        ▼
 Python defines work() normally
        │
        ▼
 timer(work) is called once, at definition time
        │
        ▼
 timer builds and returns wrapper(), a closure over work
        │
        ▼
 name `work` is rebound to wrapper
        │
        ▼
 later call: work() → wrapper() → runs extra logic → calls original work() → returns result
```

```python
import time
from functools import wraps

def timer(func):
    @wraps(func)  # keeps func's name and docstring
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start:.4f}s")
        return result
    return wrapper

@timer
def work(n):
    return sum(range(n))

work(1_000_000)  # prints: work took 0.0123s
```

Key points: the wrapper uses `*args, **kwargs` so it works with any signature, and `@wraps` preserves the original function's metadata. To pass arguments to a decorator, such as `@retry(3)`, add another outer function that returns the decorator.
