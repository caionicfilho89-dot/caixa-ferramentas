"""Smoke offscreen: tema + Hoje + barra juntos (sem sensores/respostas reais)."""
from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PyQt6.QtCore import QEventLoop, QTimer  # noqa: E402
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget  # noqa: E402

import caixa_busca_ui as busca  # noqa: E402
import caixa_home as home  # noqa: E402
import caixa_tema as tema  # noqa: E402

_APP = QApplication.instance() or QApplication(sys.argv)


def _esperar(ms: int = 100) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


class TestSmokeUi(unittest.TestCase):
    def test_janela_composta_1366(self):
        def sensores():
            return [{
                "id": "disco",
                "emoji": "💾",
                "titulo": "Disco C:",
                "valor": "120 GB livres",
                "detalhe": "SSD",
                "acao": {"rotulo": "Liberar", "chave_ferramenta": "faxina-disco"},
            }]

        def responder(texto: str):
            if "20%" in texto:
                return [{
                    "titulo": "Porcentagem",
                    "resposta": "70",
                    "detalhe": "20% de 350",
                    "chave_ferramenta": "financas",
                    "confianca": 0.99,
                }]
            return []

        win = QWidget()
        tema.aplicar_tema(win)
        win.resize(1366, 768)
        lay = QVBoxLayout(win)
        barra = busca.BarraBusca(responder=responder, debounce_ms=0)
        tela = home.TelaHoje(leitor=sensores, intervalo_ms=600_000)
        lay.addWidget(barra)
        lay.addWidget(tela, 1)
        win.show()
        _esperar(150)
        self.assertEqual(tema.colunas_para_largura(win.width()), 2)
        out = barra.consultar_texto("20% de 350")
        self.assertEqual(out[0]["resposta"], "70")
        for _ in range(20):
            _APP.processEvents()
            if tela.cartoes_visiveis():
                break
            _esperar(30)
        self.assertEqual(tela.cartoes_visiveis()[0]["id"], "disco")
        self.assertEqual(len(tela._atalhos), 15)
        tela._parar()
        win.close()

    def test_janela_4k_colunas(self):
        self.assertEqual(tema.colunas_para_largura(3840), 4)
        self.assertGreaterEqual(tema.escala_tipografia(3840), 1.2)


if __name__ == "__main__":
    unittest.main()
