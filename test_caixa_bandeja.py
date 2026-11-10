"""Testes da bandeja + atalho Ctrl+Espaco (caixa_bandeja.py)."""
from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PyQt6.QtCore import QEvent, Qt  # noqa: E402
from PyQt6.QtGui import QCloseEvent  # noqa: E402
from PyQt6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget  # noqa: E402

import caixa_bandeja as bandeja  # noqa: E402

_APP = QApplication.instance() or QApplication(sys.argv)


class _JanelaFake(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Caixa fake")
        lay = QVBoxLayout(self)
        self.barra_busca = _BarraFake()
        lay.addWidget(self.barra_busca)
        self.focou = False

    def focar_busca(self):
        self.focou = True
        self.barra_busca.focar()


class _BarraFake(QWidget):
    def __init__(self):
        super().__init__()
        self.campo = QLineEdit(self)
        self._focou = False

    def focar(self):
        self._focou = True
        self.campo.setFocus()


class TestBandeja(unittest.TestCase):
    def tearDown(self):
        _APP.processEvents()

    def test_registrar_atalho_retorna_bandeja(self):
        win = _JanelaFake()
        b = bandeja.registrar_atalho(win)
        self.assertIsInstance(b, bandeja.Bandeja)
        self.assertTrue(b.instalado)
        self.assertIs(win._caixa_bandeja, b)
        b.encerrar()
        win.deleteLater()

    def test_fechar_esconde_nao_encerra(self):
        win = _JanelaFake()
        win.show()
        _APP.processEvents()
        b = bandeja.registrar_atalho(win)
        # dispara Close via eventFilter
        ev = QCloseEvent()
        filtrado = b.eventFilter(win, ev)
        self.assertTrue(filtrado)
        self.assertTrue(win.isHidden())
        self.assertFalse(b._sair_de_verdade)
        b.encerrar()
        win.deleteLater()

    def test_mostrar_foca_busca(self):
        win = _JanelaFake()
        b = bandeja.registrar_atalho(win)
        win.hide()
        b.mostrar_janela()
        _APP.processEvents()
        self.assertTrue(win.isVisible())
        self.assertTrue(win.focou)
        b.encerrar()
        win.deleteLater()

    def test_toggle_esconde_e_mostra(self):
        win = _JanelaFake()
        win.show()
        win.activateWindow()
        _APP.processEvents()
        b = bandeja.registrar_atalho(win)
        # simula "esta ativa": forca estado e esconde via API
        b.esconder_para_bandeja()
        self.assertTrue(win.isHidden())
        b.mostrar_janela()
        self.assertTrue(win.isVisible())
        b.encerrar()
        win.deleteLater()

    def test_sair_marca_flag_e_limpa(self):
        win = _JanelaFake()
        b = bandeja.Bandeja(win)
        b.instalar()
        saiu = []
        b.pediu_sair.connect(lambda: saiu.append(1))
        # nao chama b.sair() (mata o QApplication dos outros testes) —
        # exercita o caminho de limpeza
        b._sair_de_verdade = True
        b.encerrar()
        self.assertFalse(b.instalado)
        self.assertEqual(saiu, [])
        win.deleteLater()

    def test_atalho_callback_toggle(self):
        win = _JanelaFake()
        win.show()
        b = bandeja.registrar_atalho(win)
        hits = []
        b.atalho_disparado.connect(lambda: hits.append(1))
        b._on_hotkey()
        self.assertEqual(hits, [1])
        b.encerrar()
        win.deleteLater()

    def test_icone_existe(self):
        path = bandeja._caminho_icone()
        self.assertTrue(path.endswith("caixa.ico") or path == "")
        if path:
            self.assertTrue(os.path.isfile(path))

    def test_unicode_limpo(self):
        path = os.path.join(HERE, "caixa_bandeja.py")
        with open(path, encoding="utf-8") as f:
            txt = f.read()
        ruins = [c for c in txt if 0x0300 <= ord(c) <= 0x1CFF]
        self.assertEqual(ruins, [])


if __name__ == "__main__":
    unittest.main()
