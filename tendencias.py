"""Radar de tendências — o que a comunidade dev está curtindo HOJE e que a Caixa ainda não tem.

Fontes (públicas, sem login):
  - GitHub Trending do dia (github.com/trending)
  - GitHub: repositórios criados nos últimos 7 dias com mais estrelas (API de busca)
  - Hacker News: "Show HN" com mais pontos nas últimas 48 h (API Algolia)
  - Reddit: top do dia em r/software, r/opensource, r/selfhosted, r/windows

Filtra o que é FERRAMENTA de PC (descarta framework, lib, curso, lista "awesome", modelo de IA…),
corta o que serve pra golpe/ataque, compara com o catálogo da Caixa e gera:
  - TENDENCIAS.md            ranking do dia (top 20) com link, popularidade e "parecida na Caixa"
  - TENDENCIA_DO_DIA.md      a 1ª ideia que ainda não foi feita = tarefa do agente
  - tendencias_historico.json  o que já virou tarefa (não repete)

Uso:
  python tendencias.py              # roda o radar e gera os arquivos
  python tendencias.py --feita URL  # marca a tendência como construída (sai da fila)
Roda sozinho todo dia pelo Agendador de Tarefas (tarefa "Caixa - Radar de Tendencias").
"""
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "tendencias_historico.json")
UA = "caixa-tendencias/1.0 (radar local de ferramentas)"

POSITIVAS = """tool tools app desktop cli tui utility utilities manager organizer organize cleaner clean
converter convert viewer editor tracker windows file files folder screenshot screen clipboard pdf image
images photo video audio music backup sync search launcher monitor dashboard downloader download
recorder record notes note markdown todo timer password vault finder rename duplicate disk storage
trash recycle bin compress zip ocr translate translator wallpaper window tiling hotkey shortcut
keyboard mouse terminal shell explorer browser extension privacy cleanup uninstaller installer
benchmark battery network wifi dns ip port scanner-own font color picker qr metadata exif ebook
reader podcast subtitle transcribe transcription speech voice tts stt calendar reminder habit budget
finance expense invoice spreadsheet csv json diff log logs process task automation macro""".split()

NEGATIVAS = """framework library sdk api-client boilerplate template starter tutorial course book roadmap
awesome interview leetcode dataset benchmark-suite paper papers weights model-zoo kubernetes k8s helm
terraform blockchain crypto token nft web3 defi react-component vue-component theme dotfiles config
homework cheatsheet resume""".split()

# nada que sirva pra golpe/ataque a terceiros (regra de ouro da Caixa)
PROIBIDAS = """malware exploit phishing stealer ransomware keylogger rat botnet ddos crack keygen cheat
aimbot bypass spoofer carding spam bruteforce brute-force credential-stuffing deauth jailbreak injector
osint people-search footprint doxx doxing stalk stalker username-lookup pre-configured preactivated
pre-activated activator unlocked""".split()

# iscas de pirataria/vírus que inflam estrela ("Adobe 2026 Installer com tudo liberado")
ISCAS = [r"all features enabled", r"full[- ]feature", r"desktop installer", r"standalone .*installer",
         r"20\d\d.*(installer|setup|edition|desktop build)", r"pre-?configured", r"people[- ]search",
         r"verif(y|ication) bypass", r"free (download|license)",
         r"export-?locked", r"drm", r"view-only", r"copy[- ]protect", r"paywall"]  # furar proteção = não

# pouco útil pra Caixa (desconta, não proíbe)
FORA_DO_FOCO = """agent agents mcp llm gpt claude chatgpt ios iphone ipad macos android switch nintendo emulator
emulation recomp recompilation rom roms game games vm docker self-hosted saas web-app nextjs react ai
linux gnome kde site website""".split()

