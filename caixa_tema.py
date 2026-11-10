"""Tema visual da Caixa — cara própria, não formulário genérico.

Paleta viva (base escura + accent + cor por categoria), tipografia e cartões
grande/pequeno usados pela tela Hoje e pela barra de busca.
"""
from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Breakpoints de layout (F4)
LARGURA_COMPACTA = 1366   # notebook clássico
LARGURA_4K = 2560         # a partir daqui: 3–4 colunas + tipografia maior

# ---- Cores base (contrato visual) ----
BG = "#11131a"
BG_ELEV = "#161a23"
BG_HOVER = "#1a1f2b"
BG_SOFT = "#0e1016"
BORDER = "#232a3b"
BORDER_FOCUS = "#7c5cff"
ACCENT = "#7c5cff"
ACCENT_HOVER = "#8f74ff"
TEXTO = "#e7e9f0"
TEXTO_MUDO = "#8a93a8"
TEXTO_SUAVE = "#c7cbd8"
OK = "#6ee7b7"
AVISO = "#ffd166"
ERRO = "#ff6b6b"
INFO = "#60a5fa"

# Cores por categoria (mesmas chaves da caixa.pyw)
CAT_CORES = {
    "💰 Finanças & Trabalho": "#ffd166",
    "🏠 Casa, Pet & Pessoal": "#6ee7b7",
    "🔬 Ciência & Engenharia": "#60a5fa",
    "🌐 Rede & Segurança": "#f87171",
    "💻 Dev & Dados": "#7c5cff",
    "🖼️ Imagem & Design": "#f472b6",
    "🎵 Áudio & Vídeo": "#fb923c",
    "✍️ Texto & Estudo": "#a3e635",
    "🎮 Jogos & Diversão": "#facc15",
    "🗂️ Arquivos & Sistema": "#94a3b8",
    "🧰 Outras": "#8a93a8",
    "hoje": "#7c5cff",
    "busca": "#79e0a8",
    "sistema": "#94a3b8",
    "disco": "#60a5fa",
    "downloads": "#fb923c",
    "prints": "#f472b6",
    "clipboard": "#a3e635",
    "vencendo": "#ffd166",
    "pudim": "#f87171",
}

FONTE = "Segoe UI"
FONTE_EMOJI = "Segoe UI Emoji"
FONTE_MONO = "Consolas"


def cor_categoria(nome: str) -> str:
    """Devolve a cor da categoria; fallback no accent."""
    if not nome:
        return ACCENT
    if nome in CAT_CORES:
        return CAT_CORES[nome]
    # tenta casar pelo início (emoji + nome parcial)
    for chave, cor in CAT_CORES.items():
        if nome in chave or chave in nome:
            return cor
    return ACCENT


def fonte(tamanho: int = 10, peso: int = QFont.Weight.Normal, mono: bool = False) -> QFont:
    fam = FONTE_MONO if mono else FONTE
    f = QFont(fam, tamanho)
    f.setWeight(peso)
    return f


def fonte_titulo() -> QFont:
    return fonte(22, QFont.Weight.ExtraBold)


def fonte_secao() -> QFont:
    return fonte(11, QFont.Weight.Bold)


def fonte_valor_grande() -> QFont:
    f = fonte(28, QFont.Weight.Bold)
    f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 98)
    return f


def fonte_valor_pequeno() -> QFont:
    return fonte(16, QFont.Weight.DemiBold)


def fonte_corpo() -> QFont:
    return fonte(10, QFont.Weight.Normal)


def fonte_mudo() -> QFont:
    return fonte(9, QFont.Weight.Normal)


