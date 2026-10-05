import io
import json
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Green Data Science Dashboard", layout="wide")
st.title("Green Data Science Dashboard")
st.write("Monitorowanie ekologicznych aspektów pracy Data Science.")

uploaded = st.file_uploader("Wgraj Jupyter Notebook (.ipynb)", type=["ipynb"])
hours = st.number_input("Szacowany czas wykonania [h]", min_value=0.1, value=1.0, step=0.1)
device = st.selectbox("Środowisko", ["Laptop", "Desktop", "Cloud GPU"])
region = st.selectbox("Region", ["Polska", "UE", "Norwegia"])

power = {"Laptop": 30, "Desktop": 150, "Cloud GPU": 250}
co2_factor = {"Polska": 600, "UE": 250, "Norwegia": 30}

code_lines = 0
imports = 0
if uploaded is not None:
    nb = json.load(uploaded)
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            src = "".join(cell.get("source", []))
            code_lines += len(src.splitlines())
            imports += sum(1 for line in src.splitlines() if line.strip().startswith(("import ", "from ")))

energy_kwh = power[device] * hours / 1000
co2_g = energy_kwh * co2_factor[region]
complexity_factor = 1 + min(code_lines / 1000, 1)
estimated_energy = energy_kwh * complexity_factor
estimated_co2 = co2_g * complexity_factor

c1, c2, c3 = st.columns(3)
c1.metric("Kod", f"{code_lines} linii")
c2.metric("Energia", f"{estimated_energy:.3f} kWh")
c3.metric("CO2", f"{estimated_co2:.1f} g")

chart_df = pd.DataFrame({"Wartość": [estimated_energy, estimated_co2 / 1000]}, index=["Energia [kWh]", "CO2 [kg]"])
st.bar_chart(chart_df)

st.subheader("Porównanie alternatyw")
comparison = pd.DataFrame({
    "Środowisko": ["Laptop", "Desktop", "Cloud GPU"],
    "Energia kWh": [power[x] * hours / 1000 * complexity_factor for x in ["Laptop", "Desktop", "Cloud GPU"]],
})
st.dataframe(comparison, use_container_width=True)

st.subheader("Sugestie optymalizacji")
suggestions = []
if device == "Cloud GPU": suggestions.append("Używaj GPU tylko wtedy, gdy obliczenia rzeczywiście na tym zyskują.")
if code_lines > 500: suggestions.append("Testuj najpierw na małej próbce danych.")
if imports > 15: suggestions.append("Sprawdź, czy wszystkie biblioteki są potrzebne.")
suggestions += ["Preferuj operacje wektorowe NumPy/Pandas zamiast pętli Python.", "Zamykaj nieużywane sesje i zwalniaj duże obiekty z pamięci."]
for s in suggestions:
    st.write("-", s)

report = f"""GREEN DATA SCIENCE REPORT\n\nLinie kodu: {code_lines}\nŚrodowisko: {device}\nRegion: {region}\nEnergia: {estimated_energy:.3f} kWh\nCO2: {estimated_co2:.1f} g\n"""
st.download_button("Pobierz raport TXT", data=report, file_name="green_ds_report.txt")
st.caption("Eksport PDF można dodać np. przez bibliotekę reportlab; wersja kursowa działa bez dodatkowej konfiguracji PDF.")
