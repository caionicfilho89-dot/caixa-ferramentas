"""Tela Hoje — o que importa no PC do Caio agora.

Recebe sensores_core.ler_tudo() e desenha cartões vivos com botão de ação.
Atualiza a cada 60 s numa QThread (nunca trava a janela).
Cartão sem dado real não aparece.
"""
from __future__ import annotations

import traceback
from datetime import datetime
from typing import Callable

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import caixa_tema as tema

INTERVALO_MS = 60_000
COLUNAS_PADRAO = 2

# 15 chaves que o Grok apontou em CRITICA.md (F2) — atalhos da Hoje
DESTAQUES_CRITICA = (
    ("💾", "faxina-disco", "Faxina de Disco"),
    ("📥", "organizador-downloads", "Organizador de Downloads"),
    ("🖼️", "print-anotador", "Print Anotador"),
    ("📋", "area-transferencia", "Área de Transferência"),
    ("🛡️", "controle-garantias", "Garantias"),
    ("💊", "controle-validade-remedios", "Validade de Remédios"),
    ("🔁", "controle-assinaturas", "Assinaturas"),
    ("🖥️", "info-pc", "Info do PC"),
    ("💵", "calculadora-troco", "Troco"),
    ("🚗", "calculadora-ipva", "IPVA"),
    ("🎨", "calculadora-rendimento-tinta", "Rendimento de Tinta"),
    ("📅", "dias-uteis-pagamento", "Dias Úteis"),
    ("💰", "financas", "Finanças"),
    ("📄", "kit-pdf", "Kit de PDF"),
    ("🔥", "calculadora-botijao-gas", "Botijão de Gás"),
)


def _ler_sensores_padrao() -> list[dict]:
    """Chama sensores_core.ler_tudo(); se ainda não existir, devolve []."""
    try:
        import sensores_core  # type: ignore
    except ImportError:
        return []
    try:
        dados = sensores_core.ler_tudo()
    except Exception:
        traceback.print_exc()
        return []
    if not isinstance(dados, list):
        return []
    return [d for d in dados if isinstance(d, dict) and d.get("valor")]


class _SensorWorker(QThread):
    """Lê sensores off-thread e emite a lista pronta."""

    pronto = pyqtSignal(list)
    falhou = pyqtSignal(str)

    def __init__(self, leitor: Callable[[], list[dict]], parent=None):
        super().__init__(parent)
        self._leitor = leitor

    def run(self) -> None:
        try:
            dados = self._leitor() or []
            if not isinstance(dados, list):
                dados = []
            limpos = [d for d in dados if isinstance(d, dict) and d.get("valor")]
            self.pronto.emit(limpos)
        except Exception as exc:
            self.falhou.emit(str(exc))


