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
