"""Barra que responde tudo — campo + lista, setas/Enter/Esc, debounce 150 ms.

Chama respostas_core.responder(texto) e emite abrir_ferramenta(chave).
"""
from __future__ import annotations

import traceback
from typing import Callable

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import caixa_tema as tema

DEBOUNCE_MS = 150
PLACEHOLDER = "Pergunte qualquer coisa…  ex.: 20% de 350 · ipva de 60 mil em SP"


def _responder_padrao(texto: str) -> list[dict]:
    """Chama respostas_core.responder; se não existir, devolve []."""
    try:
        import respostas_core  # type: ignore
    except ImportError:
        return []
    try:
        out = respostas_core.responder(texto)
    except Exception:
        traceback.print_exc()
        return []
    if not isinstance(out, list):
        return []
    return [d for d in out if isinstance(d, dict)]


class ItemResposta(QFrame):
    """Uma linha de resposta: título, resposta em destaque, detalhe e abrir."""

    abrir = pyqtSignal(str)
    ativado = pyqtSignal(int)

    def __init__(self, indice: int, parent=None):
        super().__init__(parent)
        self.setObjectName("itemResposta")
        self._indice = indice
        self._chave = ""
        self.setProperty("selecionado", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(10)

        col = QVBoxLayout()
        col.setSpacing(2)
        self.lbl_titulo = QLabel("")
        self.lbl_titulo.setObjectName("respTitulo")
        self.lbl_resposta = QLabel("")
        self.lbl_resposta.setObjectName("respResposta")
        self.lbl_resposta.setWordWrap(False)  # resposta em UMA linha (RUMO)
        self.lbl_resposta.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.lbl_detalhe = QLabel("")
        self.lbl_detalhe.setObjectName("respDetalhe")
        self.lbl_detalhe.setWordWrap(True)
        col.addWidget(self.lbl_titulo)
        col.addWidget(self.lbl_resposta)
        col.addWidget(self.lbl_detalhe)
        root.addLayout(col, 1)

        self.btn = QPushButton("Abrir ferramenta")
        self.btn.setObjectName("acaoCartao")
        self.btn.clicked.connect(self._abrir)
        root.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignVCenter)

    def preencher(self, dados: dict) -> None:
        self.lbl_titulo.setText(str(dados.get("titulo") or ""))
        self.lbl_resposta.setText(str(dados.get("resposta") or ""))
        detalhe = str(dados.get("detalhe") or "")
        self.lbl_detalhe.setText(detalhe)
        self.lbl_detalhe.setVisible(bool(detalhe))
        self._chave = str(dados.get("chave_ferramenta") or "")
        self.btn.setVisible(bool(self._chave))
        conf = dados.get("confianca")
        if isinstance(conf, (int, float)) and conf < 0.45 and not dados.get("resposta"):
            # resultado de busca de reserva (só sugestão de ferramenta)
            self.btn.setText("Abrir")
        else:
            self.btn.setText("Abrir ferramenta")

    def set_selecionado(self, sim: bool) -> None:
        self.setProperty("selecionado", bool(sim))
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _abrir(self) -> None:
        if self._chave:
            self.abrir.emit(self._chave)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.ativado.emit(self._indice)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        self._abrir()
        super().mouseDoubleClickEvent(event)


