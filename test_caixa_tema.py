"""Testes do tema visual da Caixa (caixa_tema.py)."""
from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PyQt6.QtWidgets import QApplication, QLabel  # noqa: E402

import caixa_tema as tema  # noqa: E402

_APP = QApplication.instance() or QApplication(sys.argv)


class TestPaleta(unittest.TestCase):
    def test_cores_base(self):
        self.assertEqual(tema.BG, "#11131a")
        self.assertEqual(tema.ACCENT, "#7c5cff")
        self.assertTrue(tema.TEXTO.startswith("#"))

    def test_cor_categoria_conhecida(self):
        self.assertEqual(tema.cor_categoria("💰 Finanças & Trabalho"), "#ffd166")
        self.assertEqual(tema.cor_categoria("disco"), "#60a5fa")
        self.assertEqual(tema.cor_categoria("downloads"), "#fb923c")

    def test_cor_categoria_fallback(self):
        self.assertEqual(tema.cor_categoria(""), tema.ACCENT)
        self.assertEqual(tema.cor_categoria("categoria-inventada-xyz"), tema.ACCENT)

    def test_qss_tem_elementos_chave(self):
        qss = tema.qss_app()
        for trecho in ("#11131a", "#7c5cff", "campoBusca", "cartaoGrande", "acaoCartao"):
            self.assertIn(trecho, qss)

    def test_fontes(self):
        self.assertGreaterEqual(tema.fonte_titulo().pointSize(), 18)
        self.assertGreaterEqual(tema.fonte_valor_grande().pointSize(), 20)
        self.assertEqual(tema.fonte_corpo().family(), "Segoe UI")


class TestCartoes(unittest.TestCase):
    def test_cartao_grande_preencher_e_acao(self):
        c = tema.CartaoGrande()
        recebido = []
        c.acao_clicada.connect(lambda a: recebido.append(a))
        c.preencher({
            "id": "disco",
            "emoji": "💾",
            "titulo": "Disco C:",
            "valor": "42 GB livres",
            "detalhe": "SSD 512 GB",
            "acao": {"rotulo": "Liberar espaço", "chave_ferramenta": "disk-analyzer"},
        })
        self.assertEqual(c.titulo.text(), "Disco C:")
        self.assertEqual(c.valor.text(), "42 GB livres")
        self.assertEqual(c.btn.text(), "Liberar espaço")
        self.assertFalse(c.btn.isHidden())
        c.btn.click()
        self.assertEqual(recebido[0]["chave_ferramenta"], "disk-analyzer")

    def test_cartao_grande_sem_acao_esconde_botao(self):
        c = tema.CartaoGrande()
        c.preencher({
            "id": "clipboard",
            "emoji": "📋",
            "titulo": "Área de transferência",
            "valor": "(vazia)",
            "detalhe": "",
        })
        self.assertTrue(c.btn.isHidden())

    def test_cartao_pequeno_preencher(self):
        c = tema.CartaoPequeno()
        c.preencher({
            "id": "prints",
            "emoji": "🖼️",
            "titulo": "Prints",
            "valor": "3 recentes",
            "detalhe": "Capturas de Tela",
            "acao": {"rotulo": "Abrir pasta", "comando": "explorer"},
        })
        self.assertEqual(c.emoji.text(), "🖼️")
        self.assertEqual(c.valor.text(), "3 recentes")
        self.assertEqual(c.dados()["id"], "prints")

    def test_estados(self):
        vazio = tema.EstadoVazio("Sem dados agora.")
        textos = [lbl.text() for lbl in vazio.findChildren(QLabel)]
        self.assertTrue(any("Sem dados" in t for t in textos))
        carregando = tema.EstadoCarregando()
        ang0 = carregando._ang
        carregando.avancar()
        self.assertNotEqual(carregando._ang, ang0)

    def test_aplicar_tema(self):
        tema.aplicar_tema(_APP)
        self.assertIn("#7c5cff", _APP.styleSheet())


