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

    def test_enter_sem_seta_nao_abre(self):
        """CRITICA F3: Enter com resposta já na lista NÃO abre ferramenta sozinho."""
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=0)
        abertos = []
        barra.abrir_ferramenta.connect(lambda k: abertos.append(k))
        barra.set_texto("20% de 350")
        self.assertEqual(len(barra.resultados()), 1)
        _tecla(barra.campo, Qt.Key.Key_Return)
        self.assertEqual(abertos, [])
        # seta = seleção de propósito → aí Enter abre
        _tecla(barra.campo, Qt.Key.Key_Down)
        _tecla(barra.campo, Qt.Key.Key_Return)
        self.assertEqual(abertos, ["calculadora-cientifica"])
        barra.deleteLater()

    def test_card_mostra_detalhe_e_pontuacao(self):
        """Fonte mono + detalhe no card (Q10/Q56: '.', ',' e conta visíveis)."""
        def resp_q10(_t: str) -> list[dict]:
            return [{
                "titulo": "Juros compostos",
                "resposta": "R$ 1.030,30",
                "detalhe": "1.000 × (1,01)^3 = 1.030,30",
                "chave_ferramenta": "financas",
                "confianca": 0.95,
            }]

        barra = busca.BarraBusca(responder=resp_q10, debounce_ms=0)
        barra.set_texto("juros compostos 1000 a 1% 3 meses")
        item = barra._widgets[0]
        self.assertEqual(item.lbl_resposta.text(), "R$ 1.030,30")
        self.assertIn(".", item.lbl_resposta.text())
        self.assertIn(",", item.lbl_resposta.text())
        self.assertIn("R$", item.lbl_resposta.text())
        self.assertFalse(item.lbl_detalhe.isHidden())
        self.assertIn("1.030,30", item.lbl_detalhe.text())
        fam = item.lbl_resposta.font().family().lower()
        self.assertTrue(
            "consolas" in fam or "cascadia" in fam or "courier" in fam,
            f"fonte do valor deveria ser mono, veio {fam!r}",
        )
        barra.deleteLater()

    def test_card_q56_gorjeta_detalhe(self):
        def resp_q56(_t: str) -> list[dict]:
            return [{
                "titulo": "Gorjeta",
                "resposta": "gorjeta 37,20; total 285,20",
                "detalhe": "15% de 248,00 = 37,20 · total 285,20",
                "chave_ferramenta": "calculadora-gorjeta",
                "confianca": 0.92,
            }]

        barra = busca.BarraBusca(responder=resp_q56, debounce_ms=0)
        barra.set_texto("gorjeta 15% numa conta de 248,00")
        item = barra._widgets[0]
        self.assertIn("37,20", item.lbl_resposta.text())
        self.assertIn("285,20", item.lbl_resposta.text())
        self.assertFalse(item.lbl_detalhe.isHidden())
        self.assertIn("15%", item.lbl_detalhe.text())
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

    def test_fonte_resposta_sem_font_merging(self):
        """NoFontMerging evita sumir '.', ',' e 'R$' (CRITICA F3)."""
        from PyQt6.QtGui import QFont
        import caixa_tema as tema

        f = tema.fonte_resposta_barra(16)
        strat = f.styleStrategy()
        flag = QFont.StyleStrategy.NoFontMerging
        # PyQt6: StyleStrategy e Flag; compara via value
        tem = bool(strat.value & flag.value) if hasattr(strat, "value") else (flag in strat)
        self.assertTrue(tem, f"strategy={strat!r} deveria incluir NoFontMerging")
        self.assertIn("consolas", f.family().lower())


if __name__ == "__main__":
    unittest.main()
