"""Cria no quadro as tarefas "🔧 Funcionar lote N" cobrindo TODAS as ferramentas do BUILTIN (FUNCIONAR.md).

Ordem: primeiro as suspeitas de resultado falso (caca_fake.json) e as que o robô pegou com erro
(robo_total.json, se existir); depois todas as outras. Lotes de 8. Não repete pasta que já está num lote.

    python criar_lotes_funcionar.py            # cria
    python criar_lotes_funcionar.py --ver      # só mostra o que criaria
"""
import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TAM = 8
QUEM = "cursor grokbuild grok"


def ferramentas():
    arv = ast.parse(open(os.path.join(HERE, "caixa.pyw"), encoding="utf-8").read())
    for no in ast.walk(arv):
        if isinstance(no, ast.Assign) and any(getattr(t, "id", "") == "BUILTIN" for t in no.targets):
            return [tuple(e.value for e in t.elts) for t in no.value.elts]
    return []


def ler(nome, padrao):
    try:
        return json.load(open(os.path.join(HERE, nome), encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import tarefas
    tools = ferramentas()
    por_pasta = {t[3]: t for t in tools}
    ja = set()
    for t in tarefas.ler():
        if t["titulo"].startswith("🔧 Funcionar lote"):
            ja.update(t.get("pastas") or [])
    suspeitas = {}
    for f in ler("caca_fake.json", []):
        suspeitas[f["pasta"]] = "suspeita de resultado falso: " + "; ".join(f["provas"][:2])
    for r in ler("robo_total.json", []):
        if r.get("erros"):
            suspeitas[r["pasta"]] = "robô achou erro: " + " | ".join(r["erros"][:2])
    ordem = [p for p in suspeitas if p in por_pasta] + sorted(p for p in por_pasta if p not in suspeitas)
    ordem = [p for p in ordem if p not in ja]
    lotes = [ordem[i:i + TAM] for i in range(0, len(ordem), TAM)]
    n0 = 1 + sum(1 for t in tarefas.ler() if t["titulo"].startswith("🔧 Funcionar lote"))
    criadas = []
    for k, lote in enumerate(lotes):
        linhas = []
        for p in lote:
            t = por_pasta[p]
            dica = f" ⚠️ {suspeitas[p][:180]}" if p in suspeitas else ""
            linhas.append(f"- C:/Users/caion/{p} ({t[4]}) — {t[1]}{dica}")
        detalhe = ("Siga FUNCIONAR.md À RISCA (C:/Users/caion/caixa-ferramentas/FUNCIONAR.md): em CADA ferramenta abaixo "
                   "faça a função REAL funcionar (nada de resultado inventado; recurso que falta no PC = mensagem "
                   "honesta; exemplo só por botão 'Exemplo'), todo botão fazendo o que diz, e deixe verde: pyflakes "
                   "(0 undefined name), robo_botoes.py (erros: []), testes. Ao concluir, cite TODAS as pastas.\n"
                   + "\n".join(linhas))
        titulo = f"🔧 Funcionar lote {n0 + k}: " + ", ".join(lote[:3]) + ("…" if len(lote) > 3 else "")
        if "--ver" in sys.argv:
            print(titulo)
            continue
        tid = tarefas.nova(titulo, detalhe, QUEM)
        ts = tarefas.ler()
        for t in ts:
            if t["id"] == tid:
                t["pastas"] = lote
        tarefas.salvar(ts)
        criadas.append(tid)
    print(f"{len(lotes)} lotes ({len(ordem)} ferramentas, {len([p for p in ordem if p in suspeitas])} suspeitas "
          f"primeiro){': ' + criadas[0] + '…' + criadas[-1] if criadas else ''}")


if __name__ == "__main__":
    main()
