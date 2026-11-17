# -*- coding: utf-8 -*-
import subprocess

ideas = [
    "calculadora-adicional-insalubridade",
    "planejador-semana-estudo-enem",
    "controle-postura-timer",
    "comparador-plano-odontologico-simples",
    "simulador-hora-extra-50-100",
    "meta-vocabulario-idioma",
    "custo-mensal-transporte-trabalho",
    "indice-satisfacao-trabalho",
    "checklist-saida-emprego",
    "calculadora-quebra-caixa",
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

for px in ["ins", "pse", "cpt", "ods", "hex", "mvi", "ctt", "ist", "cse", "qcx"]:
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
