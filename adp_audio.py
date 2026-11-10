# -*- coding: utf-8 -*-
"""Adaptadores da barra para Audio & Video e o que caiu nessa categoria.

Cada calcular chama o modulo real. Nao refaz a conta.
"""
from __future__ import annotations

import datetime
import os
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

# Idade e vencimento nao podem depender do relogio do teste.
HOJE_AUDIO = datetime.date(2026, 11, 9)

_RE_DATA = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_RE_NOTA = re.compile(r"\b([A-Ga-g](?:#|b)?)(\d)\b")
_RE_NOTA_SOLTA = re.compile(r"\b([A-Ga-g](?:#|b)?)\b")
_RE_MODO = re.compile(r"\b(te|tm)(\d)(\d)\b", re.IGNORECASE)
_ESCALAS = (
    ("menor", "Menor natural (eólio)"),
    ("maior", "Maior (jônio)"),
    ("blues", "Blues"),
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


def _datas(texto):
    achadas = []
    for dia, mes, ano in _RE_DATA.findall(texto):
        achadas.append(datetime.date(int(ano), int(mes), int(dia)))
    return achadas


def _fmt_data(d):
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def _nota_oitava(texto):
    m = _RE_NOTA.search(texto)
    if not m:
        return None
    return m.group(1).upper(), int(m.group(2))


def _notas_soltas(texto):
    return [m.group(1).upper() for m in _RE_NOTA_SOLTA.finditer(texto)]


def _extrair_andamento(texto):
    if not combina(texto, [("andamento",)]):
        return None
    return ler(texto, [C("bpm", ["andamento"], "num", True)])


def _calcular_andamento(params):
    def fazer():
        mod = carregar("metronomo", "mt_core")
        return pacote(mod.tempo_name(params["bpm"]), "Nome do andamento para esse BPM.")
    return _chamar(fazer)


def _extrair_freq_nota(texto):
    if not combina(texto, [("frequencia da nota",)]):
        return None
    nota = _nota_oitava(texto)
    if not nota:
        return None
    return {"nota": nota[0], "oitava": nota[1]}


def _calcular_freq_nota(params):
    def fazer():
        mod = carregar("teoria-musical", "esm_core")
        hz = mod.frequencia(params["nota"], params["oitava"])
        return pacote(_num(hz, 2) + " Hz", "Lá 4 em 440 Hz, padrão da ferramenta.")
    return _chamar(fazer)


def _extrair_nota_freq(texto):
    if not combina(texto, [("nota da frequencia",)]):
        return None
    return ler(texto, [C("freq", ["frequencia"], "num", True)])


def _calcular_nota_freq(params):
    def fazer():
        mod = carregar("teoria-musical", "esm_core")
        nota, oitava, _cents = mod.nota_de_frequencia(params["freq"])
        return pacote(nota + str(oitava), "Nota mais próxima. Lá 4 em 440 Hz, padrão da ferramenta.")
    return _chamar(fazer)


def _extrair_escala(texto):
    if not combina(texto, [("escala maior", "escala menor", "escala blues")]):
        return None
    t = norm(texto)
    tipo = None
    for chave, nome in _ESCALAS:
        if chave in t:
            tipo = nome
            break
    notas = _notas_soltas(texto)
    if not tipo or not notas:
        return None
    return {"tipo": tipo, "tonica": notas[-1]}


def _calcular_escala(params):
    def fazer():
        mod = carregar("teoria-musical", "esm_core")
        notas = mod.escala(params["tonica"], params["tipo"])
        return pacote(" ".join(notas), params["tipo"] + ".")
    return _chamar(fazer)


def _extrair_acorde(texto):
    if not combina(texto, [("acorde maior", "acorde menor")]):
        return None
    t = norm(texto)
    tipo = "m" if "menor" in t else ""
    notas = _notas_soltas(texto)
    if not notas:
        return None
    return {"tipo": tipo, "raiz": notas[-1]}


def _calcular_acorde(params):
    def fazer():
        mod = carregar("teoria-musical", "esm_core")
        notas = mod.acorde(params["raiz"], params["tipo"])
        return pacote(" ".join(notas), "Tríade.")
    return _chamar(fazer)


def _extrair_intervalo(texto):
    if not combina(texto, [("intervalo de",)]):
        return None
    notas = _notas_soltas(texto)
    if len(notas) < 2:
        return None
    return {"a": notas[0], "b": notas[1]}


def _calcular_intervalo(params):
    def fazer():
        mod = carregar("teoria-musical", "esm_core")
        _semitons, nome = mod.intervalo(params["a"], params["b"])
        return pacote(nome, "Intervalo ascendente dentro da oitava.")
    return _chamar(fazer)


def _extrair_transpor(texto):
    if not combina(texto, [("transpor acorde",)]):
        return None
    corpo = _depois(texto, "acorde")
    dados = ler(texto, [C("semitons", ["semitons"], "int", True)])
    if not corpo or not dados:
        return None
    cifra = corpo.split()[0]
    if not cifra:
        return None
    dados["cifra"] = cifra
    return dados


def _calcular_transpor(params):
    def fazer():
        mod = carregar("teoria-musical", "esm_core")
        return pacote(mod.transpor_acorde(params["cifra"], params["semitons"]), "Transposição da cifra.")
    return _chamar(fazer)


def _extrair_pascoa(texto):
    if not combina(texto, [("pascoa",)]):
        return None
    return ler(texto, [C("ano", ["pascoa"], "int", True)])


def _calcular_pascoa(params):
    def fazer():
        mod = carregar("calculadora-datas", "dts_core")
        return pacote(_fmt_data(mod.pascoa(params["ano"])), "Domingo de Páscoa, calendário gregoriano.")
    return _chamar(fazer)


def _extrair_uteis(texto):
    if not combina(texto, [("datas uteis",)]):
        return None
    datas = _datas(texto)
    if len(datas) < 2:
        return None
    return {"inicio": datas[0], "fim": datas[1]}


def _calcular_uteis(params):
    def fazer():
        mod = carregar("calculadora-datas", "dts_core")
        n = mod.dias_uteis_entre(params["inicio"], params["fim"])
        return pacote(
            str(n) + " dias",
            "Não conta o dia inicial. Feriados nacionais, sem ponto facultativo.",
        )
    return _chamar(fazer)


def _extrair_idade(texto):
    if not combina(texto, [("idade exata",)]):
        return None
    datas = _datas(texto)
    if not datas:
        return None
    return {"nasc": datas[0]}


def _calcular_idade(params):
    def fazer():
        mod = carregar("calculadora-datas", "dts_core")
        r = mod.idade(params["nasc"], HOJE_AUDIO)
        return pacote(str(r["anos"]) + " anos", "Idade em " + _fmt_data(HOJE_AUDIO) + ".")
    return _chamar(fazer)


def _extrair_somar(texto):
    if not combina(texto, [("somar dias na data",)]):
        return None
    datas = _datas(texto)
    dados = ler(texto, [C("quantidade", ["quantidade"], "int", True)])
    if not datas or not dados:
        return None
    dados["data"] = datas[0]
    return dados


def _calcular_somar(params):
    def fazer():
        mod = carregar("calculadora-datas", "dts_core")
        return pacote(
            _fmt_data(mod.somar_dias(params["data"], params["quantidade"])),
            "Dias corridos, sem pular fim de semana.",
        )
    return _chamar(fazer)


def _extrair_iso(texto):
    if not combina(texto, [("semana iso",)]):
        return None
    datas = _datas(texto)
    if not datas:
        return None
    return {"data": datas[0]}


def _calcular_iso(params):
    def fazer():
        mod = carregar("calculadora-datas", "dts_core")
        info = mod.info_data(params["data"])
        return pacote("semana " + str(info["semana_iso"]), info["dia_semana"] + ".")
    return _chamar(fazer)


def _extrair_am(texto):
    if not combina(texto, [("modulacao am",)]):
        return None
    return ler(texto, [
        C("portadora", ["portadora"], "num", True),
        C("modulante", ["modulante"], "num", True),
    ])


def _calcular_am(params):
    def fazer():
        mod = carregar("simulador-modulacao-am-fm", "amf_core")
        r = mod.simulate_am(params["portadora"], params["modulante"])
        return pacote(
            _num(r["mu"], 3),
            "Índice mi. Portadora 1 V e modulante 0,8 V, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_fm(texto):
    if not combina(texto, [("modulacao fm",)]):
        return None
    return ler(texto, [
        C("portadora", ["portadora"], "num", True),
        C("modulante", ["modulante"], "num", True),
        C("desvio", ["desvio"], "num", True),
    ])


def _calcular_fm(params):
    def fazer():
        mod = carregar("simulador-modulacao-am-fm", "amf_core")
        r = mod.simulate_fm(params["portadora"], params["modulante"], params["desvio"])
        return pacote(_num(r["beta"], 3), r["fm_class"] + ".")
    return _chamar(fazer)


def _extrair_guia(texto):
    if not combina(texto, [("guia retangular",)]):
        return None
    modo = _RE_MODO.search(norm(texto))
    dados = ler(texto, [
        C("a", ["a"], "num", True),
        C("b", ["b"], "num", True),
    ])
    if not modo or not dados:
        return None
    dados["m"] = int(modo.group(2))
    dados["n"] = int(modo.group(3))
    return dados


def _calcular_guia(params):
    def fazer():
        mod = carregar("calculadora-guia-ondas-retangular", "gdo_core")
        hz = mod.frequencia_corte_modo(params["a"], params["b"], params["m"], params["n"])
        return pacote(
            _num(hz / 1e9, 3) + " GHz",
            "Frequência de corte. Meio com permissividade 1, padrão da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_cerca(texto):
    if not combina(texto, [("alambrado",)]):
        return None
    return ler(texto, [
        C("perimetro", ["perimetro"], "num", True),
        C("espacamento", ["espacamento"], "num", True),
    ])


def _calcular_cerca(params):
    def fazer():
        mod = carregar("cerca-alambrado", "cer_core")
        r = mod.mourões(params["perimetro"], params["espacamento"])
        return pacote(
            str(r["mourões"]) + " mourões",
            "Cerca fechada, padrão da ferramenta. Sem preço de material.",
        )
    return _chamar(fazer)


def _extrair_srpe(texto):
    if not combina(texto, [("carga srpe",)]):
        return None
    return ler(texto, [
        C("rpe", ["rpe"], "num", True),
        C("minutos", ["minutos"], "num", True),
    ])


def _calcular_srpe(params):
    def fazer():
        mod = carregar("indice-carga-treino", "ict_core")
        carga = mod.session_load(params["rpe"], params["minutos"])
        return pacote(_num(carga, 0) + " AU", "sRPE = RPE vezes os minutos.")
    return _chamar(fazer)


def _extrair_internet(texto):
    if not combina(texto, [("internet da casa",)]):
        return None
    return ler(texto, [C("jogos", ["jogos"], "int", True)])


def _calcular_internet(params):
    def fazer():
        mod = carregar("internet-ideal-casa", "mbp_core")
        r = mod.recomendar({"Jogo online": params["jogos"]})
        return pacote(
            str(r["plano"]) + " Mbps",
            "Só jogo online, ao mesmo tempo. Folga de 50%, padrão da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_assinaturas(texto):
    if not combina(texto, [("soma de assinaturas",)]):
        return None
    corpo = _depois(texto, "assinaturas")
    if not corpo or ";" not in corpo:
        return None
    return {"corpo": corpo}


def _calcular_assinaturas(params):
    def fazer():
        mod = carregar("controle-assinaturas", "ass_core")
        r = mod.totalizar(mod.parse_linhas(params["corpo"]))
        return pacote("R$ " + _num(r["mensal"]), "Equivalente mensal.")
    return _chamar(fazer)


def _extrair_contas(texto):
    if not combina(texto, [("contas fixas",)]):
        return None
    corpo = _depois(texto, "contas fixas")
    if not corpo or ";" not in corpo:
        return None
    return {"corpo": corpo}


def _calcular_contas(params):
    def fazer():
        mod = carregar("controle-contas-fixas", "cfx_core")
        r = mod.totalizar(mod.parse_linhas(params["corpo"]), HOJE_AUDIO)
        return pacote(
            "R$ " + _num(r["total"]),
            "Soma mensal. Vencimentos contados a partir de " + _fmt_data(HOJE_AUDIO) + ".",
        )
    return _chamar(fazer)


_registrar("metronomo", ["andamento"], _extrair_andamento, _calcular_andamento)
_registrar("teoria-musical", ["frequencia da nota"], _extrair_freq_nota, _calcular_freq_nota)
_registrar("teoria-musical", ["nota da frequencia"], _extrair_nota_freq, _calcular_nota_freq)
_registrar("teoria-musical", ["escala maior", "escala menor", "escala blues"], _extrair_escala, _calcular_escala)
_registrar("teoria-musical", ["acorde maior", "acorde menor"], _extrair_acorde, _calcular_acorde)
_registrar("teoria-musical", ["intervalo de"], _extrair_intervalo, _calcular_intervalo)
_registrar("teoria-musical", ["transpor acorde"], _extrair_transpor, _calcular_transpor)
_registrar("calculadora-datas", ["pascoa"], _extrair_pascoa, _calcular_pascoa)
_registrar("calculadora-datas", ["datas uteis"], _extrair_uteis, _calcular_uteis)
_registrar("calculadora-datas", ["idade exata"], _extrair_idade, _calcular_idade)
_registrar("calculadora-datas", ["somar dias na data"], _extrair_somar, _calcular_somar)
_registrar("calculadora-datas", ["semana iso"], _extrair_iso, _calcular_iso)
_registrar("simulador-modulacao-am-fm", ["modulacao am"], _extrair_am, _calcular_am)
_registrar("simulador-modulacao-am-fm", ["modulacao fm"], _extrair_fm, _calcular_fm)
_registrar("calculadora-guia-ondas-retangular", ["guia retangular"], _extrair_guia, _calcular_guia)
_registrar("cerca-alambrado", ["alambrado"], _extrair_cerca, _calcular_cerca)
_registrar("indice-carga-treino", ["carga srpe"], _extrair_srpe, _calcular_srpe)
_registrar("internet-ideal-casa", ["internet da casa"], _extrair_internet, _calcular_internet)
_registrar("controle-assinaturas", ["soma de assinaturas"], _extrair_assinaturas, _calcular_assinaturas)
_registrar("controle-contas-fixas", ["contas fixas"], _extrair_contas, _calcular_contas)