# inglês -> palavras do catálogo (pra achar "parecida na Caixa")
EN_PT = {
    "trash": "lixeira", "recycle": "lixeira", "clipboard": "transferência", "screenshot": "print captura",
    "screen": "tela", "image": "imagem", "images": "imagens", "photo": "foto", "video": "vídeo",
    "audio": "áudio", "music": "música", "duplicate": "duplicados", "rename": "renomear",
    "password": "senha senhas", "disk": "disco", "storage": "disco", "search": "busca", "file": "arquivo",
    "files": "arquivos", "folder": "pasta", "notes": "notas", "note": "notas", "timer": "timer",
    "recorder": "gravador", "record": "gravar", "converter": "conversor", "convert": "converter",
    "color": "cor cores", "picker": "capturador", "font": "fontes", "metadata": "metadados",
    "capture": "captura print", "mount": "montar iso", "iso": "iso", "desktop": "área de trabalho",
    "compress": "compactar", "zip": "zip", "backup": "backup", "translate": "tradutor",
    "network": "rede", "wifi": "wi-fi", "battery": "bateria", "process": "processos",
    "window": "janelas", "wallpaper": "papel de parede", "calendar": "calendário",
    "budget": "orçamento finanças", "expense": "gastos", "invoice": "recibo", "ebook": "e-book leitor",
    "reader": "leitor", "subtitle": "legenda", "transcribe": "transcrever", "voice": "voz",
    "monitor": "monitor", "launcher": "lançador", "downloader": "baixar", "organizer": "organizador",
    "cleaner": "faxina limpar", "uninstaller": "desinstalar", "habit": "hábitos", "todo": "tarefas",
    "markdown": "markdown", "pdf": "pdf", "ocr": "ocr texto", "qr": "qr", "exif": "exif metadados",
    "hotkey": "atalho", "keyboard": "teclado", "spreadsheet": "planilha", "csv": "csv",
}


def _get(url, aceitar="application/json", tentativas=2):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": aceitar})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            erro = e
            time.sleep(2 + i * 3)
    print(f"  aviso: falhou {url[:70]}… ({erro})")
    return None


# ------------------------------------------------------------------ fontes
def github_trending():
    txt = _get("https://github.com/trending?since=daily", "text/html")
    if not txt:
        return []
    itens = []
    for art in re.findall(r'<article class="Box-row">(.*?)</article>', txt, re.S):
        m = re.search(r'<h2[^>]*>\s*<a[^>]*href="/([^"]+)"', art, re.S)
        if not m:
            continue
        repo = m.group(1).strip()
        d = re.search(r'<p class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', art, re.S)
        desc = html.unescape(re.sub(r"<[^>]+>", "", d.group(1))).strip() if d else ""
        h = re.search(r"([\d,]+)\s+stars today", art)
        hoje = int(h.group(1).replace(",", "")) if h else 0
        lang = re.search(r'itemprop="programmingLanguage">([^<]+)<', art)
        itens.append({"fonte": "GitHub Trending", "titulo": repo, "desc": desc,
                      "url": "https://github.com/" + repo, "pop": hoje, "pop_txt": f"+{hoje}★ hoje",
                      "lang": lang.group(1) if lang else ""})
    return itens


def github_novos():
    desde = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    q = urllib.parse.quote(f"created:>{desde} stars:>50")
    txt = _get(f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=40",
               "application/vnd.github+json")
    if not txt:
        return []
    itens = []
    for r in json.loads(txt).get("items", []):
        st, fk = r["stargazers_count"], r["forks_count"]
        # estrela comprada: muita estrela, quase nenhum fork; fazenda de fork: fork demais; repo vazio
        if fk < max(3, st * 0.02) or fk > st * 0.45 or r.get("size", 0) < 50 or not r.get("description"):
            continue
        itens.append({"fonte": "GitHub novos (7 dias)", "titulo": r["full_name"],
                      "desc": r.get("description") or "", "url": r["html_url"],
                      "pop": r["stargazers_count"] // 7, "pop_txt": f"{r['stargazers_count']}★ em 7 dias",
                      "lang": r.get("language") or "", "topics": " ".join(r.get("topics") or [])})
    return itens