class TelaHoje(QWidget):
    """Primeira tela da Caixa: cartões vivos do PC.

    Sinais:
      abrir_ferramenta(str chave) — ação com chave_ferramenta
      executar_comando(str comando) — ação com comando (ex.: explorer)
      pediu_todas() — botão "Todas as ferramentas"
    """

    abrir_ferramenta = pyqtSignal(str)
    executar_comando = pyqtSignal(str)
    pediu_todas = pyqtSignal()

    def __init__(
        self,
        leitor: Callable[[], list[dict]] | None = None,
        intervalo_ms: int = INTERVALO_MS,
        parent=None,
    ):
        super().__init__(parent)
        self._leitor = leitor or _ler_sensores_padrao
        self._intervalo_ms = max(1_000, int(intervalo_ms))
        self._worker: _SensorWorker | None = None
        self._cartoes: list[tema.CartaoGrande] = []
        self._carregando = False

        self.setObjectName("telaHoje")
        # altura natural do conteúdo — a rolagem fica no QScrollArea do caixa.pyw
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._timer = None
        tema.aplicar_tema(self)
        self._montar()
        self._timer = self.startTimer(self._intervalo_ms)
        # primeira leitura já na criação (assíncrona)
        self.atualizar(forcar=True)

    def _montar(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(*tema.margens_para_largura(1366))
        root.setSpacing(12)
        self._root = root

        topo = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(2)
        self.lbl_saudacao = QLabel(self._saudacao())
        self.lbl_saudacao.setObjectName("saudacao")
        self.lbl_hora = QLabel(self._texto_hora())
        self.lbl_hora.setObjectName("horaHoje")
        col.addWidget(self.lbl_saudacao)
        col.addWidget(self.lbl_hora)
        topo.addLayout(col, 1)

        self.btn_todas = QPushButton("Todas as ferramentas")
        # contraste alto (CRITICA F3) — não mais "fantasma" apagado
        self.btn_todas.setObjectName("todasFerramentas")
        self.btn_todas.clicked.connect(self.pediu_todas.emit)
        topo.addWidget(self.btn_todas, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(topo)

        self.lbl_secao = QLabel("AGORA NO SEU PC")
        self.lbl_secao.setObjectName("secao")
        root.addWidget(self.lbl_secao)

        self.estado_carregando = tema.EstadoCarregando("Lendo sensores…")
        self.estado_carregando.hide()
        root.addWidget(self.estado_carregando)

        # Sem scroll interno: cartões com altura real; rolagem é do caixa.pyw.
        # Scroll aninhado esmagava os sensores numa faixa de ~60 px (CRITICA F3).
        self.area = QWidget()
        self.area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.grade = QGridLayout(self.area)
        self.grade.setContentsMargins(0, 0, 4, 0)
        self.grade.setHorizontalSpacing(14)
        self.grade.setVerticalSpacing(14)
        self.grade.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.addWidget(self.area, 0)

        # alias p/ testes antigos que olhavam self.scroll
        self.scroll = self.area

        self.estado_vazio = tema.EstadoVazio(
            "Nada urgente agora. Quando o disco encher, Downloads bagunçar "
            "ou algo vencer, aparece aqui.",
            emoji="✨",
            titulo="Tudo em ordem",
        )
        self.estado_vazio.hide()
        root.addWidget(self.estado_vazio)

        self.lbl_atalhos = QLabel("ATALHOS QUE FAZEM SENTIDO")
        self.lbl_atalhos.setObjectName("secao")
        root.addWidget(self.lbl_atalhos)

        self.grade_atalhos = QGridLayout()
        self.grade_atalhos.setHorizontalSpacing(10)
        self.grade_atalhos.setVerticalSpacing(10)
        root.addLayout(self.grade_atalhos)
        self._atalhos: list[tema.CartaoPequeno] = []
        self._montar_atalhos()

    def _montar_atalhos(self) -> None:
        while self.grade_atalhos.count():
            item = self.grade_atalhos.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._atalhos.clear()
        cols = min(5, max(2, self._colunas() + 1))
        for i, (emoji, chave, nome) in enumerate(DESTAQUES_CRITICA):
            card = tema.CartaoPequeno(self)
            card.preencher({
                "id": "hoje",
                "emoji": emoji,
                "titulo": nome,
                "valor": "Abrir",
                "detalhe": chave,
                "acao": {"rotulo": "Abrir", "chave_ferramenta": chave},
            }, cor=tema.ACCENT)
            card.acao_clicada.connect(self._on_acao)
            r, c = divmod(i, cols)
            self.grade_atalhos.addWidget(card, r, c)
            self._atalhos.append(card)

    def _saudacao(self) -> str:
        h = datetime.now().hour
        if h < 6:
            return "Boa madrugada"
        if h < 12:
            return "Bom dia"
        if h < 18:
            return "Boa tarde"
        return "Boa noite"

    def _texto_hora(self) -> str:
        agora = datetime.now()
        dias = (
            "segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo",
        )
        return f"{dias[agora.weekday()]}, {agora.strftime('%d/%m · %H:%M')}"

    def timerEvent(self, event) -> None:  # noqa: N802
        if event.timerId() == self._timer:
            self.lbl_saudacao.setText(self._saudacao())
            self.lbl_hora.setText(self._texto_hora())
            self.atualizar()
        super().timerEvent(event)

    def atualizar(self, forcar: bool = False) -> None:
        """Dispara leitura em thread. Ignora se já houver uma em andamento."""
        if self._carregando and not forcar:
            return
        if self._worker is not None and self._worker.isRunning():
            return
        self._carregando = True
        self.estado_carregando.show()
        self.estado_carregando.set_mensagem("Atualizando…")
        worker = _SensorWorker(self._leitor, self)
        worker.pronto.connect(self._on_sensores)
        worker.falhou.connect(self._on_falha)
        worker.finished.connect(self._on_worker_fim)
        self._worker = worker
        worker.start()

    def _on_worker_fim(self) -> None:
        self._carregando = False
        self.estado_carregando.hide()

    def _on_falha(self, msg: str) -> None:
        self.estado_carregando.set_mensagem(f"Falha ao ler sensores: {msg}")
        # mantém cartões antigos; se não houver nenhum, mostra vazio
        if not self._cartoes:
            self._mostrar_vazio(True)

    def _on_sensores(self, itens: list) -> None:
        self.renderizar(list(itens or []))

    def renderizar(self, itens: list[dict]) -> None:
        """Desenha só cartões com valor real. Lista vazia → estado vazio."""
        while self.grade.count():
            item = self.grade.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._cartoes.clear()

        validos = [d for d in (itens or []) if isinstance(d, dict) and d.get("valor")]
        if not validos:
            self._mostrar_vazio(True)
            return

        self._mostrar_vazio(False)
        cols = self._colunas()
        for i, dados in enumerate(validos):
            card = tema.CartaoGrande(self.area)
            card.preencher(dados, cor=tema.cor_categoria(str(dados.get("id") or "")))
            card.acao_clicada.connect(self._on_acao)
            r, c = divmod(i, cols)
            self.grade.addWidget(card, r, c)
            self._cartoes.append(card)
            tema.animar_entrada(card, duracao_ms=200, atraso_ms=min(i * 40, 240))
        # estica colunas e trava altura mínima por linha (sizeHint deixa de achar 1 col)
        rows = (len(self._cartoes) + cols - 1) // cols
        card_h = max((c.minimumHeight() for c in self._cartoes), default=172)
        for c in range(cols):
            self.grade.setColumnStretch(c, 1)
        for r in range(rows):
            self.grade.setRowMinimumHeight(r, card_h)

    def _mostrar_vazio(self, vazio: bool) -> None:
        self.estado_vazio.setVisible(vazio)
        self.area.setVisible(not vazio)

    def altura_sensores(self, largura: int | None = None) -> int:
        """Altura da grade pela geometria (cols×rows), não pelo sizeHint 1-col."""
        n = len(self._cartoes)
        if n == 0 or self.area.isHidden():
            return 0
        w = int(largura) if largura else max(self.width(), 400)
        cols = max(1, tema.colunas_para_largura(w))
        rows = (n + cols - 1) // cols
        card_h = max((c.minimumHeight() for c in self._cartoes), default=172)
        spacing = max(0, int(self.grade.verticalSpacing()))
        return rows * card_h + max(0, rows - 1) * spacing

    def cabe_sensores_sem_rolar(self, largura: int, altura_viewport: int) -> bool:
        """True se topo + seção + 4 sensores cabem no viewport (sem rolar a grade)."""
        self.resize(max(400, int(largura)), max(200, int(altura_viewport)))
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        # se o resize reflowou a grade, garante que ainda há cartões medidos
        if not self._cartoes:
            return False
        topo_h = (
            self.lbl_saudacao.sizeHint().height()
            + self.lbl_hora.sizeHint().height()
            + 8
        )
        secao_h = self.lbl_secao.sizeHint().height() + 12
        sens_h = self.altura_sensores(largura)
        return (topo_h + secao_h + sens_h) <= int(altura_viewport)

    def _colunas(self) -> int:
        return tema.colunas_para_largura(max(self.width(), 400))

    def _aplicar_layout_largura(self) -> None:
        from PyQt6.QtGui import QFont

        m = tema.margens_para_largura(max(self.width(), 400))
        self._root.setContentsMargins(*m)
        escala = tema.escala_tipografia(self.width())
        self.lbl_saudacao.setFont(
            tema.fonte(max(14, int(18 * escala)), QFont.Weight.Bold)
        )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._aplicar_layout_largura()
        # reflow dos atalhos (sempre presentes)
        if self._atalhos:
            cols_at = min(5, max(2, self._colunas() + 1))
            cols_old = sum(
                1 for c in range(5) if self.grade_atalhos.itemAtPosition(0, c) is not None
            ) or 1
            if cols_at != cols_old:
                self._montar_atalhos()
        if not self._cartoes:
            return
        cols = self._colunas()
        cols_antigas = sum(
            1 for c in range(4) if self.grade.itemAtPosition(0, c) is not None
        ) or 1
        if cols != cols_antigas:
            self.renderizar([c.dados() for c in self._cartoes])

    def _on_acao(self, acao: dict) -> None:
        if not isinstance(acao, dict):
            return
        chave = acao.get("chave_ferramenta")
        if chave:
            self.abrir_ferramenta.emit(str(chave))
            return
        comando = acao.get("comando")
        if comando:
            self.executar_comando.emit(str(comando))

    def cartoes_visiveis(self) -> list[dict]:
        return [c.dados() for c in self._cartoes]

    def set_leitor(self, leitor: Callable[[], list[dict]]) -> None:
        self._leitor = leitor

    def closeEvent(self, event) -> None:  # noqa: N802
        self._parar()
        super().closeEvent(event)

    def _parar(self) -> None:
        if self._timer is not None:
            self.killTimer(self._timer)
            self._timer = None
        w = self._worker
        if w is not None and w.isRunning():
            w.wait(1500)
        self._worker = None
