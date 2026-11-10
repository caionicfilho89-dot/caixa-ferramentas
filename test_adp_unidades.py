# -*- coding: utf-8 -*-
"""Testa os adaptadores de conversão chamando o núcleo real."""
from __future__ import annotations

import unittest

import adp_financas as af
import adp_unidades as au


def _hits(texto):
    achados = []
    for ad in au.ADAPTADORES:
        if ad["extrair"](texto) is not None:
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


class Unidades(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(au.ADAPTADORES), 6)
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])

    def test_km_milhas(self):
        _, saida = _um("10 km em milhas", "conversor-unidades")
        mod = af.carregar("conversor-unidades", "cu_unidades")
        esp = mod.convert("Comprimento", 10, "km", "mi")
        self.assertIn(mod.format_number(esp), saida["resposta"])

    def test_celsius(self):
        _, saida = _um("100 celsius em fahrenheit", "conversor-unidades")
        mod = af.carregar("conversor-unidades", "cu_unidades")
        esp = mod.convert("Temperatura", 100, "C", "F")
        self.assertIn(mod.format_number(esp), saida["resposta"])

    def test_gb(self):
        _, saida = _um("2 gb em mb", "conversor-unidades")
        mod = af.carregar("conversor-unidades", "cu_unidades")
        esp = mod.convert("Dados", 2, "GB", "MB")
        self.assertIn(mod.format_number(esp), saida["resposta"])

    def test_angulo(self):
        _, saida = _um("90 graus em radianos", "conversor-unidades")
        mod = af.carregar("conversor-unidades", "cu_unidades")
        esp = mod.convert("Ângulo", 90, "deg", "rad")
        self.assertIn(mod.format_number(esp), saida["resposta"])

    def test_dia(self):
        _, saida = _um("1 dia em horas", "conversor-unidades")
        mod = af.carregar("conversor-unidades", "cu_unidades")
        esp = mod.convert("Tempo", 1, "d", "h")
        self.assertIn(mod.format_number(esp), saida["resposta"])

    def test_consumo(self):
        _, saida = _um("12 km/l em litros por 100 km", "conversor-unidades")
        mod = af.carregar("conversor-unidades", "cu_unidades")
        esp = mod.convert("Combustível", 12, "kml", "l100")
        self.assertIn(mod.format_number(esp), saida["resposta"])

    def test_tamanho(self):
        _, saida = _um("formatar tamanho 1536 bytes", "formatador-tamanho")
        mod = af.carregar("formatador-tamanho", "hsz_core")
        self.assertIn(mod.format_size(1536, binary=True), saida["resposta"])

    def test_epoch(self):
        _, saida = _um("epoch 1700000000", "conversor-epoch")
        mod = af.carregar("conversor-epoch", "epc_core")
        esp = mod.epoch_to_datetimes(1700000000)
        self.assertIn(esp["utc_iso"], saida["resposta"])

    def test_epoch_data(self):
        _, saida = _um("epoch da data 01/01/2024", "conversor-epoch")
        mod = af.carregar("conversor-epoch", "epc_core")
        esp = mod.datetime_to_epoch("01/01/2024")
        self.assertIn(str(esp["epoch"]), saida["resposta"])

    def test_cor(self):
        _, saida = _um("temperatura de cor 2700 kelvin", "conversor-temperatura-cor")
        mod = af.carregar("conversor-temperatura-cor", "ctk_core")
        esp = mod.report(2700)
        self.assertIn(af._num(esp["mired"]), saida["resposta"])

    def test_forno(self):
        _, saida = _um("tempo de forno 40 minutos de 5 para 8", "formas-bolo")
        mod = af.carregar("formas-bolo", "bol_core")
        self.assertIn(str(mod.tempo_forno(40, 5, 8)), saida["resposta"])

    def test_utm(self):
        _, saida = _um("utm -23.55 -46.63", "conversor-coordenadas")
        mod = af.carregar("conversor-coordenadas", "geo_core")
        esp = mod.dd_to_utm(-23.55, -46.63)
        self.assertIn(af._num(esp["easting_m"]), saida["resposta"])

    def test_gms(self):
        _, saida = _um("coordenada 23 graus 33 minutos 0 segundos sul", "conversor-coordenadas")
        mod = af.carregar("conversor-coordenadas", "geo_core")
        esp = mod.dms_to_dd(23, 33, 0, "S")
        self.assertIn(af._num(esp, 6), saida["resposta"])


if __name__ == "__main__":
    unittest.main()
