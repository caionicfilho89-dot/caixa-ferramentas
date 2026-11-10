# -*- coding: utf-8 -*-
"""Testa os adaptadores de Audio chamando o nucleo real."""
from __future__ import annotations

import unittest

import adp_financas as af
import adp_audio as au


def _hits(texto):
    return [a for a in au.ADAPTADORES if a["extrair"](texto) is not None]


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


class Audio(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(au.ADAPTADORES), 15)
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])

    def test_andamento(self):
        saida = _um("andamento 90", "metronomo")
        mod = af.carregar("metronomo", "mt_core")
        self.assertEqual(saida["resposta"], mod.tempo_name(90))

    def test_freq_nota(self):
        saida = _um("frequencia da nota A4", "teoria-musical")
        mod = af.carregar("teoria-musical", "esm_core")
        self.assertEqual(saida["resposta"], af._num(mod.frequencia("A", 4), 2) + " Hz")

    def test_nota_freq(self):
        saida = _um("nota da frequencia 440", "teoria-musical")
        mod = af.carregar("teoria-musical", "esm_core")
        nota, oitava, _cents = mod.nota_de_frequencia(440)
        self.assertEqual(saida["resposta"], nota + str(oitava))

    def test_escala(self):
        saida = _um("escala maior de C", "teoria-musical")
        mod = af.carregar("teoria-musical", "esm_core")
        self.assertEqual(saida["resposta"], " ".join(mod.escala("C", "Maior (jônio)")))

    def test_acorde(self):
        saida = _um("acorde menor de A", "teoria-musical")
        mod = af.carregar("teoria-musical", "esm_core")
        self.assertEqual(saida["resposta"], " ".join(mod.acorde("A", "m")))

    def test_intervalo(self):
        saida = _um("intervalo de C ate E", "teoria-musical")
        mod = af.carregar("teoria-musical", "esm_core")
        _semi, nome = mod.intervalo("C", "E")
        self.assertEqual(saida["resposta"], nome)

    def test_transpor(self):
        saida = _um("transpor acorde C semitons 2", "teoria-musical")
        mod = af.carregar("teoria-musical", "esm_core")
        self.assertEqual(saida["resposta"], mod.transpor_acorde("C", 2))

    def test_pascoa(self):
        saida = _um("pascoa 2026", "calculadora-datas")
        mod = af.carregar("calculadora-datas", "dts_core")
        self.assertEqual(saida["resposta"], _data(mod.pascoa(2026)))

    def test_uteis(self):
        frase = "datas uteis de 02/11/2026 ate 30/11/2026"
        saida = _um(frase, "calculadora-datas")
        mod = af.carregar("calculadora-datas", "dts_core")
        import datetime
        n = mod.dias_uteis_entre(datetime.date(2026, 11, 2), datetime.date(2026, 11, 30))
        self.assertEqual(saida["resposta"], str(n) + " dias")

    def test_idade(self):
        saida = _um("idade exata 15/03/1990", "calculadora-datas")
        mod = af.carregar("calculadora-datas", "dts_core")
        import datetime
        r = mod.idade(datetime.date(1990, 3, 15), au.HOJE_AUDIO)
        self.assertEqual(saida["resposta"], str(r["anos"]) + " anos")

    def test_somar(self):
        saida = _um("somar dias na data 01/11/2026 quantidade 10", "calculadora-datas")
        mod = af.carregar("calculadora-datas", "dts_core")
        import datetime
        self.assertEqual(
            saida["resposta"],
            _data(mod.somar_dias(datetime.date(2026, 11, 1), 10)),
        )

    def test_iso(self):
        saida = _um("semana iso 09/11/2026", "calculadora-datas")
        mod = af.carregar("calculadora-datas", "dts_core")
        import datetime
        info = mod.info_data(datetime.date(2026, 11, 9))
        self.assertEqual(saida["resposta"], "semana " + str(info["semana_iso"]))

    def test_am(self):
        frase = "modulacao am portadora 1000000 modulante 5000"
        saida = _um(frase, "simulador-modulacao-am-fm")
        mod = af.carregar("simulador-modulacao-am-fm", "amf_core")
        r = mod.simulate_am(1000000, 5000)
        self.assertEqual(saida["resposta"], af._num(r["mu"], 3))

    def test_fm(self):
        frase = "modulacao fm portadora 98000000 modulante 15000 desvio 75000"
        saida = _um(frase, "simulador-modulacao-am-fm")
        mod = af.carregar("simulador-modulacao-am-fm", "amf_core")
        r = mod.simulate_fm(98000000, 15000, 75000)
        self.assertEqual(saida["resposta"], af._num(r["beta"], 3))

    def test_guia(self):
        frase = "guia retangular a 22,86 b 10,16 te10"
        saida = _um(frase, "calculadora-guia-ondas-retangular")
        mod = af.carregar("calculadora-guia-ondas-retangular", "gdo_core")
        hz = mod.frequencia_corte_modo(22.86, 10.16, 1, 0)
        self.assertEqual(saida["resposta"], af._num(hz / 1e9, 3) + " GHz")

    def test_cerca(self):
        saida = _um("alambrado perimetro 40 espacamento 2,5", "cerca-alambrado")
        mod = af.carregar("cerca-alambrado", "cer_core")
        r = mod.mourões(40, 2.5)
        self.assertEqual(saida["resposta"], str(r["mourões"]) + " mourões")

    def test_srpe(self):
        saida = _um("carga srpe rpe 8 minutos 45", "indice-carga-treino")
        mod = af.carregar("indice-carga-treino", "ict_core")
        self.assertEqual(saida["resposta"], af._num(mod.session_load(8, 45), 0) + " AU")

    def test_internet(self):
        saida = _um("internet da casa jogos 2", "internet-ideal-casa")
        mod = af.carregar("internet-ideal-casa", "mbp_core")
        r = mod.recomendar({"Jogo online": 2})
        self.assertEqual(saida["resposta"], str(r["plano"]) + " Mbps")

    def test_assinaturas(self):
        frase = "soma de assinaturas netflix;39,90;mensal"
        saida = _um(frase, "controle-assinaturas")
        mod = af.carregar("controle-assinaturas", "ass_core")
        r = mod.totalizar(mod.parse_linhas("netflix;39,90;mensal"))
        self.assertEqual(saida["resposta"], "R$ " + af._num(r["mensal"]))

    def test_contas(self):
        frase = "contas fixas luz;150;10"
        saida = _um(frase, "controle-contas-fixas")
        mod = af.carregar("controle-contas-fixas", "cfx_core")
        r = mod.totalizar(mod.parse_linhas("luz;150;10"), au.HOJE_AUDIO)
        self.assertEqual(saida["resposta"], "R$ " + af._num(r["total"]))


if __name__ == "__main__":
    unittest.main()
