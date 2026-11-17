# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\caion")
TOOLS = [
    ("comparador-salario-cidade", "scd", "test_scd.py"),
    ("indice-massa-muscular", "imm", "test_imm.py"),
    ("calculadora-ir-simplificado", "irs", "test_irs.py"),
    ("custo-consulta-especialista", "ces", "test_ces.py"),
    ("simulador-dissidio", "dsi", "test_dsi.py"),
    ("roi-curso-certificacao", "roi", "test_roi.py"),
]
PY = r"C:\Python313\python.exe"


def main() -> int:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["QT_QPA_PLATFORM"] = "offscreen"
    failed = 0
    for pasta, px, test in TOOLS:
        d = ROOT / pasta
        print(f"=== {pasta} ===")
        for name in (f"{px}_core.py", f"{px}_gui.pyw", test):
            py_compile.compile(str(d / name), doraise=True)
        r = subprocess.run([PY, test], cwd=str(d), env=env, capture_output=True, text=True)
        print((r.stdout or "")[-500:])
        if r.stderr:
            print((r.stderr or "")[-300:])
        if r.returncode != 0:
            failed += 1
            print("FAIL", pasta)
        else:
            print("OK", pasta)
    print(f"FAILED={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
