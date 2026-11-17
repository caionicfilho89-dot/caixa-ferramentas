# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\caion")
TOOLS = [
    ("controle-agua-diaria-copos", "agd", "test_agd.py"),
    ("organizador-tarefas-eisenhower", "eis", "test_eis.py"),
    ("calculadora-contribuicao-sindical", "isd", "test_isd.py"),
    ("planejador-revisao-flash-rapida", "frp", "test_frp.py"),
    ("indice-estresse-percebido", "iep", "test_iep.py"),
    ("calculadora-beneficio-vr-va", "vva", "test_vva.py"),
]
PY = r"C:\Python313\python.exe"


def main() -> int:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "QT_QPA_PLATFORM": "offscreen"}
    failed = 0
    for pasta, px, test in TOOLS:
        d = ROOT / pasta
        print(f"=== {pasta} ===")
        for name in (f"{px}_core.py", f"{px}_gui.pyw", test):
            py_compile.compile(str(d / name), doraise=True)
        r = subprocess.run([PY, test], cwd=str(d), env=env, capture_output=True, text=True)
        print(((r.stdout or "") + (r.stderr or ""))[-250:])
        if r.returncode != 0:
            print("FAIL", pasta)
            failed += 1
        else:
            print("OK", pasta)
    print(f"FAILED={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