class BarraBusca(QWidget):
    """Barra no topo: digita → responde na hora (debounce 150 ms).

    Sinais:
      abrir_ferramenta(str chave)
      fechou() — Esc com campo vazio / pediu fechar overlay
    """

    abrir_ferramenta = pyqtSignal(str)
    fechou = pyqtSignal()

    def __init__(
        self,
        responder: Callable[[str], list[dict]] | None = None,
        debounce_ms: int = DEBOUNCE_MS,
        parent=None,
    ):
        super().__init__(parent)
        self._responder = responder or _responder_padrao
        self._debounce_ms = max(0, int(debounce_ms))
        self._itens_dados: list[dict] = []
        self._widgets: list[ItemResposta] = []
        self._sel = -1
        self._ultima_consulta = ""

        self.setObjectName("barraBusca")
        tema.aplicar_tema(self)
        self._montar()

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(self._debounce_ms)
        self._timer.timeout.connect(self._consultar)

    def _montar(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self.campo = QLineEdit()
        self.campo.setObjectName("campoBusca")
        self.campo.setPlaceholderText(PLACEHOLDER)
        self.campo.setClearButtonEnabled(True)
        self.campo.textChanged.connect(self._on_texto)
        self.campo.installEventFilter(self)
        root.addWidget(self.campo)

        self.lista_frame = QFrame()
        self.lista_frame.setObjectName("listaRespostas")
        self.lista_frame.hide()
        lista_lay = QVBoxLayout(self.lista_frame)
        lista_lay.setContentsMargins(6, 6, 6, 6)
        lista_lay.setSpacing(4)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setMaximumHeight(360)

        self.lista_inner = QWidget()
        self.lista_layout = QVBoxLayout(self.lista_inner)
        self.lista_layout.setContentsMargins(0, 0, 0, 0)
        self.lista_layout.setSpacing(4)
        self.lista_layout.addStretch(1)
        self.scroll.setWidget(self.lista_inner)
        lista_lay.addWidget(self.scroll)

        self.lbl_vazio = QLabel("Nada encontrado. Tente outra frase ou abra pela grade.")
        self.lbl_vazio.setObjectName("estadoVazio")
        self.lbl_vazio.setWordWrap(True)
        self.lbl_vazio.hide()
        lista_lay.addWidget(self.lbl_vazio)

        root.addWidget(self.lista_frame)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if obj is self.campo and event.type() == event.Type.KeyPress:
            return self._tecla(event)
        return super().eventFilter(obj, event)

    def _tecla(self, event: QKeyEvent) -> bool:
        key = event.key()
        if key == Qt.Key.Key_Down:
            self._mover_sel(1)
            return True
        if key == Qt.Key.Key_Up:
            self._mover_sel(-1)
            return True
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._ativar_sel()
            return True
        if key == Qt.Key.Key_Escape:
            if self.campo.text():
                self.campo.clear()
            else:
                self.esconder_lista()
                self.fechou.emit()
            return True
        return False

    def _on_texto(self, _texto: str) -> None:
        texto = self.campo.text().strip()
        if not texto:
            self._timer.stop()
            self.mostrar_resultados([])
            return
        # feedback imediato enquanto o debounce não dispara
        self.lista_frame.show()
        self.scroll.hide()
        self.lbl_vazio.setText("Buscando…")
        self.lbl_vazio.show()
        if self._debounce_ms == 0:
            self._consultar()
        else:
            self._timer.start(self._debounce_ms)

    def _consultar(self) -> None:
        texto = self.campo.text().strip()
        self._ultima_consulta = texto
        if not texto:
            self.mostrar_resultados([])
            return
        try:
            resultados = self._responder(texto) or []
        except Exception:
            traceback.print_exc()
            resultados = []
        # se o usuário digitou mais enquanto respondia, ignora
        if self.campo.text().strip() != texto:
            return
        self.mostrar_resultados(list(resultados))

    def mostrar_resultados(self, resultados: list[dict]) -> None:
        """Atualiza a lista. Lista vazia com texto → estado vazio; sem texto → esconde."""
        self._limpar_itens()
        self._itens_dados = [d for d in (resultados or []) if isinstance(d, dict)]
        texto = self.campo.text().strip()

        if not texto:
            self.lista_frame.hide()
            self.lbl_vazio.hide()
            self._sel = -1
            return

        self.lista_frame.show()
        if not self._itens_dados:
            self.lbl_vazio.setText(
                "Nada encontrado. Tente outra frase ou abra pela grade."
            )
            self.lbl_vazio.show()
            self.scroll.hide()
            self._sel = -1
            return

        self.lbl_vazio.hide()
        self.scroll.show()
        for i, dados in enumerate(self._itens_dados):
            item = ItemResposta(i, self.lista_inner)
            item.preencher(dados)
            item.abrir.connect(self.abrir_ferramenta.emit)
            item.ativado.connect(self._selecionar)
            self.lista_layout.insertWidget(i, item)
            self._widgets.append(item)
        self._selecionar(0)

    def _limpar_itens(self) -> None:
        for w in self._widgets:
            self.lista_layout.removeWidget(w)
            w.deleteLater()
        self._widgets.clear()
        self._itens_dados.clear()

    def _selecionar(self, indice: int) -> None:
        if not self._widgets:
            self._sel = -1
            return
        indice = max(0, min(indice, len(self._widgets) - 1))
        self._sel = indice
        for i, w in enumerate(self._widgets):
            w.set_selecionado(i == indice)

    def _mover_sel(self, delta: int) -> None:
        if not self._widgets:
            return
        if self._sel < 0:
            self._selecionar(0)
            return
        self._selecionar(self._sel + delta)

    def _ativar_sel(self) -> None:
        if self._sel < 0 or self._sel >= len(self._itens_dados):
            # sem seleção: consulta imediata
            self._timer.stop()
            self._consultar()
            return
        chave = self._itens_dados[self._sel].get("chave_ferramenta")
        if chave:
            self.abrir_ferramenta.emit(str(chave))

    def esconder_lista(self) -> None:
        self.lista_frame.hide()
        self._sel = -1

    def focar(self) -> None:
        self.campo.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.campo.selectAll()

    def set_texto(self, texto: str) -> None:
        self.campo.setText(texto)

    def texto(self) -> str:
        return self.campo.text()

    def resultados(self) -> list[dict]:
        return list(self._itens_dados)

    def indice_selecionado(self) -> int:
        return self._sel

    def set_responder(self, responder: Callable[[str], list[dict]]) -> None:
        self._responder = responder

    def consultar_agora(self) -> None:
        """Força consulta sem debounce (útil em testes)."""
        self._timer.stop()
        self._consultar()

    def consultar_texto(self, texto: str) -> list[dict]:
        """API sem GUI: devolve as respostas de uma frase (pro Grok comparar as 60).

        Não depende de Win32 nem de mostrar a janela. Atualiza o campo/lista
        se a barra estiver montada, e sempre retorna a lista do contrato:
        [{"titulo","resposta","detalhe","chave_ferramenta","confianca"}, ...]
        """
        texto = (texto or "").strip()
        self.campo.blockSignals(True)
        self.campo.setText(texto)
        self.campo.blockSignals(False)
        if not texto:
            self.mostrar_resultados([])
            return []
        try:
            resultados = self._responder(texto) or []
        except Exception:
            traceback.print_exc()
            resultados = []
        if not isinstance(resultados, list):
            resultados = []
        limpos = [d for d in resultados if isinstance(d, dict)]
        self.mostrar_resultados(limpos)
        return list(limpos)

    def resposta_principal(self) -> dict | None:
        """Atalho: primeiro resultado da última consulta, ou None."""
        return self._itens_dados[0] if self._itens_dados else None
