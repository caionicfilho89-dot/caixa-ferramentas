# -*- coding: utf-8 -*-
"""Testa os adaptadores de casa chamando o núcleo real de cada ferramenta."""
from __future__ import annotations

import unittest
from datetime import date

import adp_casa as ac
import adp_financas as af


def _hits(texto):
    achados = []
    for ad in ac.ADAPTADORES:
        params = ad["extrair"](texto)
        if params is not None:
            achados.append(ad)
    return achados


def _um(texto, chave):
    achados = _hits(texto)
    chaves = [a["chave"] for a in achados]
    if chaves.count(chave) != 1 or any(c != chave for c in chaves):
        raise AssertionError(f"{texto!r} casou {chaves}, esperava só {chave}")
    ad = next(a for a in achados if a["chave"] == chave)
    params = ad["extrair"](texto)
    saida = ad["calcular"](params)
    if not saida.get("resposta", "").strip() or "detalhe" not in saida:
        raise AssertionError(f"contrato inválido em {chave}: {saida!r}")
    return params, saida


class Casa(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(ac.ADAPTADORES), 30)
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])

    def test_imc(self):
        _, saida = _um("imc peso 80 altura 1,75", "saude")
        mod = af.carregar("saude", "sd_core")
        valor = mod.imc(80, 1.75)
        self.assertIn(af._num(valor), saida["resposta"])
        self.assertIn(mod.imc_classe(valor), saida["resposta"])

    def test_imc_cm(self):
        _, saida = _um("imc 80 kg e 175 cm", "saude")
        mod = af.carregar("saude", "sd_core")
        self.assertIn(af._num(mod.imc(80, 1.75)), saida["resposta"])

    def test_agua_pessoa(self):
        _, saida = _um("quanta água beber pesando 70 kg", "saude")
        mod = af.carregar("saude", "sd_core")
        self.assertIn(str(mod.agua_ml(70)), saida["resposta"])

    def test_agua_pet(self):
        _, saida = _um("água do cachorro de 12 kg", "pet")
        mod = af.carregar("pet", "pet_core")
        self.assertIn(af._num(mod.agua_dia_ml(12, "cao"), 0), saida["resposta"])

    def test_racao(self):
        _, saida = _um("ração cachorro 20 kg", "pet")
        mod = af.carregar("pet", "pet_core")
        energia = mod.mer(20, mod.FATORES["cao"]["Adulto castrado"])
        self.assertIn(af._num(energia, 0), saida["resposta"])

    def test_idade_pet(self):
        _, saida = _um("idade humana de um cachorro de 5 anos", "pet")
        mod = af.carregar("pet", "pet_core")
        self.assertIn(af._num(mod.idade_humana(5, "cao", "medio"), 1), saida["resposta"])

    def test_volumes(self):
        _, saida = _um("30 volumes de oxigenada", "cabelo")
        mod = af.carregar("cabelo", "cab_core")
        self.assertIn(af._num(mod.volumes_para_pct(30)), saida["resposta"])

    def test_diluir(self):
        _, saida = _um("diluir oxigenada de 40 volumes para 20 volumes em 100 ml", "cabelo")
        mod = af.carregar("cabelo", "cab_core")
        esp = mod.diluir_oxigenada(40, 20, 100)
        self.assertIn(af._num(esp["oxigenada_ml"]), saida["resposta"])

    def test_cafe(self):
        _, saida = _um("30 gramas de café no v60", "calculadora-cafe")
        mod = af.carregar("calculadora-cafe", "cfe_core")
        prop = next(v[0] for n, v in mod.METODOS.items() if n.startswith("Coado"))
        self.assertIn(af._num(mod.agua_para_cafe(30, prop), 0), saida["resposta"])

    def test_xicara(self):
        _, saida = _um("2 xícaras de farinha de trigo", "medidas-de-cozinha")
        mod = af.carregar("medidas-de-cozinha", "mcl_core")
        esp = mod.converter(2, "xícara", "Farinha de trigo")
        self.assertIn(af._num(esp["gramas"], 1), saida["resposta"])

    def test_pao(self):
        _, saida = _um("pão 500 g de farinha hidratação 70% sal 2%", "calculadora-pao")
        mod = af.carregar("calculadora-pao", "pao_core")
        esp = mod.massa(500, 70, 2)
        self.assertIn(af._num(esp["Água"], 0), saida["resposta"])

    def test_pizza(self):
        _, saida = _um("quantas pizzas para 8 pessoas", "calculadora-pizza")
        mod = af.carregar("calculadora-pizza", "pzz_core")
        self.assertIn(str(mod.pizzas_para_pessoas(8)), saida["resposta"])

    def test_abv(self):
        _, saida = _um("abv da cerveja og 1,060 fg 1,010", "calculadora-cerveja")
        mod = af.carregar("calculadora-cerveja", "brw_core")
        self.assertIn(af._num(mod.abv(1.06, 1.01)), saida["resposta"])

    def test_chucrute(self):
        _, saida = _um("chucrute com 1000 g de repolho", "fermentados-caseiros")
        mod = af.carregar("fermentados-caseiros", "kmb_core")
        self.assertIn(af._num(mod.chucrute(1000)["sal_g"]), saida["resposta"])

    def test_quentao(self):
        _, saida = _um("quentão de 3 litros", "festa-junina")
        mod = af.carregar("festa-junina", "jun_core")
        self.assertIn(af._num(mod.receita_quentao(3)["cachaça_ml"], 0), saida["resposta"])

    def test_aquario(self):
        _, saida = _um("aquário 100 por 40 por 50 cm", "calculadora-aquario")
        mod = af.carregar("calculadora-aquario", "aqu_core")
        self.assertIn(af._num(mod.volume_retangular(100, 40, 50), 1), saida["resposta"])

    def test_botijao(self):
        _, saida = _um("botijão p13 consumindo 0,4 kg por dia", "botijao-gas")
        mod = af.carregar("botijao-gas", "gas_core")
        self.assertIn(af._num(mod.dias_duracao("P13", 0.4), 1), saida["resposta"])

    def test_tv(self):
        _, saida = _um("televisão a 2,5 metros", "tamanho-tv")
        mod = af.carregar("tamanho-tv", "tvd_core")
        self.assertIn(af._num(mod.sugerir(2.5)["SMPTE_pol"], 0), saida["resposta"])

    def test_festa(self):
        _, saida = _um("aniversário para 30 adultos e 10 crianças", "festa")
        mod = af.carregar("festa", "fst_core")
        esp = mod.calcular("Aniversário", 30, 10)
        self.assertIn(str(esp["salgados_un"]), saida["resposta"])

    def test_junina(self):
        _, saida = _um("festa junina para 40 pessoas", "festa-junina")
        mod = af.carregar("festa-junina", "jun_core")
        self.assertIn(af._num(mod.quantidades(40)["pipoca_g"], 0), saida["resposta"])

    def test_infantil(self):
        _, saida = _um("festa infantil 15 crianças e 10 adultos", "festa-infantil")
        mod = af.carregar("festa-infantil", "fsi_core")
        self.assertIn(str(mod.quantidades(15, 10)["salgados"]), saida["resposta"])

    def test_grama(self):
        _, saida = _um("placas de grama para 50 m2", "grama-jardim")
        mod = af.carregar("grama-jardim", "grm_core")
        self.assertIn(af._num(mod.placas(50)["m2_placas"]), saida["resposta"])

    def test_fraldas(self):
        _, saida = _um("fraldas para 12 meses", "enxoval-bebe")
        mod = af.carregar("enxoval-bebe", "enx_core")
        total = sum(item[3] for item in mod.fraldas(12))
        self.assertIn(str(total), saida["resposta"])

    def test_solar(self):
        _, saida = _um("aquecedor solar para 3 pessoas, banho de 8 minutos", "aquecedor-solar")
        mod = af.carregar("aquecedor-solar", "aqs_core")
        cons = mod.consumo_banho(3, 8)
        self.assertIn(af._num(mod.volume_boiler(cons["litros_dia"]), 0), saida["resposta"])

    def test_condominio(self):
        _, saida = _um("taxa extra de condomínio 8000 em 16 apartamentos", "taxa-extra-condominio")
        mod = af.carregar("taxa-extra-condominio", "tcx_core")
        esp = mod.ratear(8000, "igualitario", 16)
        self.assertIn(af._num(esp["sua_parte"]), saida["resposta"])

    def test_dpp(self):
        _, saida = _um("dpp dum 01/03/2026", "gestacional")
        mod = af.carregar("gestacional", "gst_core")
        self.assertIn(mod.br(mod.dpp_por_dum(date(2026, 3, 1))), saida["resposta"])

    def test_cafeina(self):
        _, saida = _um("cafeína restante de 200 mg depois de 5 horas", "calculadora-sono")
        mod = af.carregar("calculadora-sono", "sno_core")
        self.assertIn(af._num(mod.cafeina_restante(200, 5), 0), saida["resposta"])

    def test_debito(self):
        _, saida = _um("débito de sono idade 30 dormi 5 horas", "calculadora-sono")
        mod = af.carregar("calculadora-sono", "sno_core")
        self.assertIn(af._num(mod.debito_sono([5], 30), 1), saida["resposta"])

    def test_sono_relogio(self):
        _, saida = _um("que horas dormir pra acordar 07:00", "calculadora-sono")
        mod = af.carregar("calculadora-sono", "sno_core")
        self.assertIn(mod.horarios_dormir("07:00")[0][0], saida["resposta"])

    def test_1rm(self):
        _, saida = _um("1rm de 100 kg com 5 repetições", "estimativa-1rm-epley")
        mod = af.carregar("estimativa-1rm-epley", "epl_core")
        self.assertIn(af._num(mod.estimar(100, 5)["media"]), saida["resposta"])

    def test_estacionamento(self):
        _, saida = _um("estacionamento de 2 horas, primeira hora 12 e hora adicional 6", "calculadora-estacionamento")
        mod = af.carregar("calculadora-estacionamento", "est_core")
        self.assertIn(af._num(mod.calcular(120, 12, 6)["valor"]), saida["resposta"])

    def test_bike(self):
        _, saida = _um("bike coroa 50 pinhão 11 roda 2100 mm cadência 90", "calculadora-marchas-bike")
        mod = af.carregar("calculadora-marchas-bike", "bik_core")
        self.assertIn(af._num(mod.velocidade_kmh(50, 11, 2100, 90), 1), saida["resposta"])

    def test_croche(self):
        _, saida = _um("crochê amostra 18 pontos largura 40 cm", "croche")
        mod = af.carregar("croche", "trc_core")
        self.assertIn(str(mod.pontos_para_largura(18, 40)), saida["resposta"])

    def test_calcado(self):
        _, saida = _um("sapato feminino 38", "tamanhos")
        mod = af.carregar("tamanhos", "tam_core")
        esp = mod.converter_calcado(38, "BR", "feminino")
        self.assertIn(str(esp["EU"]), saida["resposta"])

    def test_pneu(self):
        _, saida = _um(
            "pneu km atual 40000, instalado 20000, vida 50000, ando 1000 por mês, preço 400",
            "troca-pneu-carro",
        )
        mod = af.carregar("troca-pneu-carro", "pne_core")
        esp = mod.calcular(40000, 20000, 50000, 1000, 400)
        self.assertIn(af._num(esp["restantes"]), saida["resposta"])

    def test_cafeteria(self):
        _, saida = _um(
            "café em casa: 10 xícaras por semana, cafeteria 8 reais, pacote 20 reais, rende 20 xícaras",
            "cafe-casa-vs-cafeteria",
        )
        mod = af.carregar("cafe-casa-vs-cafeteria", "cfh_core")
        esp = mod.comparar(10, 8, 20, 20)
        self.assertIn(af._num(esp["economia"]), saida["resposta"])

    def test_petsitter(self):
        _, saida = _um("petsitter 3 dias, 8 horas, 25 por hora, creche 80, hotel 120", "petsitter-vs-creche")
        mod = af.carregar("petsitter-vs-creche", "pts_core")
        esp = mod.comparar(3, 8, 25, 80, 120)
        self.assertIn(esp["melhor"], saida["resposta"])

    def test_hotel_pet(self):
        _, saida = _um("hotelzinho do pet 4 dias a 90", "hospedagem-pet")
        mod = af.carregar("hospedagem-pet", "hpv_core")
        self.assertIn(af._num(mod.calcular(4, 90)["liquido"]), saida["resposta"])

    def test_horta(self):
        _, saida = _um("horta colhi 8 kg a 10 reais insumos 20", "economia-horta-caseira")
        mod = af.carregar("economia-horta-caseira", "hrt_core")
        self.assertIn(af._num(mod.calcular(8, 10, 20)["economia"]), saida["resposta"])

    def test_reajuste(self):
        _, saida = _um("reajuste do plano de saúde de 500 reais a 10% por 3 anos", "reajuste-plano-saude")
        mod = af.carregar("reajuste-plano-saude", "rps_core")
        self.assertIn(af._num(mod.projetar(500, 10, 3)["mensal_final"]), saida["resposta"])

    def test_reembolso(self):
        _, saida = _um("reembolso plano paguei 400 tabela 300 cobertura 80%", "reembolso-plano-saude")
        mod = af.carregar("reembolso-plano-saude", "rms_core")
        self.assertIn(af._num(mod.calcular(400, 300, 80)["reembolso"]), saida["resposta"])

    def test_lentes(self):
        _, saida = _um("lentes mensais, caixa de 6, 90 reais, dois olhos", "lentes-contato")
        mod = af.carregar("lentes-contato", "lct_core")
        self.assertIn(af._num(mod.custo_mensal(90, 6, 2, "mensal")["custo"]), saida["resposta"])

    def test_fumar(self):
        _, saida = _um("20 dias sem fumar, 10 cigarros por dia, maço de 15 reais", "parar-fumar")
        mod = af.carregar("parar-fumar", "fum_core")
        self.assertIn(af._num(mod.dinheiro_economizado(20, 10, 15)["economizado"]), saida["resposta"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
