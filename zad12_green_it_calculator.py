import matplotlib.pyplot as plt


POWER_W = {"laptop": 30, "desktop": 150, "cloud gpu": 250}
REGION_CO2_G_PER_KWH = {"polska": 600, "ue": 250, "norwegia": 30}
CAR_G_PER_KM = 120


def green_it_calculator(hours, device, region):
    device = device.strip().lower()
    region = region.strip().lower()
    if device not in POWER_W:
        raise ValueError(
            f"Nieznane urządzenie: {device!r}. Wybierz: {', '.join(POWER_W)}."
        )
    if region not in REGION_CO2_G_PER_KWH:
        raise ValueError(
            f"Nieznany region: {region!r}. Wybierz: {', '.join(REGION_CO2_G_PER_KWH)}."
        )

    energy_kwh = POWER_W[device] * hours / 1000
    co2_g = energy_kwh * REGION_CO2_G_PER_KWH[region]
    car_km = co2_g / CAR_G_PER_KM
    return energy_kwh, co2_g, car_km


if __name__ == "__main__":
    try:
        hours = float(input("Czas pracy [h]: "))
        device = input("Urządzenie (laptop/desktop/cloud gpu): ")
        region = input("Region (polska/ue/norwegia): ")
        energy, co2, car_km = green_it_calculator(hours, device, region)
    except ValueError as error:
        raise SystemExit(f"\nBłąd danych: {error}") from None

    print(f"Zużycie energii: {energy:.3f} kWh")
    print(f"Emisja CO2: {co2:.1f} g")
    print(f"Odpowiednik jazdy autem: {car_km:.2f} km")

    plt.bar(["Energia [kWh]", "CO2 [kg]"], [energy, co2 / 1000])
    plt.title("Green IT Calculator")
    plt.tight_layout()
    plt.savefig("zad12_green_it.png", dpi=150)
    plt.show()
