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


# F8: 3 jeitos de perguntar nas 20 chaves mais usadas (dia a dia do Caio).
# Mesma conta, superfície diferente: mil, R$, ponto de milhar, por cento, sem acento.
_TRES = (
    ("decimo-terceiro-proporcional", "A receber: R$ 2.000,00", (
        "13º proporcional de um salário de 3000 com 8 meses",
        "13o proporcional de um salario de R$ 3 mil com 8 meses",
        "decimo terceiro proporcional salario 3.000 com 8 meses",
    )),
    ("calculadora-clt", "Líquido: R$ 4.498,49", (
        "salário líquido de 5000 com 1 dependente",
        "salario liquido de R$ 5 mil com 1 dependente",
        "holerite bruto de 5.000 com 1 dependente",
    )),
    ("calculadora-rescisao-trabalhista", "Líquido da rescisão: R$ 6.941,54", (
        "rescisão salário 4000, 3 anos, 8 meses no ano e 15 dias trabalhados",
        "rescisao salario R$ 4 mil, 3 anos, 8 meses no ano e 15 dias trabalhados",
        "demissao salario 4.000, 3 anos, 8 meses no ano e 15 dias trabalhados",
    )),
    ("simulador-hora-extra-50-100", "Horas extras: R$ 460,00", (
        "hora extra salário 4400, 10 horas 50% e 4 horas 100%",
        "hora extra salario R$ 4.400, 10 horas 50 por cento e 4 horas 100%",
        "horas extras salario 4400, 10 horas 50% e 4 horas 100%",
    )),
    ("calculadora-adicional-noturno", "Adicional noturno no mês: R$ 109,09", (
        "adicional noturno salário 3000 com 40 horas",
        "adicional noturno salario R$ 3 mil com 40 horas",
        "hora noturna salario 3.000 com 40 horas",
    )),
    ("calculadora-adicional-periculosidade", "Periculosidade no mês: R$ 900,00", (
        "periculosidade salário 3000",
        "periculosidade salario R$ 3 mil",
        "periculosidade de 3.000",
    )),
    ("calculadora-adicional-insalubridade", "Insalubridade no mês: R$ 607,20", (
        "insalubridade grau máximo",
        "insalubridade grau maximo",
        "insalubridade 40%",
    )),
    ("calculadora-troco", "Troco: R$ 26,50", (
        "troco de 100 pra 73,50",
        "troco de R$ 100 pra 73,50",
        "troco de 100 reais pra 73,50",
    )),
    ("calculadora-gorjeta", "Total com gorjeta: R$ 198,00", (
        "gorjeta de 10% numa conta de 180 para 4 pessoas",
        "gorjeta de 10 por cento numa conta de R$ 180 para 4 pessoas",
        "gorjeta de 10% numa conta de 180 reais para 4 pessoas",
    )),
    ("juros-mora", "Total atualizado: R$ 515,00", (
        "juros de mora de 500 reais com 30 dias de atraso",
        "juros de mora de R$ 500 com 30 dias de atraso",
        "juros de mora de 500 com 30 dias de atraso",
    )),
    ("financas", "Saldo: R$ 11.268,25", (
        "quanto rende 10000 a 1% ao mês por 12 meses",
        "quanto rende R$ 10 mil a 1% ao mes por 12 meses",
        "quanto rende 10.000 a 1 por cento ao mes por 12 meses",
    )),
    ("entrada-financiamento", "Prestação: R$ 2.106,17", (
        "financiamento do imóvel de 300 mil entrada 20% em 360 meses taxa 10% ao ano",
        "financiamento do imovel de R$ 300 mil entrada 20% em 360 meses taxa 10% ao ano",
        "entrada do apartamento de 300.000 20 por cento em 360 meses taxa 10% ao ano",
    )),
    ("conversor-moedas", "100.0 USD = R$ 555,00", (
        "100 dólares em reais",
        "100 dolares em reais",
        "usd 100 em reais",
    )),
    ("taxa-pix-recebimento", "Líquido no Pix: R$ 495,00", (
        "pix taxa de 1% em uma venda de 500",
        "pix taxa de 1 por cento em uma venda de R$ 500",
        "taxa pix de 1% em uma venda de 500 reais",
    )),
    ("taxa-maquininha", "Você recebe: R$ 242,50", (
        "maquininha taxa 3% numa venda de 250",
        "maquininha taxa 3 por cento numa venda de R$ 250",
        "taxa da maquininha 3% numa venda de 250 reais",
    )),
    ("comparador-avista-parcelado", "Melhor: avista", (
        "produto de 2000 à vista com 10% de desconto ou 12x",
        "produto de R$ 2 mil a vista com 10% de desconto ou 12x",
        "produto de 2.000 avista com 10 por cento de desconto ou 12 vezes",
    )),
    ("reserva-emergencia", "Aporte da reserva: R$ 2.000,00", (
        "reserva de emergência gasto 4000 por 6 meses",
        "reserva de emergencia gasto R$ 4 mil por 6 meses",
        "colchao gasto 4.000 por 6 meses",
    )),
    ("poupanca-meta", "Saldo final: R$ 5.308,39", (
        "poupanca de 5000 por 12 meses",
        "poupanca de R$ 5 mil por 12 meses",
        "render poupanca 5.000 por 12 meses",
    )),
    ("consignado-vs-credito-pessoal", "Mais barato: Consignado", (
        "consignado de 10000 em 24 vezes a 1,5% contra pessoal 3%",
        "consignado de R$ 10 mil em 24 vezes a 1,5% contra pessoal 3%",
        "consignado de 10.000 em 24x a 1,5 por cento contra pessoal 3%",
    )),
    ("custo-empregado-domestico", "Custo mensal: R$ 1.800,00", (
        "empregada doméstica salário 1500",
        "empregada domestica salario R$ 1.500",
        "diarista salario 1.500",
    )),
)



