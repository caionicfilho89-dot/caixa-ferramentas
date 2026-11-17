# -*- coding: utf-8 -*-
import subprocess
from pathlib import Path

for pasta in ("checklist-entrevista-emprego", "planejador-leituras-semanais"):
    d = Path(r"C:\Users\caion") / pasta
    subprocess.check_call(["git", "add", "ENTREGA.json"], cwd=d)
    st = subprocess.check_output(["git", "status", "--porcelain"], cwd=d, text=True)
    print(pasta, st.strip() or "clean")
    if st.strip():
        subprocess.check_call(
            [
                "git",
                "commit",
                "-m",
                "fix: ENTREGA.json com objeto ajuda completo.\n\nCo-Authored-By: Cursor <cursoragent@cursor.com>",
            ],
            cwd=d,
        )
        print("COMMITTED", pasta)
