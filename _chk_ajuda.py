# -*- coding: utf-8 -*-
import json
from pathlib import Path

NEED = ("sinopse", "para_que", "como_usar", "exemplo")
pastas = [
    "organizador-tarefas-eisenhower",
    "calculadora-beneficio-vr-va",
    "indice-estresse-percebido",
    "controle-agua-diaria-copos",
    "calculadora-contribuicao-sindical",
    "planejador-revisao-flash-rapida",
]
for pasta in pastas:
    p = Path(r"C:\Users\caion") / pasta / "ENTREGA.json"
    if not p.exists():
        print("MISSING", pasta)
        continue
    e = json.loads(p.read_text(encoding="utf-8-sig"))
    a = e.get("ajuda")
    ok = isinstance(a, dict) and all(a.get(k) for k in NEED)
    cu = a.get("como_usar") if isinstance(a, dict) else None
    n = len(cu) if isinstance(cu, list) else -1
    campos = all(e.get(k) for k in ("pasta", "nome", "descricao", "script", "prefixo", "emoji"))
    print(pasta, "ajuda", "OK" if ok and 3 <= n <= 6 else f"BAD n={n}", "campos", "OK" if campos else "BAD", "status", e.get("status"))
