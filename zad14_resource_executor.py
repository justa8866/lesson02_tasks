from pathlib import Path
import threading
import time
import subprocess
import sys
import psutil
import pandas as pd
import matplotlib.pyplot as plt


def monitor(stop_event, rows, threshold=80):
    while not stop_event.is_set():
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        rows.append({"time": time.time(), "cpu": cpu, "ram": ram})
        if ram > threshold:
            print(f"OSTRZEŻENIE: RAM = {ram:.1f}% > {threshold}%")


def execute_notebook(notebook_path):
    rows = []
    stop_event = threading.Event()
    thread = threading.Thread(target=monitor, args=(stop_event, rows), daemon=True)
    thread.start()

    output = Path(notebook_path).with_name(Path(notebook_path).stem + "_executed.ipynb")
    cmd = [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", notebook_path, "--output", output.name]
    subprocess.run(cmd, check=True)

    stop_event.set()
    thread.join()

    df = pd.DataFrame(rows)
    if not df.empty:
        df["seconds"] = df["time"] - df["time"].iloc[0]
        plt.plot(df["seconds"], df["cpu"], label="CPU %")
        plt.plot(df["seconds"], df["ram"], label="RAM %")
        plt.xlabel("Czas [s]")
        plt.ylabel("Zużycie [%]")
        plt.legend()
        plt.tight_layout()
        plt.savefig("resource_usage.png", dpi=150)
        plt.close()
        df.to_csv("resource_usage.csv", index=False)

    html = "report.html"
    subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "html", str(output), "--output", html], check=True)
    print(f"Raport HTML: {html}")


if __name__ == "__main__":
    notebook = sys.argv[1] if len(sys.argv) > 1 else "zad06_lesson02_practice.ipynb"
    execute_notebook(notebook)
