"""Testes do catálogo enxuto (T23)."""
from __future__ import annotations

import json
import os
import tempfile
import unittest

import caixa_arquivo as arq


class TestArquivo(unittest.TestCase):
    def test_semente_tem_nichos(self):
        ch = arq.chaves_arquivo()
        self.assertIn("planetario", ch)
        self.assertIn("calculadora-matrizes", ch)
        self.assertGreaterEqual(len(ch), 30)

    def test_protegidas_nunca_arquivam(self):
        self.assertFalse(arq.esta_arquivada("financas"))
        self.assertFalse(arq.esta_arquivada("faxina"))
        self.assertFalse(arq.esta_arquivada("notas-de-voz"))
        self.assertFalse(arq.esta_arquivada("tocando-agora"))

    def test_filtrar_grade_padrao(self):
        tools = [
            ("x", "Finanças", "", "financas", "a.pyw"),
            ("y", "Planetário", "", "planetario", "b.pyw"),
        ]
        vis = arq.filtrar_grade_padrao(tools)
        self.assertEqual([t[3] for t in vis], ["financas"])
        self.assertEqual([t[3] for t in arq.tools_arquivo(tools)], ["planetario"])

    def test_categoria_efetiva(self):
        self.assertEqual(
            arq.categoria_efetiva("planetario", "🔬 Ciência & Engenharia"),
            arq.CAT_ARQUIVO,
        )
        self.assertEqual(
            arq.categoria_efetiva("financas", "💰 Finanças & Trabalho"),
            "💰 Finanças & Trabalho",
        )

    def test_proteger_atalhos(self):
        self.assertEqual(
            arq.proteger_atalhos(["financas", "planetario", "faxina"]),
            ["financas", "faxina"],
        )

    def test_json_extra(self):
        antigo = arq.ARQUIVO_JSON
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "arquivo_chaves.json")
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump({"chaves": ["teoria-musical", "financas"]}, f)
            arq.ARQUIVO_JSON = caminho
            try:
                self.assertIn("teoria-musical", arq.chaves_arquivo())
                # financas protegida mesmo se vier no JSON
                self.assertNotIn("financas", arq.chaves_arquivo())
            finally:
                arq.ARQUIVO_JSON = antigo

    def test_t17_salvar_extras_merge(self):
        antigo = arq.ARQUIVO_JSON
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "arquivo_chaves.json")
            arq.ARQUIVO_JSON = caminho
            try:
                arq.salvar_extras(["gerador-flake-nix"])
                arq.salvar_extras(["gerador-lldbinit", "estudio-tipografia"])
                ch = arq.chaves_arquivo()
                self.assertIn("gerador-flake-nix", ch)
                self.assertIn("gerador-lldbinit", ch)
                self.assertIn("estudio-tipografia", ch)
            finally:
                arq.ARQUIVO_JSON = antigo

    def test_t67_busca_reserva_ignora_arquivadas(self):
        import respostas_core as rc
        # termo generico como 'simulador' nao deve sugerir ferramentas arquivadas
        res = rc.busca_reserva("simulador")
        chaves = [r["chave_ferramenta"] for r in res]
        self.assertNotIn("simulador-pendulo-duplo", chaves)
        self.assertNotIn("simulador-gravitacional-n-corpos", chaves)
        self.assertNotIn("simulador-logica", chaves)

        # busca pelo nome exato ou chave continua achando
        res_exata = rc.busca_reserva("simulador-pendulo-duplo")
        self.assertTrue(any(r["chave_ferramenta"] == "simulador-pendulo-duplo" for r in res_exata))


if __name__ == "__main__":
    unittest.main()
