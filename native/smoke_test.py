"""Check the built SRM on sample data, for each genotype.

Each check runs a short evolution, requires the error to come down, then evaluates
the best individual the way the app does for plots.

Usage: python native/smoke_test.py
"""
import math
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRM = ROOT / "srm" / ("SRM.exe" if sys.platform == "win32" else "SRM")
DATA = ROOT / "srm" / "data_2var.txt"
TEMPLATES = ("srmGP.txt", "srmGEP.txt", "srmAP.txt")
ECF_BANNER = "ECF, version 1.6.1"
MAX_ERROR = 0.1


def check_binary_is_current() -> None:
    if not SRM.exists():
        sys.exit(f"{SRM} does not exist: build it first, see native/README.md")
    sources = [p for p in (ROOT / "native").rglob("*") if p.suffix in (".cpp", ".h") or p.name == "CMakeLists.txt"]
    newest = max(sources, key=lambda p: p.stat().st_mtime)
    if newest.stat().st_mtime > SRM.stat().st_mtime:
        sys.exit(f"{SRM} is older than {newest}: rebuild it first")


def write_parameter_file(template: Path, target: Path, overrides: dict) -> None:
    tree = ET.parse(template)
    for entry in tree.getroot().find("Registry"):
        key = entry.get("key")
        if key in overrides:
            entry.text = overrides[key]
    tree.write(target)


def run_srm(label: str, folder: Path, *arguments: str) -> str:
    result = subprocess.run(
        [str(SRM), *arguments],
        cwd=folder,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        sys.exit(f"{label}: exit code {result.returncode}\n{result.stdout}\n{result.stderr}")
    if ECF_BANNER not in result.stdout:
        sys.exit(f"{label}: '{ECF_BANNER}' not in the output\n{result.stdout}")
    return result.stdout


def evolve(template_name: str, folder: Path) -> str:
    """Run a short evolution and return the last individual in the best file."""
    write_parameter_file(
        ROOT / "srm" / template_name,
        folder / "parameters.txt",
        {
            "input_file": str(DATA),
            "bestfile": "best.txt",
            "randomizer.seed": "1",
            "population.size": "200",
            "term.maxgen": "30",
        },
    )
    run_srm(template_name, folder, "parameters.txt")
    best_file = folder / "best.txt"
    if not best_file.exists():
        sys.exit(f"{template_name}: no best file")
    individuals = re.findall(r"<Individual.*?</Individual>", best_file.read_text(), re.DOTALL)
    if not individuals:
        sys.exit(f"{template_name}: no individual in the best file")
    first, error = (float(re.search(r'FitnessMin value="([^"]+)"', i).group(1)) for i in (individuals[0], individuals[-1]))
    if not math.isfinite(error) or error > MAX_ERROR or error >= first:
        sys.exit(f"{template_name}: error went from {first} to {error}, it should end below {MAX_ERROR}")
    print(f"{template_name}: error went from {first} to {error}")
    return individuals[-1]


def evaluate(template_name: str, folder: Path, individual: str) -> None:
    """Evaluate an individual on the input data, the way the app does for plots.

    Linear scaling is off because the scaling is already part of the individual.
    """
    (folder / "individual.txt").write_text(individual)
    write_parameter_file(
        ROOT / "srm" / "srm_eval.txt",
        folder / "evaluate.txt",
        {"input_file": str(DATA), "bestfile": "evaluated.txt", "linear_scaling": "false"},
    )
    run_srm(f"{template_name} evaluation", folder, "evaluate.txt", "individual.txt")
    output = (folder / "evaluated.txt").read_text()
    points = [float(line) for line in output.split("</Individual>")[-1].split()]
    expected = len(DATA.read_text().split("\n")) - 1
    if len(points) != expected or not all(math.isfinite(point) for point in points):
        sys.exit(f"{template_name}: expected {expected} finite data points\n{output}")
    print(f"{template_name}: evaluated {len(points)} data points")


if __name__ == "__main__":
    check_binary_is_current()
    for name in TEMPLATES:
        with tempfile.TemporaryDirectory() as temporary:
            evaluate(name, Path(temporary), evolve(name, Path(temporary)))
