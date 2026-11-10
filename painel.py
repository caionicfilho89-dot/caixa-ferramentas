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
    try:  # modo economia (economia.py, atualizado pelo carteiro a cada 3 min)
        import economia
        linhas = economia.resumo()
        if linhas:
            print("💸 MODO ECONOMIA (vale pra você se for da conta indicada; regras no RUMO.md):")
            for l in linhas:
                print("   " + l)
            print("-" * 70)
    except Exception:  # noqa: BLE001
        pass
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
    ap.add_argument("--pegar", action="store_true", help="pega a próxima tarefa livre do quadro (tarefas.json)")
    ap.add_argument("--concluir", nargs="+", metavar=("ID", "RESULTADO"), help="marca tarefa do quadro como feita")
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
        # sem nada pra fazer? `python painel.py <eu>` já dá a próxima tarefa do quadro (ninguém fica parado)
        so_olhar = not any([a.fazendo, a.feito, a.bloqueado, a.pedir, a.resolvido, a.concluir, a.proximo, a.arquivos])
        fz = (d.get("fazendo") or "").lower()
        if so_olhar and a.agente != "claude" and (not fz or any(k in fz for k in ("aguard", "esperan", "parad", "idle", "nada"))):
            a.pegar = True
        if a.pegar or a.concluir:
            import tarefas
            if a.concluir:
                t = tarefas.concluir(a.agente, a.concluir[0], " ".join(a.concluir[1:]))
                if t:
                    d.setdefault("feitos", []).append(f"{time.strftime(FORMATO)} {t['id']} {t['titulo']}: {t['resultado']}")
                    d["feitos"] = d["feitos"][-15:]
                    d["fazendo"], d["arquivos"] = "", []
            freio = ""
            try:
                import economia
                if economia.nivel_do_agente(a.agente) == "critico":
                    freio = "sua conta está em 🔴 CRÍTICO (modo economia)"
                pausados = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agentes_pausados.json")
                if os.path.exists(pausados):
                    with open(pausados, encoding="utf-8") as f:
                        if a.agente in json.load(f):
                            freio = "você está em RESERVA (agentes_pausados.json)"
            except Exception:  # noqa: BLE001
                pass
            if a.pegar and freio:
                print(f"\n⛔ Sem tarefa nova: {freio}. Termine o passo atual, anuncie --feito e PARE até liberar.\n")
                a.pegar = False
            if a.pegar:
                t = tarefas.pegar(a.agente)
                if t:
                    d["fazendo"] = f"{t['id']}: {t['titulo']}"
                    print(f"\n📋 SUA TAREFA: {t['id']} — {t['titulo']}\n   {t['detalhe']}\n"
                          f"   Ao terminar: python painel.py {a.agente} --concluir {t['id']} \"o que ficou pronto\"\n")
                else:
                    print("\n📋 Quadro sem tarefa livre pra você. Proponha 3 no CRITICA.md (seção Propostas) "
                          "ou --pedir antigravity.\n")
        salvar(a.agente, d)
    mostrar(a.agente)


if __name__ == "__main__":
    main()
