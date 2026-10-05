import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time


WORKSPACE = Path(__file__).resolve().parent
RESULTS_DIR = WORKSPACE / "multi_environment_results"
REPORT_PATH = WORKSPACE / "multi_environment_report.json"
HELPER_PACKAGES = ("nbclient", "ipykernel", "nbformat")


def text_value(value):
    return "".join(value) if isinstance(value, list) else str(value)


def output_signature(notebook):
    signature = []
    for cell_number, cell in enumerate(notebook.get("cells", []), start=1):
        if cell.get("cell_type") != "code":
            continue

        cell_outputs = []
        for output in cell.get("outputs", []):
            output_type = output.get("output_type")
            if output_type == "stream":
                cell_outputs.append({
                    "type": output_type,
                    "name": output.get("name"),
                    "text": text_value(output.get("text", "")),
                })
            elif output_type in ("display_data", "execute_result"):
                data = {}
                for mime, value in sorted(output.get("data", {}).items()):
                    if mime in ("image/png", "image/jpeg"):
                        raw = base64.b64decode(text_value(value))
                        data[mime] = hashlib.sha256(raw).hexdigest()
                    elif mime.startswith("text/"):
                        data[mime] = text_value(value)
                    else:
                        data[mime] = value
                cell_outputs.append({"type": output_type, "data": data})
            elif output_type == "error":
                cell_outputs.append({
                    "type": output_type,
                    "name": output.get("ename"),
                    "value": output.get("evalue"),
                })

        signature.append({"cell": cell_number, "outputs": cell_outputs})
    return signature


def execute_worker(notebook_path, executed_path, result_path, environment, timeout):
    import nbformat
    from nbclient import NotebookClient

    notebook_path = Path(notebook_path).resolve()
    executed_path = Path(executed_path).resolve()
    result_path = Path(result_path).resolve()
    result_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLBACKEND", "Agg")

    started = time.perf_counter()
    notebook = None
    error = None
    try:
        notebook = nbformat.read(notebook_path, as_version=4)
        kernel_name = f"task18-{os.getpid()}"
        with tempfile.TemporaryDirectory(prefix="task18-kernel-") as kernel_root:
            kernel_dir = Path(kernel_root) / "kernels" / kernel_name
            kernel_dir.mkdir(parents=True)
            kernel_spec = {
                "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": environment,
                "language": "python",
            }
            (kernel_dir / "kernel.json").write_text(
                json.dumps(kernel_spec), encoding="utf-8"
            )

            previous_jupyter_path = os.environ.get("JUPYTER_PATH")
            extra_paths = [kernel_root]
            if previous_jupyter_path:
                extra_paths.append(previous_jupyter_path)
            os.environ["JUPYTER_PATH"] = os.pathsep.join(extra_paths)
            try:
                client = NotebookClient(
                    notebook,
                    timeout=timeout,
                    kernel_name=kernel_name,
                    resources={"metadata": {"path": str(notebook_path.parent)}},
                )
                client.execute()
            finally:
                if previous_jupyter_path is None:
                    os.environ.pop("JUPYTER_PATH", None)
                else:
                    os.environ["JUPYTER_PATH"] = previous_jupyter_path

        status = "success"
    except Exception as exception:
        status = "failed"
        error = f"{type(exception).__name__}: {exception}"[:4000]

    elapsed = time.perf_counter() - started
    if notebook is not None:
        nbformat.write(notebook, executed_path)
        cells = output_signature(notebook)
    else:
        cells = []

    result = {
        "environment": environment,
        "status": status,
        "execution_time_s": elapsed,
        "cell_outputs": cells,
        "executed_notebook": str(executed_path),
        "error": error,
    }
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return 0 if status == "success" else 1


def run_process(command, timeout=900, cwd=None):
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return error


def prepare_python(python_executable, requirements):
    probe = run_process([
        python_executable,
        "-c",
        "import ipykernel, nbclient, nbformat",
    ])
    if isinstance(probe, Exception):
        return str(probe)

    if probe.returncode != 0:
        install = run_process([
            python_executable,
            "-m",
            "pip",
            "install",
            "nbclient",
            "ipykernel",
        ])
        if isinstance(install, Exception) or install.returncode != 0:
            detail = str(install) if isinstance(install, Exception) else install.stderr
            return f"Nie udało się przygotować nbclient/ipykernel: {detail[-2000:]}"

    if requirements is not None:
        install = run_process([
            python_executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements),
        ])
        if isinstance(install, Exception) or install.returncode != 0:
            detail = str(install) if isinstance(install, Exception) else install.stderr
            return f"Nie udało się zainstalować wymagań notatnika: {detail[-2000:]}"
    return None


