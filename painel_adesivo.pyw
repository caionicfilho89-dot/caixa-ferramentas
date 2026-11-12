"""Painel adesivo da Fábrica — nota fixa na tela com o status do projeto e dos agentes.

Lê só arquivos locais (painel/*.json, catalogo.json, caixa.pyw, TENDENCIA_DO_DIA.md, carteiro.log)
e atualiza a cada 10 s. Sempre por cima, sem botão na barra de tarefas.
  - arrastar: move      - 2 cliques no título: recolhe/expande
  - botão direito: menu (recolher, transparência, fechar)
Posição e estado ficam salvos em ~/.caixa_painel_adesivo.json.
"""
import datetime as dt
import glob
import json
import os
import re
import sys

from PyQt6.QtCore import QPoint, QPointF, QRectF, Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (QApplication, QFrame, QLabel, QMenu, QScrollArea, QVBoxLayout, QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(os.path.expanduser("~"), ".caixa_painel_adesivo.json")
FMT = "%Y-%m-%d %H:%M"

AGENTES = [  # (chave no painel, nome que o Caio usa, emoji, papel)
    ("claude", "Claude", "🧑‍🍳", "integra e builda"),
    ("cursor", "Cursor", "🎨", "visual"),
    ("antigravity", "Antigravity", "🧠", "motor da barra"),
    ("grokbuild", "Grok CLI", "🔌", "barra + tendência"),
    ("grok", "Cocaino", "🧐", "crítico/testador"),
    ("gemini", "Gemini", "✨", "carteiro inteligente: revisa e planeja"),
]
NOME = {a[0]: a[1] for a in AGENTES}

QSS = """
#nota { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #171a26, stop:1 #10121a);
        border: 1px solid #2f3350; border-top: 3px solid #7c5cff; border-radius: 14px; }
QLabel { color: #e6e6f0; background: transparent; }
#titulo { font-weight: 700; color: #ffffff; }
#sub { color: #a9a9c2; }
#secao { color: #a99bff; font-weight: 800; font-size: 8pt; letter-spacing: 2px;
         padding: 10px 0 3px 2px; border-bottom: 1px solid #262a40; }
#agente { background: #1c1f2e; border-radius: 10px; padding: 7px 9px; border: 1px solid #262a40; }
#alerta2 { background: rgba(255,92,92,0.13); border: 1px solid rgba(255,92,92,0.45); border-radius: 9px; padding: 6px 8px; }
#alerta1 { background: rgba(245,197,66,0.10); border: 1px solid rgba(245,197,66,0.38); border-radius: 9px; padding: 6px 8px; }
#alerta0 { background: rgba(61,220,132,0.10); border: 1px solid rgba(61,220,132,0.35); border-radius: 9px; padding: 6px 8px; }
#linha { color: #c9c9da; padding: 1px 2px; }
#mapa { background: #141724; border: 1px solid #262a40; border-radius: 12px; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QScrollBar:vertical { width: 6px; background: transparent; }
QScrollBar::handle:vertical { background: #3a3d55; border-radius: 3px; }
QToolTip { background: #1c1f2e; color: #e6e6f0; border: 1px solid #7c5cff; padding: 6px; border-radius: 6px; }
QMenu { background: #1b1e2b; color: #e6e6f0; border: 1px solid #3a3d55; }
QMenu::item:selected { background: #7c5cff; }
"""


def _ler_json(caminho, padrao=None):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _quando(txt):
    try:
        return dt.datetime.strptime(txt[:16], FMT)
    except (ValueError, TypeError):
        return None


def _ha(t):
    if not t:
        return "—"
    m = int((dt.datetime.now() - t).total_seconds() // 60)
    if m < 1:
        return "agora"
    if m < 60:
        return f"há {m} min"
    return f"há {m // 60}h{m % 60:02d}"


def _corta(s, n):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


# ---------------------------------------------------------------- gastos
GROK_LOG = os.path.join(os.path.expanduser("~"), ".grok", "logs", "unified.jsonl")
_grok_cache = {"mtime": None, "dados": None}


def gasto_grok():
    """Crédito semanal do SuperGrok (creditUsagePercent) e tokens de hoje, do log local do Grok CLI."""
    try:
        mt = os.path.getmtime(GROK_LOG)
    except OSError:
        return None
    if _grok_cache["mtime"] == mt:
        return _grok_cache["dados"]
    hoje = dt.date.today()
    pct, fim, tokens, chamadas, lido = None, None, 0, 0, None
    with open(GROK_LOG, encoding="utf-8", errors="replace") as f:
        for linha in f:
            if "creditUsagePercent" in linha:
                try:
                    cfg = json.loads(linha)["ctx"]["config"]
                    pct = float(cfg["creditUsagePercent"])
                    fim = cfg.get("currentPeriod", {}).get("end")
                    lido = dt.datetime.fromisoformat(json.loads(linha)["ts"].replace("Z", "+00:00")).astimezone().strftime("%H:%M")
                except (ValueError, KeyError, TypeError):
                    pass
            elif '"prompt_tokens"' in linha:
                try:
                    j = json.loads(linha)
                    quando = dt.datetime.fromisoformat(j["ts"].replace("Z", "+00:00")).astimezone()
                    if quando.date() == hoje:
                        c = j["ctx"]
                        tokens += (c.get("prompt_tokens") or 0) - (c.get("cached_prompt_tokens") or 0)                             + (c.get("completion_tokens") or 0) + (c.get("reasoning_tokens") or 0)
                        chamadas += 1
                except (ValueError, KeyError, TypeError):
                    pass
    d = {"pct": pct, "fim": fim, "tokens": tokens, "chamadas": chamadas, "lido": lido}
    _grok_cache.update(mtime=mt, dados=d)
    return d


class BuscaClaude(QThread):
    """Uso do plano Claude pelo mesmo endereço do /usage (reaproveita ~/painel-creditos)."""
    pronto = pyqtSignal(object)

    def run(self):
        try:
            import importlib.util
            sp = importlib.util.spec_from_file_location(
                "painel_creditos", os.path.join(os.path.expanduser("~"), "painel-creditos", "painel.py"))
            m = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(m)
            self.pronto.emit(m.fetch_usage())
        except Exception as e:  # noqa: BLE001
            self.pronto.emit({"erro": str(e)[:80]})


def _falta(iso):
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone()
    except (ValueError, AttributeError):
        return ""
    s = int((t - dt.datetime.now().astimezone()).total_seconds())
    if s <= 0:
        return "renovando"
    d, r = divmod(s, 86400)
    h, r = divmod(r, 3600)
    return f"renova em {d}d {h}h" if d else (f"renova em {h}h{r // 60:02d}" if h else f"renova em {r // 60} min")


def _barra(pct):
    pct = max(0.0, min(100.0, float(pct or 0)))
    cor = "#ef4444" if pct >= 85 else ("#f59e0b" if pct >= 60 else "#22c55e")
    cheios = int(round(pct / 10))
    return f"<span style='color:{cor}'>{'█' * cheios}</span><span style='color:#3a3d55'>{'█' * (10 - cheios)}</span> <b style='color:{cor}'>{pct:.0f}%</b>"


def _arquivista():
    import shutil
    try:
        livre = shutil.disk_usage("C:/").free / 2**30
    except OSError:
        return ""
    txt = f"<br>💾 C: {livre:.0f} GB livres"
    try:
        with open("C:/Users/caion/arquivista/status.json", encoding="utf-8") as f:
            st = json.load(f)
        if st.get("bytes", 0) >= 500 * 2**20:
            txt += (f" · 🗄️ <b>{st['bytes'] / 2**30:.1f} GB prontos pro Drive</b> ({st['arquivos']} arquivos, "
                    f"lista de {st['quando']}) → clique duplo em <b>Aprovar arquivista</b> na área de trabalho")
        else:
            txt += f" · 🗄️ nada grande pra mandar pro Drive ({st['quando']})"
    except (OSError, ValueError, KeyError):
        pass
    return txt


def _quadro():
    try:
        with open(os.path.join(HERE, "tarefas.json"), encoding="utf-8") as f:
            ts = json.load(f)
    except (OSError, ValueError):
        return ""
    n = lambda st: sum(1 for t in ts if t.get("status") == st)  # noqa: E731
    return f" · 📋 quadro: {n('pegou')} fazendo, {n('livre')} livres, {n('feito')} feitas"


def coletar():
    """Tudo que a nota mostra, lido do disco."""
    painel = {}
    for f in glob.glob(os.path.join(HERE, "painel", "*.json")):
        d = _ler_json(f, {})
        if d:
            painel[d.get("agente", os.path.basename(f)[:-5])] = d
    pend = {}
    for de, d in painel.items():
        for p in d.get("pedidos", []):
            pend.setdefault(p.get("para"), []).append(de)
    try:
        src = open(os.path.join(HERE, "caixa.pyw"), encoding="utf-8").read()
        versao = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', src, re.M).group(1)
    except (OSError, AttributeError):
        versao = "?"
    cat = _ler_json(os.path.join(HERE, "catalogo.json"), [])
    n_ferr = len(cat) if isinstance(cat, list) else len(cat.get("ferramentas", cat)) if isinstance(cat, dict) else 0
    tend = ""
    try:
        t = open(os.path.join(HERE, "TENDENCIA_DO_DIA.md"), encoding="utf-8").read()
        m = re.search(r"\*\*Ideia:\*\*\s*\[(.+?)\]\(http", t)  # título pode ter [colchetes]
        tend = m.group(1) if m else ""
    except OSError:
        pass
    carteiro = "?"
    try:
        ult = open(os.path.join(HERE, "carteiro.log"), encoding="utf-8").read().strip().splitlines()[-1]
        carteiro = "ligado" if ult else "?"
        ents = [l for l in open(os.path.join(HERE, "carteiro.log"), encoding="utf-8") if "ENTREGUE" in l]
        if ents:
            carteiro += f" · última entrega {ents[-1][11:16]}"
    except (OSError, IndexError):
        pass
    feitos = []
    for chave, d in painel.items():
        for x in d.get("feitos", []):
            feitos.append((_quando(x), chave, x[17:]))
    feitos.sort(key=lambda z: z[0] or dt.datetime.min, reverse=True)
    # evolução: EVOLUCAO.md (uma linha por versão) + cobertura da barra (COBERTURA.md)
    evol = []
    try:
        for l in open(os.path.join(HERE, "EVOLUCAO.md"), encoding="utf-8"):
            m = re.match(r"- \*\*(v[^*]+)\*\* · ([^·]+) · ([^·]+) · (.+)", l.strip())
            if m:
                evol.append(tuple(x.strip() for x in m.groups()))
    except OSError:
        pass
    barra = ""
    try:
        cob = open(os.path.join(HERE, "COBERTURA.md"), encoding="utf-8").read()
        m = re.search(r"adaptador na barra: \*\*(\d+)\*\*", cob)
        barra = m.group(1) if m else ""
    except OSError:
        pass
    return {"painel": painel, "pend": pend, "versao": versao, "n": n_ferr, "tend": tend,
            "carteiro": carteiro, "feitos": feitos[:8], "evol": evol, "barra": barra}


# ------------------------------------------------------------------ Fábrica 2.0: correio (Agent Mail) e mapa
WEB_CORREIO = "http://127.0.0.1:8765/mail/"
# Desde 11/11 o painel da fábrica é o Claude Code Monitor; esta nota fica SÓ COM O MAPA (pedido do Caio).
# python painel_adesivo.pyw --completo  → volta o painel inteiro (alertas, agentes, conversas, gastos...)
SO_MAPA = "--completo" not in sys.argv


def _formacao():
    d = _ler_json(os.path.join(HERE, "formacao.json"), {}) or {}
    return d.get("formacao", "A"), set((d.get("cadeiras") or {}).keys()) if d.get("formacao") == "B" else set()



def alertas(d, correio, cad_g):
    """O que o Caio PRECISA saber, sem procurar (pedido dele, 11/11). Lista de (nível, texto); nível 2 = urgente."""
    out = []
    agora = dt.datetime.now()
    # 1) cotas: crítico/econômico e quando renova; formação B pode voltar pra A?
    try:
        import economia
        est = _ler_json(os.path.join(HERE, "ECONOMIA.json"), {}) or {}
        nomes = {"claude": "Claude", "grok": "SuperGrok", "google": "Google"}
        for conta, c in (est.get("contas") or {}).items():
            nv = c.get("nivel")
            if nv in ("critico", "economico"):
                ren = [j.get("renova") for j in c.get("janelas", []) if j.get("renova")]
                quando = _falta(ren[0]) if ren else ""
                out.append((2 if nv == "critico" else 1,
                            f"{'🔴' if nv == 'critico' else '🟡'} cota <b>{nomes.get(conta, conta)}</b> "
                            f"{'CRÍTICA' if nv == 'critico' else 'apertando'} {quando}"))
        if cad_g and economia._ler(economia.ESTADO, {}).get("contas", {}).get("grok", {}).get("nivel") == "normal":
            out.append((2, "🔀 SuperGrok voltou ao normal: já dá pra voltar pra <b>Formação A</b> "
                           "(<code>python formacao.py A</code>)"))
    except Exception:  # noqa: BLE001
        pass
    # 2) agentes travados / parados com trabalho
    for chave, nome, _e, _p in AGENTES:
        a = d["painel"].get(chave, {})
        if a.get("bloqueado"):
            out.append((2, f"⛔ <b>{nome}</b> travado: {_corta(a['bloqueado'], 80)}"))
    # 3) log do carteiro (última 1h): recusas, falhas repetidas, erros, cadeira reaberta
    try:
        linhas = open(os.path.join(HERE, "carteiro.log"), encoding="utf-8", errors="replace").read().splitlines()[-400:]
        recentes = []
        for l in linhas:
            t = _quando(l[:16])
            if t and t > agora - dt.timedelta(hours=1):
                recentes.append(l[20:] if l[16:17] == ":" else l[17:])  # log tem HH:MM:SS
        recusas = [l for l in recentes if "recusada pelo revisor" in l]
        if recusas:
            out.append((1, f"↩️ Gemini mandou refazer {len(recusas)} tarefa(s): {_corta(recusas[-1].replace('Gemini: ', ''), 90)}"))
        falhas = {}
        for l in recentes:
            if "falhou" in l.lower():
                ag = l.split(":")[0]
                falhas[ag] = falhas.get(ag, 0) + 1
        for ag, q in falhas.items():
            if q >= 3:
                out.append((1, f"⚠️ carteiro falhou {q}x com <b>{ag}</b> na última hora"))
        erros = [l for l in recentes if "Traceback" in l or " erro" in l.lower()]
        if erros:
            out.append((1, f"🐞 erro no carteiro: {_corta(erros[-1], 90)}"))
        reab = [l for l in recentes if "reabri" in l]
        if len(reab) >= 3:
            out.append((1, f"🔁 cadeira da formação B reaberta {len(reab)}x na última hora (algo derrubando o agente?)"))
    except OSError:
        pass
    # 4) correio fora do ar
    if correio and correio.get("erro"):
        out.append((2, "📭 <b>correio (Agent Mail) fora do ar</b> — clique 🏭 Ligar Fabrica"))
    # 5) novidades boas (últimas 3 h)
    for t, chave, txt in d.get("feitos", [])[:8]:
        if t and t > agora - dt.timedelta(hours=3) and re.search(r"instalad|v\d+\.\d+\.\d+|Tendência|integrad", txt, re.I):
            out.append((0, f"✨ {NOME.get(chave, chave)}: {_corta(txt, 90)}"))
            break
    out.sort(key=lambda x: -x[0])
    return out[:6]


class BuscaCorreio(QThread):
    """Lê o correio de todos os agentes (só espia, não marca lida) numa thread: mensagens recentes + não lidas."""
    pronto = pyqtSignal(dict)

    def run(self):
        out = {"msgs": [], "nao_lidas": {}, "erro": None}
        try:
            sys.path.insert(0, HERE)
            import fabrica_mail as fm
            vistos = set()
            for chave, *_r in AGENTES:
                try:
                    todas = fm.caixa(chave, so_novas=False, limite=15)
                    out["nao_lidas"][chave] = sum(1 for m in todas if not m.get("read_ts"))
                    for m in todas:
                        if m.get("id") in vistos:
                            continue
                        vistos.add(m.get("id"))
                        out["msgs"].append({"id": m.get("id"), "de": fm.apelido(m.get("from", "?")),
                                            "para": NOME.get(chave, chave), "assunto": str(m.get("subject", "")),
                                            "quando": str(m.get("created_ts", ""))})
                except Exception:  # noqa: BLE001
                    continue
            out["msgs"].sort(key=lambda m: m["quando"], reverse=True)
        except Exception as e:  # noqa: BLE001
            out["erro"] = str(e)[:80]
        self.pronto.emit(out)


def _iso_local(txt):
    try:
        t = dt.datetime.fromisoformat(txt.replace("Z", "+00:00"))
        return t.astimezone().replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None


class Mapa(QWidget):
    """A fábrica em imagem: agentes em círculo (cor = estado), linhas = quem conversou com quem na última hora,
    selo G = cadeira rodando no Google (formação B). Passe o mouse num agente; 2 cliques abre o correio no Edge."""
    COR = {"trab": "#3ddc84", "parado": "#f5c542", "sem_cota": "#ff5c5c", "off": "#6b6b80"}

    def __init__(self):
        super().__init__()
        self.setFixedHeight(262)
        self.setObjectName("mapa")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMouseTracking(True)
        self.nos = []          # [(chave, nome, emoji, estado, google, dica)]
        self.arestas = {}      # (nomeA, nomeB) -> nº de mensagens
        self._pos = {}

    def dados(self, nos, arestas):
        self.nos, self.arestas = nos, arestas
        self.update()

    def paintEvent(self, _e):  # noqa: N802
        from PyQt6.QtGui import QColor, QPainter, QPen
        import math
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy, r = w / 2, (h - 18) / 2 + 2, min(w, h - 18) / 2 - 40  # espaço embaixo pra legenda
        self._pos = {}
        n = max(1, len(self.nos))
        for i, no in enumerate(self.nos):
            ang = -math.pi / 2 + 2 * math.pi * i / n
            self._pos[no[1]] = QPointF(cx + r * math.cos(ang), cy + r * math.sin(ang))
        for (a, b), qtd in self.arestas.items():
            if a in self._pos and b in self._pos:
                pen = QPen(QColor(124, 92, 255, 90 + min(qtd, 8) * 18))
                pen.setWidthF(1.2 + min(qtd, 8) * 0.7)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                p.setPen(pen)
                p.drawLine(self._pos[a], self._pos[b])
        for chave, nome, emoji, estado, google, _dica in self.nos:
            c = self._pos[nome]
            cor = QColor(self.COR.get(estado, "#6b6b80"))
            brilho = QColor(cor)
            brilho.setAlpha(55)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(brilho)
            p.drawEllipse(c, 29, 29)              # brilho em volta
            p.setPen(QPen(QColor("#0f111a"), 3))
            p.setBrush(cor)
            p.drawEllipse(c, 21, 21)
            f = p.font(); f.setPointSize(13); p.setFont(f)
            p.setPen(QColor("#11131a"))
            p.drawText(QRectF(c.x() - 21, c.y() - 21, 42, 42), Qt.AlignmentFlag.AlignCenter, emoji)
            if google:
                p.setBrush(QColor("#4285f4")); p.setPen(QPen(QColor("#11131a"), 1.5))
                p.drawEllipse(QPointF(c.x() + 16, c.y() - 16), 8, 8)
                f.setPointSize(7); f.setBold(True); p.setFont(f); p.setPen(QColor("white"))
                p.drawText(QRectF(c.x() + 8, c.y() - 24, 16, 16), Qt.AlignmentFlag.AlignCenter, "G")
            f.setPointSize(8); f.setBold(True); p.setFont(f); p.setPen(QColor("#e6e6f0"))
            p.drawText(QRectF(c.x() - 50, c.y() + 22, 100, 16), Qt.AlignmentFlag.AlignCenter, nome)
        f = p.font(); f.setPointSize(7); f.setBold(False); p.setFont(f); p.setPen(QColor("#9a9ab0"))
        p.drawText(QRectF(4, h - 14, w - 8, 14), Qt.AlignmentFlag.AlignLeft,
                   "🟢 trabalhando  🟡 parado  🔴 sem cota  G = Google · linha = conversa (1h)")
        p.end()

    def mouseMoveEvent(self, e):  # noqa: N802
        from PyQt6.QtWidgets import QToolTip
        for _chave, nome, _emoji, _est, _g, dica in self.nos:
            c = self._pos.get(nome)
            if c and (c - e.position()).manhattanLength() < 30:
                QToolTip.showText(e.globalPosition().toPoint(), dica, self)
                return
        QToolTip.hideText()

    def mouseDoubleClickEvent(self, _e):  # noqa: N802
        from PyQt6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(WEB_CORREIO))


class Nota(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Fábrica da Caixa")
        self.cfg = _ler_json(CFG, {}) or {}
        self._arrasto = None

        fora = QVBoxLayout(self)
        fora.setContentsMargins(0, 0, 0, 0)
        self.caixa = QFrame(objectName="nota")
        fora.addWidget(self.caixa)
        lay = QVBoxLayout(self.caixa)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)
        self.titulo = QLabel("🏭 Fábrica da Caixa", objectName="titulo")
        f = QFont()
        f.setPointSize(11)
        f.setBold(True)
        self.titulo.setFont(f)
        lay.addWidget(self.titulo)
        self.resumo = QLabel("", objectName="sub")
        self.resumo.setWordWrap(True)
        lay.addWidget(self.resumo)

        self.corpo = QWidget()
        self.corpo_lay = QVBoxLayout(self.corpo)
        self.corpo_lay.setContentsMargins(0, 4, 0, 0)
        self.corpo_lay.setSpacing(5)
        self.rolagem = QScrollArea()
        self.rolagem.setWidgetResizable(True)
        self.rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.rolagem.setWidget(self.corpo)
        lay.addWidget(self.rolagem, 1)

        self.setFixedWidth(int(self.cfg.get("largura", 380)))
        self.resize(self.width(), int(self.cfg.get("altura", 640)))
        self.setWindowOpacity(max(0.99, float(self.cfg.get("opacidade", 1.0))))
        tela = QApplication.primaryScreen().availableGeometry()
        x, y = self.cfg.get("x"), self.cfg.get("y")
        if x is None or not tela.contains(QPoint(int(x) + 20, int(y) + 20)):
            x, y = tela.right() - self.width() - 16, tela.top() + 16
        self.move(int(x), int(y))
        self.recolhida = bool(self.cfg.get("recolhida", False))
        self.claude_uso = None
        self._busca = None
        self.timer_claude = QTimer(self)
        self.timer_claude.timeout.connect(self._buscar_claude)
        self.timer_claude.start(3 * 60_000)
        self._buscar_claude()

        self.correio = None
        self._busca_correio = None
        self.timer_correio = QTimer(self)
        self.timer_correio.timeout.connect(self._buscar_correio)
        self.timer_correio.start(60_000)
        QTimer.singleShot(1500, self._buscar_correio)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar)
        self.timer.start(10_000)
        self.atualizar()

    def _buscar_claude(self):
        if self._busca is not None and self._busca.isRunning():
            return
        self._busca = BuscaClaude(self)
        self._busca.pronto.connect(self._claude_chegou)
        self._busca.start()

    def _buscar_correio(self):
        if self._busca_correio is not None and self._busca_correio.isRunning():
            return
        self._busca_correio = BuscaCorreio(self)
        self._busca_correio.pronto.connect(self._correio_chegou)
        self._busca_correio.start()

    def _correio_chegou(self, d):
        self.correio = d
        self.atualizar()

    def _claude_chegou(self, d):
        self.claude_uso = d
        self.atualizar()

    def closeEvent_threads(self):
        if self._busca is not None and self._busca.isRunning():
            self._busca.wait(3000)

    # ------------------------------------------------------------ conteúdo
    def _limpar(self):
        while self.corpo_lay.count():
            it = self.corpo_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def _rotulo(self, txt, nome=None, wrap=True):
        lb = QLabel(txt, objectName=nome or "")
        lb.setWordWrap(wrap)
        lb.setTextFormat(Qt.TextFormat.RichText)
        self.corpo_lay.addWidget(lb)
        return lb

    def atualizar(self):
        d = coletar()
        n_pend = sum(len(v) for v in d["pend"].values())
        try:
            import economia
            eco = economia.resumo()
        except Exception:  # noqa: BLE001
            eco = []
        form, cad_g = _formacao()
        co = self.correio or {}
        agora = dt.datetime.now()
        ult_h = [m for m in co.get("msgs", []) if (_iso_local(m["quando"]) or dt.datetime.min) > agora - dt.timedelta(hours=1)]
        linha_form = ("<span style='color:#8ab4f8'>🔀 <b>Formação B</b> · Google em "
                      + ", ".join(NOME.get(c, c) for c in sorted(cad_g)) + "</span>" if form == "B"
                      else "<span style='color:#a9a9c2'>🔀 Formação A (original)</span>")
        self.resumo.setText(
            f"v{d['versao']} · {d['n']} ferramentas · 📨 {n_pend} pedido(s) no ar<br>{linha_form}<br>"
            f"📬 correio: {len(ult_h)} msg na última hora"
            + (f" · <span style='color:#ff5c5c'>servidor fora do ar</span>" if co.get("erro") else "")
            + _quadro() + _arquivista() + (f"<br>🔥 hoje: {_corta(d['tend'], 70)}" if d["tend"] else "")
            )
        self.resumo.setTextFormat(Qt.TextFormat.RichText)
        self.rolagem.setVisible(not self.recolhida)
        if self.recolhida:
            self.setFixedHeight(self.caixa.sizeHint().height())
            return
        self.setMinimumHeight(200)
        self.setMaximumHeight(16777215)
        self.resize(self.width(), int(self.cfg.get("altura", 640)))
        self._limpar()

        if not SO_MAPA:
            self._rotulo("⚠️ PRA VOCÊ SABER", "secao")
            lista = alertas(d, self.correio, cad_g)
            if lista:
                for nv, txt in lista:
                    self._rotulo(txt, f"alerta{nv}")
            else:
                self._rotulo("✅ tudo certo — nada precisa de você agora", "alerta0")
            self._rotulo("MAPA DA FÁBRICA", "secao")
        try:
            import economia
            nivel_de = economia.nivel_do_agente
        except Exception:  # noqa: BLE001
            def nivel_de(_a):
                return "normal"
        nos, arestas = [], {}
        for chave, nome, emoji, papel in AGENTES:
            a = d["painel"].get(chave, {})
            t = _quando(a.get("atualizado", ""))
            minutos = (dt.datetime.now() - t).total_seconds() / 60 if t else 9999
            if nivel_de(chave) == "critico":
                est = "sem_cota"
            elif (a.get("fazendo") and minutos < 30) or minutos < 10:
                est = "trab"
            elif minutos < 180:
                est = "parado"
            else:
                est = "off"
            nl = (co.get("nao_lidas") or {}).get(chave, 0)
            dica = (f"<b>{emoji} {nome}</b>{' (Google)' if chave in cad_g else ''}<br>{papel}<br>"
                    f"{_corta(a.get('fazendo') or 'parado', 120)}<br>📬 {nl} não lida(s) · {_ha(t)}")
            nos.append((chave, nome, emoji, est, chave in cad_g, dica))
        for m in ult_h:
            k = tuple(sorted((m["de"], m["para"])))
            if k[0] != k[1]:
                arestas[k] = arestas.get(k, 0) + 1
        mapa = Mapa()
        mapa.dados(nos, arestas)
        self.corpo_lay.addWidget(mapa)
        if SO_MAPA:  # só o desenho: o resto mora no Claude Code Monitor
            self.resumo.setVisible(False)
            self.rolagem.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.titulo.setText(f"🗺️ Mapa da fábrica  <span style='color:#9a9ab0;font-size:9pt'>"
                                f"{dt.datetime.now():%H:%M} · 2 cliques no mapa = correio</span>")
            self.titulo.setTextFormat(Qt.TextFormat.RichText)
            self.setFixedHeight(mapa.height() + 62)
            return

        self._rotulo("AGORA", "secao")
        for chave, nome, emoji, papel in AGENTES:
            a = d["painel"].get(chave, {})
            t = _quando(a.get("atualizado", ""))
            minutos = (dt.datetime.now() - t).total_seconds() / 60 if t else 9999
            bola = "🟢" if minutos < 20 else ("🟡" if minutos < 90 else "⚪")
            fazendo = a.get("fazendo") or ""
            estado = (f"<b>fazendo:</b> {_corta(fazendo, 110)}" if fazendo
                      else "<span style='color:#9a9ab0'>parado / esperando</span>")
            if a.get("bloqueado"):
                estado += f"<br>⛔ <b>travado:</b> {_corta(a['bloqueado'], 90)}"
            prox = a.get("proximo") or ""
            pedidos = d["pend"].get(chave, [])
            extra = (f"<br>📨 {len(pedidos)} pedido(s) de {', '.join(sorted({NOME.get(p, p) for p in pedidos}))}"
                     if pedidos else "")
            selo = " <b style='color:#4285f4'>[Google]</b>" if chave in cad_g else ""
            nl = (co.get("nao_lidas") or {}).get(chave, 0)
            selo += f" <span style='color:#f5c542'>📬{nl}</span>" if nl else ""
            caixa = QLabel(
                f"{bola} {emoji} <b>{nome}</b>{selo} <span style='color:#9a9ab0'>· {papel} · {_ha(t)}</span><br>"
                f"{estado}" + (f"<br><span style='color:#9a9ab0'>depois:</span> {_corta(prox, 90)}" if prox else "")
                + extra, objectName="agente")
            caixa.setWordWrap(True)
            caixa.setTextFormat(Qt.TextFormat.RichText)
            faixa = {"🟢": "#3ddc84", "🟡": "#f5c542"}.get(bola, "#6b6b80")
            caixa.setStyleSheet(f"#agente {{ border-left: 4px solid {faixa}; }}")
            self.corpo_lay.addWidget(caixa)

        self._rotulo("CONVERSAS (correio)", "secao")
        if co.get("msgs"):
            for m in co["msgs"][:6]:
                t = _iso_local(m["quando"])
                lb = self._rotulo(f"<span style='color:#9a9ab0'>{t.strftime('%H:%M') if t else '--:--'}</span> "
                                  f"<b>{m['de']}</b> → <b>{m['para']}</b>: "
                                  f"<a style='color:#b9a8ff;text-decoration:none' href='{WEB_CORREIO}'>"
                                  f"{_corta(m['assunto'], 70)}</a>")
                lb.setOpenExternalLinks(True)
        else:
            self._rotulo("<span style='color:#9a9ab0'>" + ("lendo o correio…" if self.correio is None
                                                         else "nenhuma mensagem ainda") + "</span>")

        self._rotulo("GASTOS", "secao")
        cu = self.claude_uso
        if cu and not cu.get("erro"):
            fh, sd = cu.get("five_hour") or {}, cu.get("seven_day") or {}
            self._rotulo(f"🧑‍🍳 <b>Claude</b> (plano) · 5h {_barra(fh.get('utilization'))} "
                         f"<span style='color:#9a9ab0'>{_falta(fh.get('resets_at') or '')}</span><br>"
                         f"&nbsp;&nbsp;&nbsp;&nbsp;semana {_barra(sd.get('utilization'))} "
                         f"<span style='color:#9a9ab0'>{_falta(sd.get('resets_at') or '')}</span>")
        else:
            self._rotulo("🧑‍🍳 <b>Claude</b>: <span style='color:#9a9ab0'>"
                         + ("lendo…" if cu is None else "não consegui ler o uso agora") + "</span>")
        g = gasto_grok()
        if g and g["pct"] is not None:
            self._rotulo(f"🔌 <b>SuperGrok</b> (Cocaino + Grok CLI + Cursor) · semana {_barra(g['pct'])} "
                         f"<span style='color:#9a9ab0'>{_falta(g['fim'] or '')}</span><br>"
                         f"&nbsp;&nbsp;&nbsp;&nbsp;lido às {g.get('lido') or '?'} (atualiza quando o Grok CLI consulta) · Grok CLI hoje: "
                         f"{g['tokens'] / 1000:,.0f} mil tokens em {g['chamadas']} chamadas"
                         .replace(",", "."))
        try:
            with open(os.path.join(HERE, "cotas_manuais.json"), encoding="utf-8") as f:
                ag = json.load(f).get("antigravity", {})
            self._rotulo(f"🧠 <b>Google</b> (Antigravity + Gemini{' + formação B' if cad_g else ''}, {ag.get('plano', '?')}) · Gemini semana {_barra(ag.get('gemini_semana_usado'))}"
                         f" · 5h {ag.get('gemini_5h_usado', '?')}%<br>&nbsp;&nbsp;&nbsp;&nbsp;Claude/GPT e Argon: "
                         f"{'esgotados' if ag.get('claude_gpt_semana_usado', 0) >= 100 else 'ok'} · "
                         f"<span style='color:#9a9ab0'>5h lida sozinha {ag.get('lido_auto', '—')} · semana: print de {ag.get('lido', '?')}</span>")
        except (OSError, ValueError):
            self._rotulo("<span style='color:#9a9ab0'>🧠 Antigravity: sem leitura (app → Models & Usage)</span>")

        if d["evol"]:
            self._rotulo("EVOLUÇÃO", "secao")
            primeira = d["evol"][-1]
            self._rotulo(f"📈 <b>{primeira[2]}</b> ({primeira[1]}) → <b>{d['n']} ferramentas</b> hoje"
                         + (f" · <b>{d['barra']}</b> respondem na barra" if d["barra"] else "")
                         + f" · {len(d['evol'])} versões")
            for ver, data, _n, oque in d["evol"][:5]:
                atual = ver.lstrip("v") == d["versao"]
                cor = "#7c5cff" if atual else "#e6e6f0"
                self._rotulo(f"<b style='color:{cor}'>{ver}</b> <span style='color:#9a9ab0'>{data}</span> "
                             f"{_corta(oque, 95)}" + (" <span style='color:#7c5cff'>← agora</span>" if atual else ""))

        self._rotulo("JÁ FEITO", "secao")
        for t, chave, txt in d["feitos"]:
            hora = t.strftime("%H:%M") if t else "--:--"
            self._rotulo(f"<span style='color:#9a9ab0'>{hora}</span> <b>{NOME.get(chave, chave)}</b>: "
                         f"{_corta(txt, 120)}")
        self.corpo_lay.addStretch(1)
        self.titulo.setText(f"🏭 Fábrica da Caixa  <span style='color:#9a9ab0;font-size:9pt'>"
                            f"{dt.datetime.now():%H:%M}</span>")
        self.titulo.setTextFormat(Qt.TextFormat.RichText)

    # ------------------------------------------------------------ interação
    def _salvar(self):
        self.cfg.update({"x": self.x(), "y": self.y(), "recolhida": self.recolhida,
                         "opacidade": round(self.windowOpacity(), 2)})
        if not self.recolhida:
            self.cfg["altura"] = self.height()
        try:
            with open(CFG, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f)
        except OSError:
            pass

    def mousePressEvent(self, e):  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self._arrasto = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):  # noqa: N802
        if self._arrasto is not None and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._arrasto)

    def mouseReleaseEvent(self, e):  # noqa: N802
        if self._arrasto is not None:
            self._arrasto = None
            self._salvar()

    def mouseDoubleClickEvent(self, e):  # noqa: N802
        self.alternar()

    def alternar(self):
        if not self.recolhida:
            self.cfg["altura"] = self.height()
        self.recolhida = not self.recolhida
        self.atualizar()
        self._salvar()

    def contextMenuEvent(self, e):  # noqa: N802
        m = QMenu(self)
        m.addAction("Expandir" if self.recolhida else "Recolher", self.alternar)
        m.addAction("Atualizar agora", self.atualizar)
        sub = m.addMenu("Transparência")
        for p in (100, 90, 80, 70, 60):
            a = QAction(f"{p}%", sub)
            a.triggered.connect(lambda _c=False, v=p: (self.setWindowOpacity(v / 100), self._salvar()))
            sub.addAction(a)
        m.addSeparator()
        m.addAction("Fechar o painel", self.close)
        m.exec(e.globalPos())

    def closeEvent(self, e):  # noqa: N802
        self.closeEvent_threads()
        self._salvar()
        super().closeEvent(e)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setQuitOnLastWindowClosed(True)
    n = Nota()
    n.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
