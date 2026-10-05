import pandas as pd
import matplotlib.pyplot as plt


data = {
    "Feature": [
        "Koszt", "Dostęp do GPU", "Praca offline", "Limity czasowe", "Kontrola środowiska"
    ],
    "Google Colab": ["Darmowy / płatne plany", "Tak", "Nie", "Tak", "Ograniczona"],
    "Jupyter Local": ["Koszt własnego sprzętu", "Jeśli komputer ma GPU", "Tak", "Brak", "Pełna"],
}

df = pd.DataFrame(data)
print(df.to_string(index=False))
df.to_csv("colab_vs_local.csv", index=False, encoding="utf-8-sig")

# Bonus: prosta punktacja wygody/niezależności
score = pd.DataFrame({"Środowisko": ["Google Colab", "Jupyter Local"], "Punkty": [3, 5]})
score.plot(kind="bar", x="Środowisko", y="Punkty", legend=False, title="Porównanie środowisk")
plt.ylabel("Punkty")
plt.tight_layout()
plt.savefig("colab_vs_local.png", dpi=150)
plt.show()
