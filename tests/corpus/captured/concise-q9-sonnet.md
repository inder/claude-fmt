```python
lst = [1, 2, 3]

lst.reverse()          # in place, returns None
reversed_lst = lst[::-1]        # new list (slice)
reversed_lst = list(reversed(lst))  # new list (iterator)
```

Use `.reverse()` to mutate, `[::-1]` for a quick copy, and `reversed(lst)` when you only need to iterate.