def qss_app() -> str:
    """QSS global da cara nova (Hoje + barra + grade)."""
    return f"""
QWidget {{
    background: {BG};
    color: {TEXTO};
    font: 10pt '{FONTE}';
}}
QScrollArea {{ border: 0; background: transparent; }}
QScrollBar:vertical {{
    background: {BG_SOFT}; width: 10px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 5px; min-height: 28px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

#tituloApp {{
    font: 800 22pt '{FONTE}';
    color: {TEXTO};
}}
#subtitulo {{
    color: {TEXTO_MUDO};
    font: 10pt '{FONTE}';
}}
#secao {{
    color: {TEXTO_MUDO};
    font: 700 10pt '{FONTE}';
    letter-spacing: 0.6px;
}}
#saudacao {{
    font: 700 18pt '{FONTE}';
    color: {TEXTO};
}}
#horaHoje {{
    color: {TEXTO_MUDO};
    font: 10pt '{FONTE}';
}}

QLineEdit#campoBusca {{
    background: {BG_ELEV};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 12px 16px;
    font: 12pt '{FONTE}';
    selection-background-color: {ACCENT};
}}
QLineEdit#campoBusca:focus {{
    border: 1px solid {ACCENT};
    background: {BG_HOVER};
}}

#listaRespostas {{
    background: {BG_ELEV};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
#itemResposta {{
    background: transparent;
    border: 0;
    border-radius: 10px;
    padding: 8px 10px;
}}
#itemResposta[selecionado="true"] {{
    background: #2a2740;
}}
#respTitulo {{
    font: 700 11pt '{FONTE}';
    color: {TEXTO};
}}
#respResposta {{
    font: 800 16pt '{FONTE}';
    color: {OK};
    padding: 2px 0 4px 0;
}}
#respDetalhe {{
    color: {TEXTO_MUDO};
    font: 9pt '{FONTE}';
}}
#hintBusca {{
    color: {TEXTO_MUDO};
    font: 8pt '{FONTE}';
}}

QPushButton {{
    background: #222a38;
    border: 0;
    border-radius: 10px;
    padding: 8px 14px;
    color: {TEXTO};
}}
QPushButton:hover {{ background: #2d3550; }}
QPushButton:pressed {{ background: #1a1f2b; }}
QPushButton#go {{
    background: {ACCENT};
    color: #ffffff;
    font-weight: 600;
    padding: 10px 16px;
}}
QPushButton#go:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#acaoCartao {{
    background: #222a38;
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 8px 12px;
    font: 600 9pt '{FONTE}';
}}
QPushButton#acaoCartao:hover {{
    border: 1px solid {ACCENT};
    background: #2a2740;
    color: #c9b8ff;
}}
QPushButton#fantasma {{
    background: transparent;
    color: {TEXTO_MUDO};
    border: 1px solid {BORDER};
}}
QPushButton#fantasma:hover {{
    color: {TEXTO};
    border: 1px solid {ACCENT};
}}

#cartaoGrande, #cartaoPequeno {{
    background: {BG_ELEV};
    border: 1px solid {BORDER};
    border-radius: 18px;
}}
#cartaoGrande:hover, #cartaoPequeno:hover {{
    background: {BG_HOVER};
    border: 1px solid #3a4460;
}}
#emojiGrande {{
    font: 28pt '{FONTE_EMOJI}';
}}
#emojiPequeno {{
    font: 18pt '{FONTE_EMOJI}';
}}
#valorGrande {{
    font: 700 26pt '{FONTE}';
    color: {TEXTO};
}}
#valorPequeno {{
    font: 700 14pt '{FONTE}';
    color: {TEXTO};
}}
#tituloCartao {{
    font: 700 11pt '{FONTE}';
    color: {TEXTO_SUAVE};
}}
#detalheCartao {{
    color: {TEXTO_MUDO};
    font: 9pt '{FONTE}';
}}
#estadoVazio {{
    color: {TEXTO_MUDO};
    font: 11pt '{FONTE}';
}}
#pill {{
    background: #2a2740;
    color: #c9b8ff;
    border-radius: 999px;
    padding: 4px 10px;
    font: 600 8pt '{FONTE}';
}}
"""


class FaixaCor(QWidget):
    """Faixa vertical colorida à esquerda do cartão (identidade por categoria)."""

    def __init__(self, cor: str = ACCENT, parent=None):
        super().__init__(parent)
        self._cor = QColor(cor)
        self.setFixedWidth(5)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def set_cor(self, cor: str) -> None:
        self._cor = QColor(cor)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._cor)
        p.drawRoundedRect(0, 6, self.width(), max(0, self.height() - 12), 3, 3)
        p.end()


class CartaoBase(QFrame):
    """Base visual dos cartões — sem cara de formulário."""

    acao_clicada = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dados: dict = {}
        self._faixa: FaixaCor | None = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def dados(self) -> dict:
        return dict(self._dados)

    def _aplicar_faixa(self, cor: str) -> None:
        if self._faixa is not None:
            self._faixa.set_cor(cor)

    def _emitir_acao(self) -> None:
        acao = (self._dados or {}).get("acao") or {}
        if acao:
            self.acao_clicada.emit(dict(acao))


