- **Standard library (`csv` module)** — no dependencies, reads rows as lists:
  ```python
  import csv

  with open("data.csv", newline="", encoding="utf-8") as f:
      reader = csv.reader(f)
      header = next(reader)  # skip/capture header row
      for row in reader:
          print(row)  # ['value1', 'value2', ...]
  ```
- **Rows as dicts (`csv.DictReader`)** — keys come from the header row:
  ```python
  import csv

  with open("data.csv", newline="", encoding="utf-8") as f:
      for row in csv.DictReader(f):
          print(row["name"], row["age"])
  ```
- **pandas** — best for analysis; loads into a DataFrame (`pip install pandas`):
  ```python
  import pandas as pd

  df = pd.read_csv("data.csv")
  print(df.head())
  print(df["age"].mean())
  ```
- **Tips**
  - Always pass `newline=""` when using the `csv` module, which prevents line-ending bugs.
  - For other delimiters, use `csv.reader(f, delimiter=";")` or `pd.read_csv(path, sep=";")`.
  - The `csv` module returns every value as a string. Convert types yourself, e.g. `int(row["age"])`, or let pandas infer them.
