#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
catalogo.py — Catalogo VIVO da Caixa de Ferramentas.

A fonte da verdade e a lista BUILTIN em caixa.pyw. Este script le ela direto do
codigo (via AST, sem abrir o Qt), por isso o catalogo NUNCA desatualiza igual o
BACKLOG fazia. Nao edite CATALOGO.md na mao: rode este script e ele e regerado.

FLUXO PRA QUALQUER AGENTE (antes de inventar ferramenta nova):
  1) python catalogo.py --check "o que voce quer criar"
       -> avisa se ja existe algo parecido (evita repetir).
  2) python catalogo.py --prefixos
       -> lista os prefixos de modulo ja usados; escolha um INEDITO.
  3) crie a ferramenta, registre em BUILTIN (caixa.pyw) + TOOLS (build_suite.py).
  4) python catalogo.py
       -> regenera CATALOGO.md + catalogo.json ja com a sua ferramenta.

Comandos:
  python catalogo.py                         regera CATALOGO.md + catalogo.json
  python catalogo.py --check "ideia"         procura ferramenta parecida
  python catalogo.py --check "ideia" -p xyz  + confere se o prefixo xyz esta livre
  python catalogo.py --prefixos              lista todos os prefixos reservados
  python catalogo.py --stats                 total por categoria
