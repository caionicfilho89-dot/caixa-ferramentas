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
    ("controle-postura-timer", "ptr", "test_ptr.py"),
    ("simulador-hora-extra-50-100", "hex", "test_hex.py"),
    ("meta-vocabulario-idioma", "mvi", "test_mvi.py"),
    ("indice-satisfacao-trabalho", "ist", "test_ist.py"),
    ("checklist-saida-emprego", "cse", "test_cse.py"),
    ("calculadora-adicional-insalubridade", "ins", "test_ins.py"),
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
            print("BAD_AJUDA")
            failed += 1
            continue
        cu = a["como_usar"]
        if not isinstance(cu, list) or not (3 <= len(cu) <= 6):
            print("BAD_COMO_USAR", len(cu) if isinstance(cu, list) else type(cu))
            failed += 1
            continue
        if not all(e.get(k) for k in ("pasta", "nome", "descricao", "script", "prefixo", "emoji")):
            print("BAD_CAMPOS")
            failed += 1
            continue
        print("ajuda OK", e.get("prefixo"))
        for name in (f"{px}_core.py", f"{px}_gui.pyw", test):
            try:
                compile((d / name).read_text(encoding="utf-8"), name, "exec")
                py_compile.compile(str(d / name), doraise=True)
            except Exception as ex:
                print("COMPILE_FAIL", name, ex)
                failed += 1
                break
        else:
            r = subprocess.run([PY, test], cwd=str(d), env=env, capture_output=True, text=True)
            print(((r.stdout or "") + (r.stderr or ""))[-220:])
            if r.returncode != 0:
                print("FAIL", pasta)
                failed += 1
            else:
                print("OK", pasta)
    print(f"FAILED={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
