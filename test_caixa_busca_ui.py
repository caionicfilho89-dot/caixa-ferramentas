"""Testes da barra de busca (caixa_busca_ui.py). Stub de respostas_core."""
from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PyQt6.QtCore import QEventLoop, Qt, QTimer  # noqa: E402
from PyQt6.QtGui import QKeyEvent  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

import caixa_busca_ui as busca  # noqa: E402

_APP = QApplication.instance() or QApplication(sys.argv)


def _stub_responder(texto: str) -> list[dict]:
    t = (texto or "").lower()
    if "20%" in t or "porcento" in t or "por cent" in t:
        return [{
            "titulo": "Porcentagem",
            "resposta": "70",
            "detalhe": "20% de 350 = 70",
            "chave_ferramenta": "calculadora-cientifica",
            "confianca": 0.95,
        }]
    if "troco" in t:
        return [{
            "titulo": "Troco",
            "resposta": "R$ 26,50",
            "detalhe": "100 − 73,50",
            "chave_ferramenta": "calculadora-gorjeta",
            "confianca": 0.9,
        }]
    if "ipva" in t:
        return [{
            "titulo": "IPVA SP",
            "resposta": "R$ 2.400,00",
            "detalhe": "4% de R$ 60.000",
            "chave_ferramenta": "calculadora-clt",
            "confianca": 0.85,
        }]
    if "xyzzy" in t:
        return []
    # busca de reserva: 5 parecidas
    return [
        {"titulo": f"Ferramenta {i}", "resposta": "", "detalhe": "sugestão",
         "chave_ferramenta": f"tool-{i}", "confianca": 0.3}
        for i in range(1, 6)
    ]


def _esperar(ms: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _tecla(widget, key: int) -> None:
    ev = QKeyEvent(QKeyEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
    _APP.sendEvent(widget, ev)
    _APP.processEvents()


class TestBarraBusca(unittest.TestCase):
    def test_debounce_responde_ao_digitar(self):
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=30)
        barra.set_texto("20% de 350")
        self.assertEqual(barra.resultados(), [])  # ainda no debounce
        _esperar(80)
        res = barra.resultados()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["resposta"], "70")
        barra.deleteLater()

    def test_consultar_agora_sem_debounce(self):
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=5000)
        barra.set_texto("troco de 100 pra 73,50")
        barra.consultar_agora()
        self.assertEqual(barra.resultados()[0]["resposta"], "R$ 26,50")
        barra.deleteLater()

    def test_lista_vazia_quando_nao_entende(self):
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=0)
        barra.set_texto("xyzzy")
        self.assertEqual(barra.resultados(), [])
        self.assertFalse(barra.lista_frame.isHidden())
        self.assertFalse(barra.lbl_vazio.isHidden())
        barra.deleteLater()

    def test_sugestoes_reserva(self):
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=0)
        barra.set_texto("algo aleatorio sem match direto")
        self.assertEqual(len(barra.resultados()), 5)
        barra.deleteLater()

    def test_setas_e_enter(self):
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=0)
        abertos = []
        barra.abrir_ferramenta.connect(lambda k: abertos.append(k))
        barra.set_texto("qualquer coisa")
        self.assertEqual(barra.indice_selecionado(), 0)
        _tecla(barra.campo, Qt.Key.Key_Down)
        self.assertEqual(barra.indice_selecionado(), 1)
        _tecla(barra.campo, Qt.Key.Key_Return)
        self.assertEqual(abertos, ["tool-2"])
        barra.deleteLater()

    def test_esc_limpa_depois_fecha(self):
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=0)
        fechou = []
        barra.fechou.connect(lambda: fechou.append(1))
        barra.set_texto("ipva")
        _tecla(barra.campo, Qt.Key.Key_Escape)
        self.assertEqual(barra.texto(), "")
        self.assertEqual(fechou, [])
        _tecla(barra.campo, Qt.Key.Key_Escape)
        self.assertEqual(fechou, [1])
        barra.deleteLater()

    def test_botao_abrir_emite_sinal(self):
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=0)
        abertos = []
        barra.abrir_ferramenta.connect(lambda k: abertos.append(k))
        barra.set_texto("20% de 350")
        barra._widgets[0].btn.click()
        self.assertEqual(abertos, ["calculadora-cientifica"])
        barra.deleteLater()

    def test_campo_vazio_esconde_lista(self):
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=0)
        barra.set_texto("troco")
        self.assertFalse(barra.lista_frame.isHidden())
        barra.set_texto("")
        self.assertTrue(barra.lista_frame.isHidden())
        barra.deleteLater()

    def test_responder_padrao_sem_modulo(self):
        out = busca._responder_padrao("20% de 350")
        self.assertIsInstance(out, list)

    def test_consultar_texto_api_sem_gui(self):
        """Contrato pro Grok: comparar as 60 sem Win32."""
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=0)
        out = barra.consultar_texto("20% de 350")
        self.assertEqual(out[0]["resposta"], "70")
        self.assertEqual(barra.resposta_principal()["titulo"], "Porcentagem")
        self.assertEqual(barra.consultar_texto(""), [])
        barra.deleteLater()

    def test_unicode_limpo(self):
        path = os.path.join(HERE, "caixa_busca_ui.py")
        with open(path, encoding="utf-8") as f:
            txt = f.read()
        ruins = [c for c in txt if 0x0300 <= ord(c) <= 0x1CFF]
        self.assertEqual(ruins, [])


if __name__ == "__main__":
    unittest.main()
