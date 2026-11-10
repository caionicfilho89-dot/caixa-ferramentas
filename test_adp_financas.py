# -*- coding: utf-8 -*-
"""Testa os adaptadores de finanças chamando o núcleo real de cada ferramenta."""
from __future__ import annotations

import unittest

import adp_financas as af
from adp_financas import ADAPTADORES, tokens


def _hits(texto):
    achados = []
    for ad in ADAPTADORES:
        try:
            params = ad["extrair"](texto)
        except Exception as e:  # pragma: no cover
            raise AssertionError(f"extrair quebrou em {ad['chave']}: {e}") from e
        if params is not None:
            achados.append(ad)
    return achados


def _um(texto, chave):
    achados = _hits(texto)
    chaves = [a["chave"] for a in achados]
    if chaves.count(chave) != 1 or any(c != chave for c in chaves):
        raise AssertionError(f"{texto!r} casou {chaves}, esperava só {chave}")
    ad = achados[0]
    params = ad["extrair"](texto)
    saida = ad["calcular"](params)
    if not isinstance(saida, dict) or "resposta" not in saida or "detalhe" not in saida:
        raise AssertionError(f"contrato inválido em {chave}: {saida!r}")
    if not saida["resposta"].strip():
        raise AssertionError(f"resposta vazia em {chave}")
    return params, saida


class Parser(unittest.TestCase):
    def test_mil_e_br(self):
        self.assertEqual(af.numero_br("1.234,50"), 1234.50)
        self.assertEqual(af.numero_br("3 mil"), 3000)
        self.assertEqual(af.numero_br("3,5 mil"), 3500)
        self.assertEqual(af.numero_br("10%"), 10)

    def test_tokens_frase(self):
        toks = tokens("troco de R$ 1.234,50 pra 3 mil com 8 meses e 10%")
        tipos = [(t.valor, t.tipo) for t in toks]
        self.assertIn((1234.50, "din"), tipos)
        self.assertIn((3000, "din"), tipos)
        self.assertIn((8, "mes"), tipos)
        self.assertIn((10, "pct"), tipos)


