# -*- coding: utf-8 -*-
import subprocess

ideas = [
    "calculadora-carga-horaria-semanal-trabalho",
    "planejador-meta-redacao",
    "controle-cafeina-doses-dia",
    "comparador-proposta-estagio",
    "simulador-adicional-noturno",
    "indice-produtividade-pessoal",
    "custo-mensal-coworking",
    "planejador-intervalo-almoço",
    "calculadora-hora-tecnica-pj",
    "checklist-onboarding-emprego",
]
for i in ideas:
    r = subprocess.run(
        [r"C:/Python313/python.exe", "catalogo.py", "--check", i],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=r"C:\Users\caion\caixa-ferramentas",
    )
    line = next(
        (l for l in (r.stdout or "").splitlines() if any(k in l for k in ("Nada", "PROVAVELMENTE", "Talvez"))),
        "?",
    )
    print(i, "=>", line)

for px in ["chs", "pmr", "caf", "cpe", "adn", "ipp", "cwk", "pia", "htp", "cob"]:
    r = subprocess.run(
        [r"C:/Python313/python.exe", "catalogo.py", "--check", "x", "-p", px],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=r"C:\Users\caion\caixa-ferramentas",
    )
    line = next((l for l in (r.stdout or "").splitlines() if "LIVRE" in l or "EM USO" in l), "?")
    print(px, "=>", line)
