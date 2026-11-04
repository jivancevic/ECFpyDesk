"""Run the built SRM once per genotype on sample data and check that it works.

Usage: python native/smoke_test.py
"""
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRM = ROOT / "srm" / ("SRM.exe" if sys.platform == "win32" else "SRM")
TEMPLATES = ("srmGP.txt", "srmGEP.txt", "srmAP.txt")
ECF_BANNER = "ECF, version 1.6.1"


def write_parameter_file(template: Path, target: Path) -> None:
    overrides = {
        "input_file": str(ROOT / "srm" / "data_2var.txt"),
        "bestfile": "best.txt",
        "population.size": "50",
        "term.maxgen": "5",
    }
    tree = ET.parse(template)
    for entry in tree.getroot().find("Registry"):
        key = entry.get("key")
        if key in overrides:
            entry.text = overrides[key]
    tree.write(target)


def run(template_name: str) -> None:
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        write_parameter_file(ROOT / "srm" / template_name, folder / "parameters.txt")
        result = subprocess.run(
            [str(SRM), "parameters.txt"],
            cwd=folder,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            sys.exit(f"{template_name}: exit code {result.returncode}\n{result.stdout}\n{result.stderr}")
        if ECF_BANNER not in result.stdout:
            sys.exit(f"{template_name}: '{ECF_BANNER}' not in the output\n{result.stdout}")
        best_file = folder / "best.txt"
        if not best_file.exists() or "<Individual" not in best_file.read_text():
            sys.exit(f"{template_name}: no individual in the best file\n{result.stdout}")
    print(f"{template_name}: ok")


if __name__ == "__main__":
    for name in TEMPLATES:
        run(name)
