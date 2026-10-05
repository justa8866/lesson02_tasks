from pathlib import Path
import json
import re
import sys


COLAB_PATTERNS = ["from google.colab import drive", "drive.mount(", "!pip install", "%pip install"]


def convert_notebook(input_path):
    src = Path(input_path)
    nb = json.loads(src.read_text(encoding="utf-8"))
    imports = set()
    new_cells = []

    setup_cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## Uruchomienie lokalne\n",
            "Utwórz venv i zainstaluj pakiety z `requirements.txt`.\n",
        ],
    }
    new_cells.append(setup_cell)

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            new_cells.append(cell)
            continue
        source = "".join(cell.get("source", []))
        if any(p in source for p in COLAB_PATTERNS):
            continue
        source = source.replace("/content/drive/MyDrive/", "./data/")
        for match in re.findall(r"^\s*(?:from|import)\s+([A-Za-z0-9_\.]+)", source, flags=re.M):
            imports.add(match.split(".")[0])
        cell["source"] = source.splitlines(keepends=True)
        new_cells.append(cell)

    nb["cells"] = new_cells
    out = src.with_name(src.stem + "_local.ipynb")
    out.write_text(json.dumps(nb, indent=2, ensure_ascii=False), encoding="utf-8")

    stdlib = {"os", "sys", "json", "re", "pathlib", "datetime", "time", "math", "random"}
    reqs = sorted(i for i in imports if i not in stdlib)
    Path("requirements.txt").write_text("\n".join(reqs) + "\n", encoding="utf-8")
    print(f"Nowy notebook: {out}")
    print("Wygenerowano requirements.txt")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python zad15_colab_to_local.py notebook.ipynb")
    else:
        convert_notebook(sys.argv[1])
