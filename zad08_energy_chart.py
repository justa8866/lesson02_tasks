import matplotlib.pyplot as plt


devices = ["Laptop", "Desktop", "Server"]
energy = [30, 150, 400]
colors = ["green", "orange", "red"]

plt.figure(figsize=(8, 5))
plt.bar(devices, energy, color=colors)
plt.title("Zużycie energii urządzeń")
plt.xlabel("Urządzenie")
plt.ylabel("Zużycie energii [Wh]")
plt.tight_layout()
plt.savefig("energy_comparison.png", dpi=150)
plt.show()
print("Zapisano: energy_comparison.png")
