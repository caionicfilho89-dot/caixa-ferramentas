# -*- coding: utf-8 -*-
"""Adaptadores da barra para Texto & Estudo e o que caiu nessa categoria.

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

# Prazos de leitura nao podem depender do relogio do teste.
HOJE_TEXTO = datetime.date(2026, 11, 9)

_RE_OCTAL = re.compile(r"\b([0-7]{3,4})\b")
_RE_SIMB = re.compile(r"[r-][w-][xsS-][r-][w-][xsS-][r-][w-][xtT-]")


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
    return texto[i + len(norm(marca)):].strip(" \n")


def _chamar(fn):
    try:
        return fn()
    except ValueError as e:
        return pacote(str(e).splitlines()[0], "A ferramenta recusou esses dados.")


def _fmt_data(d):
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def _duas_palavras(texto, marca):
    corpo = _depois(texto, marca)
    if not corpo:
        return None
    partes = corpo.split()
    if len(partes) < 2:
        return None
    return partes[0], partes[1]


def _extrair_flesch(texto):
    if not combina(texto, [("legibilidade flesch",)]):
        return None
    corpo = _depois(texto, "flesch")
    if not corpo:
        return None
    return {"corpo": corpo}


def _calcular_flesch(params):
    def fazer():
        mod = carregar("analisador-texto", "at_core")
        stats = mod.text_stats(params["corpo"])
        nota = stats["flesch"]
        if nota is None:
            return pacote("sem texto", "Flesch precisa de palavras e de uma frase.")
        faixa = stats["faixa"][0]
        return pacote(_num(nota, 1), "Flesch em português. Faixa: " + faixa + ".")
    return _chamar(fazer)


def _extrair_soundex(texto):
    if not combina(texto, [("soundex",)]):
        return None
    corpo = _depois(texto, "soundex")
    if not corpo:
        return None
    return {"nome": corpo}


def _calcular_soundex(params):
    def fazer():
        mod = carregar("codificador-fonetico", "phn_core")
        return pacote(mod.soundex(params["nome"]), "Soundex americano de 4 caracteres.")
    return _chamar(fazer)


def _extrair_metaphone(texto):
    if not combina(texto, [("metaphone",)]):
        return None
    corpo = _depois(texto, "metaphone")
    if not corpo:
        return None
    return {"nome": corpo}


def _calcular_metaphone(params):
    def fazer():
        mod = carregar("codificador-fonetico", "phn_core")
        return pacote(mod.metaphone(params["nome"]), "Metaphone simplificado da ferramenta.")
    return _chamar(fazer)


def _extrair_lev(texto):
    if not combina(texto, [("levenshtein",)]):
        return None
    par = _duas_palavras(texto, "levenshtein")
    if not par:
        return None
    return {"a": par[0], "b": par[1]}


def _calcular_lev(params):
    def fazer():
        mod = carregar("codificador-fonetico", "phn_core")
        return pacote(str(mod.levenshtein(params["a"], params["b"])), "Distância de edição.")
    return _chamar(fazer)


def _extrair_sim(texto):
    if not combina(texto, [("similaridade de",)]):
        return None
    # "de" tambem e o fim de "similaridade"; o corte tem que ser a frase inteira.
    par = _duas_palavras(texto, "similaridade de")
    if not par:
        return None
    return {"a": par[0], "b": par[1]}


def _calcular_sim(params):
    def fazer():
        mod = carregar("codificador-fonetico", "phn_core")
        return pacote(_num(mod.similarity_ratio(params["a"], params["b"]), 2), "1 menos a distância relativa.")
    return _chamar(fazer)


def _extrair_chmod(texto):
    if not combina(texto, [("chmod",)]):
        return None
    octal = _RE_OCTAL.search(texto)
    if octal:
        return {"tipo": "octal", "valor": octal.group(1)}
    simb = _RE_SIMB.search(texto)
    if simb:
        return {"tipo": "simbolico", "valor": simb.group(0)}
    return None


def _calcular_chmod(params):
    def fazer():
        mod = carregar("calculadora-chmod", "rwx_core")
        if params["tipo"] == "octal":
            return pacote(mod.to_symbolic(mod.parse_octal(params["valor"])), "Modo simbólico.")
        return pacote(mod.to_octal(mod.parse_symbolic(params["valor"])), "Modo octal.")
    return _chamar(fazer)


def _extrair_eol(texto):
    if not combina(texto, [("finais de linha",)]):
        return None
    corpo = _depois(texto, "finais de linha")
    if corpo is None:
        return None
    return {"corpo": corpo}


def _calcular_eol(params):
    def fazer():
        mod = carregar("conversor-finais-linha", "eol_core")
        return pacote(mod.analyze_text(params["corpo"]).style, "Estilo das quebras encontradas.")
    return _chamar(fazer)


def _extrair_indent(texto):
    if not combina(texto, [("indentar com espacos",)]):
        return None
    corpo = _depois(texto, "espacos")
    if not corpo:
        return None
    return {"corpo": corpo}


def _pacote_cru(resposta, detalhe):
    # pacote() faz strip e apaga a indentacao, que e a propria resposta.
    return {"resposta": str(resposta), "detalhe": str(detalhe).strip()}


def _calcular_indent(params):
    def fazer():
        mod = carregar("conversor-indentacao", "ind_core")
        convertido = mod.tabs_to_spaces(params["corpo"])
        return _pacote_cru(convertido, "Tab vira 4 espaços, padrão da ferramenta.")
    return _chamar(fazer)


def _extrair_diff(texto):
    if not combina(texto, [("comparar textos",)]):
        return None
    corpo = _depois(texto, "textos")
    if not corpo or "|" not in corpo:
        return None
    a, b = corpo.split("|", 1)
    if not a.strip() or not b.strip():
        return None
    return {"a": a.strip(), "b": b.strip()}


def _calcular_diff(params):
    def fazer():
        mod = carregar("diff-texto", "tdf_core")
        return pacote(_num(mod.ratio(params["a"], params["b"]), 2), "Semelhança de 0 a 1.")
    return _chamar(fazer)


def _extrair_sm2(texto):
    if not combina(texto, [("sm2",)]):
        return None
    return ler(texto, [C("nota", ["nota"], "int", True)])


def _calcular_sm2(params):
    def fazer():
        mod = carregar("flashcards", "fc_core")
        _ease, intervalo, _reps = mod.sm2(2.5, 0, 0, params["nota"])
        return pacote(
            str(intervalo) + " dias",
            "Cartão novo: facilidade 2,5, intervalo 0 e 0 repetições, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_meta_anual(texto):
    if not combina(texto, [("meta anual de leitura",)]):
        return None
    return ler(texto, [C("restantes", ["restantes"], "num", True)])


def _calcular_meta_anual(params):
    def fazer():
        mod = carregar("meta-leitura", "lei_core")
        ritmo = mod.paginas_por_dia(params["restantes"], HOJE_TEXTO)
        return pacote(
            _num(ritmo, 2) + " pag/dia",
            "Até 31/12, contado a partir de " + _fmt_data(HOJE_TEXTO) + ".",
        )
    return _chamar(fazer)


def _extrair_previsao(texto):
    if not combina(texto, [("previsao de leitura",)]):
        return None
    return ler(texto, [
        C("restantes", ["restantes"], "num", True),
        C("ritmo", ["ritmo"], "num", True),
    ])


def _calcular_previsao(params):
    def fazer():
        mod = carregar("meta-leitura", "lei_core")
        fim = mod.previsao_termino(params["restantes"], params["ritmo"], HOJE_TEXTO)
        if fim is None:
            return pacote("sem previsão", "O ritmo precisa ser maior que zero.")
        return pacote(_fmt_data(fim), "Ritmo em páginas por dia, a partir de " + _fmt_data(HOJE_TEXTO) + ".")
    return _chamar(fazer)


def _extrair_ritmo_pag(texto):
    if not combina(texto, [("ritmo de paginas",)]):
        return None
    return ler(texto, [
        C("lidas", ["lidas"], "num", True),
        C("dias", ["dias"], "num", True),
    ])


def _calcular_ritmo_pag(params):
    def fazer():
        mod = carregar("meta-leitura", "lei_core")
        return pacote(
            _num(mod.ritmo_atual(params["lidas"], params["dias"]), 2) + " pag/dia",
            "Páginas lidas divididas pelos dias.",
        )
    return _chamar(fazer)


def _extrair_semana(texto):
    if not combina(texto, [("leitura semanal",)]):
        return None
    return ler(texto, [
        C("livro", ["livro"], "int", True),
        C("lidas", ["lidas"], "int", True),
        C("dias", ["dias"], "int", True),
        C("minutos", ["minutos"], "num", True),
        C("ritmo", ["ritmo"], "num", True),
    ])


def _calcular_semana(params):
    def fazer():
        mod = carregar("planejador-leituras-semanais", "pls_core")
        plano = mod.planejar_semana(
            params["livro"], params["lidas"], params["dias"], params["minutos"],
            paginas_por_hora=params["ritmo"], hoje=HOJE_TEXTO,
        )
        return pacote(
            _num(plano.paginas_por_dia_necessarias, 2) + " pag/dia",
            "Ritmo da frase em páginas por hora. Data de " + _fmt_data(HOJE_TEXTO) + ".",
        )
    return _chamar(fazer)


def _extrair_meta_dia(texto):
    if not combina(texto, [("meta de paginas",)]):
        return None
    return ler(texto, [
        C("total", ["total"], "int", True),
        C("lidas", ["lidas"], "int", True),
        C("minutos", ["minutos"], "num", True),
        C("ritmo", ["ritmo"], "num", True),
        C("prazo", ["prazo"], "int", True),
    ])


def _calcular_meta_dia(params):
    def fazer():
        mod = carregar("meta-paginas-leitura-dia", "pag_core")
        plano = mod.calcular_meta(
            params["total"], params["lidas"], params["minutos"], params["ritmo"],
            prazo_dias=params["prazo"], hoje=HOJE_TEXTO,
        )
        return pacote(
            _num(plano.paginas_por_dia_necessarias, 2) + " pag/dia",
            "Prazo em dias a partir de " + _fmt_data(HOJE_TEXTO) + ". Ritmo em páginas por hora.",
        )
    return _chamar(fazer)


def _extrair_vocab(texto):
    if not combina(texto, [("vocabulario",)]):
        return None
    return ler(texto, [
        C("meta", ["meta"], "int", True),
        C("aprendidas", ["aprendidas"], "int", True),
        C("dias", ["dias"], "int", True),
        C("minutos", ["minutos"], "num", True),
        C("ppm", ["ppm"], "num", True),
    ])


def _calcular_vocab(params):
    def fazer():
        mod = carregar("meta-vocabulario-idioma", "mvi_core")
        plano = mod.planejar_vocabulario(
            params["meta"], params["aprendidas"], params["dias"], params["minutos"],
            palavras_por_minuto=params["ppm"],
        )
        return pacote(
            _num(plano.palavras_por_dia_necessarias, 2) + " palavras/dia",
            "PPM é palavras por minuto, da frase.",
        )
    return _chamar(fazer)


def _extrair_flash(texto):
    if not combina(texto, [("revisao flash",)]):
        return None
    return ler(texto, [
        C("minutos", ["minutos"], "num", True),
        C("minimo", ["minimo"], "num", True),
    ])


def _calcular_flash(params):
    def fazer():
        mod = carregar("planejador-revisao-flash-rapida", "frp_core")
        n = mod.capacidade_topicos(params["minutos"], params["minimo"])
        return pacote(str(n) + " tópicos", "Quantos blocos cabem no mínimo de minutos.")
    return _chamar(fazer)


def _extrair_ppm(texto):
    if not combina(texto, [("ritmo de leitura",)]):
        return None
    return ler(texto, [
        C("palavras", ["palavras"], "int", True),
        C("segundos", ["segundos"], "int", True),
    ])


def _calcular_ppm(params):
    def fazer():
        mod = carregar("analisador-ritmo-leitura-compreensao", "rtc_core")
        r = mod.calcular_ritmo_leitura(params["palavras"], params["segundos"])
        return pacote(
            _num(r["ppm_bruto"], 1) + " ppm",
            "Compreensão 80%, livro de 250 páginas e 280 palavras por página, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_idioma(texto):
    if not combina(texto, [("curso de idioma",)]):
        return None
    return ler(texto, [
        C("mensalidade", ["mensalidade"], "num", True),
        C("meses", ["meses"], "int", True),
    ])


def _calcular_idioma(params):
    def fazer():
        mod = carregar("custo-curso-idioma", "idi_core")
        r = mod.calcular(params["mensalidade"], params["meses"])
        return pacote(
            "R$ " + _num(r["total"]),
            "Material, matrícula e exame em 0. Duas aulas por semana, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_pressao(texto):
    if not combina(texto, [("pressao arterial",)]):
        return None
    return ler(texto, [
        C("sistolica", ["sistolica"], "int", True),
        C("diastolica", ["diastolica"], "int", True),
    ])


def _calcular_pressao(params):
    def fazer():
        mod = carregar("controle-pressao-arterial", "pas_core")
        r = mod.classificar(params["sistolica"], params["diastolica"])
        return pacote(r.categoria, "Faixa da ferramenta. Não é diagnóstico.")
    return _chamar(fazer)


_registrar("analisador-texto", ["legibilidade flesch"], _extrair_flesch, _calcular_flesch)
_registrar("codificador-fonetico", ["soundex"], _extrair_soundex, _calcular_soundex)
_registrar("codificador-fonetico", ["metaphone"], _extrair_metaphone, _calcular_metaphone)
_registrar("codificador-fonetico", ["levenshtein"], _extrair_lev, _calcular_lev)
_registrar("codificador-fonetico", ["similaridade de"], _extrair_sim, _calcular_sim)
_registrar("calculadora-chmod", ["chmod"], _extrair_chmod, _calcular_chmod)
_registrar("conversor-finais-linha", ["finais de linha"], _extrair_eol, _calcular_eol)
_registrar("conversor-indentacao", ["indentar com espacos"], _extrair_indent, _calcular_indent)
_registrar("diff-texto", ["comparar textos"], _extrair_diff, _calcular_diff)
_registrar("flashcards", ["sm2"], _extrair_sm2, _calcular_sm2)
_registrar("meta-leitura", ["meta anual de leitura"], _extrair_meta_anual, _calcular_meta_anual)
_registrar("meta-leitura", ["previsao de leitura"], _extrair_previsao, _calcular_previsao)
_registrar("meta-leitura", ["ritmo de paginas"], _extrair_ritmo_pag, _calcular_ritmo_pag)
_registrar("planejador-leituras-semanais", ["leitura semanal"], _extrair_semana, _calcular_semana)
_registrar("meta-paginas-leitura-dia", ["meta de paginas"], _extrair_meta_dia, _calcular_meta_dia)
_registrar("meta-vocabulario-idioma", ["vocabulario"], _extrair_vocab, _calcular_vocab)
_registrar("planejador-revisao-flash-rapida", ["revisao flash"], _extrair_flash, _calcular_flash)
_registrar("analisador-ritmo-leitura-compreensao", ["ritmo de leitura"], _extrair_ppm, _calcular_ppm)
_registrar("custo-curso-idioma", ["curso de idioma"], _extrair_idioma, _calcular_idioma)
_registrar("controle-pressao-arterial", ["pressao arterial"], _extrair_pressao, _calcular_pressao)
