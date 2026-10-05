from pathlib import Path


def create_sales_project():
    root = Path("sales_analysis")
    folders = [
        "data/raw", "data/processed", "notebooks", "src", "models", "reports"
    ]

    for folder in folders:
        (root / folder).mkdir(parents=True, exist_ok=True)

    (root / "README.md").write_text(
        "# Sales Analysis\n\nProjekt do analizy danych sprzedażowych.\n",
        encoding="utf-8",
    )
    (root / ".gitignore").write_text("data/raw/\n", encoding="utf-8")

    print(f"Utworzono projekt: {root.resolve()}")
    for path in sorted(root.rglob("*")):
        print(path)


if __name__ == "__main__":
    create_sales_project()
