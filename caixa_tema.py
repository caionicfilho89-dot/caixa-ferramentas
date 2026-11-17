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
# Valores da barra: mono SEM letter-spacing (Consolas Bold + tracking → "1 .030 , 30").
FONTE_VALOR = "Cascadia Mono"


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


def fonte_resposta_barra(tamanho: int = 16) -> QFont:
    """Fonte da resposta na barra — Consolas (estilo Finanças) com '.' e ',' perfeitamente nítidos."""
    f = QFont()
    f.setFamilies(["Consolas", "Segoe UI", FONTE_MONO, "Courier New"])
    f.setPointSize(max(10, int(tamanho)))
    f.setWeight(QFont.Weight.Bold)
    f.setStyleHint(QFont.StyleHint.TypeWriter)
    f.setStyleStrategy(
        QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.NoFontMerging
    )
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.0)
    f.setKerning(True)
    return f


def normalizar_valor_barra(texto: str) -> str:
    """Tira espaços estranhos ao redor de '.' e ',' em números (Q10)."""
    import re
    s = str(texto or "")
    # "1 .030 , 30" → "1.030,30"
    s = re.sub(r"(\d)\s+([.,])\s*(\d)", r"\1\2\3", s)
    s = re.sub(r"(\d)\s+([.,])\s*(\d)", r"\1\2\3", s)  # 2ª pass (vários)
    return s


def fonte_corpo() -> QFont:
    return fonte(10, QFont.Weight.Normal)


def fonte_mudo() -> QFont:
    return fonte(9, QFont.Weight.Normal)


