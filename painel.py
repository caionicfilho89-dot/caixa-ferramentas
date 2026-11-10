"""Painel dos agentes: cada um vê o que os outros estão fazendo, sem ninguém editar o arquivo do outro.

Cada agente só escreve no PRÓPRIO arquivo `painel/<agente>.json` (por este script; não edite o JSON à mão).

Ver todo mundo (rode ANTES de começar qualquer tarefa e ao terminar):
    python painel.py

Atualizar o seu (exemplos):
    python painel.py cursor --fazendo "F1: tela Hoje, layout dos cartões" --arquivos caixa_home.py
    python painel.py cursor --feito "F1: tela Hoje com stub, 12 testes OK" --proximo "F2: barra de busca"
    python painel.py antigravity --pedir cursor "preciso do sinal on_resposta_clicada(chave)"
    python painel.py cursor --resolvido antigravity      # apaga os pedidos que o antigravity fez a você
    python painel.py grok --bloqueado "não acho o .exe novo"   # e PEGA OUTRA TAREFA, não fica parado
"""
import argparse
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(AQUI, "painel")
AGENTES = ["claude", "cursor", "antigravity", "grokbuild", "grok"]
PARADO_MIN = 20   # sem atualizar há mais que isso = provavelmente parado
FORMATO = "%Y-%m-%d %H:%M"


def caminho(ag):
    return os.path.join(PASTA, f"{ag}.json")


def carregar(ag):
    try:
        with open(caminho(ag), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"agente": ag, "fazendo": "", "arquivos": [], "proximo": "", "bloqueado": "",
                "feitos": [], "pedidos": [], "atualizado": ""}


def salvar(ag, d):
    os.makedirs(PASTA, exist_ok=True)
    d["atualizado"] = time.strftime(FORMATO)
    tmp = caminho(ag) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, caminho(ag))


def minutos_desde(txt):
    try:
        return (time.time() - time.mktime(time.strptime(txt, FORMATO))) / 60
    except (ValueError, TypeError):
        return None


def mostrar(eu=None):
    print("=" * 70)
    print("PAINEL DOS AGENTES  (regras: RUMO.md)")
    print("=" * 70)
    for ag in AGENTES:
        d = carregar(ag)
        m = minutos_desde(d.get("atualizado"))
        if m is None:
            sinal = "⚪ nunca atualizou"
        elif m > PARADO_MIN:
            sinal = f"🟡 sem notícia há {int(m)} min"
        else:
            sinal = f"🟢 há {int(m)} min"
        print(f"\n▶ {ag.upper()}  {sinal}")
        print(f"   fazendo : {d.get('fazendo') or '—'}")
        if d.get("arquivos"):
            print(f"   arquivos: {', '.join(d['arquivos'])}   ← NÃO mexa nesses")
        print(f"   próximo : {d.get('proximo') or '—'}")
        if d.get("bloqueado"):
            print(f"   ⛔ travou: {d['bloqueado']}")
        for f in d.get("feitos", [])[-3:]:
            print(f"   ✔ {f}")
    # pedidos endereçados a quem está olhando (ou a todos, se não disse quem é)
    print("\n" + "-" * 70)
    achou = False
    for ag in AGENTES:
        for p in carregar(ag).get("pedidos", []):
            if eu is None or p.get("para") == eu:
                print(f"📨 {ag} → {p.get('para')}: {p.get('texto')}  ({p.get('quando')})")
                achou = True
    if not achou:
        print("📨 nenhum pedido pendente" + (f" para {eu}" if eu else ""))
    print("-" * 70)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Painel dos agentes da Caixa")
    ap.add_argument("agente", nargs="?", choices=AGENTES, help="quem é você (para atualizar o seu)")
    ap.add_argument("--fazendo")
    ap.add_argument("--arquivos", nargs="*")
    ap.add_argument("--proximo")
    ap.add_argument("--feito")
    ap.add_argument("--bloqueado")
    ap.add_argument("--pedir", nargs=2, metavar=("PARA", "TEXTO"))
    ap.add_argument("--resolvido", metavar="DE", help="apaga os pedidos que DE fez para você")
    a = ap.parse_args()

    if a.agente:
        d = carregar(a.agente)
        if a.fazendo is not None:
            d["fazendo"] = a.fazendo
            d["bloqueado"] = ""
        if a.arquivos is not None:
            d["arquivos"] = a.arquivos
        if a.proximo is not None:
            d["proximo"] = a.proximo
        if a.bloqueado is not None:
            d["bloqueado"] = a.bloqueado
        if a.feito:
            d.setdefault("feitos", []).append(f"{time.strftime(FORMATO)} {a.feito}")
            d["feitos"] = d["feitos"][-15:]
            if a.fazendo is None:
                d["fazendo"], d["arquivos"] = "", []
        if a.pedir:
            para, texto = a.pedir
            if para not in AGENTES:
                sys.exit(f"agente desconhecido: {para}")
            d.setdefault("pedidos", []).append({"para": para, "texto": texto, "quando": time.strftime(FORMATO)})
        if a.resolvido:
            outro = carregar(a.resolvido)
            outro["pedidos"] = [p for p in outro.get("pedidos", []) if p.get("para") != a.agente]
            salvar(a.resolvido, outro)
        salvar(a.agente, d)
    mostrar(a.agente)


if __name__ == "__main__":
    main()
