# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\caion")
TOOLS = [
    ("controle-medicacao-horarios", "mdh", "test_mdh.py"),
    ("carga-horaria-creditos", "chh", "test_chh.py"),
    ("comparador-salario-beneficios", "csb", "test_csb.py"),
    ("indice-qualidade-sono-psqi", "psq", "test_psq.py"),
    ("checklist-entrevista-emprego", "cie", "test_cie.py"),
    ("planejador-leituras-semanais", "pls", "test_pls.py"),
]
PY = r"C:\Python313\python.exe"
NEED = ("sinopse", "para_que", "como_usar", "exemplo")


def main() -> int:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "QT_QPA_PLATFORM": "offscreen"}
    failed = 0
    for pasta, px, test in TOOLS:
        d = ROOT / pasta
        print(f"=== {pasta} ===")
        e = json.loads((d / "ENTREGA.json").read_text(encoding="utf-8-sig"))
        a = e.get("ajuda")
        if not isinstance(a, dict) or any(not a.get(k) for k in NEED):
            print("BAD_AJUDA", type(a).__name__, list(a) if isinstance(a, dict) else a)
            failed += 1
            continue
        if not isinstance(a["como_usar"], list) or not (3 <= len(a["como_usar"]) <= 6):
            print("BAD_COMO_USAR", a.get("como_usar"))
            failed += 1
            continue
        print("ajuda OK")
        for name in (f"{px}_core.py", f"{px}_gui.pyw", test):
            py_compile.compile(str(d / name), doraise=True)
        r = subprocess.run([PY, test], cwd=str(d), env=env, capture_output=True, text=True)
        tail = ((r.stdout or "") + (r.stderr or ""))[-300:]
        print(tail)
        if r.returncode != 0:
            print("FAIL", pasta)
            failed += 1
        else:
            print("OK", pasta)
    print(f"FAILED={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
