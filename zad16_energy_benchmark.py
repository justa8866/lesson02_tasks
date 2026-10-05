import time
import psutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor


def bench(name, func):
    proc = psutil.Process()
    mem_before = proc.memory_info().rss
    cpu_before = psutil.cpu_percent(interval=None)
    start = time.perf_counter()
    func()
    duration = time.perf_counter() - start
    cpu_after = psutil.cpu_percent(interval=None)
    mem_after = proc.memory_info().rss
    return {
        "operation": name,
        "time_s": duration,
        "cpu_delta": cpu_after - cpu_before,
        "ram_delta_mb": (mem_after - mem_before) / 1024**2,
    }


n = 200_000
a = np.random.rand(n)
b = np.random.rand(n)
df = pd.DataFrame({"a": a[:100000], "b": b[:100000]})
X = np.random.rand(5000, 10)
y = np.random.rand(5000)

ops = [
    ("Python loop add", lambda: [x + y for x, y in zip(a[:50000], b[:50000])]),
    ("NumPy add", lambda: np.add(a, b)),
    ("Python loop square", lambda: [x*x for x in a[:50000]]),
    ("NumPy square", lambda: np.square(a)),
    ("Pandas iterrows", lambda: [r.a + r.b for _, r in df.head(5000).iterrows()]),
    ("Pandas vectorized", lambda: df["a"] + df["b"]),
    ("Python sum", lambda: sum(a.tolist())),
    ("NumPy sum", lambda: np.sum(a)),
    ("LinearRegression", lambda: LinearRegression().fit(X, y)),
    ("RandomForest", lambda: RandomForestRegressor(n_estimators=20, random_state=42, n_jobs=1).fit(X, y)),
]

results = pd.DataFrame([bench(name, func) for name, func in ops])
print(results.sort_values("time_s").to_string(index=False))
results.to_csv("benchmark_results.csv", index=False)

results.sort_values("time_s").plot(kind="barh", x="operation", y="time_s", legend=False, title="Benchmark czasu")
plt.xlabel("Czas [s]")
plt.tight_layout()
plt.savefig("benchmark_times.png", dpi=150)
plt.show()

print("\nRekomendacja Green IT: preferuj operacje wektorowe NumPy/Pandas zamiast pętli Python.")
print("W ML wybieraj prostszy model, jeśli daje wystarczającą jakość przy znacznie krótszym treningu.")
