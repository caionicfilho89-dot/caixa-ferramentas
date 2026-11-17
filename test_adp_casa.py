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


# F8: 3 jeitos de perguntar nas 20 chaves mais usadas da casa.
# Mesma conta: sem acento, sinônimo que o extrator já aceita, R$ / mil / por cento.
_TRES = (
    ("saude", "IMC: 26,12 (Sobrepeso)", (
        "imc peso 80 altura 1,75",
        "imc peso 80 kg altura 1,75",
        "imc 80 kg altura 1,75 m",
    )),
    ("pet", "Energia: 1.059 kcal/dia", (
        "ração cachorro 20 kg",
        "racao do cachorro 20 kg",
        "racao cachorro peso 20",
    )),
    ("calculadora-cafe", "Água: 480 ml para 30 g de café", (
        "30 gramas de café no v60",
        "30 gramas de cafe no v60",
        "cafe v60 30 gramas",
    )),
    ("medidas-de-cozinha", "2,0 xícara de Farinha de trigo = 240,0 g", (
        "2 xícaras de farinha de trigo",
        "2 xicaras de farinha de trigo",
        "xicara de farinha de trigo 2",
    )),
    ("calculadora-pao", "Água do pão: 350 g", (
        "pão 500 g de farinha hidratação 70% sal 2%",
        "pao 500 g de farinha hidratacao 70% sal 2%",
        "pao farinha 500 hidratacao 70 por cento sal 2 por cento",
    )),
    ("calculadora-pizza", "Pizzas: 3", (
        "quantas pizzas para 8 pessoas",
        "pizza para 8 pessoas",
        "pizza para 8 pessoa",
    )),
    ("botijao-gas", "Botijão P13: 32,5 dias", (
        "botijão p13 consumindo 0,4 kg por dia",
        "botijao p13 consumindo 0,4 kg por dia",
        "p13 consumindo 0,4 kg por dia",
    )),
    ("tamanho-tv", "TV (SMPTE): 60 polegadas", (
        "televisão a 2,5 metros",
        "tv a 2,5 metros",
        "televisor distancia 2,5 metros",
    )),
    ("festa", "Salgados: 360", (
        "aniversário para 30 adultos e 10 crianças",
        "aniversario para 30 adultos e 10 criancas",
        "aniversario 30 adultos e 10 criancas",
    )),
    ("grama-jardim", "Placas de grama: 52,50", (
        "placas de grama para 50 m2",
        "placa de grama para 50 m2",
        "grama placas area 50",
    )),
    ("enxoval-bebe", "Fraldas: 2970 unidades", (
        "fraldas para 12 meses",
        "fralda para 12 meses",
        "fraldas para 12 mes",
    )),
    ("aquecedor-solar", "Boiler: 300 L", (
        "aquecedor solar para 3 pessoas, banho de 8 minutos",
        "boiler para 3 pessoas, banho de 8 minutos",
        "aquecedor solar 3 pessoas 8 minutos",
    )),
    ("taxa-extra-condominio", "Sua parte: R$ 500,00", (
        "taxa extra de condomínio 8000 em 16 apartamentos",
        "taxa extra de condominio R$ 8 mil em 16 apartamentos",
        "condominio taxa 8.000 em 16 apartamentos",
    )),
    ("gestacional", "DPP: 06/12/2026", (
        "dpp dum 01/03/2026",
        "dum 01/03/2026",
        "gestacao dum 1/3/2026",
    )),
    ("calculadora-sono", "Para acordar 07:00, vá dormir às 21:45", (
        "que horas dormir pra acordar 07:00",
        "acordar 07:00",
        "pra acordar 7h",
    )),
    ("calculadora-estacionamento", "Estacionamento: R$ 18,00", (
        "estacionamento de 2 horas, primeira hora 12 e hora adicional 6",
        "estacionamento de 2 horas, primeira hora R$ 12 e hora adicional 6",
        "estacionamento 2 horas primeira 12 adicional 6",
    )),
    ("tamanhos", "Sapato BR 38 / EU 39 / US 8.0 / UK 6.0 (24.5 cm)", (
        "sapato feminino 38",
        "calcado feminino 38",
        "tenis feminino 38",
    )),
    ("reajuste-plano-saude", "Mensalidade no fim: R$ 665,50", (
        "reajuste do plano de saúde de 500 reais a 10% por 3 anos",
        "reajuste do plano de saude de R$ 500 a 10% por 3 anos",
        "reajuste do plano de 500 a 10 por cento por 3 anos",
    )),
    ("reembolso-plano-saude", "Reembolso: R$ 240,00", (
        "reembolso plano paguei 400 tabela 300 cobertura 80%",
        "reembolso paguei R$ 400 tabela 300 cobertura 80%",
        "reembolso paguei 400 tabela 300 cobertura 80 por cento",
    )),
    ("parar-fumar", "Economizado: R$ 150,00", (
        "20 dias sem fumar, 10 cigarros por dia, maço de 15 reais",
        "20 dias sem fumar, 10 cigarros por dia, maco de R$ 15",
        "20 dias sem fumar, 10 cigarro por dia, maco de 15 reais",
    )),
)



