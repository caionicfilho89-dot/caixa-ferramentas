# -*- coding: utf-8 -*-
"""Roda testes das 6 ferramentas Lane B R3."""
from __future__ import annotations

import os
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\caion")
TOOLS = [
    ("planejador-revisao-provas", "rvp", "test_rvp.py"),
    ("custo-home-office", "hof", "test_hof.py"),
    ("controle-pressao-arterial", "pas", "test_pas.py"),
    ("simulador-plr", "plr", "test_plr.py"),
    ("indice-carga-treino", "ict", "test_ict.py"),
    ("planejador-sessao-foco", "fcs", "test_fcs.py"),
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
        print("py_compile OK")
        r = subprocess.run([PY, test], cwd=str(d), env=env, capture_output=True, text=True)
        print(r.stdout)
        if r.stderr:
            print(r.stderr)
        if r.returncode != 0:
            failed += 1
            print("FAIL", pasta, r.returncode)
        else:
            print("OK", pasta)
    print(f"FAILED={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
