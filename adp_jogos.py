# -*- coding: utf-8 -*-
"""Adaptadores da barra para Jogos & Diversao e o que caiu nessa categoria.

Cada calcular chama o modulo real. Nao refaz a conta.
"""
from __future__ import annotations

import calendar
import datetime
import hashlib
import os
import random
import re
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

import adp_financas as af

norm = af.norm
combina = af.combina
ler = af.ler
C = af.C
carregar = af.carregar
pacote = af.pacote
_num = af._num

ADAPTADORES = []

# Replantio e a sentenca NMEA nao podem depender do relogio do teste.
HOJE_JOGOS = datetime.date(2026, 11, 9)
NMEA_EPOCH = calendar.timegm((2026, 11, 9, 12, 0, 0))

_RE_DADO = re.compile(r"(\d*)d(\d+)([+-]\d+)?", re.IGNORECASE)
_RE_ALVO = re.compile(r"alvo\s+(\d+)")
_RE_LL = re.compile(r"lat\s+(-?\d+(?:[.,]\d+)?)\s+lon\s+(-?\d+(?:[.,]\d+)?)")
_RE_DATA = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_RE_PALPITE = re.compile(r"([A-Za-zÀ-ÿ]+)\s+(menino|menina)\s+(\d+(?:[.,]\d+)?)")
_RE_RESULTADO = re.compile(r"resultado\s+(menino|menina)")
_RE_PLACAR = re.compile(r"([A-Za-zÀ-ÿ]+)\s+(\d+)")
_GENEROS = ("Phalaenopsis", "Dendrobium", "Cattleya", "Oncidium", "Vanda")
_JOGOS_CARTA = (
    ("copas", "Copas (Hearts)"),
    ("hearts", "Copas (Hearts)"),
    ("canastra", "Canastra"),
    ("buraco", "Buraco"),
    ("tranca", "Tranca"),
    ("pife", "Pife"),
    ("uno", "Uno"),
)


def _registrar(chave, palavras, extrair, calcular):
    ADAPTADORES.append({
        "chave": chave,
        "palavras": list(palavras),
        "extrair": extrair,
        "calcular": calcular,
    })


def _depois(texto, marca):
    t = norm(texto)
    i = t.find(norm(marca))
    if i < 0:
        return None
    return texto[i + len(norm(marca)):].strip()


def _chamar(fn):
    try:
        return fn()
    except ValueError as e:
        return pacote(str(e).splitlines()[0], "A ferramenta recusou esses dados.")


