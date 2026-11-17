# -*- coding: utf-8 -*-
import subprocess

ideas = [
    "controle-agua-diaria-copos",
    "organizador-tarefas-eisenhower",
    "simulador-venda-ferias",
    "calculadora-contribuicao-sindical",
    "planejador-revisao-flash-rapida",
    "custo-deslocamento-semana",
    "indice-estresse-percebido",
    "comparador-carga-horaria-trabalho",
    "meta-redacao-enem-semanal",
    "calculadora-beneficio-vr-va",
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

for px in ["agd", "eis", "sfv", "isd", "frp", "cds", "iep", "cht", "mre", "vva"]:
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
