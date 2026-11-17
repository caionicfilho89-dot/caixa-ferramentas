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

    def test_obra(self):
        r = _um("piso 50x50 para 30 m2", "calculadora-obra")
        self.assertIsNotNone(r)
        self.assertIn("132", r["resposta"])

    def test_pneu(self):
        r = _um("calibragem 30 psi na estrada", "calibragem-pneus")
        self.assertIsNotNone(r)
        self.assertIn("33", r["resposta"])

    def test_aluguel_quartos(self):
        r = _um("aluguel 2000 quartos 15m2 e 10m2", "aluguel-quartos")
        self.assertIsNotNone(r)
        self.assertIn("Q1", r["resposta"])
        self.assertIn("Q2", r["resposta"])

    def test_desafio_poupanca(self):
        r = _um("desafio 52 semanas", "desafio-poupanca")
        self.assertIsNotNone(r)
        self.assertIn("1.378", r["resposta"])

    def test_renda_fixa(self):
        r = _um("cdb 10000 a 12% por 365 dias", "simulador-renda-fixa")
        self.assertIsNotNone(r)
        self.assertIn("10.990", r["resposta"])

    def test_treino(self):
        r1 = _um("1rm 80kg 8 reps", "treino-academia")
        self.assertIsNotNone(r1)
        self.assertIn("1RM estimado", r1["resposta"])
        self.assertIn("100.3", r1["resposta"])

        r2 = _um("anilhas para 80kg", "treino-academia")
        self.assertIsNotNone(r2)
        self.assertIn("Por lado", r2["resposta"])
        self.assertIn("25kg", r2["resposta"])
        self.assertIn("5kg", r2["resposta"])

    def test_ficha_medica(self):
        r1 = _um("glicemia 105", "ficha-medica")
        self.assertIsNotNone(r1)
        self.assertIn("Acima do Referencial", r1["resposta"])
        self.assertIn("105", r1["resposta"])

        r2 = _um("colesterol total 180", "ficha-medica")
        self.assertIsNotNone(r2)
        self.assertIn("Normal", r2["resposta"])
        self.assertIn("180", r2["resposta"])

        r3 = _um("estoque de remedio 60 comprimidos 2 por dia", "ficha-medica")
        self.assertIsNotNone(r3)
        self.assertIn("30 dias", r3["resposta"])
        self.assertIn("Confortável", r3["resposta"])

    def test_mala_viagem(self):
        r1 = _um("mala de viagem 5 dias", "mala-viagem")
        self.assertIsNotNone(r1)
        self.assertIn("Mala", r1["resposta"])
        self.assertIn("kg", r1["resposta"])
        self.assertIn("Cabe na mala de mão", r1["resposta"])

    def test_marmitas(self):
        r1 = _um("marmitas para 5 dias", "marmitas-semana")
        self.assertIsNotNone(r1)
        self.assertIn("Total:", r1["resposta"])
        self.assertIn("/marmita", r1["resposta"])

    def test_noturno(self):
        r1 = _um("adicional noturno 40 horas salario 3000", "calculadora-adicional-noturno")
        self.assertIsNotNone(r1)
        self.assertIn("Adicional:", r1["resposta"])
        self.assertIn("109,09", r1["resposta"])

    def test_insalubridade(self):
        r1 = _um("insalubridade grau maximo", "calculadora-adicional-insalubridade")
        self.assertIsNotNone(r1)
        self.assertIn("Insalubridade:", r1["resposta"])
        self.assertIn("607,20", r1["resposta"])

        r2 = _um("adicional de insalubridade grau medio", "calculadora-adicional-insalubridade")
        self.assertIsNotNone(r2)
        self.assertIn("Insalubridade:", r2["resposta"])
        self.assertIn("303,60", r2["resposta"])

    def test_impressao_3d(self):
        r1 = _um("impressao 3d 100g 4 horas rolo 120", "calculadora-impressao-3d")
        self.assertIsNotNone(r1)
        self.assertIn("Custo:", r1["resposta"])
        self.assertIn("17,22", r1["resposta"])

    def test_piscina(self):
        r1 = _um("piscina 6x3 com 1.4 de profundidade", "calculadora-piscina")
        self.assertIsNotNone(r1)
        self.assertIn("Volume:", r1["resposta"])
        self.assertIn("25.2 m³", r1["resposta"])
        self.assertIn("78g/dia", r1["resposta"])

        r2 = _um("cloro de choque piscina 25 m3", "calculadora-piscina")
        self.assertIsNotNone(r2)
        self.assertIn("choque", r2["resposta"].lower())
        self.assertIn("385g", r2["resposta"])

    def test_periculosidade(self):
        r1 = _um("periculosidade salario 3000", "calculadora-adicional-periculosidade")
        self.assertIsNotNone(r1)
        self.assertIn("Periculosidade (30%):", r1["resposta"])
        self.assertIn("900,00", r1["resposta"])

    def test_seguro_desemprego(self):
        r1 = _um("seguro desemprego salario 2500 trabalhou 14 meses", "calculadora-seguro-desemprego")
        self.assertIsNotNone(r1)
        self.assertIn("4 parcelas de", r1["resposta"])
        self.assertIn("1.862,42", r1["resposta"])

    def test_aquario(self):
        r1 = _um("aquario 60x30x40", "calculadora-aquario")
        self.assertIsNotNone(r1)
        self.assertIn("72L", r1["resposta"])
        self.assertIn("61.2L", r1["resposta"])

    def test_hidraulica(self):
        r1 = _um("perda de carga 2 l/s tubo 50mm 100m", "calculadora-hidraulica-tubulacoes")
        self.assertIsNotNone(r1)
        self.assertIn("Perda de carga:", r1["resposta"])
        self.assertIn("mca", r1["resposta"])

    def test_rescisao(self):
        r1 = _um("rescisao salario 3000 anos 2 meses 6", "calculadora-rescisao-trabalhista")
        self.assertIsNotNone(r1)
        self.assertIn("Rescisão", r1["resposta"])
        self.assertIn("TRCT", r1["resposta"])

    def test_chmod(self):
        r1 = _um("chmod 755", "calculadora-chmod")
        self.assertIsNotNone(r1)
        self.assertIn("755", r1["resposta"])
        self.assertIn("rwxr-xr-x", r1["resposta"])

        r2 = _um("chmod 644", "calculadora-chmod")
        self.assertIsNotNone(r2)
        self.assertIn("644", r2["resposta"])
        self.assertIn("rw-r--r--", r2["resposta"])

    def test_motor(self):
        r1 = _um("motor eletrico 5 cv 220v", "calculadora-motores-eletricos")
        self.assertIsNotNone(r1)
        self.assertIn("Motor 5 CV", r1["resposta"])
        self.assertIn("In =", r1["resposta"])

    def test_bloom(self):
        r1 = _um("filtro de bloom 10000 itens 1%", "filtro-bloom")
        self.assertIsNotNone(r1)
        self.assertIn("Filtro de Bloom:", r1["resposta"])
        self.assertIn("95.851 bits", r1["resposta"])
        self.assertIn("k = 7 hashes", r1["resposta"])

    def test_posicao_solar(self):
        r1 = _um("posicao solar sao paulo 15/03 12h", "calculadora-posicao-solar-astronomia")
        self.assertIsNotNone(r1)
        self.assertIn("Posição Solar", r1["resposta"])
        self.assertIn("Elevação", r1["resposta"])
        self.assertIn("Azimute", r1["resposta"])
        self.assertIn("Zenite", r1["detalhe"])
        self.assertIn("Nascer", r1["detalhe"])

    def test_spline(self):
        r1 = _um("spline pontos 0 0 1 2 2 1 3 3 em x=1.5", "estudio-splines")
        self.assertIsNotNone(r1)
        self.assertIn("Spline Cúbico em x = 1.5", r1["resposta"])
        self.assertIn("segmentos cúbicos", r1["detalhe"])

    def test_agua_filtro(self):
        r1 = _um("agua mineral vs filtro galao 14 filtro 350", "agua-mineral-vs-filtro")
        self.assertIsNotNone(r1)
        self.assertIn("Água Mineral × Filtro", r1["resposta"])
        self.assertIn("Mineral:", r1["detalhe"])
        self.assertIn("Filtro:", r1["detalhe"])

    def test_acustica(self):
        r1 = _um("acustica sala 5x4x2.8 estudio", "calculadora-acustica-salas")
        self.assertIsNotNone(r1)
        self.assertIn("Acústica da Sala", r1["resposta"])
        self.assertIn("RT60 Sabine", r1["resposta"])
        self.assertIn("Schroeder", r1["detalhe"])

    def test_academia_casa(self):
        r1 = _um("academia vs equipamentos mensalidade 200 casa 2400 em 24 meses", "academia-vs-equipamentos")
        self.assertIsNotNone(r1)
        self.assertIn("Academia × Home Gym", r1["resposta"])
        self.assertIn("Academia:", r1["detalhe"])
        self.assertIn("Casa:", r1["detalhe"])

    def test_anki(self):
        r1 = _um("meta anki 20 novos por dia 1500 cards 30 minutos", "meta-revisoes-anki-diarias")
        self.assertIsNotNone(r1)
        self.assertIn("Meta Anki:", r1["resposta"])
        self.assertIn("revisões/dia", r1["resposta"])
        self.assertIn("Fila jovem:", r1["detalhe"])

    def test_aerodinamica(self):
        r1 = _um("aerodinamica cessna velocidade 200 km/h 1500m", "calculadora-aerodinamica-arrasto-sustentacao")
        self.assertIsNotNone(r1)
        self.assertIn("Aerodinâmica (Cessna", r1["resposta"])
        self.assertIn("L/D =", r1["resposta"])
        self.assertIn("Estol =", r1["resposta"])
        self.assertIn("Potência:", r1["detalhe"])

    def test_anticoncepcional(self):
        r1 = _um("esqueci anticoncepcional 10h dia 8", "cartela-anticoncepcional")
        self.assertIsNotNone(r1)
        self.assertIn("Esquecimento de Pílula", r1["resposta"])
        self.assertIn("LEVE", r1["resposta"])
        self.assertIn("Menos de 12 horas", r1["detalhe"])

    def test_sessao_foco(self):
        r1 = _um("sessao de foco 3 horas bloco 50 pausa 10 09:00", "planejador-sessao-foco")
        self.assertIsNotNone(r1)
        self.assertIn("Sessão de Foco:", r1["resposta"])
        self.assertIn("blocos", r1["resposta"])
        self.assertIn("Agenda: 09:00 às", r1["detalhe"])

    def test_amortizacao(self):
        r1 = _um("amortizacao extra valor 200000 taxa 10% em 360 meses aporte 1000", "comparador-credito")
        self.assertIsNotNone(r1)
        self.assertIn("Amortização Extra", r1["resposta"])
        self.assertIn("Economia de", r1["resposta"])
        self.assertIn("Prazo reduz", r1["detalhe"])

    def test_esporte_infantil(self):
        r1 = _um("esporte infantil mensalidade 250 uniforme 200 matricula 100 transporte 60", "custo-academia-infantil")
        self.assertIsNotNone(r1)
        self.assertIn("Custo de Esporte Infantil:", r1["resposta"])
        self.assertIn("Média real de", r1["resposta"])
        self.assertIn("Mensalidades:", r1["detalhe"])

    def test_decimo_terceiro(self):
        r1 = _um("decimo terceiro salario 3600 em 8 meses adiantamento 1000", "decimo-terceiro")
        self.assertIsNotNone(r1)
        self.assertIn("13º Salário (8/12 avos)", r1["resposta"])
        self.assertIn("Bruto R$ 2.400,00", r1["resposta"])
        self.assertIn("a receber R$ 1.400,00", r1["resposta"])

    def test_acl(self):
        r1 = _um("acl ntfs C:\\Users\\caion\\caixa-ferramentas", "inspetor-acl-ntfs")
        self.assertIsNotNone(r1)
        self.assertIn("ACL NTFS (caixa-ferramentas)", r1["resposta"])
        self.assertIn("Dono", r1["resposta"])
        self.assertIn("regras", r1["resposta"])

    def test_marchas_bike(self):
        r1 = _um("marchas bike coroa 50 pinhao 15 cadencia 90", "calculadora-marchas-bike")
        self.assertIsNotNone(r1)
        self.assertIn("Marcha 50x15", r1["resposta"])
        self.assertIn("m/pedalada", r1["resposta"])
        self.assertIn("km/h a 90 rpm", r1["resposta"])

    def test_forma_bolo(self):
        r1 = _um("forma de bolo 20cm para 25cm", "conversor-formas-bolo")
        self.assertIsNotNone(r1)
        self.assertIn("Forma de Bolo", r1["resposta"])
        self.assertIn("Escala = 1.56x receita", r1["resposta"])
        self.assertIn("Volume original:", r1["detalhe"])

    def test_cronometro(self):
        r1 = _um("relogio de xadrez 3+2 fischer", "estudio-cronometro")
        self.assertIsNotNone(r1)
        self.assertIn("Relógio de Xadrez (3+2 Fischer)", r1["resposta"])
        self.assertIn("Brancas 03:00.000", r1["resposta"])
        self.assertIn("Pretas 03:00.000", r1["resposta"])

    def test_base64(self):
        r1 = _um("codificar base64 ola", "conversor-base64")
        self.assertIsNotNone(r1)
        self.assertIn("Base64 Encode", r1["resposta"])
        self.assertIn("b2xh", r1["resposta"])

        r2 = _um("decodificar base64 b2xh", "conversor-base64")
        self.assertIsNotNone(r2)
        self.assertIn("Base64 Decode: ola", r2["resposta"])


if __name__ == "__main__":
    unittest.main()
