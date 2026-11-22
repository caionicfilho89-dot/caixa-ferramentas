"""Simula o carteiro chamando garantir_b() a cada 2 min com uma cadeira que fecha logo depois de aberta.

Nada abre de verdade: abrir_cadeira, o processo, a cota, as tarefas e o correio são falsos. Confere que
a espera cresce (5, 10, 20, 40, 80 min), que ele desiste depois de 5 fechamentos seguidos e que o aviso
sai uma vez por situação (não a cada 2 min).
"""
import os
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formacao  # noqa: E402

relogio = [1_000_000.0]
aberturas, avisos = [], []
vivos = set()

formacao.time.time = lambda: relogio[0]
formacao.ARQ = os.path.join(tempfile.mkdtemp(), "formacao.json")
formacao._salvar(formacao.ARQ, {"formacao": "B", "cadeiras": {"cursor": 0}})


def abrir_falso(chave):
    aberturas.append(relogio[0])
    pid = 1000 + len(aberturas)
    vivos.add(pid)
    return pid


formacao.abrir_cadeira = abrir_falso
formacao._pid_vivo = lambda pid: pid in vivos
formacao._avisar = lambda texto: avisos.append((relogio[0], texto))
sys.modules["fabrica_mail"] = types.SimpleNamespace(caixa=lambda chave: [])
sys.modules["tarefas"] = types.SimpleNamespace(livres_para=lambda chave: ["T1"], ler=lambda: [])
sys.modules["economia"] = types.SimpleNamespace(nivel_do_agente=lambda chave: "normal")

for _ in range(8 * 30):  # 8 horas, uma olhada a cada 2 min
    formacao.garantir_b()
    vivos.clear()  # a cadeira sempre morre logo depois de aberta (cota/erro)
    relogio[0] += 120

minutos = [round((t - aberturas[0]) / 60) for t in aberturas]
print("aberturas (min desde a 1ª):", minutos)
print("avisos:", len(avisos))
for t, a in avisos:
    print(f"  +{round((t - aberturas[0]) / 60):4d} min  {a}")
assert len(aberturas) == 6, aberturas  # 1ª + 5 reaberturas com espera crescente, depois desiste
gaps = [b - a for a, b in zip(minutos, minutos[1:])]
assert gaps[0] < gaps[1] < gaps[2] < gaps[3] < gaps[4], gaps
assert len(avisos) < 20, len(avisos)  # antes: um aviso + uma janela nova a cada 2 min
print("OK: em 8 h abriu 6 vezes (antes seriam ~240) e desistiu")