class CartaoGrande(CartaoBase):
    """Cartão vivo da tela Hoje: emoji, valor grande, detalhe e botão de ação."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cartaoGrande")
        self.setMinimumSize(280, 168)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._faixa = FaixaCor(ACCENT)
        root.addWidget(self._faixa)

        corpo = QVBoxLayout()
        corpo.setContentsMargins(16, 14, 16, 14)
        corpo.setSpacing(6)

        topo = QHBoxLayout()
        topo.setSpacing(10)
        self.emoji = QLabel("📦")
        self.emoji.setObjectName("emojiGrande")
        self.titulo = QLabel("—")
        self.titulo.setObjectName("tituloCartao")
        self.titulo.setWordWrap(True)
        topo.addWidget(self.emoji, 0, Qt.AlignmentFlag.AlignTop)
        topo.addWidget(self.titulo, 1, Qt.AlignmentFlag.AlignVCenter)
        corpo.addLayout(topo)

        self.valor = QLabel("—")
        self.valor.setObjectName("valorGrande")
        self.valor.setWordWrap(True)
        corpo.addWidget(self.valor)

        self.detalhe = QLabel("")
        self.detalhe.setObjectName("detalheCartao")
        self.detalhe.setWordWrap(True)
        corpo.addWidget(self.detalhe)

        corpo.addStretch(1)

        self.btn = QPushButton("Abrir")
        self.btn.setObjectName("acaoCartao")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(self._emitir_acao)
        corpo.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignLeft)

        root.addLayout(corpo, 1)

    def preencher(self, dados: dict, cor: str | None = None) -> None:
        self._dados = dict(dados or {})
        self.emoji.setText(str(self._dados.get("emoji") or "📦"))
        self.titulo.setText(str(self._dados.get("titulo") or "—"))
        self.valor.setText(str(self._dados.get("valor") or "—"))
        self.detalhe.setText(str(self._dados.get("detalhe") or ""))
        acao = self._dados.get("acao") or {}
        rotulo = acao.get("rotulo") or "Abrir"
        self.btn.setText(str(rotulo))
        self.btn.setVisible(bool(acao))
        cid = str(self._dados.get("id") or "")
        self._aplicar_faixa(cor or cor_categoria(cid) or ACCENT)


class CartaoPequeno(CartaoBase):
    """Cartão compacto (atalhos, favoritos, resultados laterais)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cartaoPequeno")
        self.setMinimumSize(200, 88)
        self.setMaximumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._faixa = FaixaCor(ACCENT)
        root.addWidget(self._faixa)

        corpo = QHBoxLayout()
        corpo.setContentsMargins(12, 10, 12, 10)
        corpo.setSpacing(10)

        self.emoji = QLabel("📦")
        self.emoji.setObjectName("emojiPequeno")
        corpo.addWidget(self.emoji, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(2)
        self.titulo = QLabel("—")
        self.titulo.setObjectName("tituloCartao")
        self.titulo.setWordWrap(True)
        self.valor = QLabel("—")
        self.valor.setObjectName("valorPequeno")
        self.valor.setWordWrap(True)
        self.detalhe = QLabel("")
        self.detalhe.setObjectName("detalheCartao")
        self.detalhe.setWordWrap(True)
        col.addWidget(self.titulo)
        col.addWidget(self.valor)
        col.addWidget(self.detalhe)
        corpo.addLayout(col, 1)

        root.addLayout(corpo, 1)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._emitir_acao()
        super().mouseReleaseEvent(event)

    def preencher(self, dados: dict, cor: str | None = None) -> None:
        self._dados = dict(dados or {})
        self.emoji.setText(str(self._dados.get("emoji") or "📦"))
        self.titulo.setText(str(self._dados.get("titulo") or "—"))
        self.valor.setText(str(self._dados.get("valor") or "—"))
        self.detalhe.setText(str(self._dados.get("detalhe") or ""))
        cid = str(self._dados.get("id") or "")
        self._aplicar_faixa(cor or cor_categoria(cid) or ACCENT)


class EstadoVazio(QWidget):
    """Estado vazio amigável (sem cartão inventado)."""

    def __init__(
        self,
        mensagem: str = "Nada por aqui agora.",
        emoji: str = "🌙",
        titulo: str = "",
        parent=None,
    ):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 40, 24, 40)
        lay.setSpacing(8)
        self._emoji = QLabel(emoji)
        self._emoji.setObjectName("emojiGrande")
        self._emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._emoji)
        self._titulo = QLabel(titulo or "Tudo quieto")
        self._titulo.setObjectName("saudacao")
        self._titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._titulo)
        self._lbl = QLabel(mensagem)
        self._lbl.setObjectName("estadoVazio")
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl.setWordWrap(True)
        lay.addWidget(self._lbl)

    def set_mensagem(self, texto: str) -> None:
        self._lbl.setText(texto)


