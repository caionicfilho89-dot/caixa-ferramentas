"""Bandeja do sistema + atalho global Ctrl+Espaco.

Uso (Claude liga no caixa.pyw):
    from caixa_bandeja import registrar_atalho
    self._bandeja = registrar_atalho(self)

Fechar a janela = esconde pra bandeja. Ctrl+Espaco mostra/esconde.
Menu da bandeja: Mostrar / Sair.
"""
from __future__ import annotations

import os
import sys
from typing import Callable

from PyQt6.QtCore import QAbstractNativeEventFilter, QObject, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

# Win32
_HOTKEY_ID = 0xCA1A  # id proprio da Caixa
_MOD_CONTROL = 0x0002
_VK_SPACE = 0x20
_WM_HOTKEY = 0x0312


def _caminho_icone() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    for nome in ("caixa.ico", "icon.ico", "app.ico"):
        p = os.path.join(here, nome)
        if os.path.isfile(p):
            return p
    # no exe empacotado
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        p = os.path.join(meipass, "caixa.ico")
        if os.path.isfile(p):
            return p
    return ""


def _icone_caixa() -> QIcon:
    path = _caminho_icone()
    if path:
        return QIcon(path)
    # fallback: icone vazio ainda cria a bandeja (Windows aceita)
    return QIcon()


class _FiltroHotkey(QAbstractNativeEventFilter):
    """Captura WM_HOTKEY do RegisterHotKey (Ctrl+Espaco)."""

    def __init__(self, on_hotkey: Callable[[], None], hotkey_id: int = _HOTKEY_ID):
        super().__init__()
        self._on_hotkey = on_hotkey
        self._id = int(hotkey_id)

    def nativeEventFilter(self, eventType, message):  # noqa: N802
        et = eventType
        if isinstance(et, bytes):
            et = et.decode("ascii", errors="ignore")
        if et not in ("windows_generic_MSG", "windows_dispatcher_MSG"):
            return False, 0
        try:
            import ctypes
            from ctypes import wintypes

            msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
            if msg.message == _WM_HOTKEY and int(msg.wParam) == self._id:
                self._on_hotkey()
                return True, 0
        except Exception:
            return False, 0
        return False, 0


