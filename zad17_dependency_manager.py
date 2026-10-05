from pathlib import Path
import ast
import json
import importlib.metadata as md
import sys


def notebook_imports(path):
    nb = json.loads(Path(path).read_text(encoding="utf-8"))
    found = set()
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        code = "".join(cell.get("source", []))
        try:
            tree = ast.parse(code)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    found.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module.split(".")[0])
    return sorted(found)


def analyze(path):
    imports = notebook_imports(path)
    stdlib = set(sys.stdlib_module_names)
    packages = [x for x in imports if x not in stdlib]
    lines = ["# Dependency report", ""]
    req_lines = []

    for pkg in packages:
        try:
            version = md.version(pkg)
            lines.append(f"- ✅ `{pkg}` zainstalowany, wersja {version}")
            req_lines.append(f"{pkg}=={version}")
        except md.PackageNotFoundError:
            lines.append(f"- ❌ `{pkg}` nie jest zainstalowany")
            req_lines.append(pkg)

    alternatives = {"pandas": "polars (często szybszy i oszczędniejszy pamięciowo)", "plotly": "matplotlib dla prostych statycznych wykresów"}
    lines += ["", "## Sugestie lżejszych alternatyw"]
    for pkg in packages:
        if pkg in alternatives:
            lines.append(f"- {pkg}: {alternatives[pkg]}")

    Path("requirements_minimal.txt").write_text("\n".join(req_lines) + "\n", encoding="utf-8")
    Path("dependency_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wygenerowano requirements_minimal.txt i dependency_report.md")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python zad17_dependency_manager.py notebook.ipynb")
    else:
        analyze(sys.argv[1])
