# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from pathlib import Path

D = Path(r"C:\Users\caion\calculadora-densidade-calorica-saciedade")
PY = r"C:\Python313\python.exe"
env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONIOENCODING": "utf-8"}

r = subprocess.run([PY, "test_dcs.py"], cwd=D, env=env)
print("test_rc", r.returncode)
if r.returncode != 0:
    sys.exit(r.returncode)

for f in ("dcs_core.py", "dcs_gui.pyw", "test_dcs.py"):
    subprocess.check_call([PY, "-m", "py_compile", f], cwd=D)

if not (D / ".git").exists():
    subprocess.check_call(["git", "init"], cwd=D)
subprocess.check_call(["git", "add", "-A"], cwd=D)
st = subprocess.check_output(["git", "status", "--porcelain"], cwd=D, text=True)
print(st)
if st.strip():
    msg = (
        "fix: testes robustos, botao Calcular, ENTREGA pronto+ajuda.\n\n"
        "Co-Authored-By: Cursor <cursoragent@cursor.com>"
    )
    subprocess.check_call(["git", "commit", "-m", msg], cwd=D)
    print("COMMITTED")
else:
    print("CLEAN")
sys.exit(0)