def worker_paths(environment):
    safe_name = "".join(char.lower() if char.isalnum() else "_" for char in environment)
    return (
        RESULTS_DIR / f"{safe_name}.ipynb",
        RESULTS_DIR / f"{safe_name}.json",
    )


def run_worker(python_executable, notebook, environment, timeout, requirements=None):
    executed_path, result_path = worker_paths(environment)
    for path in (executed_path, result_path):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    setup_error = prepare_python(python_executable, requirements)
    if setup_error:
        return {"environment": environment, "status": "failed", "error": setup_error}

    process = run_process([
        python_executable,
        str(Path(__file__).resolve()),
        "--worker",
        str(notebook),
        str(executed_path),
        str(result_path),
        environment,
        str(timeout),
    ], timeout=timeout + 60, cwd=WORKSPACE)
    if isinstance(process, Exception):
        return {"environment": environment, "status": "failed", "error": str(process)}
    if result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if process.returncode != 0 and result["status"] == "success":
            result["status"] = "failed"
            result["error"] = process.stderr[-2000:]
        return result
    return {
        "environment": environment,
        "status": "failed",
        "error": (process.stderr or process.stdout)[-4000:] or "Proces nie utworzył raportu.",
    }


def resolve_python(version):
    if os.name == "nt":
        command = ["py", f"-{version}", "-c", "import sys; print(sys.executable)"]
    else:
        executable = shutil.which(f"python{version}")
        if executable is None:
            return None, f"Python {version} nie jest zainstalowany."
        command = [executable, "-c", "import sys; print(sys.executable)"]

    process = run_process(command, timeout=15)
    if isinstance(process, Exception):
        return None, str(process)
    if process.returncode != 0:
        return None, f"Python {version} nie jest zainstalowany."
    return process.stdout.strip().splitlines()[-1], None


def run_docker(notebook, environment, timeout, requirements=None):
    docker = shutil.which("docker")
    if docker is None:
        return {"environment": environment, "status": "unavailable", "error": "Docker nie jest zainstalowany."}

    executed_path, result_path = worker_paths(environment)
    for path in (executed_path, result_path):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    notebook_rel = notebook.relative_to(WORKSPACE).as_posix()
    executed_rel = executed_path.relative_to(WORKSPACE).as_posix()
    result_rel = result_path.relative_to(WORKSPACE).as_posix()
    script_rel = Path(__file__).resolve().relative_to(WORKSPACE).as_posix()
    setup = "python -m pip install -q nbclient ipykernel"
    if requirements is not None:
        requirements_rel = requirements.relative_to(WORKSPACE).as_posix()
        setup += f" && python -m pip install -q -r /workspace/{requirements_rel}"
    setup += (
        f" && python /workspace/{script_rel} --worker"
        f" /workspace/{notebook_rel} /workspace/{executed_rel}"
        f" /workspace/{result_rel} {shlex.quote(environment)} {timeout}"
    )
    workspace_mount = str(WORKSPACE).replace("\\", "/")
    process = run_process([
        docker,
        "run",
        "--rm",
        "-v",
        f"{workspace_mount}:/workspace",
        "-w",
        "/workspace",
        "python:3.11-slim",
        "sh",
        "-lc",
        setup,
    ], timeout=1800)
    if isinstance(process, Exception):
        return {"environment": environment, "status": "failed", "error": str(process)}
    if result_path.exists():
        return json.loads(result_path.read_text(encoding="utf-8"))
    detail = (process.stderr or process.stdout)[-4000:]
    return {
        "environment": environment,
        "status": "failed",
        "error": detail or "Docker nie zwrócił raportu wykonania.",
    }


def load_colab_result(notebook_path, execution_time):
    try:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        return {
            "environment": "Google Colab",
            "status": "success",
            "execution_time_s": execution_time,
            "cell_outputs": output_signature(notebook),
            "executed_notebook": str(notebook_path),
            "error": None,
        }
    except Exception as error:
        return {"environment": "Google Colab", "status": "failed", "error": str(error)}


def compare_results(results):
    successful = [result for result in results if result.get("status") == "success"]
    if len(successful) < 2:
        return None, []

    baseline = successful[0]
    comparisons = []
    baseline_cells = {item["cell"]: item["outputs"] for item in baseline["cell_outputs"]}
    for result in successful[1:]:
        other_cells = {item["cell"]: item["outputs"] for item in result["cell_outputs"]}
        cell_numbers = sorted(set(baseline_cells) | set(other_cells))
        different_cells = [
            cell for cell in cell_numbers
            if baseline_cells.get(cell) != other_cells.get(cell)
        ]
        run_time = result.get("execution_time_s")
        baseline_time = baseline.get("execution_time_s")
        comparisons.append({
            "baseline": baseline["environment"],
            "environment": result["environment"],
            "outputs_identical": not different_cells,
            "different_cells": different_cells,
            "time_delta_s": (
                round(run_time - baseline_time, 6)
                if run_time is not None and baseline_time is not None
                else None
            ),
        })
    return baseline["environment"], comparisons