"""
import ast
import datetime
import difflib
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CAIXA = os.path.join(AQUI, "caixa.pyw")
MD_OUT = os.path.join(AQUI, "CATALOGO.md")
JSON_OUT = os.path.join(AQUI, "catalogo.json")


# ---------------------------------------------------------------- leitura (AST)
def _literal(source, nome):
    """Extrai o valor de uma atribuicao de nivel 0 (BUILTIN/CATEGORIAS/...)."""
    arvore = ast.parse(source)
    for no in arvore.body:
        if isinstance(no, ast.Assign):
            for alvo in no.targets:
                if isinstance(alvo, ast.Name) and alvo.id == nome:
                    return ast.literal_eval(no.value)
    raise KeyError(f"'{nome}' nao encontrado em caixa.pyw")


def carregar():
    with open(CAIXA, encoding="utf-8") as f:
        src = f.read()
    builtin = _literal(src, "BUILTIN")       # [(emoji, nome, desc, pasta, script), ...]
    categorias = _literal(src, "CATEGORIAS")  # [(nome_cat, (kw, kw, ...)), ...]
    cat_outras = _literal(src, "CAT_OUTRAS")
    return builtin, categorias, cat_outras


# ------------------------------------------------- classificacao (igual ao app)
def categoria_de(tool, categorias, cat_outras):
    nome = tool[1].lower()
    pasta = tool[3].lower()
    for cat, kws in categorias:
        if any(k in nome or k in pasta for k in kws):
            return cat
    txt = nome + " " + tool[2].lower() + " " + pasta
    for cat, kws in categorias:
        if any(k in txt for k in kws):
            return cat
    return cat_outras


def prefixo_de(script):
    """dlt_gui.pyw -> dlt ; busca_arquivos.pyw -> busca_arquivos (namespace proprio)."""
    stem = re.sub(r"\.pyw?$", "", script.strip())
    if re.search(r"_(gui|core)$", stem):
        return stem.rsplit("_", 1)[0]
    return stem


def montar():
    builtin, categorias, cat_outras = carregar()
    ordem = [c[0] for c in categorias] + [cat_outras]
    itens = []
    for t in builtin:
        emoji, nome, desc, pasta, script = t
        itens.append({
            "emoji": emoji,
            "nome": nome,
            "desc": desc,
            "chave": pasta,
            "script": script,
            "prefixo": prefixo_de(script),
            "categoria": categoria_de(t, categorias, cat_outras),
        })
    return itens, ordem


# ----------------------------------------------------------------- geracao .md
def gerar(itens, ordem):
    hoje = datetime.date.today().isoformat()
    prefixos = sorted({i["prefixo"] for i in itens})
    por_cat = {c: [] for c in ordem}
    for i in itens:
        por_cat.setdefault(i["categoria"], []).append(i)

    L = []
    L.append("# 🧰 Catálogo da Caixa de Ferramentas")
    L.append("")
    L.append(f"> **GERADO AUTOMATICAMENTE por `catalogo.py` — NÃO edite à mão.**  ")
    L.append(f"> Fonte da verdade: a lista `BUILTIN` em `caixa.pyw`. "
             f"Rode `python catalogo.py` pra atualizar.")
    L.append(f"> Última geração: **{hoje}** · Total: "
             f"**{len(itens)} ferramentas** · **{len(prefixos)} prefixos** usados.")
    L.append("")
    L.append("## ⚠️ Antes de criar QUALQUER ferramenta nova (todo agente)")
    L.append("")
    L.append("1. `python catalogo.py --check \"o que vou criar\"` — confere se já existe parecida.")
    L.append("2. `python catalogo.py --prefixos` — pegue um prefixo **inédito**.")
    L.append("3. Crie, registre em `BUILTIN` (caixa.pyw) + `TOOLS` (build_suite.py).")
    L.append("4. `python catalogo.py` — regenera este arquivo já com a sua.")
    L.append("")
    L.append("---")
    L.append("")
    # indice
    L.append("## Índice por categoria")
    L.append("")
    for cat in ordem:
        n = len(por_cat.get(cat, []))
        if n:
            L.append(f"- {cat} — {n}")
    L.append("")
    L.append("---")
    L.append("")
    # tabelas
    for cat in ordem:
        grupo = sorted(por_cat.get(cat, []), key=lambda x: x["nome"].lower())
        if not grupo:
            continue
        L.append(f"## {cat}  ·  {len(grupo)}")
        L.append("")
        L.append("| | Ferramenta | O que faz | chave | prefixo |")
        L.append("|---|---|---|---|---|")
        for i in grupo:
            desc = i["desc"].replace("|", "\\|")
            L.append(f"| {i['emoji']} | **{i['nome']}** | {desc} "
                     f"| `{i['chave']}` | `{i['prefixo']}` |")
        L.append("")
    # prefixos
    L.append("---")
    L.append("")
    L.append(f"## 🔒 Prefixos reservados ({len(prefixos)}) — NÃO repetir")
    L.append("")
    L.append("```text")
    linha = []
    for p in prefixos:
        linha.append(p)
        if len(linha) == 10:
            L.append("  ".join(linha))
            linha = []
    if linha:
        L.append("  ".join(linha))
    L.append("```")
    L.append("")

    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump({"gerado_em": hoje, "total": len(itens),
                   "ferramentas": itens, "prefixos": prefixos},
                  f, ensure_ascii=False, indent=2)
    return len(itens), len(prefixos)


# ------------------------------------------------------------------- checagem
# palavras genericas que quase toda ferramenta tem -> nao servem pra diferenciar
STOP = {"calculadora", "calcular", "gerador", "gerar", "simulador", "simular",
        "conversor", "converter", "analisador", "analisar", "estudio", "editor",
        "visualizador", "inspetor", "laboratorio", "painel", "estudo", "para",
        "com", "sem", "por", "das", "dos", "uma", "seu", "sua", "que", "the"}


def _tokens(s):
    return set(re.findall(r"[a-zá-ú0-9]{3,}", s.lower()))


def _distintivos(s):
    return _tokens(s) - STOP


def checar(consulta, itens, prefixo=None):
    q = consulta.lower().strip()
    qdist = _distintivos(q)
    pontuados = []
    for i in itens:
        alvo = (i["nome"] + " " + i["desc"]).lower()
        # overlap dos termos DISTINTIVOS (sinal principal)
        inter = qdist & _distintivos(alvo)
        overlap = len(inter) / max(1, len(qdist))
        # ratio dos nomes, mas sem as palavras genericas (sinal secundario)
        nome_limpo = " ".join(_tokens(i["nome"]) - STOP)
        q_limpo = " ".join(qdist)
        ratio = difflib.SequenceMatcher(None, q_limpo, nome_limpo).ratio()
        sub = 0.6 if (q in alvo and len(q) > 6) else 0.0
        score = max(overlap, sub, 0.55 * ratio)
        pontuados.append((score, inter, i))
    pontuados.sort(key=lambda x: x[0], reverse=True)

    print(f'\n🔎 Procurando ferramenta parecida com: "{consulta}"\n')
    top = pontuados[0][0]
    if top >= 0.6:
        print("⚠️  PROVAVELMENTE JÁ EXISTE algo parecido — confira antes de criar:\n")
    elif top >= 0.4:
        print("🤔 Talvez exista algo relacionado — dá uma olhada:\n")
    else:
        print("✅ Nada muito parecido. Parece inédita (confirme na lista mesmo assim).\n")

    for score, inter, i in pontuados[:6]:
        if score < 0.2:
            continue
        bar = "█" * int(score * 10)
        com = (" · termos: " + ", ".join(sorted(inter))) if inter else ""
        print(f"  {score*100:3.0f}% {bar:<10} {i['emoji']} {i['nome']} "
              f"[{i['chave']}]{com}")
        print(f"            {i['desc']}")

    if prefixo:
        pset = {i["prefixo"] for i in itens}
        p = re.sub(r"_$", "", prefixo.lower())
        print()
        if p in pset:
            dono = next(i for i in itens if i["prefixo"] == p)
            print(f"🔒 Prefixo '{p}_' JÁ ESTÁ EM USO ({dono['nome']}). Escolha outro.")
        else:
            print(f"🆓 Prefixo '{p}_' está LIVRE. Pode usar.")
    print()


def listar_prefixos(itens):
    prefixos = sorted({i["prefixo"] for i in itens})
    print(f"\n🔒 {len(prefixos)} prefixos reservados (NÃO repetir):\n")
    for n in range(0, len(prefixos), 8):
        print("  " + "  ".join(f"{p}_" for p in prefixos[n:n + 8]))
    print()


def stats(itens, ordem):
    por = {}
    for i in itens:
        por[i["categoria"]] = por.get(i["categoria"], 0) + 1
    print(f"\n📊 {len(itens)} ferramentas no total:\n")
    for cat in ordem:
        if por.get(cat):
            print(f"  {por[cat]:>3}  {cat}")
    print()


# ------------------------------------------------------------------------ main
def main():
    args = sys.argv[1:]
    itens, ordem = montar()

    if args and args[0] in ("--check", "-c"):
        if len(args) < 2:
            print("uso: python catalogo.py --check \"ideia\" [-p prefixo]")
            return
        prefixo = None
        if "-p" in args:
            j = args.index("-p")
            prefixo = args[j + 1] if j + 1 < len(args) else None
        elif "--prefixo" in args:
            j = args.index("--prefixo")
            prefixo = args[j + 1] if j + 1 < len(args) else None
        checar(args[1], itens, prefixo)
        return

    if args and args[0] in ("--prefixos", "-p"):
        listar_prefixos(itens)
        return

    if args and args[0] in ("--stats", "-s"):
        stats(itens, ordem)
        return

    n, p = gerar(itens, ordem)
    print(f"✅ CATALOGO.md e catalogo.json gerados: {n} ferramentas, {p} prefixos.")


if __name__ == "__main__":
    main()
