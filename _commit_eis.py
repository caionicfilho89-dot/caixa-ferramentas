# -*- coding: utf-8 -*-
import subprocess
from pathlib import Path

d = Path(r"C:\Users\caion\organizador-tarefas-eisenhower")
subprocess.check_call(["git", "add", "ENTREGA.json"], cwd=d)
st = subprocess.check_output(["git", "status", "--porcelain"], cwd=d, text=True)
print(st)
if st.strip():
    subprocess.check_call(
        [
            "git",
            "commit",
            "-m",
            "fix: como_usar com no maximo 6 passos.\n\nCo-Authored-By: Cursor <cursoragent@cursor.com>",
        ],
        cwd=d,
    )
    print("COMMITTED")
