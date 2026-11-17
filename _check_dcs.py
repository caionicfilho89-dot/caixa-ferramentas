# -*- coding: utf-8 -*-
import json
import os
import pathlib
import subprocess
import sys

PY = r"C:\Python313\python.exe"
D = pathlib.Path(r"C:\Users\caion\calculadora-densidade-calorica-saciedade")

print("=== unicode ===")
for f in sorted(D.iterdir()):
    if f.suffix not in {".py", ".pyw", ".json", ".md", ".txt"}:
        continue
    t = f.read_text(encoding="utf-8", errors="replace")
    bad = [(i, hex(ord(c)), repr(c)) for i, c in enumerate(t) if 0x0300 <= ord(c) <= 0x1CFF]
    print(f.name, "bad", len(bad), bad[:6])

print("=== tests ===")
env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONIOENCODING": "utf-8"}
r = subprocess.run([PY, "test_dcs.py"], cwd=str(D), capture_output=True, text=True, timeout=240, env=env)
print("rc", r.returncode)
print("stdout", (r.stdout or "")[-400:])
print("stderr", (r.stderr or "")[-400:])

print("=== entrega ===")
e = json.loads((D / "ENTREGA.json").read_text(encoding="utf-8-sig"))
print("status", e.get("status"))
a = e.get("ajuda")
print("ajuda keys", list(a) if isinstance(a, dict) else type(a))
