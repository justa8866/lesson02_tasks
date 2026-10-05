from pathlib import Path
import subprocess
import sys
import json


def run(cmd, cwd=None):
    print(">", " ".join(map(str, cmd)))
    subprocess.run(cmd, cwd=cwd, check=True)


def setup_project(project_name):
    root = Path(project_name)
    root.mkdir(exist_ok=True)

    for folder in ["data/raw", "data/processed", "notebooks", "src", "models", "reports"]:
        (root / folder).mkdir(parents=True, exist_ok=True)

    (root / "README.md").write_text(f"# {project_name}\n\nProjekt Data Science.\n", encoding="utf-8")
    (root / ".gitignore").write_text(".venv/\n__pycache__/\ndata/raw/\n.ipynb_checkpoints/\n", encoding="utf-8")

    run(["git", "init"], cwd=root)
    run([sys.executable, "-m", "venv", ".venv"], cwd=root)

    pip = root / ".venv" / ("Scripts/pip.exe" if sys.platform.startswith("win") else "bin/pip")
    run([str(pip), "install", "jupyter", "pandas", "numpy", "matplotlib", "scikit-learn"])

    notebook = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": [f"# {project_name}\n"]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["import pandas as pd\n", "import numpy as np\n"]},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (root / "notebooks" / "template.ipynb").write_text(json.dumps(notebook, indent=2), encoding="utf-8")

    run([str(pip), "freeze"], cwd=root)
    result = subprocess.run([str(pip), "freeze"], capture_output=True, text=True, check=True)
    (root / "requirements.txt").write_text(result.stdout, encoding="utf-8")

    print("\n=== RAPORT ===")
    print(f"Projekt: {root.resolve()}")
    print("Struktura folderów: OK")
    print("Git: OK")
    print("venv: OK")
    print("Pakiety: OK")
    print("Notebook template: OK")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "new_ds_project"
    setup_project(name)
