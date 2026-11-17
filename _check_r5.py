# -*- coding: utf-8 -*-
import subprocess

ideas = [
    "controle-medicacao-horarios",
    "carga-horaria-creditos",
    "calculadora-burnout-carga",
    "comparador-salario-beneficios",
    "tempo-ultradian-foco",
    "indice-qualidade-sono-psqi",
    "custo-mensalidade-pos",
    "simulador-banco-horas",
    "checklist-entrevista-emprego",
    "planejador-leituras-semanais",
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

for px in ["mdh", "chc", "brn", "csb", "ult", "psq", "cmp", "sbh", "cie", "pls"]:
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
