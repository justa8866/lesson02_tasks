import time
import psutil
import numpy as np


def gb(value):
    return value / (1024 ** 3)


ram_before = psutil.virtual_memory().used
cpu_before = psutil.cpu_percent(interval=1)
start = time.perf_counter()

matrix = np.random.rand(1000, 1000)
# stabilniejsza macierz do odwracania
matrix = matrix @ matrix.T + np.eye(1000) * 0.01
inverse = np.linalg.inv(matrix)

duration = time.perf_counter() - start
cpu_after = psutil.cpu_percent(interval=1)
ram_after = psutil.virtual_memory().used

print("=== RAPORT ZUŻYCIA ZASOBÓW ===")
print(f"CPU przed: {cpu_before:.1f}%")
print(f"CPU po: {cpu_after:.1f}%")
print(f"RAM przed: {gb(ram_before):.2f} GB")
print(f"RAM po: {gb(ram_after):.2f} GB")
print(f"Różnica RAM: {gb(ram_after - ram_before):.4f} GB")
print(f"Czas obliczeń: {duration:.2f} s")
