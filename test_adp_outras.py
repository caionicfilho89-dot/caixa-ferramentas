# -*- coding: utf-8 -*-
"""Testa os adaptadores de Outras chamando o nucleo real."""
from __future__ import annotations

import unittest

import adp_financas as af
import adp_outras as ao


def _hits(texto):
    return [a for a in ao.ADAPTADORES if a["extrair"](texto) is not None]


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


class Outras(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(ao.ADAPTADORES), 24)
        for frase in (
            "que horas o onibus passa na praca",
            "20% de 350",
            "ipva de um carro de 60 mil em SP",
            "troco de 100 pra 73,50",
        ):
            self.assertEqual(_hits(frase), [], frase)

    def test_iptu_tres_jeitos(self):
        mod = af.carregar("calculadora-iptu", "ipt_core")
        esperado = af._brl(mod.calcular(300000, 1, 0, 1)["liquido"])
        frases = (
            "iptu venal 300000 aliquota 1%",
            "iptu venal R$ 300 mil aliquota 1%",
            "iptu venal 300.000 aliquota 1 por cento",
        )
        for frase in frases:
            self.assertEqual(_um(frase, "calculadora-iptu")["resposta"], esperado, frase)

    def test_caucao(self):
        mod = af.carregar("calculadora-caucao", "cau_core")
        r = mod.calcular(2000, 3, 30, 0.8)
        frases = (
            "caucao aluguel 2000",
            "caucao aluguel R$ 2 mil",
            "caucao de aluguel 2.000",
        )
        for frase in frases:
            self.assertEqual(_um(frase, "calculadora-caucao")["resposta"], af._brl(r["deposito"]), frase)

    def test_caixa(self):
        mod = af.carregar("autonomia-caixa-dagua", "cda_core")
        r = mod.autonomia(1000, 4, 150)
        frases = (
            "autonomia da caixa dagua volume 1000 pessoas 4 por pessoa 150",
            "caixa d'agua volume 1000 pessoas 4 por pessoa 150",
            "caixa d agua volume R$ 1 mil pessoas 4 por pessoa 150",
        )
        for frase in frases:
            self.assertEqual(
                _um(frase, "autonomia-caixa-dagua")["resposta"],
                af._num(r["dias"], 1) + " dias",
                frase,
            )

    def test_limpeza(self):
        mod = af.carregar("diluicao-limpeza", "dil_core")
        r = mod.diluir(10, 1, 1000)
        frases = (
            "diluir limpeza produto 10% desejada 1% volume 1000",
            "diluicao de limpeza produto 10% desejada 1% volume 1000",
            "diluicao limpeza concentrado 10 por cento desejada 1% volume 1 mil",
        )
        for frase in frases:
            self.assertEqual(
                _um(frase, "diluicao-limpeza")["resposta"],
                af._num(r["produto_ml"], 1) + " ml",
                frase,
            )

    def test_extenso(self):
        mod = af.carregar("numero-extenso", "ext_core")
        esperado = mod.extenso(1234)
        for frase in (
            "numero por extenso 1234",
            "por extenso 1234",
            "escreve por extenso 1.234",
        ):
            self.assertEqual(_um(frase, "numero-extenso")["resposta"], esperado, frase)

    def test_romano(self):
        mod = af.carregar("numero-extenso", "ext_core")
        esperado = mod.to_roman(2026)
        for frase in (
            "algarismo romano 2026",
            "em romanos 2026",
            "numero romano 2026",
        ):
            self.assertEqual(_um(frase, "numero-extenso")["resposta"], esperado, frase)

    def test_reajuste(self):
        mod = af.carregar("reajuste-aluguel", "alu_core")
        novo, _ = mod.reajustar(1800, 5)
        for frase in (
            "reajuste de aluguel valor 1800 percentual 5%",
            "reajuste do aluguel valor R$ 1.800 percentual 5%",
            "reajustar aluguel valor 1800 percentual 5 por cento",
        ):
            self.assertEqual(_um(frase, "reajuste-aluguel")["resposta"], af._brl(novo), frase)

    def test_btu(self):
        mod = af.carregar("calculadora-ar-condicionado", "btu_core")
        bruto = mod.btu_necessario(20, 2, 0)
        modelo = mod.modelo_comercial(bruto)
        esperado = af._num(modelo, 0) + " BTU"
        for frase in (
            "ar condicionado area 20 pessoas 2",
            "ar-condicionado area 20 pessoas 2",
            "ar condicionado area 20 m2 pessoas 2",
        ):
            self.assertEqual(_um(frase, "calculadora-ar-condicionado")["resposta"], esperado, frase)

    def test_chuveiro(self):
        mod = af.carregar("consumo-energia", "kwh_core")
        _kwh, custo = mod.chuveiro(5500, 10, 2, 0.9)
        for frase in (
            "conta do chuveiro watts 5500 minutos 10 banhos 2 tarifa 0,90",
            "chuveiro eletrico watts 5500 minutos 10 banhos 2 tarifa 0,90",
            "gasto do chuveiro watts 5.500 minutos 10 banhos 2 tarifa R$ 0,90",
        ):
            self.assertEqual(_um(frase, "consumo-energia")["resposta"], af._brl(custo), frase)

    def test_das(self):
        mod = af.carregar("calculadora-simples-nacional", "snl_core")
        anexo = list(mod.ANEXOS)[0]
        das, _ef = mod.das_mensal(10000, 120000, anexo)
        for frase in (
            "simples nacional receita 10000 rbt12 120000 anexo comercio",
            "simples nacional receita R$ 10 mil rbt12 120000 comercio",
            "simples nacional faturamento 10000 rbt12 120.000 anexo comercio",
        ):
            self.assertEqual(_um(frase, "calculadora-simples-nacional")["resposta"], af._brl(das), frase)

    def test_fila(self):
        mod = af.carregar("teoria-filas", "qth_core")
        r = mod.mm1(8, 10)
        self.assertEqual(
            _um("fila mm1 chegada 8 atendimento 10", "teoria-filas")["resposta"],
            af._num(r["Wq"], 3) + " h",
        )
        ruim = mod.mm1(10, 8)
        self.assertEqual(
            _um("fila m/m/1 chegada 10 atendimento 8", "teoria-filas")["resposta"],
            ruim["message"],
        )

    def test_calor(self):
        mod = af.carregar("calculadora-indice-conforto", "wci_core")
        r = mod.heat_index_c(32, 70)
        for frase in (
            "indice de calor temperatura 32 umidade 70%",
            "heat index temperatura 32 umidade 70%",
            "indice de calor temp 32 ur 70 por cento",
        ):
            self.assertEqual(
                _um(frase, "calculadora-indice-conforto")["resposta"],
                af._num(r["heat_index_c"], 1) + " °C",
                frase,
            )

    def test_engrenagem(self):
        mod = af.carregar("calculadora-engrenagens", "grs_core")
        r = mod.calculate_gear_pair(2, 20, 40)
        for frase in (
            "engrenagem modulo 2 z1 20 z2 40",
            "engrenagens modulo 2 pinhao 20 coroa 40",
            "engrenagem modulo 2 z1 20 z2 40 dentes",
        ):
            self.assertEqual(
                _um(frase, "calculadora-engrenagens")["resposta"],
                af._num(r["center_distance_mm"], 1) + " mm",
                frase,
            )

    def test_cubado(self):
        mod = af.carregar("cubagem-cargas", "cub_core")
        r = mod.calculate_volumetric_freight(40, 30, 20, 5)
        for frase in (
            "frete cubado comp 40 larg 30 alt 20 peso 5",
            "peso cubado comprimento 40 largura 30 altura 20 peso 5",
            "frete cubado comp 40 larg 30 alt 20 kg 5",
        ):
            self.assertEqual(
                _um(frase, "cubagem-cargas")["resposta"],
                af._num(r["air_billable_kg"], 2) + " kg",
                frase,
            )

    def test_gray(self):
        mod = af.carregar("estudio-gray-code", "gry_core")
        esperado = str(mod.bin_to_gray(13))
        for frase in ("codigo gray 13", "codigo de gray 13", "gray 13"):
            self.assertEqual(_um(frase, "estudio-gray-code")["resposta"], esperado, frase)

    def test_cisterna(self):
        mod = af.carregar("cisterna-chuva", "cis_core")
        r = mod.captacao_mensal(80, 120)
        for frase in (
            "cisterna area 80 chuva 120",
            "cisterna telhado 80 chuva 120",
            "cisterna area 80 mm 120",
        ):
            self.assertEqual(
                _um(frase, "cisterna-chuva")["resposta"],
                af._num(r["litros"], 0) + " L",
                frase,
            )

    def test_eolica(self):
        mod = af.carregar("calculadora-energia-eolica-aerogerador", "eoc_core")
        w = mod.potencia_vento_disponivel(2, 8)
        for frase in (
            "potencia eolica raio 2 vento 8",
            "energia eolica raio 2 vento 8",
            "aerogerador raio 2 vento 8",
        ):
            self.assertEqual(
                _um(frase, "calculadora-energia-eolica-aerogerador")["resposta"],
                af._num(w, 0) + " W",
                frase,
            )

    def test_dizimo(self):
        mod = af.carregar("dizimo-doacoes", "dzm_core")
        valor = mod.calcular_dizimo(5000, 10)
        for frase in (
            "dizimo renda 5000",
            "dizimo renda R$ 5 mil",
            "dizimo renda 5000 percentual 10%",
        ):
            self.assertEqual(_um(frase, "dizimo-doacoes")["resposta"], af._brl(valor), frase)

    def test_pensao(self):
        mod = af.carregar("pensao-alimenticia", "pen_core")
        r = mod.calcular(4000, 30, 2)
        for frase in (
            "pensao alimenticia renda 4000 percentual 30% filhos 2",
            "pensao renda R$ 4 mil percentual 30% filhos 2",
            "pensao alimenticia renda 4000 percentual 30 por cento filhos 2",
        ):
            self.assertEqual(_um(frase, "pensao-alimenticia")["resposta"], af._brl(r["pensao"]), frase)

    def test_cashback(self):
        mod = af.carregar("cashback-real", "csh_core")
        r = mod.calcular(2000, 1.5)
        for frase in (
            "cashback real gasto 2000 percentual 1,5%",
            "cashback gasto R$ 2 mil percentual 1,5%",
            "cashback real gasto 2000 percentual 1.5%",
        ):
            self.assertEqual(_um(frase, "cashback-real")["resposta"], af._brl(r["liquido"]), frase)

    def test_prestacoes(self):
        mod = af.carregar("saldo-prestacoes", "pst_core")
        r = mod.saldo(350, 48, 10)
        for frase in (
            "saldo de prestacoes parcela 350 totais 48 pagas 10",
            "saldo das prestacoes parcela R$ 350 totais 48 pagas 10",
            "prestacoes parcela 350 total 48 paguei 10",
        ):
            self.assertEqual(_um(frase, "saldo-prestacoes")["resposta"], af._brl(r["total_devido"]), frase)

    def test_viagem(self):
        mod = af.carregar("meta-poupanca-viagem", "rvg_core")
        r = mod.planejar(8000, 10, 0)
        for frase in (
            "poupanca viagem meta 8000 em 10 meses",
            "poupanca de viagem meta R$ 8 mil em 10 meses",
            "guardar pra viagem meta 8000 em 10 meses",
        ):
            self.assertEqual(
                _um(frase, "meta-poupanca-viagem")["resposta"],
                af._brl(r["parcela"]) + "/mes",
                frase,
            )

    def test_km(self):
        mod = af.carregar("custo-total-por-km", "ckm_core")
        r = mod.calcular(6, 12, 800)
        for frase in (
            "custo por km litro 6 kml 12 rodados 800",
            "custo do km preco 6 consumo 12 rodados 800",
            "custo por km litro R$ 6 kml 12 km mes 800",
        ):
            self.assertEqual(
                _um(frase, "custo-total-por-km")["resposta"],
                "R$ " + af._num(r["total_km"], 3) + "/km",
                frase,
            )

    def test_frete(self):
        mod = af.carregar("estimativa-frete", "fre_core")
        r = mod.estimar(2, 400)
        for frase in (
            "estimativa de frete peso 2 distancia 400",
            "estimar frete peso 2 distancia 400",
            "estimativa de frete peso 2 km 400",
        ):
            self.assertEqual(_um(frase, "estimativa-frete")["resposta"], af._brl(r["total"]), frase)

    def test_tag(self):
        mod = af.carregar("custo-pedagio-tag", "tag_core")
        r = mod.calcular(18.5, 20, 5)
        for frase in (
            "pedagio com tag valor 18,50 viagens 20 desconto 5%",
            "pedagio tag valor R$ 18,50 viagens 20 desconto 5%",
            "tag de pedagio valor 18,50 vezes 20 desconto 5 por cento",
        ):
            self.assertEqual(_um(frase, "custo-pedagio-tag")["resposta"], af._brl(r["com_tag"]), frase)

    def test_dsr(self):
        mod = af.carregar("calculadora-dsr-hora-extra", "dsr_core")
        r = mod.calcular_dsr(800, 22, 5)
        for frase in (
            "dsr sobre hora extra valor 800 uteis 22 domingos 5",
            "dsr da hora extra valor R$ 800 uteis 22 domingos 5",
            "dsr hora extra extras 800 uteis 22 feriados 5",
        ):
            self.assertEqual(_um(frase, "calculadora-dsr-hora-extra")["resposta"], mod.brl(r["dsr"]), frase)


if __name__ == "__main__":
    unittest.main()