class Adaptadores(unittest.TestCase):
    def test_contrato_e_quantidade(self):
        self.assertGreaterEqual(len(ADAPTADORES), 40)
        for ad in ADAPTADORES:
            self.assertTrue(ad["chave"] and ad["palavras"])
            self.assertTrue(callable(ad["extrair"]) and callable(ad["calcular"]))

    def test_frase_alheia_nao_dispara(self):
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])

    def test_13_proporcional_bate_o_core(self):
        params, saida = _um("13º proporcional de um salário de 3000 com 8 meses", "decimo-terceiro-proporcional")
        mod = af.carregar("decimo-terceiro-proporcional", "d13_core")
        esp = mod.calcular(params["salario"], params["meses_trabalhados"], params["adiantamento"])
        self.assertIn(af._num(esp["a_receber"]), saida["resposta"])
        self.assertEqual(esp["a_receber"], 2000)

    def test_salario_liquido_bate_o_core(self):
        params, saida = _um("salário líquido de 5000 com 1 dependente", "calculadora-clt")
        mod = af.carregar("calculadora-clt", "clt_calc")
        esp = mod.salario_liquido(params["bruto"], params["dependentes"])
        self.assertIn(mod.brl(esp.liquido), saida["resposta"])

    def test_ferias(self):
        _, saida = _um("férias de um salário de 4000", "calculadora-clt")
        self.assertIn("R$", saida["resposta"])

    def test_fgts(self):
        params, saida = _um("fgts de um salário de 3000 por 24 meses", "calculadora-clt")
        self.assertEqual(params["meses"], 24)
        self.assertIn("R$", saida["resposta"])

    def test_rescisao_por_anos(self):
        _, saida = _um("rescisão salário 4000 depois de 3 anos", "calculadora-clt")
        self.assertIn("R$", saida["resposta"])

    def test_rescisao_detalhada(self):
        params, saida = _um(
            "rescisão salário 4000, 3 anos, 8 meses no ano e 15 dias trabalhados",
            "calculadora-rescisao-trabalhista",
        )
        mod = af.carregar("calculadora-rescisao-trabalhista", "rst_core")
        esp = mod.calcular_rescisao_clt(**{k: v for k, v in params.items()})
        self.assertIn(af._num(esp["total_liquido_disponivel"]), saida["resposta"])

    def test_hora_extra(self):
        params, saida = _um(
            "hora extra salário 4400, 10 horas 50% e 4 horas 100%",
            "simulador-hora-extra-50-100",
        )
        mod = af.carregar("simulador-hora-extra-50-100", "hex_core")
        esp = mod.simular(params["salario_mensal"], params["horas_base_mes"], params["horas_he50"], params["horas_he100"])
        self.assertEqual(params["horas_he50"], 10)
        self.assertEqual(params["horas_he100"], 4)
        self.assertIn(af._num(esp["total_extras"]), saida["resposta"])

    def test_noturno(self):
        params, saida = _um("adicional noturno salário 3000 com 40 horas", "calculadora-adicional-noturno")
        mod = af.carregar("calculadora-adicional-noturno", "adt_core")
        esp = mod.calcular(**{k: v for k, v in params.items()})
        self.assertIn(af._num(esp["valor_adicional_mes"]), saida["resposta"])

    def test_periculosidade(self):
        _, saida = _um("periculosidade salário 3000", "calculadora-adicional-periculosidade")
        self.assertIn("R$", saida["resposta"])

    def test_insalubridade_piso_da_ferramenta(self):
        _, saida = _um("insalubridade grau máximo", "calculadora-adicional-insalubridade")
        mod = af.carregar("calculadora-adicional-insalubridade", "ins_core")
        esp = mod.calcular("maximo", mod.SALARIO_MINIMO_PADRAO)
        self.assertIn(af._num(esp["adicional_mensal"]), saida["resposta"])

    def test_troco(self):
        _, saida = _um("troco de 100 pra 73,50", "calculadora-troco")
        mod = af.carregar("calculadora-troco", "tro_core")
        esp = mod.calcular_troco(73.50, 100)
        self.assertIn(af._num(esp["troco"]), saida["resposta"])

    def test_gorjeta(self):
        params, saida = _um("gorjeta de 10% numa conta de 180 para 4 pessoas", "calculadora-gorjeta")
        mod = af.carregar("calculadora-gorjeta", "tg_core")
        esp = mod.calcular(params["valor_conta"], params["porcentagem_gorjeta"], params["num_pessoas"])
        self.assertIn(af._num(esp["total"]), saida["resposta"])

    def test_juros_mora(self):
        params, saida = _um("juros de mora de 500 reais com 30 dias de atraso", "juros-mora")
        mod = af.carregar("juros-mora", "jmr_core")
        from datetime import date, timedelta
        pag = date.today()
        esp = mod.calcular(params["principal"], pag - timedelta(days=int(params["dias"])), pag)
        self.assertIn(af._num(esp["total"]), saida["resposta"])

    def test_compostos(self):
        _, saida = _um("quanto rende 10000 a 1% ao mês por 12 meses", "financas")
        mod = af.carregar("financas", "fin_calc")
        saldo = mod.compound(10000, 0, 0.01, 12)[-1][3]
        self.assertIn(af._num(saldo), saida["resposta"])

    def test_price(self):
        _, saida = _um("prestação price de 200 mil em 360 meses a 0,8% ao mês", "financas")
        mod = af.carregar("financas", "fin_calc")
        pmt = mod.price_pmt(200000, 0.008, 360)
        self.assertIn(af._num(pmt), saida["resposta"])

    def test_entrada(self):
        _, saida = _um(
            "financiamento do imóvel de 300 mil entrada 20% em 360 meses taxa 10% ao ano",
            "entrada-financiamento",
        )
        self.assertIn("R$", saida["resposta"])

    def test_dividir(self):
        _, saida = _um("dividir a conta de 200 entre 4 pessoas", "financas")
        self.assertIn("50,00", saida["resposta"])

    def test_moeda(self):
        _, saida = _um("100 dólares em reais", "conversor-moedas")
        mod = af.carregar("conversor-moedas", "cm_core")
        esp = mod.converter(100, "USD", "BRL")
        self.assertIn(mod.formatar(esp, "BRL"), saida["resposta"])

    def test_pix(self):
        _, saida = _um("pix taxa de 1% em uma venda de 500", "taxa-pix-recebimento")
        self.assertIn("495,00", saida["resposta"])

    def test_reserva(self):
        _, saida = _um("reserva de emergência gasto 4000 por 6 meses", "reserva-emergencia")
        self.assertIn("R$", saida["resposta"])

    def test_plr(self):
        params, saida = _um("plr de 2 salários com meta 100% salário 4000", "simulador-plr")
        mod = af.carregar("simulador-plr", "plr_core")
        esp = mod.simular(params["salario_base"], params["multiplo"], params["meta_pct"])
        self.assertIn(af._num(esp["liquido"]), saida["resposta"])

    def test_domestico(self):
        _, saida = _um("empregada doméstica salário 1500", "custo-empregado-domestico")
        self.assertIn("R$", saida["resposta"])

    def test_abono(self):
        _, saida = _um("abono pecuniário de férias salário 4000", "simulador-abono-pecuniario-ferias")
        self.assertIn("R$", saida["resposta"])

    def test_freelancer(self):
        _, saida = _um("freelancer quero ganhar 8000 por mês", "calculadora-preco-freelancer")
        self.assertIn("R$", saida["resposta"])

    def test_importacao(self):
        params, saida = _um("compra internacional de 40 dólares câmbio 5,50", "imposto-compra-internacional")
        mod = af.carregar("imposto-compra-internacional", "imx_core")
        esp = mod.calcular(params["produto_usd"], cambio=params["cambio"])
        self.assertIn(af._num(esp["total_brl"]), saida["resposta"])

    def test_festa(self):
        _, saida = _um("festa para 30 adultos comida 25 bebida 15", "orcamento-festa")
        self.assertIn("R$", saida["resposta"])

    def test_consignado(self):
        _, saida = _um("consignado de 10000 em 24 vezes a 1,5% contra pessoal 3%", "consignado-vs-credito-pessoal")
        self.assertIn("Consignado", saida["resposta"])

    def test_avista(self):
        _, saida = _um("produto de 2000 à vista com 10% de desconto ou 12x", "comparador-avista-parcelado")
        self.assertTrue(saida["resposta"])

    def test_maquininha(self):
        _, saida = _um("maquininha taxa 3% numa venda de 250", "taxa-maquininha")
        self.assertIn("242,50", saida["resposta"])

    def test_buffet_nao_e_gorjeta(self):
        _, saida = _um("buffet 80 por pessoa para 10 pessoas gorjeta 10%", "gorjeta-buffet")
        self.assertIn("R$", saida["resposta"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
