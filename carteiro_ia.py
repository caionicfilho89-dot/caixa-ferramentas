"""Carteiro inteligente: o script entrega/mede/testa; o GEMINI (conta Pro do Caio, via agy) PENSA.

Ideia do Caio (11/11): "e se o carteiro fosse uma IA?". Híbrido: o Gemini só é chamado quando há algo pra julgar
(nunca a cada 30 s), em modo plan (só responde texto — não edita arquivo nem roda comando):
  1. revisar()  — leu o resultado de cada tarefa concluída: resolve mesmo o que foi pedido? Não → tarefa "↩️ Refazer"
                   pro mesmo agente com o motivo (o portão pega teste quebrado; a IA pega "fez outra coisa").
  2. planejar() — quadro baixo: lê CRITICA.md, o que o Caio mais usa e as tendências, e cria tarefas ÚTEIS e
                   pequenas (os lotes de QA do quadro_cheio viram plano B).
Teste à mão: python carteiro_ia.py --revisar | --planejar | --perguntar "texto"
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
AGY = os.path.join(os.environ.get("LOCALAPPDATA", ""), "agy", "bin", "agy.exe")
MODELO = "gemini-3.8-flash-low"   # barato e rápido; trocar aqui se quiser o modelo grande
ESTADO = os.path.join(HERE, "carteiro_ia.json")


def _json(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _log(t, painel=False):
    try:
        import carteiro
        carteiro.log("Gemini: " + t)
    except Exception:  # noqa: BLE001
        print("Gemini:", t)
    if painel:  # o Gemini é o 6º agente: aparece no painel/adesivo como os outros
        subprocess.run([sys.executable, os.path.join(HERE, "painel.py"), "gemini", "--feito", t[:200],
                        "--proximo", "revisar o que for concluído e planejar quando o quadro baixar"],
                       capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def perguntar(prompt, timeout=230):
    """Manda pro Gemini (conta Gemini Pro do Caio) e devolve o texto ('' se falhar).

    Pelo agy: em 11/11/2026 o Google desligou o login pessoal do Gemini CLI ("migrate to the Antigravity suite"),
    então o caminho oficial da assinatura Pro fora do navegador é o agy. Modo plan + "não use ferramentas":
    sem esse aviso ele saía lendo arquivo sozinho e estourava o tempo (resposta vazia); com ele responde em ~8 s.
    """
    if not os.path.isfile(AGY):
        return ""
    prompt = ("NÃO use ferramentas e NÃO leia arquivos: tudo o que você precisa está aqui. Responda direto, só texto.\n\n"
              + prompt)
    try:
        r = subprocess.run([AGY, "-p", prompt, "--model", MODELO, "--mode", "plan", "--print-timeout", "200s"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           cwd=os.environ.get("TEMP", HERE), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return (r.stdout or "").strip()
    except Exception as e:  # noqa: BLE001
        _log(f"Gemini não respondeu: {e}")
        return ""


def _extrair_json(txt):
    m = re.search(r"```(?:json)?\s*(.+?)```", txt, re.S)
    if m:
        bruto = m.group(1)
    else:
        inicios = [i for i in (txt.find("["), txt.find("{")) if i >= 0]
        bruto = txt[min(inicios):] if inicios else txt
    for fim in range(len(bruto), 0, -1):  # corta lixo depois do JSON
        try:
            return json.loads(bruto[:fim])
        except ValueError:
            continue
    return None


def _estado():
    return _json(ESTADO, {"revisadas": [], "ultimo_plano": 0})


def _salvar(e):
    e["revisadas"] = e["revisadas"][-300:]
    with open(ESTADO, "w", encoding="utf-8") as f:
        json.dump(e, f, ensure_ascii=False, indent=1)


# ------------------------------------------------------------------ 1. revisar
def revisar(maximo=1):
    """Revisa até N tarefas concluídas ainda não revisadas (as mais novas primeiro)."""
    import tarefas
    e = _estado()
    feitas = [t for t in tarefas.ler() if t["status"] == "feito" and t["id"] not in e["revisadas"]
              and not t["titulo"].startswith("↩️")]
    if not e["revisadas"]:  # 1ª vez: não revisa o passado inteiro, só daqui pra frente
        e["revisadas"] = [t["id"] for t in feitas]
        _salvar(e)
        return []
    refazer = []
    for t in sorted(feitas, key=lambda x: x["quando"], reverse=True)[:maximo]:
        resp = perguntar(
            "Você é o revisor da fábrica de ferramentas offline do Caio (pt-BR). Um agente diz que concluiu uma tarefa.\n"
            f"TAREFA {t['id']}: {t['titulo']}\nPEDIDO: {t.get('detalhe', '')}\nRESULTADO DECLARADO: {t.get('resultado', '')}\n\n"
            "Os testes automáticos já passaram. Julgue só: o resultado resolve DE VERDADE o que foi pedido, e é útil pro "
            "Caio? Seja justo: resultado curto mas coerente = ok. Responda SÓ um JSON: "
            '{"ok": true/false, "motivo": "uma frase em pt-BR dizendo o que falta, se não ok"}')
        j = _extrair_json(resp) or {}
        e["revisadas"].append(t["id"])
        if j.get("ok") is False and j.get("motivo"):
            nova = tarefas.nova(f"↩️ Refazer {t['id']}: {t['titulo'][:60]}",
                                f"O revisor (Gemini) recusou {t['id']}: {j['motivo']} | Pedido original: {t.get('detalhe', '')}",
                                [t.get("por") or "antigravity"])
            refazer.append(nova)
            _log(f"{t['id']} recusada pelo revisor → {nova}: {j['motivo']}", painel=True)
        elif j:
            _log(f"{t['id']} aprovada pelo revisor", painel=True)
    _salvar(e)
    return refazer


# ------------------------------------------------------------------ 2. planejar
def _contexto():
    partes = []
    try:
        crit = open(os.path.join(HERE, "CRITICA.md"), encoding="utf-8").read()
        partes.append("CRITICA.md (problemas apontados pelos testadores, final):\n" + crit[-3500:])
    except OSError:
        pass
    cfg = _json(os.path.join(os.path.expanduser("~"), ".caixa_ferramentas.json"), {}) or _json(
        os.path.join(HERE, "config.json"), {})
    uses = cfg.get("uses") if isinstance(cfg, dict) else None
    if uses:
        top = sorted(uses.items(), key=lambda kv: -kv[1])[:15]
        partes.append("Ferramentas que o Caio MAIS USA: " + ", ".join(f"{k} ({v}x)" for k, v in top))
    try:
        tend = open(os.path.join(HERE, "TENDENCIAS.md"), encoding="utf-8").read()
        partes.append("Tendências de hoje (topo):\n" + "\n".join(tend.splitlines()[6:14])[:2000])
    except OSError:
        pass
    return "\n\n".join(partes)


def planejar(quantas=4, agentes=("antigravity", "cursor", "grokbuild")):
    """Cria até N tarefas úteis no quadro. No máx. 1 vez por hora. Devolve os IDs criados."""
    import tarefas
    e = _estado()
    if time.time() - e.get("ultimo_plano", 0) < 3600:
        return []
    e["ultimo_plano"] = time.time()
    _salvar(e)
    abertas = [t["titulo"] for t in tarefas.ler() if t["status"] != "feito"][-30:]
    recentes = [t["titulo"] for t in tarefas.ler() if t["status"] == "feito"][-25:]
    resp = perguntar(
        "Você é o planejador da 'Caixa de Ferramentas' do Caio: app Windows offline (PyQt6, pt-BR) com 750+ "
        "ferramentas. Agentes de código vão executar suas tarefas.\n\n" + _contexto() +
        "\n\nJá abertas: " + "; ".join(abertas) + "\nFeitas recentemente: " + "; ".join(recentes) +
        f"\n\nCrie {quantas} tarefas NOVAS, PEQUENAS (cabem em 30 min) e ÚTEIS de verdade pro Caio: consertar problema do "
        "CRITICA.md, melhorar ferramenta que ele mais usa, ou ideia de tendência sem parecida. PROIBIDO: ferramenta de nicho "
        "inútil, adaptador de barra de nicho, repetir tarefa aberta, build do .exe, nada pra golpe/ataque. Cada uma diz a "
        "PASTA da ferramenta (C:/Users/caion/<pasta>) e como testar. Responda SÓ um JSON: "
        '[{"titulo": "...", "detalhe": "...", "quem": ["antigravity", "cursor", "grokbuild"]}]')
    lista = _extrair_json(resp)
    if not isinstance(lista, list):
        _log("planejador não devolveu lista; fica o plano B (lotes de QA). Resposta: " + repr(resp[:300]))
        return []
    criadas = []
    for t in lista[:quantas]:
        if not isinstance(t, dict) or not t.get("titulo") or t["titulo"] in abertas:
            continue
        quem = [q for q in (t.get("quem") or agentes) if q in agentes] or list(agentes)
        criadas.append(tarefas.nova("🧠 " + t["titulo"][:90], str(t.get("detalhe", ""))[:600], quem))
    if criadas:
        _log(f"planejei {len(criadas)} tarefa(s) útil(eis): {', '.join(criadas)}", painel=True)
    return criadas


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    a = sys.argv[1:]
    if a[:1] == ["--revisar"]:
        print(revisar())
    elif a[:1] == ["--planejar"]:
        e = _estado(); e["ultimo_plano"] = 0; _salvar(e)
        print(planejar())
    elif a[:1] == ["--perguntar"]:
        print(perguntar(" ".join(a[1:])))
    else:
        print(__doc__)