def qss_app() -> str:
    """QSS global da cara nova (Hoje + barra + grade)."""
    return f"""
/* Fundo só em janelas/containers — NÃO em todo QWidget (vira faixa por label). */
QMainWindow, QDialog, #telaHoje, #barraBusca, QWidget#janelaCaixa {{
    background: {BG};
    color: {TEXTO};
    font: 10pt '{FONTE}';
}}
QWidget {{
    color: {TEXTO};
    font: 10pt '{FONTE}';
}}
QLabel {{
    background: transparent;
    border: 0;
}}
QFrame {{
    background: transparent;
}}
QScrollArea {{
    border: 0;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: {BG_SOFT};
    width: 12px;
    margin: 0;
    border: 0;
}}
QScrollBar::handle:vertical {{
    background: #3a4460;
    border-radius: 6px;
    min-height: 32px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: transparent;
    border: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: {BG_SOFT};
    border: 0;
}}
QScrollBar:horizontal {{
    background: {BG_SOFT};
    height: 12px;
    margin: 0;
    border: 0;
}}
QScrollBar::handle:horizontal {{
    background: #3a4460;
    border-radius: 6px;
    min-width: 32px;
    margin: 2px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0; background: transparent; border: 0;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: {BG_SOFT}; border: 0;
}}

#tituloApp {{
    background: transparent;
    font: 800 22pt '{FONTE}';
    color: {TEXTO};
}}
#subtitulo {{
    background: transparent;
    color: {TEXTO_MUDO};
    font: 10pt '{FONTE}';
}}
#secao {{
    background: transparent;
    color: {TEXTO_MUDO};
    font: 700 10pt '{FONTE}';
    letter-spacing: 0.6px;
}}
#saudacao {{
    background: transparent;
    font: 700 18pt '{FONTE}';
    color: {TEXTO};
}}
#horaHoje {{
    background: transparent;
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
    background: transparent;
    font: 700 11pt '{FONTE}';
    color: {TEXTO};
}}
#respResposta {{
    background: transparent;
    font: 700 16pt 'Consolas', 'Segoe UI', '{FONTE_MONO}', monospace;
    color: {OK};
    padding: 2px 0 4px 0;
    letter-spacing: 0;
}}
#respDetalhe {{
    background: transparent;
    color: {TEXTO_SUAVE};
    font: 10pt '{FONTE}';
    padding: 0 0 2px 0;
}}
QPushButton#todasFerramentas {{
    background: #2a2740;
    color: #e7e9f0;
    border: 1px solid {ACCENT};
    border-radius: 10px;
    padding: 10px 16px;
    font: 700 10pt '{FONTE}';
}}
QPushButton#todasFerramentas:hover {{
    background: {ACCENT};
    color: #ffffff;
}}
#hintBusca {{
    background: transparent;
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
    background: #2a2740;
    border: 1px solid {ACCENT};
    border-radius: 12px;
    padding: 12px 20px;
    min-height: 36px;
    font: 700 11pt '{FONTE}';
    color: #e7e9f0;
}}
QPushButton#acaoCartao:hover {{
    border: 1px solid {ACCENT_HOVER};
    background: {ACCENT};
    color: #ffffff;
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
#cartaoPequeno[flash="true"] {{
    background: #2a2148;
    border: 2px solid {ACCENT};
}}
#cartaoGrande QLabel, #cartaoPequeno QLabel {{
    background: transparent;
}}
QPushButton#chipUltima {{
    background: #2a2148;
    color: #e7e9f0;
    border: 1px solid {ACCENT};
    border-radius: 999px;
    padding: 4px 12px;
    font: 700 9pt '{FONTE}';
}}
QPushButton#chipUltima:hover {{
    background: {ACCENT};
    color: #ffffff;
}}
QPushButton#chipUltima[flash="true"] {{
    background: {ACCENT};
    color: #ffffff;
}}
#emojiGrande {{
    background: transparent;
    font: 28pt '{FONTE_EMOJI}';
}}
#emojiPequeno {{
    background: transparent;
    font: 18pt '{FONTE_EMOJI}';
}}
#valorGrande {{
    background: transparent;
    font: 700 18pt '{FONTE}';
    color: {TEXTO};
}}
#valorPequeno {{
    background: transparent;
    font: 700 13pt '{FONTE}';
    color: {TEXTO};
}}
#tituloCartao {{
    background: transparent;
    font: 700 11pt '{FONTE}';
    color: {TEXTO_SUAVE};
}}
#detalheCartao {{
    background: transparent;
    color: {TEXTO_MUDO};
    font: 9pt '{FONTE}';
}}
#estadoVazio {{
    background: transparent;
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

/* ---- Grade "Todas" (CRITICA F7 + T10: legível em 1366 e 4K@300%) ---- */
#card {{
    background: #243044;
    border: 1px solid #5a6788;
    border-radius: 16px;
}}
#card:hover {{
    background: #2c3750;
    border: 1px solid {ACCENT};
}}
#card QLabel {{
    background: transparent;
}}
#name {{
    background: transparent;
    font: 700 11pt '{FONTE}';
    color: #f2f4fa;
}}
#desc {{
    background: transparent;
    color: #d0d5e4;
    font: 9pt '{FONTE}';
}}
#emoji, #badge {{
    background: transparent;
    font: 20pt '{FONTE_EMOJI}';
}}
#catlbl {{
    background: transparent;
    font: 8pt '{FONTE}';
    color: {TEXTO_MUDO};
}}
#star {{
    background: transparent;
    color: {AVISO};
    font: 12pt '{FONTE}';
}}
#missing {{
    background: transparent;
    color: {ERRO};
    font: 9pt '{FONTE}';
}}
#title {{
    background: transparent;
    font: 800 22pt '{FONTE}';
    color: {TEXTO};
}}
#sub {{
    background: transparent;
    color: {TEXTO_MUDO};
}}
#section {{
    background: transparent;
    color: {TEXTO_MUDO};
    font: 700 10pt '{FONTE}';
}}
#hero {{
    background: transparent;
    color: {OK};
    font: 600 10pt '{FONTE}';
}}
#side {{
    background: {BG_ELEV};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 6px;
    color: {TEXTO};
    outline: none;
}}
#side::item {{
    padding: 9px 12px;
    border-radius: 9px;
    color: {TEXTO_SUAVE};
    margin: 1px 0;
}}
#side::item:hover {{
    background: {BG_HOVER};
    color: {TEXTO};
}}
/* T28: selecionado com accent — legível em 100% e 300% DPI */
#side::item:selected {{
    background: rgba(124, 92, 255, 0.28);
    color: #f2f4fa;
    border: 1px solid {ACCENT};
    font-weight: 600;
}}
#side::item:selected:hover {{
    background: rgba(124, 92, 255, 0.36);
    color: #ffffff;
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
        # altura de verdade — nunca esmagar numa faixa de 60 px (CRITICA F3 / F7 / T09)
        # T26/T314: piso ajustado pra caber valor + detalhe + botão Anotar/Assistir sem overflow em 1366x768
        self.setMinimumSize(250, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

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
        self.valor.setMinimumHeight(28)
        self.valor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        corpo.addWidget(self.valor)

        self.detalhe = QLabel("")
        self.detalhe.setObjectName("detalheCartao")
        self.detalhe.setWordWrap(True)
        self.detalhe.setMaximumHeight(44)  # no máx. ~2 linhas — não empurra o botão pra fora
        corpo.addWidget(self.detalhe)

        corpo.addStretch(1)

        # T26: rodapé com altura mínima própria — o stretch não pode esmagar o botão
        rodape = QWidget()
        rodape.setObjectName("rodapeCartao")
        rodape.setMinimumHeight(48)
        rodape.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        rod_lay = QHBoxLayout(rodape)
        rod_lay.setContentsMargins(0, 2, 0, 0)
        rod_lay.setSpacing(0)
        self.btn = QPushButton("Abrir")
        self.btn.setObjectName("acaoCartao")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setMinimumHeight(40)
        self.btn.setMinimumWidth(140)
        self.btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.btn.clicked.connect(self._emitir_acao)
        rod_lay.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignLeft)
        rod_lay.addStretch(1)
        corpo.addWidget(rodape, 0)

        root.addLayout(corpo, 1)
        # garante que o fundo do card (não dos labels) pinte pelo QSS
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def preencher(self, dados: dict, cor: str | None = None) -> None:
        self._dados = dict(dados or {})
        self.emoji.setText(str(self._dados.get("emoji") or "📦"))
        self.titulo.setText(str(self._dados.get("titulo") or "—"))
        self.valor.setText(str(self._dados.get("valor") or "—"))
        self.detalhe.setText(str(self._dados.get("detalhe") or ""))
        # labels sem faixa própria (bug visual 1.5.3)
        for lbl in (self.emoji, self.titulo, self.valor, self.detalhe):
            lbl.setAutoFillBackground(False)
            lbl.setStyleSheet("background: transparent; border: 0;")
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
        for lbl in (self.emoji, self.titulo, self.valor, self.detalhe):
            lbl.setAutoFillBackground(False)
            lbl.setStyleSheet("background: transparent; border: 0;")
        cid = str(self._dados.get("id") or "")
        self._aplicar_faixa(cor or cor_categoria(cid) or ACCENT)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def destacar(self, ms: int = 450) -> None:
        """T19: flash visual quando a tecla 1–8 aciona o cartão."""
        self.setProperty("flash", True)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

        def _off():
            try:
                self.setProperty("flash", False)
                self.style().unpolish(self)
                self.style().polish(self)
                self.update()
            except RuntimeError:
                pass

        QTimer.singleShot(max(80, int(ms)), _off)


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


def dpr_de_widget(widget: QWidget | None = None) -> float:
    """Lê o devicePixelRatio do screen do widget (fallback 1.0)."""
    try:
        if widget is not None:
            scr = widget.screen()
            if scr is not None:
                return float(scr.devicePixelRatio())
        from PyQt6.QtGui import QGuiApplication
        scr = QGuiApplication.primaryScreen()
        if scr is not None:
            return float(scr.devicePixelRatio())
    except Exception:
        pass
    return 1.0


def largura_logica(largura_px: int, dpr: float = 1.0) -> int:
    """Converte largura física → lógica (4K @ 300% ≈ 1280 lógica)."""
    escala = float(dpr) if float(dpr) > 0 else 1.0
    return max(1, int(round(int(largura_px or 0) / escala)))


def colunas_para_largura(largura: int, dpr: float = 1.0) -> int:
    """Grade responsiva: usa largura lógica (DPI). 1366→2; 4K@100%→4; 4K@300%→2."""
    w = largura_logica(largura, dpr) if float(dpr or 1.0) > 1.0 else int(largura or 0)
    if w >= LARGURA_4K:
        return 4
    if w >= 1800:
        return 3
    if w >= 900:
        return 2
    return 1


def margens_para_largura(largura: int, dpr: float = 1.0) -> tuple[int, int, int, int]:
    """Margens da tela Hoje conforme o monitor (respeita DPI)."""
    w = largura_logica(largura, dpr) if float(dpr or 1.0) > 1.0 else int(largura or 0)
    if w >= LARGURA_4K:
        return (48, 28, 48, 28)
    if w <= LARGURA_COMPACTA:
        return (16, 12, 16, 12)
    return (20, 16, 20, 16)


def escala_tipografia(largura: int, dpr: float = 1.0) -> float:
    """Fator de escala leve. Em DPI alto (>=2.5) não infla fonte (o SO já escala)."""
    dpr_f = float(dpr or 1.0)
    if dpr_f >= 2.5:
        return 1.0
    # com DPR intermediário, usa largura lógica
    w = largura_logica(largura, dpr_f) if dpr_f > 1.0 else int(largura or 1366)
    if w >= LARGURA_4K:
        return 1.25
    if w >= 1920:
        return 1.1
    if w <= 1280:
        return 0.95
    return 1.0


def tamanho_card_grade(dpr: float = 1.0) -> tuple[int, int, int]:
    """(CARD_W, CARD_H, GAP) sugeridos pra grade Todas — lógico, não físico."""
    # em DPI alto o Qt já escala; manter tamanho lógico estável
    if float(dpr or 1.0) >= 2.5:
        return (260, 112, 10)
    if float(dpr or 1.0) >= 1.5:
        return (268, 114, 11)
    return (272, 116, 12)


def layout_grade(largura: int, dpr: float = 1.0) -> dict:
    """T20: pacote único pra reflow da grade Todas / Hoje ao mudar DPI."""
    dpr_f = float(dpr) if float(dpr or 0) > 0 else 1.0
    w_log = largura_logica(largura, dpr_f) if dpr_f > 1.0 else int(largura or 0)
    cw, ch, gap = tamanho_card_grade(dpr_f)
    return {
        "dpr": dpr_f,
        "largura_logica": w_log,
        "colunas": colunas_para_largura(largura, dpr_f),
        "margens": margens_para_largura(largura, dpr_f),
        "escala": escala_tipografia(largura, dpr_f),
        "card_w": cw,
        "card_h": ch,
        "gap": gap,
    }


def contraste_grade_todas_ok(qss: str | None = None) -> bool:
    """True se o QSS da grade eleva o cartão acima do fundo (não preto-no-preto)."""
    texto = qss if qss is not None else qss_app()
    # cartão precisa ser mais claro que o BG base
    return (
        "#243044" in texto
        and "#5a6788" in texto
        and "#f2f4fa" in texto
        and "#card" in texto
    )


class ObservadorDpi(QWidget):
    """T20: observa troca de tela/DPI e emite layout novo.

    Uso (Grok CLI / caixa.pyw):
        obs = ObservadorDpi(janela)
        obs.dpi_mudou.connect(lambda dpr, lay: janela.aplicar_layout_grade(lay))
        obs.forcar()  # aplica já na abertura
    """

    dpi_mudou = pyqtSignal(float, dict)

    def __init__(self, host: QWidget, parent=None):
        super().__init__(parent or host)
        self._host = host
        self._dpr = -1.0
        self._assinatura: tuple | None = None
        self.hide()
        host.installEventFilter(self)
        # Qt 6: muda de monitor / escala
        try:
            from PyQt6.QtGui import QGuiApplication
            app = QGuiApplication.instance()
            if app is not None and hasattr(app, "screenAdded"):
                app.screenAdded.connect(lambda *_: self.forcar())
        except Exception:
            pass

    def eventFilter(self, obj, event):  # noqa: N802
        from PyQt6.QtCore import QEvent
        tipos = {QEvent.Type.Show, QEvent.Type.Resize, QEvent.Type.WindowActivate}
        # ScreenChangeInternal existe em alguns builds do Qt6
        sci = getattr(QEvent.Type, "ScreenChangeInternal", None)
        if sci is not None:
            tipos.add(sci)
        if obj is self._host and event.type() in tipos:
            self._checar()
        return super().eventFilter(obj, event)

    def _checar(self) -> None:
        dpr = dpr_de_widget(self._host)
        w = max(1, int(self._host.width() or 1366))
        lay = layout_grade(w, dpr)
        assinatura = (round(dpr, 2), lay["colunas"], lay["card_w"], lay["escala"])
        if assinatura == self._assinatura:
            return
        self._dpr = dpr
        self._assinatura = assinatura
        self.dpi_mudou.emit(dpr, lay)

    def forcar(self) -> dict:
        self._assinatura = None
        self._checar()
        w = max(1, int(self._host.width() or 1366))
        return layout_grade(w, dpr_de_widget(self._host))


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
    "ObservadorDpi",
    "colunas_para_largura",
    "contraste_grade_todas_ok",
    "cor_categoria",
    "dpr_de_widget",
    "escala_tipografia",
    "largura_logica",
    "layout_grade",
    "tamanho_card_grade",
    "fonte",
    "fonte_corpo",
    "fonte_mudo",
    "fonte_resposta_barra",
    "fonte_secao",
    "fonte_titulo",
    "fonte_valor_grande",
    "fonte_valor_pequeno",
    "margens_para_largura",
    "normalizar_valor_barra",
    "qss_app",
]