class TestResponsivo(unittest.TestCase):
    def test_colunas_1366_e_4k(self):
        self.assertEqual(tema.colunas_para_largura(800), 1)
        self.assertEqual(tema.colunas_para_largura(1366), 2)
        self.assertEqual(tema.colunas_para_largura(1920), 3)
        self.assertEqual(tema.colunas_para_largura(2560), 4)
        self.assertEqual(tema.colunas_para_largura(3840), 4)

    def test_grade_4k_300_dpi(self):
        """4K físico @ 300% → ~1280 lógica → 2 colunas, tipografia sem inflar."""
        self.assertEqual(tema.largura_logica(3840, 3.0), 1280)
        self.assertEqual(tema.colunas_para_largura(3840, dpr=3.0), 2)
        self.assertEqual(tema.colunas_para_largura(1366, dpr=1.0), 2)
        self.assertEqual(tema.escala_tipografia(3840, dpr=3.0), 1.0)
        self.assertEqual(tema.margens_para_largura(3840, dpr=3.0)[0], 16)

    def test_t20_layout_dpr_1_para_3(self):
        """Simula notebook 1366@100% → 4K@300%: colunas e tipografia mudam certo."""
        lay100 = tema.layout_grade(1366, dpr=1.0)
        self.assertEqual(lay100["colunas"], 2)
        self.assertEqual(lay100["card_w"], 272)
        self.assertAlmostEqual(lay100["escala"], 1.0, places=2)

        lay300 = tema.layout_grade(3840, dpr=3.0)
        self.assertEqual(lay300["colunas"], 2)
        self.assertEqual(lay300["largura_logica"], 1280)
        self.assertEqual(lay300["escala"], 1.0)
        self.assertEqual(lay300["card_w"], 260)

        # 4K nativo @100% continua com 4 colunas
        lay4k = tema.layout_grade(3840, dpr=1.0)
        self.assertEqual(lay4k["colunas"], 4)
        self.assertGreaterEqual(lay4k["escala"], 1.2)

    def test_t20_observador_dpi_emite(self):
        from PyQt6.QtWidgets import QWidget
        host = QWidget()
        host.resize(1366, 768)
        hits = []
        obs = tema.ObservadorDpi(host)
        obs.dpi_mudou.connect(lambda dpr, lay: hits.append((dpr, lay["colunas"])))
        lay = obs.forcar()
        self.assertTrue(hits)
        self.assertEqual(lay["colunas"], hits[-1][1])
        host.deleteLater()

    def test_contraste_grade_todas(self):
        self.assertTrue(tema.contraste_grade_todas_ok())
        qss = tema.qss_app()
        self.assertIn("#243044", qss)
        self.assertIn("#f2f4fa", qss)

    def test_t28_side_selected_com_accent(self):
        """Lateral de categorias: selected com #7c5cff legível (100%/300%)."""
        qss = tema.qss_app()
        self.assertIn("#side::item:selected", qss)
        trecho = qss.split("#side::item:selected")[1][:280]
        self.assertIn(tema.ACCENT, trecho)
        self.assertIn("#f2f4fa", trecho)
        self.assertIn("rgba(124, 92, 255", trecho)

    def test_margens_e_escala(self):
        self.assertEqual(tema.margens_para_largura(1366)[0], 16)
        self.assertEqual(tema.margens_para_largura(3000)[0], 48)
        self.assertGreaterEqual(tema.escala_tipografia(3840), 1.2)
        self.assertLessEqual(tema.escala_tipografia(1280), 1.0)

    def test_animar_entrada(self):
        from PyQt6.QtWidgets import QLabel
        w = QLabel("oi")
        anim = tema.animar_entrada(w, duracao_ms=50)
        self.assertIsNotNone(anim)
        self.assertEqual(anim.duration(), 50)


class TestUnicodeLimpo(unittest.TestCase):
    def test_sem_chars_estranhos_no_modulo(self):
        path = os.path.join(HERE, "caixa_tema.py")
        with open(path, encoding="utf-8") as f:
            txt = f.read()
        ruins = [c for c in txt if 0x0300 <= ord(c) <= 0x1CFF]
        self.assertEqual(ruins, [], f"chars estranhos: {[hex(ord(c)) for c in ruins[:10]]}")


if __name__ == "__main__":
    unittest.main()