def _semente(texto):
    digest = hashlib.sha256(texto.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little")


def _notacao(texto):
    m = _RE_DADO.search(texto)
    if not m:
        return None
    bruto = m.group(0).replace(" ", "")
    if bruto[0] in "+-":
        return None
    return bruto


def _genero(texto):
    t = norm(texto)
    for nome in _GENEROS:
        if norm(nome) in t:
            return nome
    return None


def _float_br(s):
    return float(s.replace(",", "."))


def _extrair_esperado(texto):
    if not combina(texto, [("dado rpg",)]):
        return None
    if "chance" in norm(texto):
        return None
    nota = _notacao(texto)
    if not nota:
        return None
    return {"notacao": nota}


def _calcular_esperado(params):
    def fazer():
        mod = carregar("dados-rpg", "rpg_core")
        n, faces, k = mod.parse_notacao(params["notacao"])
        return pacote(
            _num(mod.esperanca(n, faces, k), 2),
            "Valor esperado de " + params["notacao"] + ".",
        )
    return _chamar(fazer)


def _extrair_chance(texto):
    if not combina(texto, [("chance dado",)]):
        return None
    nota = _notacao(texto)
    alvo = _RE_ALVO.search(norm(texto))
    if not nota or not alvo:
        return None
    return {"notacao": nota, "alvo": int(alvo.group(1))}


def _calcular_chance(params):
    def fazer():
        mod = carregar("dados-rpg", "rpg_core")
        n, faces, k = mod.parse_notacao(params["notacao"])
        dist = mod.distribuicao(n, faces, k)
        return pacote(
            str(mod.prob_min(dist, params["alvo"])),
            "Probabilidade exata de tirar pelo menos " + str(params["alvo"]) + ".",
        )
    return _chamar(fazer)


def _extrair_vantagem(texto):
    t = norm(texto)
    if "desvantagem" in t or not combina(texto, [("vantagem d20",)]):
        return None
    return {"desvantagem": False}


def _extrair_desvantagem(texto):
    if not combina(texto, [("desvantagem d20",)]):
        return None
    return {"desvantagem": True}


def _calcular_d20(params):
    def fazer():
        mod = carregar("dados-rpg", "rpg_core")
        info = mod.resumo(mod.d20_vantagem(params["desvantagem"]))
        modo = "menor" if params["desvantagem"] else "maior"
        return pacote(_num(info["media"], 2), "Média de 2d20 ficando com o " + modo + ".")
    return _chamar(fazer)


def _extrair_amigo(texto):
    if not combina(texto, [("amigo secreto",)]):
        return None
    corpo = _depois(texto, "amigo secreto")
    if not corpo:
        return None
    return {"corpo": corpo}


def _calcular_amigo(params):
    def fazer():
        mod = carregar("sorteios", "st_core")
        nomes = mod.parse_names(params["corpo"])
        rng = random.Random(_semente("|".join(nomes)))
        pares = mod.secret_santa(nomes, rng=rng)
        texto = ", ".join(a + " tira " + b for a, b in pares.items())
        return pacote(texto, "Semente fixa da lista, pra mesma busca repetir o sorteio.")
    return _chamar(fazer)


def _extrair_roleta(texto):
    if not combina(texto, [("roleta",)]):
        return None
    corpo = _depois(texto, "roleta")
    if not corpo:
        return None
    return {"corpo": corpo}


def _calcular_roleta(params):
    def fazer():
        mod = carregar("sorteios", "st_core")
        opcoes = mod.parse_names(params["corpo"])
        rng = random.Random(_semente("|".join(opcoes)))
        indice = mod.wheel_pick(opcoes, rng=rng)
        return pacote(opcoes[indice], "Semente fixa das opções, pra mesma busca repetir.")
    return _chamar(fazer)


def _extrair_times(texto):
    if not combina(texto, [("dividir times",)]):
        return None
    corpo = _depois(texto, "dividir times")
    if not corpo:
        return None
    m = re.match(r"(\d+)\s+(.+)", corpo, re.S)
    if not m:
        return None
    return {"qtd": int(m.group(1)), "corpo": m.group(2).strip()}


def _calcular_times(params):
    def fazer():
        mod = carregar("sorteios", "st_core")
        nomes = mod.parse_names(params["corpo"])
        rng = random.Random(_semente(str(params["qtd"]) + "|" + "|".join(nomes)))
        times = mod.split_teams(nomes, params["qtd"], rng=rng)
        texto = " | ".join(", ".join(time) for time in times)
        return pacote(texto, "Semente fixa da lista. Níveis não informados, a ferramenta trata todos iguais.")
    return _chamar(fazer)


def _extrair_palavras(texto):
    if not combina(texto, [("contar palavras",)]):
        return None
    corpo = _depois(texto, "contar palavras")
    if not corpo:
        return None
    return {"corpo": corpo}


def _calcular_palavras(params):
    def fazer():
        mod = carregar("contador-palavras", "wdc_core")
        stats = mod.analyze(params["corpo"])
        return pacote(
            str(stats.words),
            "Leitura estimada em " + _num(stats.reading_min, 1) + " min a 200 palavras por minuto.",
        )
    return _chamar(fazer)


def _extrair_xadrez(texto):
    if not combina(texto, [("material xadrez",)]):
        return None
    return {"pastor": "pastor" in norm(texto)}


def _calcular_xadrez(params):
    def fazer():
        mod = carregar("estudio-xadrez", "chz_core")
        if params["pastor"]:
            fen = next(f for nome, f, _nota in mod.FAMOUS_POSITIONS if "Pastor" in nome)
            titulo = "Mate do Pastor, posição da ferramenta."
        else:
            fen = mod.INITIAL_FEN
            titulo = "Posição inicial."
        estado = mod.parse_fen(fen)
        mat = mod.evaluate_material(estado["board"])
        return pacote(
            mat["advantage"],
            titulo + " Brancas " + str(mat["white_material"]) + ", pretas " + str(mat["black_material"]) + ".",
        )
    return _chamar(fazer)


def _grade(texto):
    digitos = re.sub(r"\D", "", texto)
    if len(digitos) != 81:
        return None
    return [int(ch) for ch in digitos]


def _extrair_sudoku(texto):
    if not combina(texto, [("resolver sudoku",)]):
        return None
    grade = _grade(texto)
    if grade is None:
        return None
    return {"grade": grade}


def _calcular_sudoku(params):
    def fazer():
        mod = carregar("sudoku", "sdk_core")
        sol = mod.solve(params["grade"])
        if not sol:
            return pacote("sem solução", "O solver não achou uma grade completa.")
        return pacote("".join(str(d) for d in sol), "Primeira solução do solver.")
    return _chamar(fazer)


def _extrair_nivel(texto):
    if not combina(texto, [("dificuldade sudoku",)]):
        return None
    grade = _grade(texto)
    if grade is None:
        return None
    return {"grade": grade}


def _calcular_nivel(params):
    def fazer():
        mod = carregar("sudoku", "sdk_core")
        return pacote(str(mod.grade(params["grade"])), "Nivel de tecnica de 1 a 4.")
    return _chamar(fazer)


def _extrair_capital(texto):
    if not combina(texto, [("capital do pais",)]):
        return None
    pais = _depois(texto, "capital do pais")
    if not pais:
        return None
    return {"pais": pais}


def _calcular_capital(params):
    def fazer():
        mod = carregar("quiz-geografia", "qg_core")
        alvo = mod.normalizar(params["pais"])
        achou = [linha for linha in mod.linhas_paises(alvo) if mod.normalizar(linha[0]) == alvo]
        if not achou:
            return pacote("país fora da lista", "O quiz não tem esse país.")
        return pacote(achou[0][1], achou[0][0] + ", " + achou[0][2] + ".")
    return _chamar(fazer)


def _extrair_pontos(texto):
    if not combina(texto, [("pontos do quiz",)]):
        return None
    return ler(texto, [C("seguidos", ["seguidos"], "int", True)])


def _calcular_pontos(params):
    def fazer():
        mod = carregar("quiz-geografia", "qg_core")
        pts = mod.pontos_resposta(True, params["seguidos"])
        return pacote(str(pts), "Conta como acerto. 10 mais 2 por acerto seguido, teto de 5.")
    return _chamar(fazer)


def _extrair_familia(texto):
    if not combina(texto, [("quiz familia",)]):
        return None
    p = ler(texto, [C("semente", ["semente"], "int", False, 1)])
    return p or {"semente": 1}


def _calcular_familia(params):
    def fazer():
        mod = carregar("quiz-familia", "qzf_core")
        semente = int(params["semente"])
        quiz = mod.Quiz(mod.banco_padrao(), ["casa"], seed=semente)
        item = quiz.proxima()
        resp = item["respostas"][item["correta"]]
        return pacote(resp, "Pergunta: " + item["pergunta"] + ". Semente " + str(semente) + ".")
    return _chamar(fazer)


def _extrair_orquidea(texto):
    if not combina(texto, [("orquidea",)]):
        return None
    t = norm(texto)
    if "sintoma" in t or "replantio" in t:
        return None
    genero = _genero(texto)
    if not genero:
        return None
    estacao = "inverno" if "inverno" in t else "verão"
    return {"genero": genero, "estacao": estacao}


def _calcular_orquidea(params):
    def fazer():
        mod = carregar("cuidados-orquideas", "orq_core")
        info = mod.cuidado(params["genero"], params["estacao"])
        return pacote(
            str(info["rega_dias"]) + " dias",
            params["genero"] + ", " + params["estacao"] + ". Luz: " + info["luz"] + ".",
        )
    return _chamar(fazer)


def _extrair_replantio(texto):
    if not combina(texto, [("replantio",)]):
        return None
    genero = _genero(texto)
    datas = _RE_DATA.findall(texto)
    if not genero or not datas:
        return None
    dia, mes, ano = datas[0]
    return {"genero": genero, "data": datetime.date(int(ano), int(mes), int(dia))}


def _calcular_replantio(params):
    def fazer():
        mod = carregar("cuidados-orquideas", "orq_core")
        falta = mod.precisa_replantar(params["data"], params["genero"], hoje=HOJE_JOGOS)
        return pacote("sim" if falta else "não", "Conta em 09/11/2026, prazo da própria ficha.")
    return _chamar(fazer)


def _extrair_sintoma(texto):
    if not combina(texto, [("orquidea",), ("sintoma",)]):
        return None
    corpo = _depois(texto, "sintoma")
    if not corpo:
        return None
    return {"sintoma": corpo}


def _calcular_sintoma(params):
    def fazer():
        mod = carregar("cuidados-orquideas", "orq_core")
        return pacote(mod.diagnosticar(params["sintoma"]), "Texto da ficha da ferramenta.")
    return _chamar(fazer)


def _extrair_nmea(texto):
    if not combina(texto, [("sentenca nmea",)]):
        return None
    m = _RE_LL.search(norm(texto))
    if not m:
        return None
    return {"lat": _float_br(m.group(1)), "lon": _float_br(m.group(2))}


def _calcular_nmea(params):
    def fazer():
        mod = carregar("gps-falso", "nmea")
        frase = mod.gga(params["lat"], params["lon"], t=NMEA_EPOCH)
        return pacote(frase, "GGA em 09/11/2026 12:00 UTC. Altitude 10 m, 9 satélites e HDOP 0,9, padrões da função.")
    return _chamar(fazer)


def _extrair_toml(texto):
    if not combina(texto, [("validar toml",)]):
        return None
    corpo = _depois(texto, "validar toml")
    if not corpo:
        return None
    return {"corpo": corpo}


def _calcular_toml(params):
    def fazer():
        mod = carregar("validador-toml", "tml_core")
        _ok, msg, _data = mod.validate(params["corpo"])
        return pacote(msg, "tomllib da ferramenta.")
    return _chamar(fazer)


def _extrair_dotenv(texto):
    if not combina(texto, [("validar dotenv",)]):
        return None
    corpo = _depois(texto, "validar dotenv")
    if not corpo:
        return None
    return {"corpo": corpo}


def _calcular_dotenv(params):
    def fazer():
        mod = carregar("validador-dotenv", "den_core")
        relatorio = mod.parse_env(params["corpo"])
        linha = mod.summarize(relatorio).splitlines()[0]
        return pacote(linha, "Resumo do parser de .env.")
    return _chamar(fazer)


def _extrair_diff(texto):
    if not combina(texto, [("diff config",)]):
        return None
    corpo = _depois(texto, "diff config")
    if not corpo or "|" not in corpo:
        return None
    a, b = corpo.split("|", 1)
    if not a.strip() or not b.strip():
        return None
    return {"a": a.strip(), "b": b.strip()}


def _calcular_diff(params):
    def fazer():
        mod = carregar("comparador-dados", "dfx_core")
        diff = mod.diff_structured(
            mod.parse_structured(params["a"]),
            mod.parse_structured(params["b"]),
        )
        return pacote(str(diff["modified"]), "Campos modificados no diff estrutural.")
    return _chamar(fazer)


def _extrair_cha(texto):
    if not combina(texto, [("bolao do cha",)]):
        return None
    palpites = []
    for nome, sexo, valor in _RE_PALPITE.findall(texto):
        palpites.append((nome, sexo, float(valor.replace(",", "."))))
    resultado = _RE_RESULTADO.search(norm(texto))
    if len(palpites) < 1 or not resultado:
        return None
    return {"palpites": palpites, "resultado": resultado.group(1)}


def _calcular_cha(params):
    def fazer():
        mod = carregar("cha-revelacao", "rev_core")
        dados = {"palpites": []}
        for nome, sexo, valor in params["palpites"]:
            mod.registrar_palpite(dados, nome, sexo, valor)
        rateio = mod.rateio_bolao(dados, params["resultado"])
        return pacote("R$ " + _num(rateio["por_pessoa"]), "Cada vencedor, sobre o bolao informado.")
    return _chamar(fazer)


def _extrair_placar(texto):
    if not combina(texto, [("placar",)]):
        return None
    jogo = None
    marca = None
    for gatilho, oficial in _JOGOS_CARTA:
        if combina(texto, [(gatilho,)]):
            jogo = oficial
            marca = gatilho
            break
    if not jogo:
        return None
    corpo = _depois(texto, marca)
    pares = _RE_PLACAR.findall(corpo or "")
    if len(pares) < 2:
        return None
    return {"jogo": jogo, "pares": [(n, int(p)) for n, p in pares]}


def _calcular_placar(params):
    def fazer():
        mod = carregar("placar-cartas", "plc_core")
        nomes = [n for n, _p in params["pares"]]
        pontos = [p for _n, p in params["pares"]]
        placar = mod.Placar(nomes, params["jogo"])
        placar.adicionar(pontos)
        vencedor = placar.vencedor()
        if vencedor:
            return pacote(vencedor, params["jogo"] + ", meta " + str(placar.meta) + " da ferramenta.")
        lider, total = placar.classificacao()[0]
        return pacote(lider + " " + str(total), "Ainda não bateu a meta " + str(placar.meta) + ".")
    return _chamar(fazer)


_registrar("dados-rpg", ["dado rpg"], _extrair_esperado, _calcular_esperado)
_registrar("dados-rpg", ["chance dado"], _extrair_chance, _calcular_chance)
_registrar("dados-rpg", ["vantagem d20"], _extrair_vantagem, _calcular_d20)
_registrar("dados-rpg", ["desvantagem d20"], _extrair_desvantagem, _calcular_d20)
_registrar("sorteios", ["amigo secreto"], _extrair_amigo, _calcular_amigo)
_registrar("sorteios", ["roleta"], _extrair_roleta, _calcular_roleta)
_registrar("sorteios", ["dividir times"], _extrair_times, _calcular_times)
_registrar("contador-palavras", ["contar palavras"], _extrair_palavras, _calcular_palavras)
_registrar("estudio-xadrez", ["material xadrez"], _extrair_xadrez, _calcular_xadrez)
_registrar("sudoku", ["resolver sudoku"], _extrair_sudoku, _calcular_sudoku)
_registrar("sudoku", ["dificuldade sudoku"], _extrair_nivel, _calcular_nivel)
_registrar("quiz-geografia", ["capital do pais"], _extrair_capital, _calcular_capital)
_registrar("quiz-geografia", ["pontos do quiz"], _extrair_pontos, _calcular_pontos)
_registrar("quiz-familia", ["quiz familia"], _extrair_familia, _calcular_familia)
_registrar("cuidados-orquideas", ["orquidea"], _extrair_orquidea, _calcular_orquidea)
_registrar("cuidados-orquideas", ["replantio"], _extrair_replantio, _calcular_replantio)
_registrar("cuidados-orquideas", ["sintoma"], _extrair_sintoma, _calcular_sintoma)
_registrar("gps-falso", ["sentenca nmea"], _extrair_nmea, _calcular_nmea)
_registrar("validador-toml", ["validar toml"], _extrair_toml, _calcular_toml)
_registrar("validador-dotenv", ["validar dotenv"], _extrair_dotenv, _calcular_dotenv)
_registrar("comparador-dados", ["diff config"], _extrair_diff, _calcular_diff)
_registrar("cha-revelacao", ["bolao do cha"], _extrair_cha, _calcular_cha)
_registrar("placar-cartas", ["placar"], _extrair_placar, _calcular_placar)