class Bandeja(QObject):
    """Bandeja + atalho global. Fechar a janela esconde; Sair encerra de verdade."""

    pediu_mostrar = pyqtSignal()
    pediu_sair = pyqtSignal()
    atalho_disparado = pyqtSignal()

    def __init__(self, janela: QWidget, parent=None):
        super().__init__(parent or janela)
        self._janela = janela
        self._tray: QSystemTrayIcon | None = None
        self._filtro: _FiltroHotkey | None = None
        self._hotkey_ok = False
        self._sair_de_verdade = False
        self._instalado = False

    @property
    def instalado(self) -> bool:
        return self._instalado

    @property
    def hotkey_ativo(self) -> bool:
        return self._hotkey_ok

    @property
    def tray(self) -> QSystemTrayIcon | None:
        return self._tray

    def instalar(self) -> bool:
        """Cria icone na bandeja, registra Ctrl+Espaco e intercepta o fechar."""
        if self._instalado:
            return True
        self._montar_tray()
        self._registrar_hotkey()
        self._janela.installEventFilter(self)
        self._instalado = True
        return True

    def _montar_tray(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        # offscreen / headless: tray pode nao existir — segue sem quebrar
        disponivel = True
        try:
            disponivel = QSystemTrayIcon.isSystemTrayAvailable()
        except Exception:
            disponivel = False
        if not disponivel:
            return

        tray = QSystemTrayIcon(_icone_caixa(), self)
        tray.setToolTip("Caixa de Ferramentas — Ctrl+Espaco")
        menu = QMenu()
        act_mostrar = QAction("Mostrar Caixa", menu)
        act_mostrar.triggered.connect(self.mostrar_janela)
        act_sair = QAction("Sair", menu)
        act_sair.triggered.connect(self.sair)
        menu.addAction(act_mostrar)
        menu.addSeparator()
        menu.addAction(act_sair)
        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        self._tray = tray

    def _on_tray_activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.toggle()

    def _registrar_hotkey(self) -> bool:
        if sys.platform != "win32":
            return False
        try:
            import ctypes

            user32 = ctypes.windll.user32
            # HWND NULL = hotkey no thread atual (fila do Qt)
            ok = bool(
                user32.RegisterHotKey(
                    None, _HOTKEY_ID, _MOD_CONTROL, _VK_SPACE
                )
            )
            if not ok:
                # ja registrado por outra instancia — nao quebra
                self._hotkey_ok = False
                return False
            app = QApplication.instance()
            if app is not None:
                self._filtro = _FiltroHotkey(self._on_hotkey)
                app.installNativeEventFilter(self._filtro)
            self._hotkey_ok = True
            return True
        except Exception:
            self._hotkey_ok = False
            return False

    def _desregistrar_hotkey(self) -> None:
        if sys.platform != "win32" or not self._hotkey_ok:
            return
        try:
            import ctypes

            ctypes.windll.user32.UnregisterHotKey(None, _HOTKEY_ID)
        except Exception:
            pass
        app = QApplication.instance()
        if app is not None and self._filtro is not None:
            try:
                app.removeNativeEventFilter(self._filtro)
            except Exception:
                pass
        self._filtro = None
        self._hotkey_ok = False

    def _on_hotkey(self) -> None:
        self.atalho_disparado.emit()
        self.toggle()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        from PyQt6.QtCore import QEvent

        if obj is self._janela and event.type() == QEvent.Type.Close:
            if not self._sair_de_verdade:
                event.ignore()
                self.esconder_para_bandeja()
                return True
        return super().eventFilter(obj, event)

    def esconder_para_bandeja(self) -> None:
        """Fechar = minimizar pra bandeja (nao encerra o app)."""
        self._janela.hide()
        if self._tray is not None and self._tray.isVisible():
            self._tray.showMessage(
                "Caixa de Ferramentas",
                "Continuo na bandeja. Ctrl+Espaco pra voltar.",
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )

    def mostrar_janela(self) -> None:
        """Traz a janela pra frente e tenta focar a barra de busca."""
        w = self._janela
        w.show()
        w.setWindowState(w.windowState() & ~Qt.WindowState.WindowMinimized)
        w.raise_()
        w.activateWindow()
        self._focar_busca()
        self.pediu_mostrar.emit()

    def _focar_busca(self) -> None:
        # Claude pode expor barra_busca / focar_busca; senão procura BarraBusca
        for nome in ("focar_busca", "focus_busca"):
            fn = getattr(self._janela, nome, None)
            if callable(fn):
                try:
                    fn()
                    return
                except Exception:
                    pass
        barra = getattr(self._janela, "barra_busca", None) or getattr(
            self._janela, "barra", None
        )
        if barra is not None and hasattr(barra, "focar"):
            try:
                barra.focar()
                return
            except Exception:
                pass
        # varre filhos por objeto com .focar()
        for child in self._janela.findChildren(QWidget):
            if child.__class__.__name__ == "BarraBusca" and hasattr(child, "focar"):
                try:
                    child.focar()
                except Exception:
                    pass
                return

    def toggle(self) -> None:
        if self._janela.isVisible() and self._janela.isActiveWindow():
            self.esconder_para_bandeja()
        else:
            self.mostrar_janela()

    def sair(self) -> None:
        """Sair de verdade pelo menu da bandeja."""
        self._sair_de_verdade = True
        self.pediu_sair.emit()
        self._desregistrar_hotkey()
        if self._tray is not None:
            self._tray.hide()
        app = QApplication.instance()
        if app is not None:
            app.quit()
        else:
            self._janela.close()

    def encerrar(self) -> None:
        """Limpa hotkey/tray sem necessariamente matar o QApplication (testes)."""
        self._sair_de_verdade = True
        self._desregistrar_hotkey()
        if self._tray is not None:
            self._tray.hide()
            self._tray = None
        try:
            self._janela.removeEventFilter(self)
        except Exception:
            pass
        self._instalado = False


def registrar_atalho(janela: QWidget) -> Bandeja:
    """Instala bandeja + Ctrl+Espaco na janela principal. Claude chama no caixa.pyw."""
    bandeja = Bandeja(janela)
    bandeja.instalar()
    # guarda ref na janela pra GC nao matar
    janela._caixa_bandeja = bandeja  # type: ignore[attr-defined]
    return bandeja


__all__ = ["Bandeja", "registrar_atalho"]
