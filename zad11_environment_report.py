from pathlib import Path
from datetime import datetime
import json
import platform
import sys
import importlib.metadata as md
import psutil


def generate_environment_report(output_dir="reports"):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    packages = sorted([f"{d.metadata['Name']}=={d.version}" for d in md.distributions() if d.metadata.get('Name')])
    vm = psutil.virtual_memory()

    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "python_version": sys.version,
        "os": platform.platform(),
        "processor": platform.processor(),
        "cpu_logical": psutil.cpu_count(logical=True),
        "cpu_physical": psutil.cpu_count(logical=False),
        "ram_total_gb": round(vm.total / 1024**3, 2),
        "ram_available_gb": round(vm.available / 1024**3, 2),
        "installed_packages_count": len(packages),
        "installed_packages": packages,
        "gpu": "Nie sprawdzono / brak PyTorch",
    }

    try:
        import torch
        report["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Brak GPU CUDA"
    except ImportError:
        pass

    filename = out / f"environment_report_{datetime.now():%Y%m%d_%H%M%S}.json"
    filename.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(filename)


if __name__ == "__main__":
    path = generate_environment_report("reports")
    print(f"Raport zapisano: {path}")
