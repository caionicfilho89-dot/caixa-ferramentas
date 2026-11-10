"""Testes da tela Hoje (caixa_home.py). Usa stub de sensores_core."""
from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PyQt6.QtCore import QEventLoop, QTimer  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

import caixa_home as home  # noqa: E402

_APP = QApplication.instance() or QApplication(sys.argv)


def _stub_sensores():
    return [
        {
            "id": "disco",
            "emoji": "💾",
            "titulo": "Disco C:",
            "valor": "42 GB livres",
            "detalhe": "de 512 GB · 8% livre",
            "acao": {"rotulo": "Liberar espaço", "chave_ferramenta": "disk-analyzer"},
        },
        {
            "id": "downloads",
            "emoji": "📥",
            "titulo": "Downloads",
            "valor": "17 arquivos soltos",
            "detalhe": "3 instaladores velhos",
            "acao": {"rotulo": "Arrumar", "chave_ferramenta": "organizador-downloads"},
        },
        {
            "id": "vazio-falso",
            "emoji": "👻",
            "titulo": "Não deve aparecer",
            "valor": "",
            "detalhe": "sem dado real",
            "acao": {"rotulo": "X", "chave_ferramenta": "x"},
        },
    ]


def _esperar(ms: int = 200) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


class TestTelaHoje(unittest.TestCase):
    def tearDown(self):
        # garante que threads de sensores morreram antes do próximo teste
        _APP.processEvents()

    def _tela(self, leitor):
        tela = home.TelaHoje(leitor=leitor, intervalo_ms=600_000)
        # espera a 1ª leitura do __init__ terminar pra não competir com renderizar()
        for _ in range(40):
            _APP.processEvents()
            if not tela._carregando:
                break
            _esperar(25)
        return tela

    def test_renderiza_so_com_valor(self):
        tela = self._tela(_stub_sensores)
        tela.renderizar(_stub_sensores())
        ids = [c["id"] for c in tela.cartoes_visiveis()]
        self.assertEqual(ids, ["disco", "downloads"])
        self.assertNotIn("vazio-falso", ids)
        tela._parar()
        tela.deleteLater()

    def test_lista_vazia_mostra_estado_vazio(self):
        tela = self._tela(lambda: [])
        tela.renderizar([])
        self.assertEqual(tela.cartoes_visiveis(), [])
        self.assertFalse(tela.estado_vazio.isHidden())
        tela._parar()
        tela.deleteLater()

    def test_sinal_abrir_ferramenta(self):
        tela = self._tela(_stub_sensores)
        tela.renderizar(_stub_sensores())
        recebido = []
        tela.abrir_ferramenta.connect(lambda k: recebido.append(k))
        tela._cartoes[0].btn.click()
        self.assertEqual(recebido, ["disk-analyzer"])
        tela._parar()
        tela.deleteLater()

    def test_sinal_comando(self):
        tela = self._tela(lambda: [])
        tela.renderizar([{
            "id": "prints",
            "emoji": "🖼️",
            "titulo": "Prints",
            "valor": "2 recentes",
            "detalhe": "",
            "acao": {"rotulo": "Abrir pasta", "comando": "explorer:Capturas"},
        }])
        cmds = []
        tela.executar_comando.connect(lambda c: cmds.append(c))
        tela._cartoes[0].btn.click()
        self.assertEqual(cmds, ["explorer:Capturas"])
        tela._parar()
        tela.deleteLater()

    def test_thread_atualiza_sem_travar(self):
        chamadas = {"n": 0}

        def leitor():
            chamadas["n"] += 1
            return _stub_sensores()

        tela = self._tela(leitor)
        self.assertGreaterEqual(chamadas["n"], 1)
        self.assertEqual(len(tela.cartoes_visiveis()), 2)
        self.assertTrue(tela.estado_carregando.isHidden())
        tela._parar()
        tela.deleteLater()

    def test_pediu_todas(self):
        tela = self._tela(lambda: [])
        hits = []
        tela.pediu_todas.connect(lambda: hits.append(1))
        tela.btn_todas.click()
        self.assertEqual(hits, [1])
        tela._parar()
        tela.deleteLater()

    def test_leitor_padrao_sem_sensores_core(self):
        dados = home._ler_sensores_padrao()
        self.assertIsInstance(dados, list)

    def test_atalhos_da_critica(self):
        tela = self._tela(lambda: [])
        self.assertEqual(len(home.DESTAQUES_CRITICA), 15)
        self.assertEqual(len(tela._atalhos), 15)
        chaves = [c.dados()["acao"]["chave_ferramenta"] for c in tela._atalhos]
        self.assertIn("faxina-disco", chaves)
        self.assertIn("calculadora-troco", chaves)
        abertos = []
        tela.abrir_ferramenta.connect(lambda k: abertos.append(k))
        tela._atalhos[0].acao_clicada.emit(tela._atalhos[0].dados()["acao"])
        self.assertEqual(abertos, ["faxina-disco"])
        tela._parar()
        tela.deleteLater()

    def test_unicode_limpo(self):
        path = os.path.join(HERE, "caixa_home.py")
        with open(path, encoding="utf-8") as f:
            txt = f.read()
        ruins = [c for c in txt if 0x0300 <= ord(c) <= 0x1CFF]
        self.assertEqual(ruins, [])


if __name__ == "__main__":
    unittest.main()
