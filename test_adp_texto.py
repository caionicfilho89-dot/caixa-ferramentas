# -*- coding: utf-8 -*-
"""Testa os adaptadores de Texto chamando o nucleo real."""
from __future__ import annotations

import datetime
import unittest

import adp_financas as af
import adp_texto as at


def _hits(texto):
    return [a for a in at.ADAPTADORES if a["extrair"](texto) is not None]


def _um(texto, chave):
    achados = _hits(texto)
    chaves = [a["chave"] for a in achados]
    if chaves.count(chave) != 1 or any(c != chave for c in chaves):
        raise AssertionError(f"{texto!r} casou {chaves}, esperava so {chave}")
    item = next(a for a in achados if a["chave"] == chave)
    saida = item["calcular"](item["extrair"](texto))
    if not saida.get("resposta", "").strip() or "detalhe" not in saida:
        raise AssertionError(f"contrato invalido em {chave}: {saida!r}")
    return saida


def _data(d):
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


class Texto(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(at.ADAPTADORES), 15)
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])

    def test_flesch(self):
        corpo = "O rato roeu a roupa do rei."
        saida = _um("legibilidade flesch " + corpo, "analisador-texto")
        mod = af.carregar("analisador-texto", "at_core")
        self.assertEqual(saida["resposta"], af._num(mod.text_stats(corpo)["flesch"], 1))

    def test_soundex(self):
        saida = _um("soundex Silva", "codificador-fonetico")
        mod = af.carregar("codificador-fonetico", "phn_core")
        self.assertEqual(saida["resposta"], mod.soundex("Silva"))

    def test_metaphone(self):
        saida = _um("metaphone Silva", "codificador-fonetico")
        mod = af.carregar("codificador-fonetico", "phn_core")
        self.assertEqual(saida["resposta"], mod.metaphone("Silva"))

    def test_levenshtein(self):
        saida = _um("levenshtein casa caso", "codificador-fonetico")
        mod = af.carregar("codificador-fonetico", "phn_core")
        self.assertEqual(saida["resposta"], str(mod.levenshtein("casa", "caso")))

    def test_similaridade(self):
        saida = _um("similaridade de casa caso", "codificador-fonetico")
        mod = af.carregar("codificador-fonetico", "phn_core")
        self.assertEqual(saida["resposta"], af._num(mod.similarity_ratio("casa", "caso"), 2))

    def test_chmod(self):
        saida = _um("chmod 755", "calculadora-chmod")
        mod = af.carregar("calculadora-chmod", "rwx_core")
        self.assertEqual(saida["resposta"], mod.to_symbolic(mod.parse_octal("755")))

    def test_chmod_simbolico(self):
        saida = _um("chmod rwxr-xr-x", "calculadora-chmod")
        mod = af.carregar("calculadora-chmod", "rwx_core")
        self.assertEqual(saida["resposta"], mod.to_octal(mod.parse_symbolic("rwxr-xr-x")))

    def test_eol(self):
        corpo = "uma\r\nduas"
        saida = _um("finais de linha " + corpo, "conversor-finais-linha")
        mod = af.carregar("conversor-finais-linha", "eol_core")
        self.assertEqual(saida["resposta"], mod.analyze_text(corpo).style)

    def test_indent(self):
        corpo = "\tcaixa"
        saida = _um("indentar com espacos " + corpo, "conversor-indentacao")
        mod = af.carregar("conversor-indentacao", "ind_core")
        self.assertEqual(saida["resposta"], mod.tabs_to_spaces(corpo))

    def test_diff(self):
        saida = _um("comparar textos casa | caso", "diff-texto")
        mod = af.carregar("diff-texto", "tdf_core")
        self.assertEqual(saida["resposta"], af._num(mod.ratio("casa", "caso"), 2))

    def test_sm2(self):
        saida = _um("sm2 nota 3", "flashcards")
        mod = af.carregar("flashcards", "fc_core")
        _ease, intervalo, _reps = mod.sm2(2.5, 0, 0, 3)
        self.assertEqual(saida["resposta"], str(intervalo) + " dias")

    def test_meta_anual(self):
        saida = _um("meta anual de leitura restantes 100", "meta-leitura")
        mod = af.carregar("meta-leitura", "lei_core")
        self.assertEqual(
            saida["resposta"],
            af._num(mod.paginas_por_dia(100, at.HOJE_TEXTO), 2) + " pag/dia",
        )

    def test_previsao(self):
        saida = _um("previsao de leitura restantes 90 ritmo 3", "meta-leitura")
        mod = af.carregar("meta-leitura", "lei_core")
        self.assertEqual(
            saida["resposta"],
            _data(mod.previsao_termino(90, 3, at.HOJE_TEXTO)),
        )

    def test_ritmo_paginas(self):
        saida = _um("ritmo de paginas lidas 40 dias 10", "meta-leitura")
        mod = af.carregar("meta-leitura", "lei_core")
        self.assertEqual(saida["resposta"], af._num(mod.ritmo_atual(40, 10), 2) + " pag/dia")

    def test_semana(self):
        frase = "leitura semanal livro 200 lidas 40 dias 5 minutos 30 ritmo 20"
        saida = _um(frase, "planejador-leituras-semanais")
        mod = af.carregar("planejador-leituras-semanais", "pls_core")
        plano = mod.planejar_semana(200, 40, 5, 30, paginas_por_hora=20, hoje=at.HOJE_TEXTO)
        self.assertEqual(saida["resposta"], af._num(plano.paginas_por_dia_necessarias, 2) + " pag/dia")

    def test_meta_dia(self):
        frase = "meta de paginas total 300 lidas 50 minutos 40 ritmo 30 prazo 10"
        saida = _um(frase, "meta-paginas-leitura-dia")
        mod = af.carregar("meta-paginas-leitura-dia", "pag_core")
        plano = mod.calcular_meta(300, 50, 40, 30, prazo_dias=10, hoje=at.HOJE_TEXTO)
        self.assertEqual(saida["resposta"], af._num(plano.paginas_por_dia_necessarias, 2) + " pag/dia")

    def test_vocabulario(self):
        frase = "vocabulario meta 50 aprendidas 10 dias 4 minutos 20 ppm 2"
        saida = _um(frase, "meta-vocabulario-idioma")
        mod = af.carregar("meta-vocabulario-idioma", "mvi_core")
        plano = mod.planejar_vocabulario(50, 10, 4, 20, palavras_por_minuto=2)
        self.assertEqual(saida["resposta"], af._num(plano.palavras_por_dia_necessarias, 2) + " palavras/dia")

    def test_flash(self):
        saida = _um("revisao flash minutos 25 minimo 5", "planejador-revisao-flash-rapida")
        mod = af.carregar("planejador-revisao-flash-rapida", "frp_core")
        self.assertEqual(saida["resposta"], str(mod.capacidade_topicos(25, 5)) + " tópicos")

    def test_ppm(self):
        saida = _um("ritmo de leitura palavras 600 segundos 120", "analisador-ritmo-leitura-compreensao")
        mod = af.carregar("analisador-ritmo-leitura-compreensao", "rtc_core")
        r = mod.calcular_ritmo_leitura(600, 120)
        self.assertEqual(saida["resposta"], af._num(r["ppm_bruto"], 1) + " ppm")

    def test_idioma(self):
        saida = _um("curso de idioma mensalidade 200 meses 6", "custo-curso-idioma")
        mod = af.carregar("custo-curso-idioma", "idi_core")
        r = mod.calcular(200, 6)
        self.assertEqual(saida["resposta"], "R$ " + af._num(r["total"]))

    def test_pressao(self):
        saida = _um("pressao arterial sistolica 118 diastolica 76", "controle-pressao-arterial")
        mod = af.carregar("controle-pressao-arterial", "pas_core")
        self.assertEqual(saida["resposta"], mod.classificar(118, 76).categoria)


if __name__ == "__main__":
    unittest.main()
