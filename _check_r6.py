# -*- coding: utf-8 -*-
import subprocess

ideas = [
    "calculadora-imc-meta-semanal",
    "planejador-pausa-cafe",
    "custo-curso-idioma-mensal",
    "simulador-ferias-venda",
    "controle-agua-diaria-copos",
    "comparador-home-office-hibrido",
    "tempo-estudo-pomodoro-custom",
    "calculadora-imposto-sindical",
    "meta-passos-kcal",
    "organizador-tarefas-eisenhower",
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

for px in ["ims", "pcf", "cim", "sfv", "agd", "hoh", "tpc", "isd", "mpk", "eis"]:
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