def hacker_news():
    desde = int(time.time()) - 48 * 3600
    txt = _get("https://hn.algolia.com/api/v1/search?tags=show_hn&hitsPerPage=50"
               f"&numericFilters=created_at_i>{desde},points>20")
    if not txt:
        return []
    itens = []
    for h in json.loads(txt).get("hits", []):
        titulo = re.sub(r"^Show HN:\s*", "", h.get("title") or "")
        itens.append({"fonte": "Show HN", "titulo": titulo, "desc": titulo,
                      "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                      "pop": h.get("points", 0) * 3, "pop_txt": f"{h.get('points', 0)} pontos", "lang": ""})
    return itens


def reddit():
    """RSS (o JSON do Reddit bloqueia robô). RSS não traz votos: a posição no top do dia vira popularidade."""
    itens = []
    for sub in ["software", "opensource", "selfhosted", "windows"]:
        txt = _get(f"https://www.reddit.com/r/{sub}/top/.rss?t=day&limit=15", "application/atom+xml")
        if not txt:
            continue
        for i, e in enumerate(re.findall(r"<entry>(.*?)</entry>", txt, re.S)):
            t = re.search(r"<title>(.*?)</title>", e, re.S)
            l = re.search(r'<link href="([^"]+)"', e)
            c = re.search(r"<content[^>]*>(.*?)</content>", e, re.S)
            desc = re.sub(r"<[^>]+>", " ", html.unescape(html.unescape(c.group(1)))) if c else ""
            pop = max(10, 300 - 20 * i)
            itens.append({"fonte": f"Reddit r/{sub}", "titulo": html.unescape(t.group(1)) if t else "",
                          "desc": re.sub(r"\s+", " ", desc)[:300], "pop": pop, "pop_txt": f"#{i + 1} do dia",
                          "url": l.group(1) if l else "", "lang": ""})
        time.sleep(5)  # Reddit dá 429 se for rápido
    return itens


# ------------------------------------------------------------------ filtro e ranking
def _palavras(s):
    return set(re.findall(r"[a-z0-9][a-z0-9\-]+", s.lower()))


def nota_ferramenta(it):
    texto = " ".join([it["titulo"], it["desc"], it.get("topics", "")]).lower()
    w = _palavras(texto.replace("/", " "))
    if w & set(PROIBIDAS) or any(re.search(p, texto) for p in ISCAS):
        return -1
    pos = len(w & set(POSITIVAS))
    neg = len(w & set(NEGATIVAS))
    fora = len(w & set(FORA_DO_FOCO))
    # discussão/pergunta do Reddit não é ferramenta
    if it["fonte"].startswith("Reddit") and re.match(r"(why|should|how|what|which|is |are |looking for|any |help)",
                                                      it["titulo"].lower()):
        return -1
    return pos - 2 * neg - 2 * fora


def parecida_na_caixa(it, catalogo):
    """Devolve (nota 0-1, ferramenta) da ferramenta mais parecida já existente."""
    termos = set()
    for p in _palavras(it["titulo"] + " " + it["desc"]):
        if p in EN_PT:
            termos |= set(EN_PT[p].split())
    if not termos:
        return 0.0, None
    melhor = (0.0, None)
    for f in catalogo:
        alvo = (f["nome"] + " " + f["desc"]).lower()
        hit = sum(1 for t in termos if re.search(r"" + re.escape(t), alvo))
        nota = hit / len(termos) if len(termos) > 1 else hit * 0.7
        if nota > melhor[0]:
            melhor = (nota, f)
    return melhor


def carregar_catalogo():
    try:
        sys.path.insert(0, HERE)
        import catalogo
        itens, _ = catalogo.montar()
        return itens
    except Exception as e:  # noqa: BLE001
        print("  aviso: catálogo não carregou:", e)
        return []


def ler_hist():
    try:
        with open(HIST, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"tarefas": [], "feitas": []}


def salvar_hist(h):
    with open(HIST, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=1)


def rodar():
    print("📡 Radar de tendências —", dt.datetime.now().strftime("%d/%m/%Y %H:%M"))
    brutos = []
    for nome, fn in [("GitHub Trending", github_trending), ("GitHub novos", github_novos),
                     ("Show HN", hacker_news), ("Reddit", reddit)]:
        r = fn()
        print(f"  {nome}: {len(r)} itens")
        brutos += r
    catalogo = carregar_catalogo()
    hist = ler_hist()
    ja = {t["url"] for t in hist["tarefas"]} | set(hist["feitas"])

    cands, vistos = [], set()
    for it in brutos:
        chave = it["url"].lower().rstrip("/")
        if chave in vistos:
            continue
        vistos.add(chave)
        n = nota_ferramenta(it)
        if n < 1:
            continue
        sim, f = parecida_na_caixa(it, catalogo)
        it["nota_ferramenta"] = n
        it["parecida"] = f"{f['emoji']} {f['nome']} [{f['chave']}] ({sim:.0%})" if f and sim >= 0.5 else ""
        it["ja_tem"] = sim >= 0.8
        # popularidade pesa, ser ferramenta pesa, já ter na Caixa derruba
        it["score"] = round((it["pop"] ** 0.5) * (1 + 0.5 * n) * (0.35 if it["ja_tem"] else 1.0), 1)
        cands.append(it)
    cands.sort(key=lambda x: x["score"], reverse=True)
    top = cands[:20]

    hoje = dt.date.today().strftime("%d/%m/%Y")
    linhas = [f"# 📡 Tendências do dia — {hoje}", "",
              "Gerado por `python tendencias.py` (roda sozinho todo dia). Fontes: GitHub Trending, GitHub novos "
              "(7 dias), Show HN, Reddit. Só ferramentas de PC; nada de golpe/ataque.", "",
              "| # | Ideia | Fonte | Popularidade | Parecida na Caixa |", "|---|---|---|---|---|"]
    for i, it in enumerate(top, 1):
        desc = (it["desc"] or "")[:110].replace("|", "/").replace("\n", " ")
        linhas.append(f"| {i} | [{it['titulo']}]({it['url']}) — {desc} | {it['fonte']} | {it['pop_txt']} | "
                      f"{it['parecida'] or '—'} |")
    with open(os.path.join(HERE, "TENDENCIAS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")

    escolhida = next((it for it in top if it["url"] not in ja and not it["ja_tem"]), None)
    if escolhida:
        hist["tarefas"].append({"data": hoje, "url": escolhida["url"], "titulo": escolhida["titulo"]})
        salvar_hist(hist)
        tarefa = f"""# 🔥 Tendência do dia — {hoje}

**Ideia:** [{escolhida['titulo']}]({escolhida['url']})
**O que é:** {escolhida['desc'] or '(veja o link)'}
**Por que:** {escolhida['fonte']}, {escolhida['pop_txt']}.
**Parecida na Caixa:** {escolhida['parecida'] or 'nada parecido'}

## Tarefa (agente da fila "Tendência do dia" no RUMO.md)
1. Abra o link, entenda o que faz e **por que está fazendo sucesso** (a função que o povo curtiu).
2. `python catalogo.py --check "<ideia em português>"`. Se já existir algo parecido, **melhore a nossa**
   com o que a tendência tem de bom em vez de criar outra.
3. Faça a **versão nossa, igual ou melhor**: offline, PyQt6, pt-BR, tema escuro, útil pro Caio.
   **Escreva o código do zero** (não copie código de outro projeto: licença). Inspiração na ideia, não no código.
4. Se a ideia não couber (só nuvem, só Mac/Linux, precisa de conta, serve pra ataque):
   `python tendencias.py --feita {escolhida['url']}` e pegue a próxima do `TENDENCIAS.md`.
5. Pronto e testado: integre na Caixa, ACRESCENTE a pasta em `tendencias_caixa.json` (categoria 🔥 Tendências), `python tendencias.py --feita {escolhida['url']}` + `python painel.py <você> --feito "..."`.
   O Claude revisa, integra na Caixa e builda.
"""
        with open(os.path.join(HERE, "TENDENCIA_DO_DIA.md"), "w", encoding="utf-8") as f:
            f.write(tarefa)
        print(f"🔥 Tendência do dia: {escolhida['titulo']} ({escolhida['pop_txt']})")
    else:
        print("Nenhuma tendência nova hoje (todas já viraram tarefa ou a Caixa já tem).")
    print(f"✅ TENDENCIAS.md com {len(top)} ideias.")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if len(sys.argv) >= 3 and sys.argv[1] == "--feita":
        h = ler_hist()
        if sys.argv[2] not in h["feitas"]:
            h["feitas"].append(sys.argv[2])
        salvar_hist(h)
        print("Marcada como feita:", sys.argv[2])
        return
    rodar()


if __name__ == "__main__":
    main()
