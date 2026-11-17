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
    if "fraco t16" in t:
        # simula exe sem Tocando Agora: só hits fracos tipo "agora" na descrição
        return [
            {"titulo": "Agenda de Medicacao por Horarios", "resposta": "",
             "detalhe": "a partir de agora", "chave_ferramenta": "controle-medicacao-horarios",
             "confianca": 0.33},
            {"titulo": "Matriz Eisenhower", "resposta": "", "detalhe": "sugestão",
             "chave_ferramenta": "organizador-tarefas-eisenhower", "confianca": 0.33},
            {"titulo": "Sessão Flash", "resposta": "", "detalhe": "sugestão",
             "chave_ferramenta": "planejador-revisao-flash-rapida", "confianca": 0.33},
        ]
    # busca de reserva: 5 parecidas (acima do piso da UI)
    return [
        {"titulo": f"Ferramenta {i}", "resposta": "", "detalhe": "sugestão",
         "chave_ferramenta": f"tool-{i}", "confianca": 0.55}
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

    def test_t27_buscando_mostra_frase_e_limpa_cartas(self):
        """CRITICA proposta 10: skeleton com a consulta atual; sem cartas velhas."""
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=5000)
        barra.set_texto("troco")
        barra.consultar_agora()
        self.assertEqual(len(barra.resultados()), 1)
        # digita de novo: limpa cartas e mostra a frase em voo
        barra.set_texto("20% de 350")
        self.assertEqual(barra.resultados(), [])
        self.assertFalse(barra.lbl_vazio.isHidden())
        msg = barra.lbl_vazio.text()
        self.assertIn("Buscando", msg)
        self.assertIn("20%", msg)
        self.assertLessEqual(barra.lista_frame.maximumHeight(), 80)
        # consulta muda no meio do debounce → texto acompanha
        barra.set_texto("ipva de um carro bem caro em SP")
        self.assertIn("ipva", barra.lbl_vazio.text().lower())
        self.assertIn("…", barra.lbl_vazio.text())  # truncado
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

    def test_t16_busca_fraca_vira_nada_encontrado(self):
        """CRITICA T16: 'tocando agora' sem ferramenta boa não oferece Agenda errada."""
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=0)
        out = barra.consultar_texto("fraco t16 tocando agora")
        self.assertEqual(out, [])
        self.assertEqual(barra.resultados(), [])
        self.assertIn("Nada encontrado", barra.lbl_vazio.text())
        # Enter com lista vazia não abre nada
        abertos = []
        barra.abrir_ferramenta.connect(lambda k: abertos.append(k))
        _tecla(barra.campo, Qt.Key.Key_Return)
        self.assertEqual(abertos, [])
        barra.deleteLater()

    def test_t16_filtra_irmaos_fracos_do_topo(self):
        def resp(_t):
            return [
                {"titulo": "Tocando Agora", "resposta": "", "detalhe": "",
                 "chave_ferramenta": "tocando-agora", "confianca": 0.65},
                {"titulo": "Agenda", "resposta": "", "detalhe": "",
                 "chave_ferramenta": "controle-medicacao-horarios", "confianca": 0.33},
            ]

        barra = busca.BarraBusca(responder=resp, debounce_ms=0)
        out = barra.consultar_texto("tocando agora")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["chave_ferramenta"], "tocando-agora")
        barra.deleteLater()

    def test_filtrar_fracos_unit(self):
        self.assertEqual(busca._filtrar_fracos([]), [])
        self.assertEqual(
            busca._filtrar_fracos([{"titulo": "x", "confianca": 0.33}]),
            [],
        )
        ok = [{"titulo": "y", "confianca": 0.55, "chave_ferramenta": "a"}]
        self.assertEqual(busca._filtrar_fracos(ok), ok)

    def test_t17_titulo_amigavel_insalubridade(self):
        """CRITICA T17: carta não pode mostrar a chave no lugar do nome."""
        chave = "calculadora-adicional-insalubridade"
        amig = busca.titulo_amigavel({
            "titulo": chave,
            "chave_ferramenta": chave,
            "resposta": "Insalubridade no mês: R$ 151,80",
            "confianca": 0.9,
        })
        self.assertNotEqual(amig, chave)
        self.assertIn("Insalubridade", amig)
        # card na lista
        barra = busca.BarraBusca(
            responder=lambda _t: [{
                "titulo": chave,
                "resposta": "Insalubridade no mês: R$ 151,80",
                "detalhe": "",
                "chave_ferramenta": chave,
                "confianca": 0.9,
            }],
            debounce_ms=0,
        )
        barra.consultar_texto("insalubridade")
        self.assertIn("Insalubridade", barra._widgets[0].lbl_titulo.text())
        self.assertNotEqual(barra._widgets[0].lbl_titulo.text(), chave)
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
        """CRITICA F3: Enter com resposta já na lista NÃO abre ferramenta sozinho e copia resultado."""
        barra = busca.BarraBusca(responder=_stub_responder, debounce_ms=0)
        abertos = []
        barra.abrir_ferramenta.connect(lambda k: abertos.append(k))
        barra.set_texto("20% de 350")
        self.assertEqual(len(barra.resultados()), 1)
        cb = QApplication.clipboard()
        if cb:
            cb.clear()
        _tecla(barra.campo, Qt.Key.Key_Return)
        self.assertEqual(abertos, [])
        if cb:
            self.assertEqual(cb.text(), "70")
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
        families = " ".join(
            f.lower() for f in (item.lbl_resposta.font().families() or [fam])
        )
        self.assertTrue(
            any(x in families or x in fam for x in ("consolas", "cascadia", "courier")),
            f"fonte do valor deveria ser mono, veio {fam!r} / {families!r}",
        )
        # sem espaços fantasma ao redor de . e ,
        self.assertEqual(
            item.lbl_resposta.text(),
            "R$ 1.030,30",
        )
        barra.deleteLater()

    def test_normalizar_kerning_q10(self):
        import caixa_tema as tema
        self.assertEqual(
            tema.normalizar_valor_barra("1 .030 , 30"),
            "1.030,30",
        )
        self.assertEqual(
            tema.normalizar_valor_barra("R$ 1.030,30"),
            "R$ 1.030,30",
        )

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

    def test_t09_nada_encontrado_compacto(self):
        """Estado vazio da barra não pode roubar altura da Hoje (T09 P1)."""
        barra = busca.BarraBusca(responder=lambda _t: [], debounce_ms=0)
        barra.set_texto("xyzzy-sem-resultado")
        self.assertFalse(barra.lista_frame.isHidden())
        self.assertLessEqual(barra.lista_frame.maximumHeight(), 80)
        self.assertIn("Nada encontrado", barra.lbl_vazio.text())
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
        self.assertEqual(f.letterSpacing(), 0.0)
        fams = " ".join(x.lower() for x in (f.families() or [f.family()]))
        self.assertTrue(
            any(x in fams for x in ("consolas", "cascadia", "courier")),
            f"mono esperado, veio {fams!r}",
        )

    def test_acentuacao_ptbr_titulos_e_sugestoes(self):
        """T110 / Proposta 14: títulos dos cartões e sugestões respeitam acentuação pt-BR."""
        # 1. titulo_amigavel com nome sem acento ou chave
        t1 = busca.titulo_amigavel({
            "titulo": "Agenda de Medicacao por Horarios",
            "chave_ferramenta": "controle-medicacao-horarios",
        })
        self.assertIn("Medicação", t1)
        self.assertIn("Horários", t1)

        t2 = busca.titulo_amigavel({
            "titulo": "calculadora-rescisao-trabalhista",
            "chave_ferramenta": "calculadora-rescisao-trabalhista",
        })
        self.assertIn("Rescisão", t2)

        # 2. ItemResposta.preencher ajusta título e texto 'Abrir ferramenta (...)'
        item = busca.ItemResposta(0)
        item.preencher({
            "titulo": "Agenda de Medicacao por Horarios",
            "resposta": "Abrir ferramenta (Agenda de Medicacao por Horarios)",
            "chave_ferramenta": "controle-medicacao-horarios",
            "confianca": 0.65,
        })
        self.assertIn("Medicação", item.lbl_titulo.text())
        self.assertIn("Medicação", item.lbl_resposta.text())
        self.assertIn("Horários", item.lbl_resposta.text())
        item.deleteLater()


if __name__ == "__main__":
    unittest.main()
