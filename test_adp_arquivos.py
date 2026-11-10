# -*- coding: utf-8 -*-
"""Testa os adaptadores de Arquivos chamando o nucleo real."""
from __future__ import annotations

import datetime
import unittest

import adp_arquivos as aq
import adp_financas as af


def _hits(texto):
    return [a for a in aq.ADAPTADORES if a["extrair"](texto) is not None]


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


class Arquivos(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(aq.ADAPTADORES), 15)
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])

    def test_bateria(self):
        frase = "autonomia bateria capacidade 100 unidade tensao 12 volts carga 50"
        saida = _um(frase, "calculadora-baterias")
        mod = af.carregar("calculadora-baterias", "bat_core")
        self.assertEqual(saida["resposta"], af._num(mod.autonomia_h(100, 12, 50), 2) + " h")

    def test_hohmann(self):
        frase = "transferencia hohmann baixa 300 km alta 35786"
        saida = _um(frase, "calculadora-dinamica-orbital-hohmann")
        mod = af.carregar("calculadora-dinamica-orbital-hohmann", "hmn_core")
        r = mod.calculate_hohmann_transfer("Terra", 300, 35786)
        self.assertEqual(saida["resposta"], af._num(r["total_delta_v_m_s"], 1) + " m/s")

    def test_zipf(self):
        corpo = "casa casa casa rato rato sol"
        saida = _um("lei de zipf " + corpo, "analisador-zipf")
        mod = af.carregar("analisador-zipf", "zpf_core")
        self.assertEqual(saida["resposta"], mod.zipf_analyze(corpo)["rows"][0]["word"])

    def test_espacos(self):
        corpo = "a\n\n\nb"
        saida = _um("compactar espacos " + corpo, "compactador-whitespace")
        mod = af.carregar("compactador-whitespace", "wsp_core")
        self.assertEqual(saida["resposta"], mod.stats(corpo, mod.normalize(corpo)))

    def test_nome(self):
        nome = "Meu Arquivo.PDF"
        saida = _um("normalizar arquivo " + nome, "normalizador-nomes")
        mod = af.carregar("normalizador-nomes", "nfn_core")
        self.assertEqual(saida["resposta"], mod.normalize_name(nome))

    def test_rateio(self):
        frase = "acerto rateio ana pagou 90 divide ana bia caio"
        saida = _um(frase, "rateio")
        mod = af.carregar("rateio", "rct_core")
        nomes = ["ana", "bia", "caio"]
        despesas = [{"desc": "conta", "valor": 90.0, "pagou": "ana", "entre": nomes}]
        trans = mod.acertar(mod.saldos(nomes, despesas))
        esperado = "; ".join(a + " paga " + mod.brl(v) + " para " + b for a, b, v in trans)
        self.assertEqual(saida["resposta"], esperado)

    def test_ciclo(self):
        frase = "ciclo menstrual inicio 01/10/2026 e inicio 29/10/2026"
        saida = _um(frase, "ciclo-menstrual")
        mod = af.carregar("ciclo-menstrual", "cic_core")
        inicios = [datetime.date(2026, 10, 1), datetime.date(2026, 10, 29)]
        prev = mod.previsoes(inicios)
        self.assertEqual(saida["resposta"], f"{prev[0]['inicio'].day:02d}/{prev[0]['inicio'].month:02d}/{prev[0]['inicio'].year}")

    def test_pausas(self):
        saida = _um("pausas da jornada horas 8", "ergonomia-pausas-trabalho")
        mod = af.carregar("ergonomia-pausas-trabalho", "erg_core")
        r = mod.calcular_cronograma_jornada(8)
        self.assertEqual(saida["resposta"], str(r["num_pausas_sugeridas"]) + " pausas")

    def test_liquido(self):
        frase = "foco de estudo bruto 120 interrupcoes 4 cada 5 perda 20"
        saida = _um(frase, "tempo-liquido-estudo")
        mod = af.carregar("tempo-liquido-estudo", "tnr_core")
        r = mod.calcular_tempo_liquido(120, 4, 5, 20)
        self.assertEqual(saida["resposta"], af._num(r.tempo_liquido, 2) + " min")

    def test_roi(self):
        frase = "roi da pos mensalidade 800 prazo 18 atual 4000 projetado 6000"
        saida = _um(frase, "calculadora-roi-educacao-pos")
        mod = af.carregar("calculadora-roi-educacao-pos", "cbf_core")
        r = mod.calcular_roi_educacao(800, 18, 0.0, 4000, 6000)
        self.assertEqual(saida["resposta"], af._num(r["mes_payback_simples"], 1) + " meses")

    def test_pendulo(self):
        frase = "periodo do pendulo comprimento 1 gravidade 9,8"
        saida = _um(frase, "simulador-pendulo-duplo")
        mod = af.carregar("simulador-pendulo-duplo", "pdl_core")
        self.assertEqual(saida["resposta"], af._num(mod.periodo_pequenas_osc(1, 9.8), 3) + " s")

    def test_forno(self):
        saida = _um("tempo de forno frango inteiro peso 2", "forno-carnes")
        mod = af.carregar("forno-carnes", "asd_core")
        r = mod.tempo_forno("Frango inteiro", 2)
        self.assertEqual(saida["resposta"], str(r["minutos"]) + " min")

    def test_gelo(self):
        saida = _um("descongelar geladeira peso 1", "descongelar-com-seguranca")
        mod = af.carregar("descongelar-com-seguranca", "dsc_core")
        self.assertEqual(saida["resposta"], af._num(mod.horas_descongelar(1, "Geladeira"), 2) + " h")

    def test_cozinha(self):
        saida = _um("tempo de cozimento ovo duro", "cozimento-alimentos")
        mod = af.carregar("cozimento-alimentos", "coz_core")
        self.assertEqual(saida["resposta"], str(mod.tempo("ovo duro")["minutos"]) + " min")

    def test_composto(self):
        saida = _um("volume composteira pessoas 4", "compostagem")
        mod = af.carregar("compostagem", "cmp_core")
        self.assertEqual(saida["resposta"], str(mod.volume_composteira(4)["volume_l"]) + " L")

    def test_prova(self):
        frase = "estrategia de prova minutos 300 questoes 90"
        saida = _um(frase, "planejador-tempo-estrategia-prova")
        mod = af.carregar("planejador-tempo-estrategia-prova", "etp_core")
        r = mod.calcular_estrategia_prova(300, 90)
        self.assertEqual(saida["resposta"], r["tempo_formatado"])

    def test_nuvem(self):
        frase = "crescimento nuvem fotos 200 unidade foto 4 video 10 bloco minuto 8"
        saida = _um(frase, "plano-nuvem-backup")
        mod = af.carregar("plano-nuvem-backup", "nuv_core")
        self.assertEqual(saida["resposta"], af._num(mod.crescimento_gb(200, 4, 10, 8), 2) + " GB/mês")


if __name__ == "__main__":
    unittest.main()
