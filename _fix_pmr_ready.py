# -*- coding: utf-8 -*-
import json
import subprocess
from pathlib import Path

d = Path(r"C:\Users\caion\planejador-meta-redacao")
# ensure compiles
for name in ("pmr_core.py", "pmr_gui.pyw", "test_pmr.py"):
    t = (d / name).read_text(encoding="utf-8")
    compile(t, name, "exec")
    print("compile", name, "OK")

p = d / "ENTREGA.json"
e = json.loads(p.read_text(encoding="utf-8-sig"))
e["status"] = "pronto"
e.pop("integrado_por", None)
# ensure required fields
assert e.get("nome") and e.get("descricao") and e.get("ajuda", {}).get("sinopse")
p.write_text(json.dumps(e, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("ENTREGA status=pronto")

subprocess.check_call(["git", "add", "-A"], cwd=d)
st = subprocess.check_output(["git", "status", "--porcelain"], cwd=d, text=True)
print(st or "clean")
if st.strip():
    subprocess.check_call(
        [
            "git",
            "commit",
            "-m",
            "fix: reconfirma compilacao e ENTREGA pronto.\n\nCo-Authored-By: Cursor <cursoragent@cursor.com>",
        ],
        cwd=d,
    )
    print("COMMITTED")
