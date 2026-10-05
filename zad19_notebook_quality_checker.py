from pathlib import Path
import ast
import json
import re
import sys


def check_notebook(path):
    nb = json.loads(Path(path).read_text(encoding="utf-8"))
    cells = nb.get("cells", [])
    total = max(len(cells), 1)
    markdown = [c for c in cells if c.get("cell_type") == "markdown"]
    code = [c for c in cells if c.get("cell_type") == "code"]
    text = "\n".join("".join(c.get("source", [])) for c in cells)

    markdown_ratio = len(markdown) / total
    has_magic = bool(re.search(r"%(time|timeit|matplotlib)", text))
    has_seed = bool(re.search(r"(random\.seed|np\.random\.seed|random_state\s*=|manual_seed|set_seed)", text))
    saves_plot = "savefig(" in text
    has_sections = len(re.findall(r"^#{1,3}\s", text, flags=re.M)) >= 3

    lengths = []
    nesting_scores = []
    for c in code:
        src = "".join(c.get("source", []))
        lengths.append(len(src.splitlines()))
        try:
            tree = ast.parse(src)
            nesting_scores.append(sum(isinstance(n, (ast.For, ast.While, ast.If, ast.FunctionDef, ast.ClassDef)) for n in ast.walk(tree)))
        except SyntaxError:
            nesting_scores.append(5)

    avg_len = sum(lengths) / max(len(lengths), 1)
    avg_nesting = sum(nesting_scores) / max(len(nesting_scores), 1)

    score = 0
    score += 20 if markdown_ratio >= 0.20 else round(markdown_ratio / 0.20 * 20)
    score += 15 if has_magic else 0
    score += 20 if has_seed else 0
    score += 15 if saves_plot else 0
    score += 15 if has_sections else 0
    score += 15 if avg_len <= 30 and avg_nesting <= 5 else 5

    recs = []
    if markdown_ratio < 0.20: recs.append("Dodaj więcej komórek Markdown (minimum 20%).")
    if not has_magic: recs.append("Dodaj użyteczne magic commands, np. %time lub %matplotlib inline.")
    if not has_seed: recs.append("Ustaw random seed dla reprodukowalności.")
    if not saves_plot: recs.append("Zapisuj ważne wykresy przez savefig().")
    if not has_sections: recs.append("Dodaj wyraźne sekcje: importy, konfiguracja, EDA, modelowanie, wnioski.")
    if avg_len > 30: recs.append("Skróć zbyt długie komórki kodu.")

    return score, recs


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "zad06_lesson02_practice.ipynb"
    score, recs = check_notebook(path)
    print(f"Quality score: {score}/100")
    print("Rekomendacje:")
    for r in recs or ["Notebook spełnia główne wymagania."]:
        print("-", r)
