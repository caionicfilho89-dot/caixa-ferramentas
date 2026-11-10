# -*- coding: utf-8 -*-
"""Testa os adaptadores de Jogos chamando o nucleo real."""
from __future__ import annotations

import datetime
import random
import unittest

import adp_financas as af
import adp_jogos as aj

CONHECIDO = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"


def _hits(texto):
    return [a for a in aj.ADAPTADORES if a["extrair"](texto) is not None]


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


class Jogos(unittest.TestCase):
    def test_quantidade_e_frase_alheia(self):
        self.assertGreaterEqual(len(aj.ADAPTADORES), 15)
        self.assertEqual(_hits("que horas o onibus passa na praca"), [])

    def test_esperado(self):
        saida = _um("dado rpg 2d6+3", "dados-rpg")
        mod = af.carregar("dados-rpg", "rpg_core")
        n, faces, k = mod.parse_notacao("2d6+3")
        self.assertEqual(saida["resposta"], af._num(mod.esperanca(n, faces, k), 2))

    def test_chance(self):
        saida = _um("chance dado rpg 2d6 alvo 7", "dados-rpg")
        mod = af.carregar("dados-rpg", "rpg_core")
        n, faces, k = mod.parse_notacao("2d6")
        dist = mod.distribuicao(n, faces, k)
        self.assertEqual(saida["resposta"], str(mod.prob_min(dist, 7)))

    def test_vantagem(self):
        saida = _um("vantagem d20", "dados-rpg")
        mod = af.carregar("dados-rpg", "rpg_core")
        info = mod.resumo(mod.d20_vantagem(False))
        self.assertEqual(saida["resposta"], af._num(info["media"], 2))

    def test_desvantagem(self):
        saida = _um("desvantagem d20", "dados-rpg")
        mod = af.carregar("dados-rpg", "rpg_core")
        info = mod.resumo(mod.d20_vantagem(True))
        self.assertEqual(saida["resposta"], af._num(info["media"], 2))

    def test_amigo(self):
        corpo = "Ana; Bia; Caio; Davi"
        saida = _um("amigo secreto " + corpo, "sorteios")
        mod = af.carregar("sorteios", "st_core")
        nomes = mod.parse_names(corpo)
        rng = random.Random(aj._semente("|".join(nomes)))
        pares = mod.secret_santa(nomes, rng=rng)
        esperado = ", ".join(a + " tira " + b for a, b in pares.items())
        self.assertEqual(saida["resposta"], esperado)

    def test_roleta(self):
        corpo = "pizza; sushi; burger"
        saida = _um("roleta " + corpo, "sorteios")
        mod = af.carregar("sorteios", "st_core")
        opcoes = mod.parse_names(corpo)
        rng = random.Random(aj._semente("|".join(opcoes)))
        indice = mod.wheel_pick(opcoes, rng=rng)
        self.assertEqual(saida["resposta"], opcoes[indice])

    def test_times(self):
        corpo = "Ana; Bia; Caio; Davi"
        saida = _um("dividir times 2 " + corpo, "sorteios")
        mod = af.carregar("sorteios", "st_core")
        nomes = mod.parse_names(corpo)
        rng = random.Random(aj._semente("2|" + "|".join(nomes)))
        times = mod.split_teams(nomes, 2, rng=rng)
        esperado = " | ".join(", ".join(time) for time in times)
        self.assertEqual(saida["resposta"], esperado)

    def test_palavras(self):
        corpo = "O rato roeu a roupa do rei."
        saida = _um("contar palavras " + corpo, "contador-palavras")
        mod = af.carregar("contador-palavras", "wdc_core")
        self.assertEqual(saida["resposta"], str(mod.analyze(corpo).words))

    def test_xadrez_inicial(self):
        saida = _um("material xadrez", "estudio-xadrez")
        mod = af.carregar("estudio-xadrez", "chz_core")
        mat = mod.evaluate_material(mod.parse_fen(mod.INITIAL_FEN)["board"])
        self.assertEqual(saida["resposta"], mat["advantage"])

    def test_xadrez_pastor(self):
        saida = _um("material xadrez pastor", "estudio-xadrez")
        mod = af.carregar("estudio-xadrez", "chz_core")
        fen = next(f for nome, f, _nota in mod.FAMOUS_POSITIONS if "Pastor" in nome)
        mat = mod.evaluate_material(mod.parse_fen(fen)["board"])
        self.assertEqual(saida["resposta"], mat["advantage"])

    def test_sudoku(self):
        saida = _um("resolver sudoku " + CONHECIDO, "sudoku")
        mod = af.carregar("sudoku", "sdk_core")
        sol = mod.solve([int(ch) for ch in CONHECIDO])
        self.assertEqual(saida["resposta"], "".join(str(d) for d in sol))

    def test_nivel_sudoku(self):
        saida = _um("dificuldade sudoku " + CONHECIDO, "sudoku")
        mod = af.carregar("sudoku", "sdk_core")
        self.assertEqual(saida["resposta"], str(mod.grade([int(ch) for ch in CONHECIDO])))

    def test_capital(self):
        saida = _um("capital do pais franca", "quiz-geografia")
        mod = af.carregar("quiz-geografia", "qg_core")
        alvo = mod.normalizar("franca")
        linha = next(x for x in mod.linhas_paises(alvo) if mod.normalizar(x[0]) == alvo)
        self.assertEqual(saida["resposta"], linha[1])

    def test_pontos_quiz(self):
        saida = _um("pontos do quiz seguidos 3", "quiz-geografia")
        mod = af.carregar("quiz-geografia", "qg_core")
        self.assertEqual(saida["resposta"], str(mod.pontos_resposta(True, 3)))

    def test_familia(self):
        saida = _um("quiz familia semente 1", "quiz-familia")
        mod = af.carregar("quiz-familia", "qzf_core")
        quiz = mod.Quiz(mod.banco_padrao(), ["casa"], seed=1)
        item = quiz.proxima()
        self.assertEqual(saida["resposta"], item["respostas"][item["correta"]])

    def test_orquidea(self):
        saida = _um("orquidea phalaenopsis verao", "cuidados-orquideas")
        mod = af.carregar("cuidados-orquideas", "orq_core")
        info = mod.cuidado("Phalaenopsis", "verão")
        self.assertEqual(saida["resposta"], str(info["rega_dias"]) + " dias")

    def test_replantio(self):
        saida = _um("replantio orquidea phalaenopsis desde 01/01/2024", "cuidados-orquideas")
        mod = af.carregar("cuidados-orquideas", "orq_core")
        falta = mod.precisa_replantar(datetime.date(2024, 1, 1), "Phalaenopsis", hoje=aj.HOJE_JOGOS)
        self.assertEqual(saida["resposta"], "sim" if falta else "não")

    def test_sintoma(self):
        saida = _um("orquidea sintoma folha amarela", "cuidados-orquideas")
        mod = af.carregar("cuidados-orquideas", "orq_core")
        self.assertEqual(saida["resposta"], mod.diagnosticar("folha amarela"))

    def test_nmea(self):
        saida = _um("sentenca nmea lat -23,55 lon -46,63", "gps-falso")
        mod = af.carregar("gps-falso", "nmea")
        self.assertEqual(saida["resposta"], mod.gga(-23.55, -46.63, t=aj.NMEA_EPOCH))

    def test_toml(self):
        corpo = 'titulo = "oi"'
        saida = _um("validar toml " + corpo, "validador-toml")
        mod = af.carregar("validador-toml", "tml_core")
        _ok, msg, _data = mod.validate(corpo)
        self.assertEqual(saida["resposta"], msg)

    def test_dotenv(self):
        corpo = "API_KEY=abcdefgh"
        saida = _um("validar dotenv " + corpo, "validador-dotenv")
        mod = af.carregar("validador-dotenv", "den_core")
        self.assertEqual(saida["resposta"], mod.summarize(mod.parse_env(corpo)).splitlines()[0])

    def test_diff(self):
        esq = '{"a": 1}'
        dire = '{"a": 2}'
        saida = _um("diff config " + esq + " | " + dire, "comparador-dados")
        mod = af.carregar("comparador-dados", "dfx_core")
        diff = mod.diff_structured(mod.parse_structured(esq), mod.parse_structured(dire))
        self.assertEqual(saida["resposta"], str(diff["modified"]))

    def test_cha(self):
        saida = _um("bolao do cha ana menino 10 bia menina 20 resultado menino", "cha-revelacao")
        mod = af.carregar("cha-revelacao", "rev_core")
        dados = {"palpites": []}
        mod.registrar_palpite(dados, "ana", "menino", 10)
        mod.registrar_palpite(dados, "bia", "menina", 20)
        rateio = mod.rateio_bolao(dados, "menino")
        self.assertEqual(saida["resposta"], "R$ " + af._num(rateio["por_pessoa"]))

    def test_placar(self):
        saida = _um("placar uno ana 500 bia 40", "placar-cartas")
        mod = af.carregar("placar-cartas", "plc_core")
        placar = mod.Placar(["ana", "bia"], "Uno")
        placar.adicionar([500, 40])
        self.assertEqual(saida["resposta"], placar.vencedor())


if __name__ == "__main__":
    unittest.main()
