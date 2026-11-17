# -*- coding: utf-8 -*-
import subprocess

ideas = [
    "calculadora-adicional-periculosidade",
    "planejador-revisao-provas-orais",
    "controle-hidratacao-escritorio",
    "comparador-carga-horaria-estagio-clt",
    "simulador-aviso-previo",
    "meta-flashcards-diaria",
    "indice-burnout-simplificado",
    "checklist-primeira-semana-estagio",
    "calculadora-dsr-hora-extra",
    "planejador-pausa-olhos-20-20-20",
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

for px in ["per", "rpo", "hid", "cec", "avp", "mfd", "ibs", "cpe", "dsr", "p20"]:
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