def parse_args():
    parser = argparse.ArgumentParser(
        description="Uruchamia ten sam notebook w lokalnych Pythonach i Dockerze, a potem porównuje wyjścia."
    )
    parser.add_argument(
        "notebook",
        nargs="?",
        default="zad06_lesson02_practice.ipynb",
        help="Notatnik .ipynb (domyślnie zad06_lesson02_practice.ipynb).",
    )
    parser.add_argument(
        "--requirements",
        help="Opcjonalny plik wymagań instalowany w testowanych środowiskach; musi wspierać Python 3.9.",
    )
    parser.add_argument("--colab-result", help="Wykonany i pobrany z Colaba plik .ipynb do porównania.")
    parser.add_argument("--colab-time-s", type=float, help="Czas wykonania zanotowany w Colabie.")
    parser.add_argument("--timeout", type=int, default=300, help="Limit czasu wykonania notebooka w sekundach.")
    parser.add_argument("--report", default=str(REPORT_PATH), help="Ścieżka raportu JSON.")
    parser.add_argument("--worker", nargs=5, metavar=("NOTEBOOK", "OUTPUT", "RESULT", "ENV", "TIMEOUT"))
    return parser.parse_args()


def main():
    args = parse_args()
    if args.worker:
        notebook, output, result, environment, timeout = args.worker
        return execute_worker(notebook, output, result, environment, int(timeout))

    notebook = Path(args.notebook)
    if not notebook.is_absolute():
        notebook = WORKSPACE / notebook
    notebook = notebook.resolve()
    if not notebook.is_file() or notebook.suffix.lower() != ".ipynb":
        print(f"Nie znaleziono notatnika .ipynb: {notebook}", file=sys.stderr)
        return 2
    try:
        notebook.relative_to(WORKSPACE)
    except ValueError:
        print("Notatnik musi znajdować się w folderze projektu.", file=sys.stderr)
        return 2

    requirements = None
    if args.requirements:
        requirements = Path(args.requirements)
        if not requirements.is_absolute():
            requirements = WORKSPACE / requirements
        requirements = requirements.resolve()
        if not requirements.is_file():
            print(f"Nie znaleziono pliku wymagań: {requirements}", file=sys.stderr)
            return 2

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    current_version = sys.version.split()[0]
    results.append(run_worker(
        sys.executable,
        notebook,
        f"Local Python {current_version} (bieżący)",
        args.timeout,
        requirements,
    ))

    for version in ("3.9", "3.11"):
        environment = f"Local Python {version}"
        executable, error = resolve_python(version)
        if error:
            results.append({"environment": environment, "status": "unavailable", "error": error})
        else:
            results.append(run_worker(executable, notebook, environment, args.timeout, requirements))

    results.append(run_docker(notebook, "Docker Python 3.11", args.timeout, requirements))
    if args.colab_result:
        colab_path = Path(args.colab_result)
        if not colab_path.is_absolute():
            colab_path = WORKSPACE / colab_path
        results.append(load_colab_result(colab_path.resolve(), args.colab_time_s))
    else:
        results.append({
            "environment": "Google Colab",
            "status": "manual_required",
            "error": "Uruchom notebook w Colabie, pobierz plik .ipynb z wynikami i przekaż go przez --colab-result.",
        })

    baseline, comparisons = compare_results(results)
    report = {
        "notebook": str(notebook),
        "baseline": baseline,
        "timing_note": "Czas obejmuje start kernela i wykonanie komórek; instalacja pakietów jest poza pomiarem.",
        "results": results,
        "comparisons": comparisons,
    }
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = WORKSPACE / report_path
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    for result in results:
        duration = result.get("execution_time_s")
        duration_text = f"{duration:.2f} s" if duration is not None else "brak pomiaru"
        print(f"{result['environment']}: {result['status']} ({duration_text})")
        if result.get("error"):
            print(f"  {result['error']}")
    for comparison in comparisons:
        verdict = "identyczne" if comparison["outputs_identical"] else "różnice"
        print(
            f"Porównanie z {comparison['baseline']}: {comparison['environment']} - "
            f"{verdict}; różne komórki: {comparison['different_cells']}"
        )
    print(f"\nRaport zapisano: {report_path}")
    if not args.colab_result:
        print("Colab: po wykonaniu notebooka pobierz jego kopię z wynikami i użyj --colab-result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
