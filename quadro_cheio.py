"""Quadro sempre cheio: ninguém fica parado por falta de tarefa (pedido do Caio, 11/11).

Prática de quem roda vários agentes juntos: o líder quebra o trabalho em tarefas pequenas ANTES de alguém
ficar parado. O carteiro chama encher() a cada 10 min; mantém >= 3 tarefas livres por agente ativo com:
  - 🔥 Tendência extra: ideias do TENDENCIAS.md sem parecida na Caixa (no máx. 2 por dia);
  - 🧪 QA: lotes de 5 ferramentas do catálogo pra testar DE VERDADE e consertar (o portão roda os testes).
Teste à mão: python quadro_cheio.py
"""
import json
import os
import random
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.join(HERE, "qa_testadas.json")


def _json(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _log(t):
    try:
        import carteiro
        carteiro.log(t)
    except Exception:  # noqa: BLE001
        print(t)


def _ativos():
    pausados = _json(os.path.join(HERE, "agentes_pausados.json"), {})
    try:
        import economia
        nivel = economia.nivel_do_agente
    except Exception:  # noqa: BLE001
        def nivel(_a):
            return "normal"
    return [ag for ag in ("cursor", "antigravity", "grok", "grokbuild") if ag not in pausados and nivel(ag) != "critico"]


def _tendencias_extras(texto_quadro):
    """Ideias do TENDENCIAS.md sem parecida na Caixa (última coluna '—') que ainda não viraram tarefa."""
    try:
        txt = open(os.path.join(HERE, "TENDENCIAS.md"), encoding="utf-8").read()
    except OSError:
        return []
    hist = _json(os.path.join(HERE, "tendencias_historico.json"), {})
    feitas = set(hist.get("feitas", [])) | {t["url"] for t in hist.get("tarefas", [])}
    saida = []
    for linha in txt.splitlines():
        m = re.match(r"\| \d+ \| \[(.+?)\]\((\S+?)\)", linha)
        if not m:
            continue
        titulo, url = m.group(1), m.group(2)
        if url in feitas or url in texto_quadro or linha.rstrip().rstrip("|").rstrip().split("|")[-1].strip() != "—":
            continue
        saida.append((titulo, url))
    return saida


def _arquivadas():
    d = _json(os.path.join(HERE, "arquivo_chaves.json"), {})
    if isinstance(d, dict):
        v = d.get("chaves", d.get("arquivadas", []))
        return set(v if isinstance(v, list) else d.keys())
    return set(d) if isinstance(d, list) else set()


def soltar_presas(horas=2):
    """Tarefa "pegou" há mais de N horas com o dono sem dar notícia no painel há 1 h → volta a ficar livre."""
    import tarefas
    ts = tarefas.ler()
    agora = time.time()
    soltas = []
    for t in ts:
        if t["status"] != "pegou":
            continue
        try:
            desde = time.mktime(time.strptime(t["quando"], "%Y-%m-%d %H:%M"))
            p = _json(os.path.join(HERE, "painel", f"{t['por']}.json"), {})
            noticia = time.mktime(time.strptime(p.get("atualizado", "2000-01-01 00:00"), "%Y-%m-%d %H:%M"))
        except (ValueError, OverflowError):
            continue
        if agora - desde > horas * 3600 and agora - noticia > 3600:
            soltas.append(f"{t['id']}({t['por']})")
            t.update(status="livre", por="", quando=time.strftime("%Y-%m-%d %H:%M"))
    if soltas:
        tarefas.salvar(ts)
        _log(f"quadro: soltei tarefa(s) presa(s) com dono sumido: {', '.join(soltas)}")
    return soltas


def encher(minimo_por_agente=2, maximo_por_vez=4):  # 12/11: as 3 contas zeraram numa madrugada — ritmo que a cota aguenta
    import tarefas
    soltar_presas()
    ts = tarefas.ler()
    ativos = _ativos()
    livres = sum(1 for t in ts if t["status"] == "livre")
    falta = min(maximo_por_vez, minimo_por_agente * len(ativos) - livres)
    if falta <= 0:
        return []
    criadas = []
    try:  # 1º o Gemini (carteiro inteligente) planeja tarefas ÚTEIS; os lotes de QA abaixo são plano B
        import carteiro_ia
        criadas += carteiro_ia.planejar(quantas=min(4, falta))
    except Exception as e:  # noqa: BLE001
        _log(f"planejador Gemini: {e}")
    hoje_iso, hoje = time.strftime("%Y-%m-%d"), time.strftime("%d/%m")
    texto_quadro = " ".join(t["titulo"] + " " + t.get("detalhe", "") for t in ts)
    extras_hoje = sum(1 for t in ts if t["titulo"].startswith("🔥 Tendência extra") and t["quando"].startswith(hoje_iso))
    quem_tend = [a for a in ("grokbuild", "antigravity", "cursor") if a in ativos] or ativos
    for titulo, url in _tendencias_extras(texto_quadro)[:max(0, 2 - extras_hoje)]:
        if len(criadas) >= falta:
            break
        criadas.append(tarefas.nova(
            f"🔥 Tendência extra {hoje}: {titulo[:70]}",
            f"Ideia em alta ({url}). Mesmo método do TENDENCIA_DO_DIA.md: catalogo.py --check; versão nossa do zero, "
            "offline, PyQt6, pt-BR, com teste; registrar na Caixa (BUILTIN + TOOLS) + tendencias_caixa.json; "
            f"python tendencias.py --feita {url}. Não cabe (só nuvem/Mac/ataque)? --feita e conclua dizendo por quê.",
            quem_tend))
    # RUMO NOVO (12/11): nada de lote de QA aleatório do catálogo — a fábrica trabalha na VITRINE (vitrine.json):
    # cada tarefa ⭐ Paridade deixa UMA ferramenta tão boa quanto o programa famoso que ela substitui.
    vit = _json(os.path.join(HERE, "vitrine.json"), {}).get("vitrine", [])
    prog = _json(os.path.join(HERE, "vitrine_progresso.json"), {"proxima": 0})
    abertas = " ".join(t["titulo"] for t in ts if t["status"] != "feito")
    tentativas = 0
    while vit and len(criadas) < falta and tentativas < len(vit):
        v = vit[prog["proxima"] % len(vit)]
        prog["proxima"] += 1
        tentativas += 1
        if f"[{v['chave']}]" in abertas:
            continue  # essa já tem tarefa aberta
        if v.get("construir"):  # aparece nas listas (Ninite/Showmetech) e a Caixa ainda não tem: CONSTRUIR
            criadas.append(tarefas.nova(
                f"🆕 Construir [{v['chave']}]: substituir {v['substitui']}",
                f"Pesquisa (vitrine.json, {v.get('evidencia', '')}): as pessoas instalam {v['substitui']} e a Caixa não tem. "
                f"Crie C:/Users/caion/{v['chave']} do zero (código próprio, offline, PyQt6, pt-BR, tema escuro, prefixo livre "
                f"via catalogo.py --prefixos), com: {'; '.join(v['essenciais'])}. Teste test_*.py; registre em BUILTIN/TOOLS; "
                "no --concluir: o que tem, como testou.",
                ativos))
            continue
        criadas.append(tarefas.nova(
            f"⭐ Paridade [{v['chave']}]: tão boa quanto {v['substitui']}",
            f"Ferramenta da VITRINE (RUMO NOVO). Pasta C:/Users/caion/{v['chave']}. Ela substitui {v['substitui']}: "
            f"tem que ter {'; '.join(v['essenciais'])}. 1) Abra a ferramenta e confira cada item (o que já tem, o que "
            "falta, o que está ruim). 2) Implemente o que FALTA mais importante (1–2 itens por tarefa), no código-fonte "
            "da pasta, com teste novo em test_*.py. 3) No --concluir diga item por item: tinha / fiz agora / falta, e "
            "como testou. Visual em pt-BR, tema escuro, sem travar.",
            ativos))
    with open(os.path.join(HERE, "vitrine_progresso.json"), "w", encoding="utf-8") as f:
        json.dump(prog, f)
    qa = _json(QA, [])
    cat = []  # lotes de QA aleatórios desligados pelo RUMO NOVO
    fora = set(qa) | _arquivadas()
    pool = [f["chave"] for f in cat if f["chave"] not in fora and os.path.isdir(os.path.join(os.path.dirname(HERE), f["chave"]))]
    random.shuffle(pool)
    lotes_qa = 0
    while len(criadas) < falta and len(pool) >= 5 and lotes_qa < 1:  # no máx. 1 lote de teste por rodada
        lotes_qa += 1
        lote, pool = pool[:5], pool[5:]
        criadas.append(tarefas.nova(
            f"🧪 QA lote {len(qa) // 5 + 1}: testar 5 ferramentas",
            "Teste DE VERDADE: " + ", ".join(lote) + ". Pra cada uma: rode test_*.py da pasta C:/Users/caion/<pasta>, "
            "abra a GUI e confira 2 contas/resultados na mão. Quebrou? Conserte no CÓDIGO-FONTE da pasta (nunca "
            "staged/dist) e rode o teste de novo. Inútil pro Caio? Anote no CRITICA.md. No --concluir CITE as 5 pastas "
            "(o portão de qualidade roda os testes delas).",
            ativos))
        qa += lote
    with open(QA, "w", encoding="utf-8") as f:
        json.dump(qa, f, ensure_ascii=False)
    if criadas:
        _log(f"quadro: {livres} livres pra {len(ativos)} agentes → criei {', '.join(criadas)}")
    return criadas


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    print("ativos:", _ativos())
    print("tendências extras disponíveis:", len(_tendencias_extras("")))
    print("criadas:", encher())
