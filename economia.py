"""Modo economia da fábrica — mede as cotas, PREVÊ se vão estourar antes de renovar e define o nível.

Contas medidas (só dado real, nada inventado):
  - claude : plano do Claude (limite de 5 h e da semana) — mesmo endereço do /usage (reusa ~/painel-creditos)
  - grok   : crédito semanal do SuperGrok (log local do Grok CLI) — vale pro Grok CLI e pro Cocaino
  Cursor e Antigravity não têm medidor no PC → sempre "normal".

Níveis por conta:
  normal     longe do limite
  economico  >= 70%, ou a previsão (ritmo dos últimos 45 min) diz que estoura ANTES de renovar
  critico    >= 90%, ou vai estourar e já está em >= 75%

Quem usa:
  - carteiro.py roda atualizar() a cada 3 min e segura entregas (econômico: 1 a cada 10 min; crítico: nenhuma)
  - painel.py mostra o modo no topo (todo agente roda ele antes de cada tarefa)
  - painel_adesivo.pyw mostra a faixa colorida
Arquivos: ECONOMIA.json (estado atual) e economia_historico.json (amostras pra previsão).

Uso: python economia.py            # mede agora e mostra
     python economia.py --forcar critico|economico|normal|auto   # trava o nível na mão (auto = volta a medir)
"""
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(HERE, "ECONOMIA.json")
HIST = os.path.join(HERE, "economia_historico.json")
GROK_LOG = os.path.join(os.path.expanduser("~"), ".grok", "logs", "unified.jsonl")
CREDITOS = os.path.join(os.path.expanduser("~"), "painel-creditos", "painel.py")

CONTA_DO_AGENTE = {"claude": "claude", "grokbuild": "grok", "grok": "grok", "cursor": None, "antigravity": None}
ICONE = {"normal": "🟢", "economico": "🟡", "critico": "🔴"}
REGRAS = {
    "normal": "tudo normal",
    "economico": "tarefas pequenas, sem varrer pasta inteira nem ler arquivo inteiro, /new entre tarefas, sem build à toa",
    "critico": "termine o que está fazendo, anuncie --feito e PARE até a cota renovar (ou até amanhã, se foi o orçamento do dia)",
}


def _agora():
    return dt.datetime.now().astimezone()


