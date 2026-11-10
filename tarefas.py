"""Quadro de tarefas compartilhado — ninguém fica parado.

tarefas.json = lista de tarefas com quem PODE fazer. Um agente parado roda:
    python painel.py <eu> --pegar          → pega a próxima tarefa livre que combina com ele (fica marcada como dele)
    python painel.py <eu> --concluir T07 "o que ficou pronto"
    python tarefas.py                      → mostra o quadro
    python tarefas.py --nova "titulo" "detalhe" cursor,grokbuild   → acrescenta tarefa
O carteiro cutuca quem está parado há 10+ min; quando sobram < 5 livres, pede propostas ao Antigravity.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(HERE, "tarefas.json")
FMT = "%Y-%m-%d %H:%M"


def ler():
    try:
        with open(ARQ, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def salvar(ts):
    tmp = ARQ + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ts, f, ensure_ascii=False, indent=1)
    os.replace(tmp, ARQ)


def nova(titulo, detalhe, quem):
    ts = ler()
    n = 1 + max([int(t["id"][1:]) for t in ts] or [0])
    ts.append({"id": f"T{n:02d}", "titulo": titulo, "detalhe": detalhe, "quem": quem,
               "status": "livre", "por": "", "quando": time.strftime(FMT), "resultado": ""})
    salvar(ts)
    return f"T{n:02d}"


def pegar(agente):
    """Já tem uma em andamento? devolve ela. Senão marca a próxima livre que combina."""
    ts = ler()
    for t in ts:
        if t["status"] == "pegou" and t["por"] == agente:
            return t
    for t in ts:
        if t["status"] == "livre" and (agente in t["quem"] or "todos" in t["quem"]):
            t.update(status="pegou", por=agente, quando=time.strftime(FMT))
            salvar(ts)
            return t
    return None


def concluir(agente, tid, resultado=""):
    ts = ler()
    for t in ts:
        if t["id"] == tid:
            t.update(status="feito", por=agente, quando=time.strftime(FMT), resultado=resultado[:300])
            salvar(ts)
            return t
    return None


def livres_para(agente):
    return [t for t in ler() if t["status"] == "livre" and (agente in t["quem"] or "todos" in t["quem"])]


def mostrar():
    ts = ler()
    for st, ic in (("pegou", "🔨"), ("livre", "📋"), ("feito", "✅")):
        grupo = [t for t in ts if t["status"] == st]
        if st == "feito":
            grupo = grupo[-5:]
        for t in grupo:
            dono = f" ({t['por']})" if t["por"] else f" [pode: {', '.join(t['quem'])}]"
            print(f"{ic} {t['id']} {t['titulo']}{dono}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    a = sys.argv[1:]
    if a[:1] == ["--nova"] and len(a) >= 4:
        print("criada", nova(a[1], a[2], a[3].split(",")))
    mostrar()


if __name__ == "__main__":
    main()
