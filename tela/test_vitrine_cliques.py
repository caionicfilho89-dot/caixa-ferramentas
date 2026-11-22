# -*- coding: utf-8 -*-
"""T505: os 27 cartões da vitrine resolvem e abrem via ponte (mesmo caminho do clique)."""
from __future__ import annotations

import os
import py_compile
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CAIXA = os.path.dirname(HERE)
sys.path.insert(0, CAIXA)

os.environ["CAIXA_TESTE"] = "1"
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import caixa as cx  # noqa: E402
import ponte_tela as ponte  # noqa: E402


class TestVitrineCliques(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = ponte.op_dados({})
        cls.vitrine = cls.dados["vitrine"]
        cls.por_chave = {t[3]: t for t in ponte._ferramentas()}

    def test_vitrine_tem_27_e_substitui_inteiro(self):
        self.assertEqual(len(self.vitrine), 27)
        for v in self.vitrine:
            self.assertTrue(v.get("substitui"), v)
            self.assertNotIn("…", v["substitui"])
            self.assertNotIn("...", v["substitui"])

    def test_clique_abre_as_27(self):
        """Clique = ponte op_abrir (CaixaTela chama isso) + script existe e compila."""
        ok, falhas = [], []
        for v in self.vitrine:
            chave = v["chave"]
            tool = self.por_chave.get(chave)
            if not tool:
                falhas.append(f"{chave}: fora do catálogo")
                continue
            caminho = os.path.join(cx.BASE, tool[3], tool[4])
            if not os.path.isfile(caminho):
                falhas.append(f"{chave}: falta {caminho}")
                continue
            try:
                py_compile.compile(caminho, doraise=True)
                info = ponte.op_abrir({"chave": chave})
                if info.get("nome") != tool[1]:
                    falhas.append(f"{chave}: ponte devolveu {info!r}, esperado {tool[1]!r}")
                    continue
                ok.append(chave)
            except Exception as e:  # noqa: BLE001
                falhas.append(f"{chave}: {e}")
        self.assertEqual(len(ok), 27, f"abriram {len(ok)}/27; falhas={falhas}")
        self.assertFalse(falhas)


if __name__ == "__main__":
    unittest.main(verbosity=2)