# F8: os 22 registros que faltavam, fora das 20 chaves do dia a dia.
_MAIS = (
    ('saude', 'Água: 2450 ml (10 copos)', (
        'beber agua peso 70',
        'hidratar agua pesando 70',
        'beber agua 70 kg',
    )),
    ('pet', 'Água do cão: 1.200 ml por dia', (
        'agua do cachorro 20 kg',
        'agua da cadela peso 20',
        'agua do cao 20 kg',
    )),
    ('pet', 'Idade humana: 56,8 anos', (
        'idade humana do cachorro 5 anos',
        'anos humanos cachorro 5 anos',
        'idade humana cachoro 5 anos',
    )),
    ('cabelo', '30 volumes = 9,00% de água oxigenada', (
        '30 volumes',
        'oxigenada 30 volumes',
        '30 volumen',
    )),
    ('cabelo', 'Oxigenada na mistura: 50,00', (
        'diluir 40 volumes para 20 volumes em 100 ml',
        'diluicao 40 volumes para 20 volumes 100 ml',
        'diluir 40 volume em 20 volume 100 mililitro',
    )),
    ('calculadora-cerveja', 'ABV: 5,25%', (
        'og 1,050 fg 1,010',
        'cerveja og 1,050 e fg 1,010',
        'abv og 1,050 fg 1,010',
    )),
    ('fermentados-caseiros', 'Sal do chucrute: 20,00', (
        'chucrute 1000 g de repolho',
        'chucrute repolho 1000 sal 2%',
        'chucrute 1.000 g',
    )),
    ('festa-junina', 'Cachaça: 800 ml', (
        'quentao 2 litros',
        'quentao 2 litro',
        'quentao de 2 litros',
    )),
    ('calculadora-aquario', 'Aquário: 60,0 L brutos', (
        'aquario 50 30 40',
        'aquario de 50 por 30 por 40',
        'aquario 50 30 40 cm',
    )),
    ('festa-junina', 'Pipoca: 1.600 g', (
        'festa junina 40 pessoas',
        'junina 40 convidados',
        'junina pra 40 pessoa',
    )),
    ('festa-infantil', 'Salgados: 150', (
        'festa infantil 15 criancas',
        'festa infantil 15 crianca',
        'aniversario infantil 15 criancas',
    )),
    ('calculadora-sono', 'Cafeína restante: 100 mg', (
        'cafeina 200 mg depois de 5 horas',
        'cafeina 200 miligrama 5 horas',
        'cafeina 200 mg 5h',
    )),
    ('calculadora-sono', 'Débito desta noite: 2,0 h', (
        'debito de sono dormi 5 horas idade 30',
        'debito de sono 5 horas idade 30',
        'debito sono dormi 5h idade 30',
    )),
    ('estimativa-1rm-epley', '1RM médio: 114,58', (
        '1rm 100 kg 5 repeticoes',
        'epley 100 kg 5 reps',
        '1rm com 100 kg 5 repet',
    )),
    ('calculadora-marchas-bike', 'Velocidade: 33,6 km/h', (
        'bike coroa 50 pinhao 15 roda 2100 mm cadencia 80',
        'coroa 50 pinhao 15 circunferencia 2100 rpm 80',
        'coroa 50 pinhao 15 roda 2100 cadencia 80',
    )),
    ('croche', 'Monte 80 pontos', (
        'croche amostra 20 pontos largura 40',
        'trico 20 pontos para 40',
        'croche 20 ponto largura 40',
    )),
    ('troca-pneu-carro', 'Pneu ainda roda: 20.000,00', (
        'pneu atual 40000 instalado 10000 vida 50000 ando 1000 por mes preco 400',
        'pneu atual 40000 instalacao 10000 vida 50000 por mes 1000 preco 400',
        'pneu atual 40000 instalado 10000 vida 50000 ando 1000 por mes preco R$ 400',
    )),
    ('cafe-casa-vs-cafeteria', 'Economia do café em casa: R$ 325,87', (
        'cafeteria 10 por semana cafeteria 8 pacote 20 rende 40',
        'cafeteria 10 xicaras por semana cafeteria 8 reais pacote 20 rende 40',
        'cafeteria 10 por semana cafeteria R$ 8 pacote R$ 20 rende 40',
    )),
    ('petsitter-vs-creche', 'Mais barato: creche', (
        'petsitter 5 dias 8 horas sitter 30 creche 80 hotel 100',
        'pet sitter 5 dias 8 horas por hora 30 creche 80 hotel 100',
        'petsitter 5 dias 8 horas sitter R$ 30 creche R$ 80 hotel R$ 100',
    )),
    ('hospedagem-pet', 'Hotel do pet: R$ 360,00', (
        'hotelzinho 4 dias diaria 90',
        'hospedagem 4 dias a 90 reais',
        'hotelzinho 4 dias diaria R$ 90',
    )),
    ('economia-horta-caseira', 'Economia da horta: R$ 33,00', (
        'horta colhi 8 kg a 6 reais insumos 15',
        'horta colheita 8 kg preco 6 insumos 15',
        'horta colhi 8 kg a R$ 6 insumos R$ 15',
    )),
    ('lentes-contato', 'Custo das lentes: R$ 26,67', (
        'lentes caixa 6 preco 80',
        'lente caixa de 6 por 80 reais',
        'lentes caixa 6 preco R$ 80',
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

    def test_resto_dos_adaptadores(self):
        """Abreviado, com erro e com R$/mil no que ainda não estava nas 20."""
        self.assertEqual(len(_MAIS), 22)
        for chave, esperado, frases in _MAIS:
            self.assertEqual(len(frases), 3, chave)
            for frase in frases:
                _, saida = _um(frase, chave)
                self.assertEqual(saida["resposta"], esperado, frase)



# T02: 2 frases cada. Números iguais; a segunda só muda a ordem das palavras.
_LOTE_CASA = (
    ('calculadora-botijao-gas', 'Dura 21,7 dias', (
        'glp 13 kg por 110 reais 2 bocas 1,5 horas',
        'glp de 13 kg a 110 reais com 2 bocas por 1,5 horas',
    )),
    ('estimativa-conta-agua', 'Conta de água: R$ 117,00', (
        'conta de agua 12 m3 tarifa 8,50 taxa 15',
        'conta de agua de 12 m3 com tarifa 8,50 e taxa 15',
    )),
    ('troca-oleo', 'Troca de óleo: R$ 180,00', (
        'troca de oleo 4 litros a 35 reais filtro 40',
        'oleo do carro 4 litros 35 reais e filtro 40',
    )),
    ('carro-ou-app', 'Corrida de app: R$ 47,50', (
        'corrida de app 12 km em 25 minutos base 5 por km 2,50 por minuto 0,50',
        'corrida de app com 12 km em 25 minutos base 5 por km 2,50 por minuto 0,50',
    )),
    ('rotina-skincare', 'O frasco dura: 100,00', (
        'frasco de protetor com 50 ml e dose de 0,5 ml',
        'protetor frasco 50 ml dose 0,5 ml',
    )),
    ('sono-bebe', 'Sono do bebê: 13,5 h', (
        'bebe de 6 meses quanto sono',
        'sono do bebe de 6 meses',
    )),
    ('diario-pressao', 'Pressão: Pré-hipertensão', (
        'pressao sistolica 120 diastolica 80',
        'pressao 120 e diastolica 80',
    )),
    ('calendario-safra', 'Safra da manga: forte', (
        'safra da manga em novembro',
        'em novembro a safra da manga',
    )),
    ('rega-plantas', 'Rega: 1.570 ml', (
        'regar vaso de 20 cm',
        'vaso de 20 cm para regar',
    )),
    ('tarefas-casa', 'Mesada: R$ 16,00', (
        'mesada 8 feitas de um total de 10 base 20 bonus 10 minimo 70%',
        'mesada com 8 feitas total 10 base 20 bonus 10 minimo 70%',
    )),
    ('comparador-hospedagens', 'Estadia: R$ 800,00', (
        'airbnb diaria de 200 reais por 4 noites para 2 pessoas',
        'airbnb 4 noites 2 pessoas diaria 200 reais',
    )),
    ('adaptacao-jet-lag', 'Fuso: 5 h', (
        'jet lag do fuso 3 para o fuso 8',
        'jetlag fuso 3 e fuso 8',
    )),
    ('horta-jardim', 'Mudas: 27', (
        'canteiro de alface comprimento 2 largura 1',
        'alface no canteiro comprimento 2 e largura 1',
    )),
    ('calendario-da-horta', 'Replante a cada 15 dias', (
        'calendario da horta alface',
        'alface no calendario da horta',
    )),
    ('controle-cafeina-doses-dia', 'Cafeína: 80 mg', (
        'expresso 200 ml a 0,4 mg por ml',
        'expresso de 200 ml com 0,4 mg por ml',
    )),
)


class LoteCasa(unittest.TestCase):
    def test_quinze_chaves_duas_frases(self):
        self.assertEqual(len(_LOTE_CASA), 15)
        for chave, esperado, frases in _LOTE_CASA:
            self.assertEqual(len(frases), 2, chave)
            for frase in frases:
                _, saida = _um(frase, chave)
                self.assertEqual(saida["resposta"], esperado, frase)


if __name__ == "__main__":
    unittest.main(verbosity=1)
