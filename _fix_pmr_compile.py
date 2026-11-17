# -*- coding: utf-8 -*-
import pathlib
import re
import subprocess
import sys

d = pathlib.Path(r"C:\Users\caion\planejador-meta-redacao")
for f in sorted(d.iterdir()):
    if not f.suffix in {".py", ".pyw"}:
        continue
    t = f.read_text(encoding="utf-8", errors="replace")
    bad = sorted({hex(ord(c)) for c in t if 0x0300 <= ord(c) <= 0x1CFF})
    print(f.name, "bad_unicode", bad[:8] if bad else "none")
    try:
        compile(t, f.name, "exec")
        print(f.name, "compile OK")
    except Exception as ex:
        print(f.name, "COMPILE FAIL", ex)
        # show around problem
        if hasattr(ex, "lineno") and ex.lineno:
            lines = t.splitlines()
            i = ex.lineno - 1
            for j in range(max(0, i - 2), min(len(lines), i + 3)):
                print(f"{j+1}: {lines[j]!r}")

# also py_compile
r = subprocess.run(
    [sys.executable, "-m", "py_compile", str(d / "pmr_core.py"), str(d / "pmr_gui.pyw"), str(d / "test_pmr.py")],
    capture_output=True,
    text=True,
)
print("py_compile rc", r.returncode, r.stderr)
