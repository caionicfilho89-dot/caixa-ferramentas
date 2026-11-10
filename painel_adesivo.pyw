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

from PyQt6.QtCore import QPoint, Qt, QThread, QTimer, pyqtSignal
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
]
NOME = {a[0]: a[1] for a in AGENTES}

QSS = """
#nota { background: rgba(17,19,26,235); border: 1px solid #7c5cff; border-radius: 12px; }
QLabel { color: #e6e6f0; background: transparent; }
#titulo { font-weight: 700; color: #ffffff; }
#sub { color: #9a9ab0; }
#secao { color: #7c5cff; font-weight: 700; letter-spacing: 1px; }
#agente { background: rgba(255,255,255,10); border-radius: 8px; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QScrollBar:vertical { width: 6px; background: transparent; }
QScrollBar::handle:vertical { background: #3a3d55; border-radius: 3px; }
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
        m = re.search(r"\*\*Ideia:\*\*\s*\[([^\]]+)\]", t)
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
        self.setWindowOpacity(float(self.cfg.get("opacidade", 0.96)))
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
        self.resumo.setText(
            f"v{d['versao']} · {d['n']} ferramentas · 📨 {n_pend} pedido(s) no ar<br>"
            f"📬 carteiro: {d['carteiro']}" + _quadro() + _arquivista() + (f"<br>🔥 hoje: {_corta(d['tend'], 70)}" if d["tend"] else "")
            + "".join(f"<br><b>{_corta(l, 140)}</b>" for l in eco if not l.startswith("🟢")))
        self.resumo.setTextFormat(Qt.TextFormat.RichText)
        self.rolagem.setVisible(not self.recolhida)
        if self.recolhida:
            self.setFixedHeight(self.caixa.sizeHint().height())
            return
        self.setMinimumHeight(200)
        self.setMaximumHeight(16777215)
        self.resize(self.width(), int(self.cfg.get("altura", 640)))
        self._limpar()

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
            caixa = QLabel(
                f"{bola} {emoji} <b>{nome}</b> <span style='color:#9a9ab0'>· {papel} · {_ha(t)}</span><br>"
                f"{estado}" + (f"<br><span style='color:#9a9ab0'>depois:</span> {_corta(prox, 90)}" if prox else "")
                + extra, objectName="agente")
            caixa.setWordWrap(True)
            caixa.setTextFormat(Qt.TextFormat.RichText)
            caixa.setContentsMargins(8, 6, 8, 6)
            self.corpo_lay.addWidget(caixa)

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
            self._rotulo(f"🧠 <b>Antigravity</b> ({ag.get('plano', '?')}) · Gemini semana {_barra(ag.get('gemini_semana_usado'))}"
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