# F8: os 59 registros, na ordem do ADAPTADORES.
_TODOS = (
    ('decimo-terceiro-proporcional', 'A receber: R$ 2.000,00', (
        '13o proporcional salario 3000 8 meses',
        'decmo proporcional salario 3000 8 meses',
        '13 de um salario de R$ 3 mil com 8 meses',
    )),
    ('calculadora-clt', 'Líquido: R$ 4.498,49', (
        'holerite salario 5000 1 dependente',
        'salario liq 5000 1 dependente',
        'salario liquido de R$ 5 mil com 1 dependente',
    )),
    ('calculadora-clt', 'Líquido: R$ 4.662,70', (
        'ferias salario 4000',
        'ferias salaro 4000',
        'ferias de um salario de R$ 4 mil',
    )),
    ('calculadora-clt', 'Líquido: R$ 2.751,40', (
        '13 inss salario 3000',
        'decimo holerite salario 3000',
        '13 salario inss de R$ 3 mil',
    )),
    ('calculadora-clt', 'Saldo final: R$ 6.413,56', (
        'fgts salario 3000 24 meses',
        'fundo de garantia salario 3000 24 meses',
        'fgts de um salario de R$ 3 mil por 24 meses',
    )),
    ('calculadora-clt', 'Líquido: R$ 10.509,17', (
        'rescisao salario 4000 3 anos',
        'recisao salario 4000 3 anos',
        'rescisao salario de R$ 4 mil depois de 3 anos',
    )),
    ('calculadora-rescisao-trabalhista', 'Líquido da rescisão: R$ 12.412,88', (
        'rescisao salario 4000 3 anos 8 meses 15 dias',
        'recisao salario 4000 3 anos 8 meses 15 dias',
        'rescisao salario de R$ 4 mil, 3 anos, 8 meses e 15 dias',
    )),
    ('simulador-abono-pecuniario-ferias', 'Venda de férias: R$ 4.000,00', (
        'abono ferias salario 4000',
        'vender ferias salario 4000',
        'abono pecuniario de ferias salario de R$ 4 mil',
    )),
    ('simulador-hora-extra-50-100', 'Horas extras: R$ 460,00', (
        'he50 salario 4400 10 horas 50% e 4 horas 100%',
        'hora estra salario 4400 10h 50% e 4h 100%',
        'hora extra salario de R$ 4.400, 10 horas 50% e 4 horas 100%',
    )),
    ('calculadora-adicional-noturno', 'Adicional noturno no mês: R$ 109,09', (
        'noturno salario 3000 40 horas',
        'notuno salario 3000 40h',
        'adicional noturno salario de R$ 3 mil com 40 horas',
    )),
    ('calculadora-adicional-periculosidade', 'Periculosidade no mês: R$ 900,00', (
        'pericul salario 3000',
        'periculozidade salario 3000',
        'periculosidade salario de R$ 3 mil',
    )),
    ('calculadora-adicional-insalubridade', 'Insalubridade no mês: R$ 607,20', (
        'insalubr grau max',
        'insalubridade grau maximo',
        'insalubridade grau máximo',
    )),
    ('calculadora-adicional-sobreaviso-prontidao', 'Sobreaviso/prontidão no mês: R$ 272,73', (
        'sobreaviso salario 3000',
        'sobreaviso salario 3000 escala 60 horas',
        'sobreaviso de R$ 3 mil',
    )),
    ('calculadora-equiparacao-salarial-clt', 'Diferença total: R$ 31.578,67', (
        'paradigma 5000 salario 3000 12 meses',
        'equiparacao colega 5000 eu ganho 3000 12 meses',
        'equiparacao colega R$ 5 mil meu salario R$ 3 mil em 12 meses',
    )),
    ('simulador-banco-horas-compensacao', 'Saldo do banco: +10h 00m', (
        'banco de hora salario 3000 10 horas',
        'banco de hora salario 3000 10h extras',
        'banco de horas salario de R$ 3 mil com 10 horas',
    )),
    ('calculadora-custo-contratacao-funcionario', 'Custo mensal do funcionário: R$ 5.288,00', (
        'custo funcionario salario 4000',
        'folha do empregado salario 4000',
        'custo de contratar funcionario salario de R$ 4 mil',
    )),
    ('custo-empregado-domestico', 'Custo mensal: R$ 1.800,00', (
        'diarista salario 1500',
        'empregada domestica salario 1500',
        'empregada domestica salario de R$ 1.500',
    )),
    ('comparador-clt-pj', 'PJ para empatar: R$ 8.387,23 de faturamento por mês', (
        'pj clt salario 5000',
        'virar pj salario 5000',
        'quanto faturar pj salario de R$ 5 mil',
    )),
    ('calculadora-beneficio-vr-va', 'Líquido do vale: R$ 660,00', (
        'vr 30 por dia 22 dias',
        'vale refeicao 30 por dia 22 dias',
        'vale refeicao de R$ 30 por dia 22 dias',
    )),
    ('simulador-plr', 'PLR líquida: R$ 7.973,00', (
        'plr 2 salarios meta 100% salario 4000',
        'plr 2 salrios meta 100% salario 4000',
        'plr de 2 salarios meta 100% salario de R$ 4 mil',
    )),
    ('calculadora-preco-freelancer', 'Hora freelancer: R$ 107,96', (
        'freela ganhar 8000',
        'hora tecnica ganhar 8000',
        'freelancer quero ganhar R$ 8 mil por mes',
    )),
    ('comparador-salario-beneficios', 'Melhor pacote: A', (
        'proposta salario 5000 contra salario 4500',
        'beneficio salario 5000 versus salario 4500',
        'proposta salario de R$ 5 mil contra salario de R$ 4.500',
    )),
    ('comparador-salario-cidade', 'Para igualar A, B precisa pagar: R$ 6.000,00', (
        'indice 100 salario 5000 contra indice 120 salario 5500',
        'indice 100 salario 5000 vs indice 120 salario 5500',
        'indice 100 salario de R$ 5 mil contra indice 120 salario de R$ 5.500',
    )),
    ('juros-mora', 'Total atualizado: R$ 515,00', (
        'mora 500 30 dias boleto',
        'boleto 500 atraso 30 dias',
        'juros de mora de R$ 500 com 30 dias de atraso',
    )),
    ('financas', 'Saldo: R$ 11.268,25', (
        'rende 10000 1% 12 meses',
        'aplicado 10000 rende 1% ao mes 12 meses',
        'quanto rende R$ 10 mil a 1% ao mes por 12 meses',
    )),
    ('financas', 'Prestação Price: R$ 1.696,32', (
        'price 200000 360 meses 0,8% ao mes',
        'prestacao 200000 360 meses taxa 0,8% ao mes',
        'price de R$ 200 mil em 360 meses a 0,8% ao mes',
    )),
    ('financas', 'Cada um paga: R$ 50,00', (
        'rachar 200 entre 4',
        'dividir 200 entre 4 pessoas',
        'dividir a conta de R$ 200 entre 4 pessoas',
    )),
    ('entrada-financiamento', 'Prestação: R$ 2.106,17', (
        'entrada 20% imovel 300000 360 meses taxa 10% ao ano',
        'apartamento 300000 entrada 20% 360 meses juros 10% ao ano',
        'financiamento do imovel de R$ 300 mil entrada 20% em 360 meses taxa 10% ao ano',
    )),
    ('consignado-vs-credito-pessoal', 'Mais barato: Consignado', (
        'consignado 10000 24x 1,5% pessoal 3%',
        'consignado 10000 24 vezes 1,5% pessoal 3%',
        'consignado de R$ 10 mil em 24 vezes a 1,5% contra pessoal 3%',
    )),
    ('cartao-rotativo', 'Custo extra do rotativo: R$ 492,09', (
        'rotativo fatura 1000 pagar 200',
        'rotativo fatura 1000 pago 200',
        'rotativo fatura R$ 1 mil pagamento R$ 200',
    )),
    ('cartao-rotativo', 'Parcela: R$ 100,46', (
        'parcelar fatura 1000 12x taxa 3%',
        'parcelamento da fatura 1000 12 vezes juros 3%',
        'parcelar a fatura de R$ 1 mil em 12 vezes taxa 3%',
    )),
    ('simulador-aposentadoria', 'Patrimônio: R$ 284.499,53', (
        'aposentadoria guardo 500 por mes 20 anos taxa 8% ao ano',
        'independencia financeira aporte 500 por mes 20 anos juros 8% ao ano',
        'aposentadoria guardo R$ 500 por mes por 20 anos taxa 8% ao ano',
    )),
    ('simulador-aposentadoria', 'Patrimônio necessário: R$ 1.200.000,00', (
        'aposentadoria gastar 4000 por mes',
        'regra dos 4 aposentar gastar 4000',
        'aposentadoria quero gastar R$ 4 mil por mes',
    )),
    ('poupanca-meta', 'Saldo final: R$ 5.308,39', (
        'poupanca 5000 12 meses',
        'poupanca de 5000 em 12 meses',
        'poupanca de R$ 5 mil por 12 meses',
    )),
    ('poupanca-meta', 'Meses até a meta: 20', (
        'poupanca meta 10000 guardo 500 por mes',
        'juntar meta 10000 aporte 500',
        'poupanca meta de R$ 10 mil guardo R$ 500 por mes',
    )),
    ('reserva-emergencia', 'Aporte da reserva: R$ 2.000,00', (
        'colchao gasto 4000 6 meses',
        'reserva emergencia gasto 4000 6 meses',
        'reserva de emergencia gasto de R$ 4 mil por 6 meses',
    )),
    ('taxa-maquininha', 'Você recebe: R$ 242,50', (
        'maquininha taxa 3% venda 250',
        'maquininha debito 3% venda 250',
        'maquininha taxa 3% numa venda de R$ 250',
    )),
    ('taxa-pix-recebimento', 'Líquido no Pix: R$ 495,00', (
        'pix taxa 1% venda 500',
        'pix recebimento taxa 1% valor 500',
        'pix taxa de 1% em uma venda de R$ 500',
    )),
    ('imposto-compra-internacional', 'Total em reais: R$ 318,06', (
        'importacao 40 dolares cambio 5,50',
        'compra internacional 40 usd cambio 5,50',
        'compra internacional de 40 dolares cambio 5,50',
    )),
    ('cartao-ou-especie-viagem', 'No cartão sai R$ 569,25', (
        'viagem cartao gastar 100 dolares cotacao 5,50',
        'iof viagem dolar gastar 100 cotacao 5,50',
        'viagem no cartao gastar 100 dolares cotacao 5,50',
    )),
    ('calculadora-troco', 'Troco: R$ 26,50', (
        'troco 100 pra 73,50',
        'troco paguei 100 conta 73,50',
        'troco de R$ 100 pra R$ 73,50',
    )),
    ('calculadora-gorjeta', 'Total com gorjeta: R$ 198,00', (
        'gorjeta 10% conta 180 4 pessoas',
        'gorjeta de 10% numa conta de 180 para 4 pessoas',
        'gorjeta de 10% conta de R$ 180 para 4 pessoas',
    )),
    ('gorjeta-buffet', 'Total do buffet: R$ 880,00', (
        'buffet 80 10 pessoas gorjeta 10%',
        'buffet 80 por pessoa 10 pessoas gorjeta 10%',
        'buffet de R$ 80 por pessoa para 10 pessoas gorjeta 10%',
    )),
    ('calculadora-taxa-delivery', 'Total do delivery: R$ 58,00', (
        'delivery pedido 50 taxa 8',
        'ifood pedido 50 entrega 8',
        'delivery pedido R$ 50 taxa R$ 8',
    )),
    ('comparador-avista-parcelado', 'Melhor: avista', (
        'avista 2000 desconto 10% 12x',
        'a vista 2000 desconto 10% ou 12x',
        'produto de R$ 2 mil a vista com 10% de desconto ou 12x',
    )),
    ('conversor-moedas', '100.0 USD = R$ 555,00', (
        '100 usd em reais',
        '100 dolares em real',
        '100 dolares em reais',
    )),
    ('comparador-preco-unitario', 'Mais barato por unidade: opção 1', (
        'preco unitario 10 reais com 2 un contra 15 reais com 3 un',
        'por quilo 10 reais com 2 kg contra 15 reais com 3 kg',
        'preco unitario R$ 10 com 2 un contra R$ 15 com 3 un',
    )),
    ('comparador-atacado-varejo', 'Melhor: atacado', (
        'atacado 20 reais 10 unidades do atacado varejo 5 reais 1 unidades do varejo',
        'atacado 20 real 10 unidades do atacado varejo 5 real 1 unidades do varejo',
        'atacado R$ 20 com 10 unidades do atacado varejo R$ 5 com 1 unidades do varejo',
    )),
    ('comparador-generico-marca', 'Economia do genérico: R$ 15,00', (
        'generico 15 marca 30',
        'generico 15 reais marca 30 reais',
        'generico R$ 15 marca R$ 30',
    )),
    ('cartucho-vs-toner', 'Mais barato: toner', (
        'cartucho 80 200 paginas do cartucho toner 300 2000 paginas do toner 100 por mes',
        'cartucho R$ 80 200 paginas do cartucho toner R$ 300 2000 paginas do toner 100 por mes',
        'cartucho 80 reais 200 paginas do cartucho toner 300 reais 2000 paginas do toner 100 por mes',
    )),
    ('frete-sedex-vs-pac', 'Recomendação: sedex', (
        'sedex 40 reais 2 dias sedex pac 25 reais 6 dias pac',
        'sedex 40 reais 2 dia sedex pac 25 reais 6 dia pac',
        'sedex R$ 40 2 dias sedex pac R$ 25 6 dias pac',
    )),
    ('orcamento-festa', 'Total da festa: R$ 1.200,00', (
        'festa 30 adultos comida 25 bebida 15',
        'aniversario 30 pessoas comida 25 bebida 15',
        'festa para 30 adultos comida de R$ 25 bebida de R$ 15',
    )),
    ('lance-consorcio', 'Recomendação: dar_lance', (
        'lance 30% consorcio credito 50000 parcela 500 40 meses',
        'lance consorcio 30% carta 50000 prestacao 500 faltam 40 meses',
        'lance de 30% no consorcio credito de R$ 50 mil parcela de R$ 500 restam 40 meses',
    )),
    ('comparador-credito', 'Juros economizados: R$ 9.259,57', (
        'amortizar financiamento 100000 120 meses juros 10% extra 200',
        'amortizacao saldo 100000 120 meses taxa 10% ao ano a mais 200',
        'amortizar financiamento de R$ 100 mil em 120 meses juros 10% ao ano extra de R$ 200',
    )),
    ('comparador-credito', 'Mais barato: financiamento', (
        'consorcio financiamento carro 80000 60 meses juros 12% admin 15%',
        'consorcio ou financiamento bem 80000 60 meses juros 12% administracao 15%',
        'consorcio vs financiamento carro de R$ 80 mil em 60 meses taxa do financiamento 12% taxa do consorcio 15%',
    )),
    ('calculadora-alavancagem', 'Quantidade de equilíbrio: 100,00', (
        'alavancagem preco 50 variavel 20 fixo 3000',
        'ponto de equilibrio preco 50 variavel 20 fixos 3000',
        'alavancagem preco R$ 50 variavel R$ 20 fixo R$ 3 mil',
    )),
    ('calculadora-financeira-black-scholes', 'Call: R$ 8,18', (
        'black scholes acao 100 strike 110 1 ano juros 10% vol 20%',
        'opcao de compra preco 100 exercicio 110 1 ano taxa 10% volatilidade 20%',
        'black-scholes acao R$ 100 strike R$ 110 em 1 ano selic 10% vol 20%',
    )),
    ('simulador-financiamento-estudantil-fies', 'Saldo na formatura: R$ 36.000,00', (
        'fies mensalidade 1500 financiado 50% 48 meses',
        'financiamento estudantil faculdade 1500 percentual 50% 48 meses',
        'fies mensalidade de R$ 1.500 financiado 50% em 48 meses',
    )),
    ('simulador-transicao-carreira-reserva', 'Meses de fôlego: 4,20', (
        'runway reserva 20000 essencial 4000',
        'folego financeiro guardado 20000 gasto 4000',
        'transicao de carreira tenho R$ 20 mil despesa R$ 4 mil',
    )),
    ('lista-feira-orcamento', 'Total da feira: R$ 17,00', (
        'lista da feira orcamento 100 quantidade 2 preco 8,50',
        'feira orcamento 100 qtd 2 preco 8,50',
        'lista da feira teto de 100 reais quantidade 2 preco 8,50',
    )),
    ('rateio-condominio', 'Total em atraso: R$ 460,50', (
        'condominio 450 atrasado 10 dias',
        'condominio de 450 atrasado 10 dias',
        'condominio de 450 reais atrasado ha 10 dias',
    )),
    ('conta-luz-republica', 'Cada um: R$ 106,67', (
        'conta de luz da republica 320 reais para 3 moradores',
        'luz na republica 320 reais entre 3 pessoas',
        'conta de luz da republica de 320 reais com 3 moradores',
    )),
    ('orcamento-mudanca', 'Total da mudança: R$ 1.020,00', (
        'mudanca volume 12 capacidade 20 frete 600 30 caixas por caixa 4 2 ajudantes diaria 150',
        'mudanca volume 12 capacidade 20 frete 600 caixas 30 por caixa 4 ajudantes 2 diaria 150',
        'orcamento de mudanca volume 12 capacidade 20 frete 600 30 caixas por caixa 4 2 ajudantes diaria 150',
    )),
    ('comparador-mercado', 'Economia no mês: R$ 10,80', (
        'no mercado o caro sai 12,50 e o barato 9,80 consumo 4',
        'caro 12,50 barato 9,80 consumo 4',
        'o caro sai R$ 12,50 o barato R$ 9,80 consumo 4',
    )),
    ('frete-vendas', 'Preço mínimo: R$ 105,88', (
        'preco minimo produto 50 embalagem 4 frete 18 taxa 12% margem 20%',
        'preco minimo produto 50 reais embalagem 4 reais frete 18 reais taxa 12% margem 20%',
        'preco minimo produto R$ 50 embalagem R$ 4 frete R$ 18 taxa 12% margem 20%',
    )),
    ('planejador-compras-atacado', 'Custo no atacado: R$ 64,00', (
        'compras no atacado consumo 2 estoque 4 semanas preco 8 orcamento 100 validade 90 dias',
        'atacado consumo 2 estoque 4 preco 8 orcamento 100 validade 90 dias',
        'lista de compras no atacado consumo 2 estoque 4 semanas preco 8 orcamento 100 validade 90 dias',
    )),
    ('orcamento-reforma', 'Total da reforma: R$ 750,00', (
        'orcamento de reforma material 200 mao de obra 150 quantidade 3',
        'reforma material 200 mao de obra 150 quantidade 3',
        'reforma material de 200 mao de obra de 150 quantidade 3',
    )),
    ('orcamento-natal', 'Ceia de natal: R$ 540,00', (
        'ceia de natal para 12 convidados a 45 reais',
        'ceia de natal 12 convidados 45 reais',
        'ceia de natal para 12 convidados a 45 reais de extra 0',
    )),
    ('orcamento-lua-de-mel', 'Total da lua de mel: R$ 4.800,00', (
        'lua de mel passagem 2000 hotel 400 por 7 noites',
        'lua de mel passagem 2000 reais hotel 400 7 noites',
        'lua de mel passagem R$ 2 mil diaria 400 7 noites',
    )),
    ('orcamento-reforma-cozinha', 'Total da cozinha: R$ 12.320,00', (
        'reforma da cozinha moveis 4000 eletros 2500 bancada 1800 revestimento 900 mao de obra 2000',
        'cozinha moveis 4000 eletros 2500 bancada 1800 revestimento 900 mao de obra 2000',
        'cozinha moveis 4 mil eletros 2500 bancada 1800 revestimento 900 mao de obra 2 mil',
    )),
    ('orcamento-presentes-casamento', 'Presentes do casamento: R$ 8.400,00', (
        'lista de casamento 80 convidados presente medio 150 reais',
        'casamento 80 convidados presente de 150 reais',
        'lista de casamento 80 convidados presente medio de R$ 150',
    )),
    ('custo-fralda-geriatrica', 'Fralda no mês: R$ 405,00', (
        'fralda geriatrica 6 trocas pacote de 45 reais com 20 unidades',
        'geriatrica 6 trocas pacote de 45 reais 20 unidades',
        'custo da fralda geriatrica 6 trocas pacote de 45 reais 20 unidades',
    )),
    ('planejador-casamento', 'Custo por pessoa: R$ 200,00', (
        'custo do casamento 20000 reais por pessoa com 100 pessoas',
        'casamento de 20000 reais por pessoa com 100 pessoas',
        'casamento de R$ 20 mil por pessoa com 100 pessoas',
    )),
    ('orcamento-manutencao-predial', 'Por unidade no mês: R$ 70,00', (
        'manutencao predial elevador 400 limpeza 300 para 10 unidades',
        'manutencao do predio elevador 400 limpeza 300 10 unidades',
        'manutencao predial elevador 400 reais limpeza 300 reais para 10 unidades',
    )),
)

class TresJeitos(unittest.TestCase):
    def test_vinte_chaves_tres_frases(self):
        self.assertEqual(len(_TRES), 20)
        for chave, esperado, frases in _TRES:
            self.assertEqual(len(frases), 3, chave)
            for frase in frases:
                _, saida = _um(frase, chave)
                self.assertEqual(saida["resposta"], esperado, frase)

    def test_todos_os_adaptadores(self):
        """Cada registro: abreviado, com erro e com R$/mil, a mesma resposta."""
        self.assertEqual([a["chave"] for a in ADAPTADORES], [c for c, _, _ in _TODOS])
        for chave, esperado, frases in _TODOS:
            self.assertEqual(len(frases), 3, chave)
            for frase in frases:
                _, saida = _um(frase, chave)
                self.assertEqual(saida["resposta"], esperado, frase)



if __name__ == "__main__":
    unittest.main(verbosity=2)