class EstadoCarregando(QWidget):
    """Indicador leve de carregamento (sem travar a UI)."""

    def __init__(self, mensagem: str = "Atualizando…", parent=None):
        super().__init__(parent)
        self._ang = 0
        lay = QHBoxLayout(self)
        lay.setContentsMargins(28, 8, 12, 8)
        self._lbl = QLabel(mensagem)
        self._lbl.setObjectName("estadoVazio")
        lay.addWidget(self._lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        self.setFixedHeight(36)
        self._tick = QTimer(self)
        self._tick.setInterval(40)
        self._tick.timeout.connect(self.avancar)

    def set_mensagem(self, texto: str) -> None:
        self._lbl.setText(texto)

    def showEvent(self, event) -> None:  # noqa: N802
        self._tick.start()
        super().showEvent(event)

    def hideEvent(self, event) -> None:  # noqa: N802
        self._tick.stop()
        super().hideEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(ACCENT))
        pen.setWidth(2)
        p.setPen(pen)
        r = 10
        cx, cy = 14, self.height() // 2
        p.drawArc(cx - r, cy - r, r * 2, r * 2, self._ang * 16, 270 * 16)
        p.end()

    def avancar(self) -> None:
        self._ang = (self._ang + 18) % 360
        self.update()


def colunas_para_largura(largura: int) -> int:
    """Grade responsiva: 1 col no estreito, 2 no 1366, 3–4 no 4K."""
    w = int(largura or 0)
    if w >= LARGURA_4K:
        return 4
    if w >= 1800:
        return 3
    if w >= 900:
        return 2
    return 1


def margens_para_largura(largura: int) -> tuple[int, int, int, int]:
    """Margens da tela Hoje conforme o monitor."""
    w = int(largura or 0)
    if w >= LARGURA_4K:
        return (48, 28, 48, 28)
    if w <= LARGURA_COMPACTA:
        return (16, 12, 16, 12)
    return (20, 16, 20, 16)


def escala_tipografia(largura: int) -> float:
    """Fator de escala leve pra 4K (1.0 no 1366, até 1.25)."""
    w = int(largura or 1366)
    if w >= LARGURA_4K:
        return 1.25
    if w >= 1920:
        return 1.1
    if w <= 1280:
        return 0.95
    return 1.0


def animar_entrada(widget: QWidget, duracao_ms: int = 220, atraso_ms: int = 0) -> QPropertyAnimation:
    """Fade-in leve do widget (opacidade 0 → 1). Não bloqueia a UI."""
    efeito = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(efeito)
    efeito.setOpacity(0.0)
    anim = QPropertyAnimation(efeito, b"opacity", widget)
    anim.setDuration(max(1, int(duracao_ms)))
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    if atraso_ms > 0:
        QTimer.singleShot(int(atraso_ms), anim.start)
    else:
        anim.start()
    # guarda ref no widget pra GC não matar a animação
    widget._anim_entrada = anim  # type: ignore[attr-defined]
    return anim


def aplicar_tema(app_or_widget) -> None:
    """Aplica o QSS da cara nova num QApplication ou QWidget."""
    app_or_widget.setStyleSheet(qss_app())


__all__ = [
    "ACCENT",
    "AVISO",
    "BG",
    "BG_ELEV",
    "BORDER",
    "CAT_CORES",
    "CartaoGrande",
    "CartaoPequeno",
    "ERRO",
    "EstadoCarregando",
    "EstadoVazio",
    "FaixaCor",
    "INFO",
    "LARGURA_4K",
    "LARGURA_COMPACTA",
    "OK",
    "TEXTO",
    "TEXTO_MUDO",
    "animar_entrada",
    "aplicar_tema",
    "colunas_para_largura",
    "cor_categoria",
    "escala_tipografia",
    "fonte",
    "fonte_corpo",
    "fonte_mudo",
    "fonte_secao",
    "fonte_titulo",
    "fonte_valor_grande",
    "fonte_valor_pequeno",
    "margens_para_largura",
    "qss_app",
]
