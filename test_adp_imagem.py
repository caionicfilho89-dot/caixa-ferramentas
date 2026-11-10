# -*- coding: utf-8 -*-
"""Testa os adaptadores de Imagem chamando o nucleo real."""
from __future__ import annotations

import unittest

import adp_financas as af
import adp_imagem as ai


def _hits(texto):
    return [a for a in ai.ADAPTADORES if a["extrair"](texto) is not None]


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


class Imagem(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(ai.ADAPTADORES), 20)
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])
        self.assertEqual(_hits("dose de cloro da piscina 30 ppm 3"), [])

    def test_ritmo(self):
        frase = "ritmo de corrida 45:00 em 10 km"
        saida = _um(frase, "pace")
        mod = af.carregar("pace", "pac_core")
        segundos = mod.parse_time("45:00")
        self.assertEqual(saida["resposta"], mod.fmt_pace(mod.pace_from(segundos, 10)))

    def test_vo2(self):
        saida = _um("vo2max prova 10 km em 45:00", "pace")
        mod = af.carregar("pace", "pac_core")
        segundos = mod.parse_time("45:00")
        self.assertEqual(saida["resposta"], af._num(mod.vo2max(10, segundos), 1))

    def test_riegel(self):
        saida = _um("riegel base 10 km em 45:00 alvo 21,1", "pace")
        mod = af.carregar("pace", "pac_core")
        segundos = mod.parse_time("45:00")
        self.assertEqual(saida["resposta"], mod.fmt_time(mod.riegel(segundos, 10, 21.1)))

    def test_paleta(self):
        saida = _um("paleta complementar #ff0000", "gerador-paleta-cores")
        mod = af.carregar("gerador-paleta-cores", "pal_core")
        self.assertEqual(saida["resposta"], ", ".join(mod.harmonia("#ff0000", "Complementar")))

    def test_texto_ideal(self):
        saida = _um("texto ideal #336699", "gerador-paleta-cores")
        mod = af.carregar("gerador-paleta-cores", "pal_core")
        self.assertEqual(saida["resposta"], mod.texto_ideal("#336699"))

    def test_wcag(self):
        saida = _um("contraste wcag #000000 #ffffff", "contraste-wcag")
        mod = af.carregar("contraste-wcag", "wcg_core")
        razao = mod.contrast(mod.parse_color("#000000"), mod.parse_color("#ffffff"))
        self.assertEqual(saida["resposta"], af._num(razao, 2))

    def test_daltonismo(self):
        saida = _um("daltonismo protanopia #ff0000", "contraste-wcag")
        mod = af.carregar("contraste-wcag", "wcg_core")
        rgb = mod.simulate(mod.parse_color("#ff0000"), "Protanopia")
        self.assertEqual(saida["resposta"], mod.to_hex(rgb))

    def test_escala(self):
        saida = _um("escala tipografica base 16 razao 1,25", "estudio-tipografia")
        mod = af.carregar("estudio-tipografia", "tip_core")
        escala = mod.calculate_modular_scale(16, 1.25)
        self.assertEqual(saida["resposta"], str(escala["h1_px"]).replace(".", ",") + " px")

    def test_rle(self):
        saida = _um("rle codificar AAAABBB", "compressao-rle")
        mod = af.carregar("compressao-rle", "rle_core")
        self.assertEqual(saida["resposta"], mod.rle_encode_text("AAAABBB"))

    def test_rle_voltar(self):
        saida = _um("rle decodificar A4B3", "compressao-rle")
        mod = af.carregar("compressao-rle", "rle_core")
        self.assertEqual(saida["resposta"], mod.rle_decode_text("A4B3"))

    def test_markov(self):
        corpo = "o rato roeu a roupa do rei de roma o rato"
        frase = "markov semente 7 tamanho 6 texto " + corpo
        saida = _um(frase, "gerador-markov")
        mod = af.carregar("gerador-markov", "mkv_core")
        modelo = mod.build_model(mod.tokenize(corpo), 2)
        self.assertEqual(saida["resposta"], mod.generate(modelo, 6, 7))

    def test_lux(self):
        saida = _um("iluminancia candela 100 distancia 2", "calculadora-fotometria-lux-lumen")
        mod = af.carregar("calculadora-fotometria-lux-lumen", "lux_core")
        self.assertEqual(saida["resposta"], af._num(mod.inverse_square_law(100, 2), 2) + " lux")

    def test_lumens(self):
        frase = "metodo dos lumens comprimento 5 largura 4 lux 300 fluxo 800"
        saida = _um(frase, "calculadora-fotometria-lux-lumen")
        mod = af.carregar("calculadora-fotometria-lux-lumen", "lux_core")
        r = mod.calculate_lumen_method(5, 4, 300, 800)
        self.assertEqual(saida["resposta"], str(r["num_fixtures"]) + " luminárias")

    def test_fotovoltaica(self):
        saida = _um("fotovoltaica consumo 300 hsp 5", "calculadora-fotovoltaica")
        mod = af.carregar("calculadora-fotovoltaica", "pvs_core")
        r = mod.dimensionar(300, 5)
        self.assertEqual(saida["resposta"], str(r["modulos"]) + " módulos")

    def test_ev(self):
        saida = _um("exposicao fotografica f 8 tempo 1/125 iso 100", "calculadora-fotografia")
        mod = af.carregar("calculadora-fotografia", "fot_core")
        self.assertEqual(saida["resposta"], "EV " + af._num(mod.ev(8, 1 / 125, 100), 2))

    def test_nd(self):
        saida = _um("filtro nd tempo 1/30 stops 6", "calculadora-fotografia")
        mod = af.carregar("calculadora-fotografia", "fot_core")
        self.assertEqual(saida["resposta"], mod.formatar_tempo(mod.tempo_nd(1 / 30, 6)))

    def test_impressao(self):
        frase = "tamanho impressao largura 6000 altura 4000 dpi 300"
        saida = _um(frase, "calculadora-fotografia")
        mod = af.carregar("calculadora-fotografia", "fot_core")
        largura, altura = mod.tamanho_impressao_cm(6000, 4000, 300)
        self.assertEqual(saida["resposta"], af._num(largura, 1) + " x " + af._num(altura, 1) + " cm")

    def test_regra500(self):
        saida = _um("regra 500 focal 24 mm crop 1,5", "calculadora-fotografia")
        mod = af.carregar("calculadora-fotografia", "fot_core")
        self.assertEqual(saida["resposta"], af._num(mod.regra_500(24, 1.5), 2) + " s")

    def test_hiperfocal(self):
        frase = "hiperfocal focal 50 abertura 8 largura 36 altura 24"
        saida = _um(frase, "calculadora-fotografia")
        mod = af.carregar("calculadora-fotografia", "fot_core")
        mm = mod.hiperfocal_mm(50, 8, mod.coc(36, 24))
        self.assertEqual(saida["resposta"], af._num(mm / 1000.0, 2) + " m")

    def test_piscina(self):
        frase = "volume piscina retangular comprimento 8 largura 4 profundidade 1,5"
        saida = _um(frase, "calculadora-piscina")
        mod = af.carregar("calculadora-piscina", "psc_core")
        self.assertEqual(saida["resposta"], af._num(mod.volume_retangular(8, 4, 1.5), 2) + " m3")

    def test_piscina_redonda(self):
        frase = "volume piscina redonda diametro 6 profundidade 1,4"
        saida = _um(frase, "calculadora-piscina")
        mod = af.carregar("calculadora-piscina", "psc_core")
        self.assertEqual(saida["resposta"], af._num(mod.volume_redonda(6, 1.4), 2) + " m3")

    def test_cortina(self):
        saida = _um("cortina trilho 3 altura 2,6", "metragem-costura")
        mod = af.carregar("metragem-costura", "cst_core")
        r = mod.metros_cortina(3, 2.6)
        self.assertEqual(saida["resposta"], af._num(r["metros_compra"], 1) + " m")

    def test_mojibake(self):
        ruim = "ção".encode("utf-8").decode("latin-1")
        saida = _um("corrigir mojibake " + ruim, "conversor-encoding")
        mod = af.carregar("conversor-encoding", "enc_core")
        self.assertEqual(saida["resposta"], mod.fix_mojibake(ruim))

    def test_piso(self):
        frase = "piso vinilico area 20 largura 20 comprimento 120"
        saida = _um(frase, "piso-vinilico")
        mod = af.carregar("piso-vinilico", "vin_core")
        r = mod.material(20, 20, 120)
        self.assertEqual(saida["resposta"], str(r["caixas"]) + " caixas")

    def test_ean(self):
        saida = _um("ean digito 789100031234", "codigo-barras")
        mod = af.carregar("codigo-barras", "bar_core")
        self.assertEqual(saida["resposta"], mod.calc_ean_check_digit("789100031234"))

    def test_pais(self):
        saida = _um("pais gs1 789", "codigo-barras")
        mod = af.carregar("codigo-barras", "bar_core")
        self.assertEqual(saida["resposta"], mod.detect_gs1_country("789"))

    def test_grashof(self):
        frase = "grashof base 10 manivela 4 biela 9 balancim 8"
        saida = _um(frase, "simulador-mecanismo-quatro-barras")
        mod = af.carregar("simulador-mecanismo-quatro-barras", "mqb_core")
        r = mod.classificar_grashof(10, 4, 9, 8)
        self.assertEqual(saida["resposta"], r["classe"])

    def test_simulado(self):
        frase = "simulado cespe total 100 acertos 70 erros 10 branco 20 tempo 240 corte 70"
        saida = _um(frase, "analisador-desempenho-simulados")
        mod = af.carregar("analisador-desempenho-simulados", "qsm_core")
        r = mod.calcular_desempenho_simulado(100, 70, 10, 20, 240, "cespe_1_para_1", 70)
        self.assertEqual(saida["resposta"], af._num(r["pontuacao_liquida"], 1))

    def test_sisu(self):
        frase = "sisu redacao 800 matematica 700 natureza 600 humanas 650 linguagens 680"
        saida = _um(frase, "analisador-nota-corte-sisu-enem")
        mod = af.carregar("analisador-nota-corte-sisu-enem", "nce_core")
        r = mod.calcular_sisu_enem(800, 1, 700, 1, 600, 1, 650, 1, 680, 1)
        self.assertEqual(saida["resposta"], af._num(r["media_ponderada"], 2))

    def test_fala(self):
        saida = _um("ritmo de fala palavras 900 slot 10", "ritmo-fala-apresentacao")
        mod = af.carregar("ritmo-fala-apresentacao", "spm_core")
        r = mod.analisar_apresentacao(900, 10)
        self.assertEqual(saida["resposta"], af._num(r["wpm_necessario"], 1) + " pal/min")

    def test_fotos(self):
        frase = "espaco fotos livre 64 megapixels 12 jpeg 1080p30"
        saida = _um(frase, "espaco-fotos-videos-celular")
        mod = af.carregar("espaco-fotos-videos-celular", "arm_core")
        r = mod.calcular(64, 12, "JPEG", "1080p 30fps", False)
        self.assertEqual(saida["resposta"], str(r["so_fotos"]) + " fotos")


if __name__ == "__main__":
    unittest.main()
