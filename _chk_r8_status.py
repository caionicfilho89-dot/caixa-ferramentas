# -*- coding: utf-8 -*-
import json
from pathlib import Path

NEED = ("sinopse", "para_que", "como_usar", "exemplo")
pastas = [
    "controle-postura-timer",
    "simulador-hora-extra-50-100",
    "meta-vocabulario-idioma",
    "indice-satisfacao-trabalho",
    "checklist-saida-emprego",
    "calculadora-adicional-insalubridade",
]
for pasta in pastas:
    p = Path(r"C:\Users\caion") / pasta / "ENTREGA.json"
    if not p.exists():
        print("MISSING", pasta)
        continue
    e = json.loads(p.read_text(encoding="utf-8-sig"))
    a = e.get("ajuda")
    ok = isinstance(a, dict) and all(a.get(k) for k in NEED)
    n = len(a["como_usar"]) if ok and isinstance(a.get("como_usar"), list) else -1
    campos = all(e.get(k) for k in ("pasta", "nome", "descricao", "script", "prefixo", "emoji"))
    print(
        pasta,
        "px",
        e.get("prefixo"),
        "ajuda",
        "OK" if ok and 3 <= n <= 6 else f"BAD n={n}",
        "campos",
        "OK" if campos else "BAD",
        e.get("status"),
    )