def _iso(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def medir_claude():
    import importlib.util
    sp = importlib.util.spec_from_file_location("painel_creditos", CREDITOS)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    d = m.fetch_usage()
    fh, sd = d.get("five_hour") or {}, d.get("seven_day") or {}
    return [{"janela": "5h", "pct": float(fh.get("utilization") or 0), "renova": fh.get("resets_at")},
            {"janela": "semana", "pct": float(sd.get("utilization") or 0), "renova": sd.get("resets_at")}]


def medir_grok():
    pct = fim = None
    with open(GROK_LOG, encoding="utf-8", errors="replace") as f:
        for linha in f:
            if "creditUsagePercent" in linha:
                try:
                    cfg = json.loads(linha)["ctx"]["config"]
                    pct, fim = float(cfg["creditUsagePercent"]), cfg.get("currentPeriod", {}).get("end")
                except (ValueError, KeyError, TypeError):
                    pass
    return [] if pct is None else [{"janela": "semana", "pct": pct, "renova": fim}]


def _ler(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _salvar(caminho, dados):
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    os.replace(tmp, caminho)


def prever(hist, conta, janela, pct, renova):
    """Ritmo (pontos % por hora) nos últimos 45 min e se estoura antes de renovar."""
    agora = _agora()
    pontos = [(_iso(h["t"]), h["pct"]) for h in hist
              if h["conta"] == conta and h["janela"] == janela and _iso(h["t"])]
    pontos = [(t, p) for t, p in pontos if (agora - t).total_seconds() <= 45 * 60]
    if len(pontos) < 2:
        return None, None
    (t0, p0), (t1, p1) = pontos[0], pontos[-1]
    horas = (t1 - t0).total_seconds() / 3600
    if horas < 0.1 or p1 < p0:  # pouco tempo de amostra, ou a janela renovou no meio
        return None, None
    ritmo = (p1 - p0) / horas
    if ritmo <= 0.05:
        return ritmo, None
    bate_100 = agora + dt.timedelta(hours=(100 - pct) / ritmo)
    t_renova = _iso(renova) if renova else None
    estoura = bool(t_renova and bate_100 < t_renova)
    return ritmo, (bate_100 if estoura else None)


def orcamento_do_dia(hist, conta, janela, pct, renova):
    """Orçamento diário das cotas SEMANAIS: o que sobrava no começo do dia ÷ dias até renovar.
    Devolve (usado_hoje, orcamento_hoje) em pontos percentuais, ou (None, None) se não der pra calcular."""
    t_renova = _iso(renova) if renova else None
    if not t_renova:
        return None, None
    agora = _agora()
    meia_noite = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    hoje = [(_iso(h["t"]), h["pct"]) for h in hist
            if h["conta"] == conta and h["janela"] == janela and _iso(h["t"]) and _iso(h["t"]) >= meia_noite]
    inicio = min(hoje)[1] if hoje else pct          # 1ª leitura do dia (ou agora)
    if pct < inicio:                                # a semana renovou hoje: conta a partir do zero
        inicio = 0.0
    dias = max(1.0, (t_renova - meia_noite).total_seconds() / 86400)
    return round(pct - inicio, 1), round((100 - inicio) / dias, 1)


def nivel_semana(usado, orcamento):
    if usado is None or not orcamento:
        return "normal"
    if usado >= orcamento * 1.25:
        return "critico"
    if usado >= orcamento:
        return "economico"
    return "normal"


def nivel(pct, estoura_em):
    if pct >= 90 or (estoura_em is not None and pct >= 75):
        return "critico"
    if pct >= 70 or estoura_em is not None:
        return "economico"
    return "normal"


def atualizar():
    """Mede, guarda amostra, prevê e grava ECONOMIA.json. Nunca levanta exceção."""
    estado = _ler(ESTADO, {})
    forcado = estado.get("forcado")
    hist = _ler(HIST, [])
    agora = _agora()
    contas = {}
    for conta, medir in (("claude", medir_claude), ("grok", medir_grok)):
        try:
            janelas = medir()
        except Exception as e:  # noqa: BLE001 — sem medida = mantém o último nível conhecido
            antigo = estado.get("contas", {}).get(conta)
            if antigo:
                antigo["aviso"] = f"sem leitura agora ({str(e)[:60]})"
                contas[conta] = antigo
            continue
        pior = {"nivel": "normal", "janelas": []}
        for j in janelas:
            hist.append({"t": agora.isoformat(), "conta": conta, "janela": j["janela"], "pct": j["pct"]})
            ritmo, estoura_em = prever(hist, conta, j["janela"], j["pct"], j["renova"])
            nv = nivel(j["pct"], estoura_em)
            usado = orc = None
            if j["janela"] == "semana":  # cota semanal: além do limite, respeita o orçamento do dia
                usado, orc = orcamento_do_dia(hist, conta, j["janela"], j["pct"], j["renova"])
                nv_dia = nivel_semana(usado, orc)
                if ["normal", "economico", "critico"].index(nv_dia) > ["normal", "economico", "critico"].index(nv):
                    nv = nv_dia
            j.update(nivel=nv, ritmo_h=round(ritmo, 1) if ritmo else None,
                     estoura_em=estoura_em.strftime("%H:%M") if estoura_em else None,
                     usado_hoje=usado, orcamento_hoje=orc)
            pior["janelas"].append(j)
            if ["normal", "economico", "critico"].index(nv) > ["normal", "economico", "critico"].index(pior["nivel"]):
                pior["nivel"] = nv
        contas[conta] = pior
    corte = agora - dt.timedelta(hours=6)
    hist = [h for h in hist if (_iso(h["t"]) or agora) >= corte][-2000:]
    _salvar(HIST, hist)
    if forcado in ("normal", "economico", "critico"):
        for c in contas.values():
            c["nivel"] = forcado
    novo = {"atualizado": agora.strftime("%Y-%m-%d %H:%M"), "forcado": forcado, "contas": contas}
    _salvar(ESTADO, novo)
    return novo


def nivel_do_agente(agente, estado=None):
    estado = estado if estado is not None else _ler(ESTADO, {})
    conta = CONTA_DO_AGENTE.get(agente)
    if not conta:
        return "normal"
    return estado.get("contas", {}).get(conta, {}).get("nivel", "normal")


def resumo(estado=None):
    """Linhas curtas pro painel.py / painel adesivo."""
    estado = estado if estado is not None else _ler(ESTADO, {})
    linhas = []
    for conta, c in estado.get("contas", {}).items():
        partes = []
        for j in c.get("janelas", []):
            p = f"{j['janela']} {j['pct']:.0f}%"
            if j.get("orcamento_hoje"):
                p += f" (hoje {j['usado_hoje']:.0f}% de {j['orcamento_hoje']:.0f}% do dia)"
            if j.get("estoura_em"):
                p += f" (no ritmo atual estoura ~{j['estoura_em']}, antes de renovar)"
            partes.append(p)
        nome = {"claude": "Claude", "grok": "SuperGrok (Grok CLI + Cocaino)"}.get(conta, conta)
        linhas.append(f"{ICONE[c.get('nivel', 'normal')]} {nome}: {c.get('nivel', 'normal').upper()} · "
                      + ", ".join(partes) + (f" · regra: {REGRAS[c['nivel']]}" if c.get("nivel") != "normal" else ""))
    return linhas


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if len(sys.argv) >= 3 and sys.argv[1] == "--forcar":
        e = _ler(ESTADO, {})
        e["forcado"] = None if sys.argv[2] == "auto" else sys.argv[2]
        _salvar(ESTADO, e)
    e = atualizar()
    print("💸 Modo economia —", e["atualizado"], "(forçado: " + e["forcado"] + ")" if e.get("forcado") else "")
    for l in resumo(e):
        print("  " + l)


if __name__ == "__main__":
    main()
