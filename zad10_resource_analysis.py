import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


np.random.seed(42)
models = ["LinearRegression", "RandomForest", "SVM", "KNN", "NeuralNetwork"]
rows = []

for model in models:
    for _ in range(10):
        training_time = np.random.uniform(1, 120)
        cpu = np.random.uniform(20, 100)
        ram = np.random.uniform(1, 16)
        energy = (training_time / 60) * ((cpu / 100) * 0.30 + (ram / 16) * 0.10)
        rows.append([model, training_time, cpu, ram, energy])

columns = ["model_name", "training_time_min", "cpu_percent", "ram_gb", "energy_kwh"]
df = pd.DataFrame(rows, columns=columns)
summary = df.groupby("model_name").mean(numeric_only=True).round(3)
print("=== ŚREDNIE ZUŻYCIE ===")
print(summary)

energy_avg = summary["energy_kwh"].sort_values()
energy_avg.plot(kind="bar", title="Średnie zużycie energii modeli ML")
plt.ylabel("kWh")
plt.tight_layout()
plt.savefig("zad10_energy_models.png", dpi=150)
plt.show()

best = energy_avg.index[0]
print(f"\nWniosek: najbardziej energooszczędny w tej symulacji jest model: {best}.")
print("Niższy czas treningu, użycie CPU i RAM zwykle zmniejszają zużycie energii.")
