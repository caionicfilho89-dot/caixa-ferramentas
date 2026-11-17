# -*- coding: utf-8 -*-
"""Adaptadores da barra para Casa, Pet e Pessoal.

Cada calcular chama a função do _core da ferramenta. Não refaz a conta.
Diário, checklist e inspetor de arquivo ficam de fora: não respondem uma frase.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import date

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

import adp_financas as af

norm = af.norm
tokens = af.tokens
combina = af.combina
ler = af.ler
C = af.C
carregar = af.carregar
mostrar = af.mostrar
pacote = af.pacote
_num = af._num
_brl = af._brl

ADAPTADORES = []


def _registrar(chave, palavras, extrair, calcular):
    ADAPTADORES.append({
        "chave": chave,
        "palavras": list(palavras),
        "extrair": extrair,
        "calcular": calcular,
    })


def _data(texto):
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", norm(texto))
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def _relogio(texto):
    t = norm(texto)
    m = re.search(r"\b(\d{1,2})\s*:\s*(\d{2})\b", t)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
    else:
        m = re.search(r"\b(\d{1,2})\s*h(?:\s*(\d{2}))?\b", t)
        if not m:
            return None
        h = int(m.group(1))
        mi = int(m.group(2) or 0)
    if not (0 <= h <= 23 and 0 <= mi <= 59):
        return None
    return f"{h:02d}:{mi:02d}"


def _altura_m(valor, texto):
    t = norm(texto)
    if "cm" in t or valor > 3:
        return valor / 100.0, "li como centímetros"
    return valor, "li como metros"


def _especie(texto):
    t = norm(texto)
    if any(p in t for p in ("gato", "gata")):
        return "gato"
    if any(p in t for p in ("cachorro", "cadela", " cao", "cao ")):
        return "cao"
    if t.startswith("cao") or " cao" in t:
        return "cao"
    return None


def _chamar(pasta, modulo, funcao, kwargs, titulo, destaque=None, moeda=True, nota=""):
    mod = carregar(pasta, modulo)
    try:
        r = getattr(mod, funcao)(**kwargs)
    except ValueError as e:
        return pacote(str(e), str(e))
    saida = mostrar(mod, r, titulo, destaque, moeda)
    if nota:
        saida["detalhe"] = (saida["detalhe"] + "\n" + nota).strip()
    return saida


def _ligar(chave, palavras, grupos, evitar, extrair_params, pasta, modulo, funcao, titulo, destaque=None, moeda=True, nota=""):
    def extrair(texto):
        if not combina(texto, grupos, evitar):
            return None
        return extrair_params(texto)

    def calcular(params):
        return _chamar(pasta, modulo, funcao, params, titulo, destaque, moeda, nota)

    _registrar(chave, palavras, extrair, calcular)


# ---------------------------------------------------------------- saúde
def _extrair_imc(texto):
    if not combina(texto, [["imc"]], ["cachorro", "gato", "racao"]):
        return None
    p = ler(texto, [
        C("peso", ["peso", "kg"], "num", True, solto=True),
        C("altura", ["altura", "cm"], "num", True, solto=True),
    ])
    if not p:
        return None
    p["_texto"] = texto
    return p


def _calcular_imc(params):
    texto = params.pop("_texto")
    altura, como = _altura_m(params["altura"], texto)
    mod = carregar("saude", "sd_core")
    try:
        valor = mod.imc(params["peso"], altura)
    except ValueError as e:
        return pacote(str(e), str(e))
    classe = mod.imc_classe(valor)
    resp = f"IMC: {_num(valor)} ({classe})"
    det = f"Peso { _num(params['peso']) } kg, altura {_num(altura, 2)} m ({como}).\n{resp}"
    return pacote(resp, det)


_registrar("saude", ["imc", "peso", "altura"], _extrair_imc, _calcular_imc)


def _extrair_agua_pessoa(texto):
    if not combina(texto, [["beber", "hidratar"]], ["cachorro", "gato", "cadela", "racao", "pet", " cao"]):
        return None
    if "agua" not in norm(texto):
        return None
    p = ler(texto, [C("peso", ["peso", "kg", "pesando"], "num", True, solto=True)])
    return p


def _calcular_agua_pessoa(params):
    mod = carregar("saude", "sd_core")
    try:
        ml = mod.agua_ml(params["peso"])
    except ValueError as e:
        return pacote(str(e), str(e))
    copos = mod.agua_copos(ml)
    resp = f"Água: {ml} ml ({copos} copos)"
    det = resp + "\nSem exercício e sem calor. A ferramenta soma 500 ml por hora de exercício e mais 500 ml no calor."
    return pacote(resp, det)


_registrar("saude", ["agua", "beber"], _extrair_agua_pessoa, _calcular_agua_pessoa)


# ---------------------------------------------------------------- pet
def _extrair_agua_pet(texto):
    if not combina(texto, [["agua"]], ["beber", "hidratar"]):
        return None
    esp = _especie(texto)
    if not esp:
        return None
    p = ler(texto, [C("peso", ["peso", "kg"], "num", True, solto=True)])
    if not p:
        return None
    p["especie"] = esp
    return p


def _calcular_agua_pet(params):
    mod = carregar("pet", "pet_core")
    try:
        ml = mod.agua_dia_ml(params["peso"], params["especie"])
    except ValueError as e:
        return pacote(str(e), str(e))
    nome = "cão" if params["especie"] == "cao" else "gato"
    resp = f"Água do {nome}: {_num(ml, 0)} ml por dia"
    return pacote(resp, resp + "\nEstimativa da ferramenta (cerca de 60 ml/kg no cão e 50 ml/kg no gato).")


_registrar("pet", ["agua", "cachorro", "gato"], _extrair_agua_pet, _calcular_agua_pet)


def _fase_pet(texto, especie):
    t = norm(texto)
    if especie == "gato" and "filhote" in t:
        return "Filhote (0-12 meses)"
    if "filhote" in t:
        return "Filhote (0-4 meses)"
    if "idoso" in t or "senior" in t:
        return "Idoso/senior"
    if "inteiro" in t:
        return "Adulto inteiro"
    return "Adulto castrado"


def _extrair_racao(texto):
    if not combina(texto, [["racao"]], ["idade humana", "anos humanos"]):
        return None
    esp = _especie(texto)
    if not esp:
        return None
    p = ler(texto, [
        C("kcal", ["kcal", "caloria"], "num", False),
        C("peso", ["peso", "kg"], "num", True, solto=True),
    ])
    if not p:
        return None
    p["especie"] = esp
    p["fase"] = _fase_pet(texto, esp)
    return p


def _calcular_racao(params):
    mod = carregar("pet", "pet_core")
    fase = params["fase"]
    try:
        energia = mod.mer(params["peso"], mod.FATORES[params["especie"]][fase])
    except (ValueError, KeyError) as e:
        return pacote(str(e), str(e))
    if "kcal" not in params:
        resp = f"Energia: {_num(energia, 0)} kcal/dia"
        det = resp + f"\nFase usada: {fase}. Sem a kcal/kg do pacote não dá pra dizer as gramas."
        return pacote(resp, det)
    try:
        plano = mod.plano(params["peso"], params["especie"], fase, params["kcal"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Ração: {_num(plano['gramas_dia'], 0)} g/dia"
    det = (
        f"{resp} ({_num(plano['por_refeicao'], 0)} g em cada uma das {plano['refeicoes']} refeições).\n"
        f"Fase usada: {fase}. Pacote: {_num(params['kcal'], 0)} kcal/kg."
    )
    return pacote(resp, det)


_registrar("pet", ["racao", "cachorro", "gato"], _extrair_racao, _calcular_racao)


def _extrair_idade_pet(texto):
    if not combina(texto, [["idade humana", "anos humanos"]]):
        return None
    esp = _especie(texto) or "cao"
    p = ler(texto, [C("anos", ["anos", "ano"], "ano", True, solto=True)])
    if not p:
        return None
    t = norm(texto)
    porte = "grande" if "grande" in t else ("pequeno" if "pequeno" in t else "medio")
    p["especie"] = esp
    p["porte"] = porte
    return p


def _calcular_idade_pet(params):
    mod = carregar("pet", "pet_core")
    try:
        anos = mod.idade_humana(params["anos"], params["especie"], params["porte"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Idade humana: {_num(anos, 1)} anos"
    det = resp + f"\nPorte {params['porte']} (médio se não disse outro)."
    return pacote(resp, det)


_registrar("pet", ["idade humana", "anos humanos"], _extrair_idade_pet, _calcular_idade_pet)


# ---------------------------------------------------------------- cabelo
def _vols(texto):
    t = norm(texto)
    toks = tokens(texto)
    achados = []
    ini = 0
    while True:
        i = t.find("volume", ini)
        if i < 0:
            break
        fim = i + len("volume")
        antes = [tok for tok in toks if tok.fim <= i and i - tok.fim <= 8]
        if antes:
            achados.append(max(antes, key=lambda tok: tok.fim).valor)
        ini = fim
    return achados


def _extrair_volumes(texto):
    if not combina(texto, [["volume"]], ["diluir", "diluicao"]):
        return None
    vols = _vols(texto)
    if len(vols) != 1:
        return None
    return {"vol": vols[0]}


def _calcular_volumes(params):
    mod = carregar("cabelo", "cab_core")
    try:
        pct = mod.volumes_para_pct(params["vol"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"{_num(params['vol'], 0)} volumes = {_num(pct)}% de água oxigenada"
    return pacote(resp, resp)


_registrar("cabelo", ["volumes", "oxigenada"], _extrair_volumes, _calcular_volumes)


def _extrair_diluir(texto):
    if not combina(texto, [["diluir", "diluicao"]], []):
        return None
    vols = _vols(texto)
    ml = ler(texto, [C("ml", ["ml", "mililitro"], "num", True, solto=True)])
    if len(vols) < 2 or not ml:
        return None
    return {"vol_tem": vols[0], "vol_quer": vols[1], "qtd_final_ml": ml["ml"]}


def _calcular_diluir(params):
    return _chamar(
        "cabelo", "cab_core", "diluir_oxigenada", params,
        "Oxigenada na mistura", "oxigenada_ml", False,
    )


_registrar("cabelo", ["diluir", "oxigenada"], _extrair_diluir, _calcular_diluir)


# ---------------------------------------------------------------- cozinha e bebida
def _extrair_cafe(texto):
    if not combina(
        texto,
        [["cafe"], ["v60", "coado", "prensa", "aeropress", "espresso", "moka", "chemex", "clever", "proporcao", "gramas"]],
        ["cafeina", "cafeteria", "xicara"],
    ):
        return None
    p = ler(texto, [
        C("proporcao", ["proporcao", "razao"], "num", False),
        C("gramas", ["gramas", "g de", "po"], "num", True, solto=True),
    ])
    if not p:
        return None
    mod = carregar("calculadora-cafe", "cfe_core")
    t = norm(texto)
    origem = ""
    if "proporcao" not in p:
        aliases = (
            ("v60", "Coado"), ("coado", "Coado"), ("melitta", "Coado"),
            ("prensa", "Prensa"), ("aeropress", "AeroPress"), ("espresso", "Espresso"),
            ("moka", "Moka"), ("italiana", "Moka"), ("cold", "Cold"),
            ("chemex", "Chemex"), ("clever", "Clever"),
        )
        for ali, prefixo in aliases:
            if ali in t:
                for nome, dados in mod.METODOS.items():
                    if norm(nome).startswith(norm(prefixo)):
                        p["proporcao"] = dados[0]
                        origem = nome
                        break
            if origem:
                break
    if "proporcao" not in p:
        return None
    p["_origem"] = origem
    return p


def _calcular_cafe(params):
    origem = params.pop("_origem", "")
    mod = carregar("calculadora-cafe", "cfe_core")
    try:
        agua = mod.agua_para_cafe(params["gramas"], params["proporcao"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Água: {_num(agua, 0)} ml para {_num(params['gramas'], 0)} g de café"
    det = resp + f"\nProporção {_num(params['proporcao'], 1)}:1."
    if origem:
        det += f" Veio do método {origem} da ferramenta."
    return pacote(resp, det)


_registrar("calculadora-cafe", ["cafe", "v60", "coado"], _extrair_cafe, _calcular_cafe)


def _extrair_xicara(texto):
    if not combina(texto, [["xicara", "colher de sopa", "colher de cha", "copo americano"]]):
        return None
    mod = carregar("medidas-de-cozinha", "mcl_core")
    t = norm(texto)
    unidade = None
    for nome in sorted(mod.UNIDADES_ML, key=lambda s: len(s), reverse=True):
        if norm(nome) in t:
            unidade = nome
            break
    ing = None
    melhor = 0
    for nome in mod.G_POR_XICARA:
        n = norm(nome)
        if n in t and len(n) > melhor:
            ing, melhor = nome, len(n)
    if ing is None:
        for nome in mod.G_POR_XICARA:
            primeiro = norm(nome).split()[0]
            if re.search(r"(?<!\w)" + re.escape(primeiro) + r"(?!\w)", t):
                if ing and ing != nome:
                    return None
                ing = nome
    if not unidade or not ing:
        return None
    p = ler(texto, [C("qtd", ["xicara", "colher", "copo"], "num", True, solto=True)])
    if not p:
        return None
    p["unidade"] = unidade
    p["ingrediente"] = ing
    return p


def _calcular_xicara(params):
    mod = carregar("medidas-de-cozinha", "mcl_core")
    try:
        r = mod.converter(params["qtd"], params["unidade"], params["ingrediente"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"{_num(params['qtd'], 1)} {params['unidade']} de {params['ingrediente']} = {_num(r['gramas'], 1)} g"
    return pacote(resp, resp + f"\n{_num(r['ml'], 1)} ml.")


_registrar("medidas-de-cozinha", ["xicara", "farinha", "colher"], _extrair_xicara, _calcular_xicara)


def _extrair_pao(texto):
    if not combina(texto, [["pao"], ["farinha"]]):
        return None
    return ler(texto, [
        C("hidratacao", ["hidratacao"], "pct", True),
        C("sal", ["sal"], "pct", True),
        C("farinha", ["farinha"], "num", True, solto=True),
    ])


def _calcular_pao(params):
    mod = carregar("calculadora-pao", "pao_core")
    try:
        r = mod.massa(params["farinha"], params["hidratacao"], params["sal"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Água do pão: {_num(r['Água'], 0)} g"
    det = resp + "\nFermento, açúcar e gordura ficaram 0 porque não foram ditos."
    for k, v in r.items():
        det += f"\n{k}: {_num(v, 1)} g"
    return pacote(resp, det)


_registrar("calculadora-pao", ["pao", "farinha", "hidratacao"], _extrair_pao, _calcular_pao)


def _extrair_pizza(texto):
    if not combina(texto, [["pizza"]], ["junina", "infantil", "aniversario"]):
        return None
    return ler(texto, [C("pessoas", ["pessoas", "pessoa"], "int", True, solto=True)])


def _calcular_pizza(params):
    mod = carregar("calculadora-pizza", "pzz_core")
    try:
        n = mod.pizzas_para_pessoas(params["pessoas"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Pizzas: {n}"
    return pacote(resp, resp + "\nFome normal e 8 fatias, padrão da ferramenta.")


_registrar("calculadora-pizza", ["pizza", "pessoas"], _extrair_pizza, _calcular_pizza)


def _extrair_abv(texto):
    if not combina(texto, [["og"], ["fg"]]):
        return None
    return ler(texto, [
        C("og", ["og"], "num", True),
        C("fg", ["fg"], "num", True),
    ])


def _calcular_abv(params):
    mod = carregar("calculadora-cerveja", "brw_core")
    try:
        teor = mod.abv(params["og"], params["fg"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"ABV: {_num(teor)}%"
    return pacote(resp, resp)


_registrar("calculadora-cerveja", ["abv", "og", "fg"], _extrair_abv, _calcular_abv)


def _extrair_chucrute(texto):
    if not combina(texto, [["chucrute"]]):
        return None
    return ler(texto, [
        C("sal", ["sal"], "pct", False, 2.0),
        C("repolho", ["repolho", "g"], "num", True, solto=True),
    ])


def _calcular_chucrute(params):
    return _chamar(
        "fermentados-caseiros", "kmb_core", "chucrute",
        {"repolho_g": params["repolho"], "sal_pct": params["sal"]},
        "Sal do chucrute", "sal_g", False,
        "Sal 2% se você não disse outro. A ferramenta usa 14 dias.",
    )


_registrar("fermentados-caseiros", ["chucrute", "repolho"], _extrair_chucrute, _calcular_chucrute)


def _extrair_quentao(texto):
    if not combina(texto, [["quentao"]]):
        return None
    return ler(texto, [C("litros", ["litro", "litros"], "num", True, solto=True)])


def _calcular_quentao(params):
    mod = carregar("festa-junina", "jun_core")
    try:
        r = mod.receita_quentao(params["litros"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Cachaça: {_num(r['cachaça_ml'], 0)} ml"
    det = "\n".join(f"{k}: {v}" for k, v in r.items())
    return pacote(resp, resp + "\n" + det)


_registrar("festa-junina", ["quentao"], _extrair_quentao, _calcular_quentao)


# ---------------------------------------------------------------- casa e festa
def _extrair_aquario(texto):
    if not combina(texto, [["aquario"]]):
        return None
    nums = [tok.valor for tok in tokens(texto) if tok.tipo in ("solto", "din")]
    if len(nums) < 3:
        return None
    return {"c": nums[0], "l": nums[1], "a": nums[2]}


def _calcular_aquario(params):
    mod = carregar("calculadora-aquario", "aqu_core")
    try:
        bruto = mod.volume_retangular(params["c"], params["l"], params["a"])
        real = mod.volume_real(bruto)
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Aquário: {_num(bruto, 1)} L brutos"
    det = resp + f"\nVolume útil {_num(real, 1)} L (fator da ferramenta)."
    return pacote(resp, det)


_registrar("calculadora-aquario", ["aquario", "litros"], _extrair_aquario, _calcular_aquario)


def _extrair_botijao(texto):
    if not combina(texto, [["botijao", "p13", "p45"]]):
        return None
    p = ler(texto, [C("kg", ["kg", "quilo"], "num", True)])
    if not p:
        return None
    p["tipo"] = "P45" if "p45" in norm(texto) else "P13"
    return p


def _calcular_botijao(params):
    mod = carregar("botijao-gas", "gas_core")
    try:
        dias = mod.dias_duracao(params["tipo"], params["kg"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Botijão {params['tipo']}: {_num(dias, 1)} dias"
    return pacote(resp, resp)


_registrar("botijao-gas", ["botijao", "p13", "p45"], _extrair_botijao, _calcular_botijao)


def _extrair_tv(texto):
    if not combina(texto, [["tv", "televisao", "televisor"]]):
        return None
    return ler(texto, [C("distancia", ["metro", "metros", "distancia"], "num", True, solto=True)])


def _calcular_tv(params):
    mod = carregar("tamanho-tv", "tvd_core")
    try:
        r = mod.sugerir(params["distancia"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"TV (SMPTE): {_num(r['SMPTE_pol'], 0)} polegadas"
    det = resp + f"\nTHX {_num(r['THX_pol'], 0)} pol. Acuidade 4K {_num(r['acuidade_pol'], 0)} pol. Resolução 4K é o padrão da ferramenta."
    return pacote(resp, det)


_registrar("tamanho-tv", ["tv", "televisao", "polegadas"], _extrair_tv, _calcular_tv)


def _extrair_festa(texto):
    if not combina(texto, [["aniversario", "coquetel", "casamento", "churrasco"]], ["junina", "infantil", "pizza"]):
        return None
    p = ler(texto, [
        C("criancas", ["criancas", "crianca"], "int", False, 0),
        C("adultos", ["adultos", "adulto"], "int", True, solto=True),
    ])
    if not p:
        return None
    t = norm(texto)
    if "churrasco" in t:
        tipo = "Churrasco"
    elif "casamento" in t:
        tipo = "Casamento"
    elif "coquetel" in t:
        tipo = "Coquetel"
    else:
        tipo = "Aniversário"
    p["tipo"] = tipo
    p["_alcool"] = "sem alcool" not in t
    return p


def _calcular_festa(params):
    alcool = params.pop("_alcool")
    mod = carregar("festa", "fst_core")
    try:
        r = mod.calcular(params["tipo"], params["adultos"], params.get("criancas", 0), tem_alcool=alcool)
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Salgados: {r['salgados_un']}"
    det = f"Tipo {params['tipo']}. Duração de 4 h, padrão da ferramenta. Álcool: {'sim' if alcool else 'não'}."
    for k, v in r.items():
        det += f"\n{k}: {v}"
    return pacote(resp, det)


_registrar("festa", ["aniversario", "churrasco", "coquetel", "casamento"], _extrair_festa, _calcular_festa)


def _extrair_junina(texto):
    if not combina(texto, [["junina"]], ["quentao"]):
        return None
    return ler(texto, [C("pessoas", ["pessoas", "pessoa", "convidados"], "int", True, solto=True)])


def _calcular_junina(params):
    mod = carregar("festa-junina", "jun_core")
    try:
        r = mod.quantidades(params["pessoas"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Pipoca: {_num(r['pipoca_g'], 0)} g"
    det = resp + "\n" + "\n".join(f"{k}: {v}" for k, v in r.items())
    return pacote(resp, det)


_registrar("festa-junina", ["junina", "pipoca"], _extrair_junina, _calcular_junina)


def _extrair_infantil(texto):
    if not combina(texto, [["festa infantil", "aniversario infantil"]]):
        return None
    return ler(texto, [
        C("criancas", ["criancas", "crianca"], "int", True, solto=True),
        C("adultos", ["adultos", "adulto"], "int", False, 0),
    ])


def _calcular_infantil(params):
    mod = carregar("festa-infantil", "fsi_core")
    try:
        r = mod.quantidades(params["criancas"], params.get("adultos", 0))
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Salgados: {r['salgados']}"
    det = resp + "\nPorções por pessoa são as da ferramenta.\n" + "\n".join(f"{k}: {v}" for k, v in r.items())
    return pacote(resp, det)


_registrar("festa-infantil", ["festa infantil"], _extrair_infantil, _calcular_infantil)


def _extrair_grama(texto):
    if not combina(texto, [["placa"], ["grama"]]):
        return None
    return ler(texto, [C("area", ["m2", "m²", "metros", "area"], "num", True, solto=True)])


def _calcular_grama(params):
    return _chamar(
        "grama-jardim", "grm_core", "placas", {"area_m2": params["area"]},
        "Placas de grama", "m2_placas", False,
        "Perda de 5%, padrão da ferramenta.",
    )


_registrar("grama-jardim", ["grama", "placas"], _extrair_grama, _calcular_grama)


def _extrair_fraldas(texto):
    if not combina(texto, [["fralda"]]):
        return None
    return ler(texto, [C("meses", ["meses", "mes"], "int", False, 24, solto=True)])


def _calcular_fraldas(params):
    mod = carregar("enxoval-bebe", "enx_core")
    try:
        lista = mod.fraldas(params["meses"])
    except ValueError as e:
        return pacote(str(e), str(e))
    total = sum(item[3] for item in lista)
    resp = f"Fraldas: {total} unidades"
    det = resp + f"\nCobertura de {params['meses']} meses. Folga de 10%, padrão da ferramenta."
    for tam, peso, meses, un in lista:
        det += f"\n{tam} ({peso}): {un} un em {meses} meses"
    return pacote(resp, det)


_registrar("enxoval-bebe", ["fralda", "enxoval"], _extrair_fraldas, _calcular_fraldas)


def _extrair_solar(texto):
    if not combina(texto, [["aquecedor solar", "boiler"]]):
        return None
    return ler(texto, [
        C("minutos", ["minuto", "minutos"], "num", True),
        C("pessoas", ["pessoas", "pessoa"], "int", True, solto=True),
    ])


def _calcular_solar(params):
    mod = carregar("aquecedor-solar", "aqs_core")
    try:
        cons = mod.consumo_banho(params["pessoas"], params["minutos"])
        boiler = mod.volume_boiler(cons["litros_dia"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Boiler: {_num(boiler, 0)} L"
    det = (
        f"Banho: {_num(cons['litros_dia'], 1)} L/dia.\n{resp}\n"
        f"Vazão {cons['vazao_lpm']} L/min e 1 banho por dia, padrões da ferramenta."
    )
    return pacote(resp, det)


_registrar("aquecedor-solar", ["aquecedor solar", "boiler"], _extrair_solar, _calcular_solar)


def _extrair_condominio(texto):
    if not combina(texto, [["condominio"], ["taxa", "extra", "rateio"]]):
        return None
    p = ler(texto, [
        C("unidades", ["apartamentos", "apartamento", "unidades", "apto"], "int", True),
        C("total", ["taxa", "valor", "reais", "de"], "din", True, solto=True),
    ])
    return p


def _calcular_condominio(params):
    return _chamar(
        "taxa-extra-condominio", "tcx_core", "ratear",
        {"valor_total": params["total"], "modo": "igualitario", "unidades": params["unidades"]},
        "Sua parte", "sua_parte", True,
        "Rateio igualitário (a frase não falou em fração ideal).",
    )


_registrar("taxa-extra-condominio", ["condominio", "taxa extra"], _extrair_condominio, _calcular_condominio)


# ---------------------------------------------------------------- corpo, sono, gestação
def _extrair_dpp(texto):
    if not combina(texto, [["dum", "dpp", "gestacao", "gestante"]]):
        return None
    dum = _data(texto)
    if not dum:
        return None
    p = ler(texto, [C("ciclo", ["ciclo"], "int", False)])
    p = p or {}
    p["dum"] = dum
    return p


def _calcular_dpp(params):
    mod = carregar("gestacional", "gst_core")
    ciclo = int(params["ciclo"]) if "ciclo" in params else 28
    try:
        dpp = mod.dpp_por_dum(params["dum"], ciclo)
        resumo = mod.resumo(params["dum"], ciclo)
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"DPP: {mod.br(dpp)}"
    det = (
        f"{resp}\nDUM {mod.br(params['dum'])}. Ciclo de {ciclo} dias"
        + (" (padrão da ferramenta)." if "ciclo" not in params else ".")
        + f"\nTrimestre {resumo['trimestre']}, {resumo['semanas']} semanas e {resumo['dias']} dias hoje."
    )
    return pacote(resp, det)


_registrar("gestacional", ["dpp", "dum", "gestacao"], _extrair_dpp, _calcular_dpp)


def _extrair_cafeina(texto):
    if not combina(texto, [["cafeina"]]):
        return None
    return ler(texto, [
        C("horas", ["horas", "hora", "depois"], "hora", True, solto=True),
        C("mg", ["mg", "miligrama"], "num", True, solto=True),
    ])


def _calcular_cafeina(params):
    mod = carregar("calculadora-sono", "sno_core")
    try:
        resto = mod.cafeina_restante(params["mg"], params["horas"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Cafeína restante: {_num(resto, 0)} mg"
    return pacote(resp, resp + "\nMeia-vida de 5 h, padrão da ferramenta.")


_registrar("calculadora-sono", ["cafeina"], _extrair_cafeina, _calcular_cafeina)


def _extrair_debito(texto):
    if not combina(texto, [["debito"], ["sono"]]):
        return None
    return ler(texto, [
        C("horas", ["dormi", "horas", "hora"], "hora", True, solto=True),
        C("idade", ["idade", "anos"], "int", True, solto=True),
    ])


def _calcular_debito(params):
    mod = carregar("calculadora-sono", "sno_core")
    try:
        falta = mod.debito_sono([params["horas"]], params["idade"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Débito desta noite: {_num(falta, 1)} h"
    return pacote(resp, resp + "\nConta uma noite só, contra o mínimo da faixa etária.")


_registrar("calculadora-sono", ["debito", "sono"], _extrair_debito, _calcular_debito)


def _extrair_relogio_sono(texto):
    if not combina(texto, [["acordar", "deitar"]], ["debito", "cafeina"]):
        return None
    hora = _relogio(texto)
    if not hora:
        return None
    return {"hora": hora, "acordar": "acordar" in norm(texto)}


def _calcular_relogio_sono(params):
    mod = carregar("calculadora-sono", "sno_core")
    if params["acordar"]:
        linhas = mod.horarios_dormir(params["hora"])
        titulo = f"Para acordar {params['hora']}, vá dormir"
    else:
        linhas = mod.horarios_acordar(params["hora"])
        titulo = f"Se deitar {params['hora']}, acorde"
    if not linhas:
        return pacote("Sem horário.", "Sem horário.")
    primeiro = linhas[0][0]
    resp = f"{titulo} às {primeiro}"
    det = resp + "\nLatência de 15 min, padrão da ferramenta."
    for hora, ciclos, _h in linhas:
        det += f"\n{hora} ({ciclos} ciclos)"
    return pacote(resp, det)


_registrar("calculadora-sono", ["acordar", "dormir", "sono"], _extrair_relogio_sono, _calcular_relogio_sono)


def _extrair_1rm(texto):
    if not combina(texto, [["1rm", "epley", "brzycki"]]):
        return None
    return ler(texto, [
        C("reps", ["repet", "reps", "repeticoes"], "int", True),
        C("peso", ["kg", "peso", "com"], "num", True, solto=True),
    ])


def _calcular_1rm(params):
    return _chamar(
        "estimativa-1rm-epley", "epl_core", "estimar",
        {"peso": params["peso"], "reps": params["reps"]},
        "1RM médio", "media", False,
    )


_registrar("estimativa-1rm-epley", ["1rm", "epley"], _extrair_1rm, _calcular_1rm)


# ---------------------------------------------------------------- rua, dinheiro da casa
def _extrair_estacionamento(texto):
    if not combina(texto, [["estacionamento"]]):
        return None
    p = ler(texto, [
        C("horas", ["horas", "hora"], "hora", False),
        C("minutos", ["minutos", "minuto"], "int", False),
        C("adicional", ["adicional"], "din", True, solto=True),
        C("primeira", ["primeira"], "din", True, solto=True),
    ])
    if not p or ("horas" not in p and "minutos" not in p):
        return None
    return p


def _calcular_estacionamento(params):
    if "minutos" in params:
        minutos = int(params["minutos"])
    else:
        minutos = int(round(params["horas"] * 60))
    return _chamar(
        "calculadora-estacionamento", "est_core", "calcular",
        {"minutos": minutos, "primeira_hora": params["primeira"], "hora_adicional": params["adicional"]},
        "Estacionamento", "valor", True,
        "Fração de 60 minutos, padrão da ferramenta. Sem teto diário.",
    )


_registrar("calculadora-estacionamento", ["estacionamento"], _extrair_estacionamento, _calcular_estacionamento)


def _extrair_bike(texto):
    if not combina(texto, [["coroa"], ["pinhao"]]):
        return None
    return ler(texto, [
        C("cadencia", ["cadencia", "rpm"], "num", True),
        C("circ", ["mm", "roda", "circunferencia"], "num", True),
        C("pinhao", ["pinhao"], "int", True),
        C("coroa", ["coroa"], "int", True),
    ])


def _calcular_bike(params):
    mod = carregar("calculadora-marchas-bike", "bik_core")
    try:
        vel = mod.velocidade_kmh(params["coroa"], params["pinhao"], params["circ"], params["cadencia"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Velocidade: {_num(vel, 1)} km/h"
    return pacote(resp, resp)


_registrar("calculadora-marchas-bike", ["bike", "coroa", "pinhao"], _extrair_bike, _calcular_bike)


def _extrair_croche(texto):
    if not combina(texto, [["croche", "trico"]]):
        return None
    return ler(texto, [
        C("largura", ["largura", "para"], "num", True),
        C("pontos", ["pontos", "ponto", "amostra"], "num", True, solto=True),
    ])


def _calcular_croche(params):
    mod = carregar("croche", "trc_core")
    try:
        n = mod.pontos_para_largura(params["pontos"], params["largura"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Monte {n} pontos"
    return pacote(resp, resp + "\nA amostra é em 10 cm, como a ferramenta pede.")


_registrar("croche", ["croche", "trico", "pontos"], _extrair_croche, _calcular_croche)


def _extrair_calcado(texto):
    if not combina(texto, [["sapato", "calcado", "tenis"]]):
        return None
    p = ler(texto, [C("numero", ["numero", "br", "eu", "us", "uk"], "num", True, solto=True)])
    if not p:
        return None
    t = norm(texto)
    if "americano" in t or re.search(r"(?<!\w)us(?!\w)", t):
        sistema = "US"
    elif "europeu" in t or re.search(r"(?<!\w)eu(?!\w)", t):
        sistema = "EU"
    elif re.search(r"(?<!\w)uk(?!\w)", t):
        sistema = "UK"
    elif " cm" in t or t.endswith("cm"):
        sistema = "CM"
    else:
        sistema = "BR"
    p["sistema"] = sistema
    p["categoria"] = "masculino" if "masculino" in t or "homem" in t else "feminino"
    p["_disse_genero"] = "masculino" in t or "homem" in t or "feminino" in t or "mulher" in t
    return p


def _calcular_calcado(params):
    disse = params.pop("_disse_genero")
    mod = carregar("tamanhos", "tam_core")
    try:
        r = mod.converter_calcado(params["numero"], params["sistema"], params["categoria"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"Sapato BR {r['BR']} / EU {r['EU']} / US {r['US']} / UK {r['UK']} ({r['cm']} cm)"
    det = resp + f"\nLido como {params['sistema']} {params['categoria']}."
    if not disse:
        det += " Gênero feminino, porque a frase não disse."
    return pacote(resp, det)


_registrar("tamanhos", ["sapato", "calcado", "tenis"], _extrair_calcado, _calcular_calcado)


def _extrair_pneu(texto):
    if not combina(texto, [["pneu"]]):
        return None
    return ler(texto, [
        C("km_atual", ["atual"], "num", True),
        C("km_instalacao", ["instalado", "instalacao"], "num", True),
        C("vida", ["vida"], "num", True),
        C("km_mes", ["por mes", "ando"], "num", True),
        C("preco", ["preco"], "din", True, solto=True),
    ])


def _calcular_pneu(params):
    return _chamar(
        "troca-pneu-carro", "pne_core", "calcular",
        {
            "km_atual": params["km_atual"],
            "km_instalacao": params["km_instalacao"],
            "vida_util_km": params["vida"],
            "km_mes": params["km_mes"],
            "preco_pneu": params["preco"],
        },
        "Pneu ainda roda", "restantes", False,
        "Quatro pneus, sem alinhamento nem montagem: padrões da ferramenta.",
    )


_registrar("troca-pneu-carro", ["pneu"], _extrair_pneu, _calcular_pneu)


def _extrair_cafeteria(texto):
    if not combina(texto, [["cafeteria"]]):
        return None
    return ler(texto, [
        C("xicaras_semana", ["por semana", "semana"], "int", True),
        C("preco_cafeteria", ["cafeteria"], "din", True),
        C("preco_pacote", ["pacote"], "din", True),
        C("rende", ["rende", "rende o pacote"], "int", True),
    ])


def _calcular_cafeteria(params):
    return _chamar(
        "cafe-casa-vs-cafeteria", "cfh_core", "comparar",
        {
            "xicaras_semana": params["xicaras_semana"],
            "preco_cafeteria": params["preco_cafeteria"],
            "preco_pacote": params["preco_pacote"],
            "xicaras_por_pacote": params["rende"],
        },
        "Economia do café em casa", "economia", True,
        "Leite e filtro ficaram 0 porque não foram ditos.",
    )


_registrar("cafe-casa-vs-cafeteria", ["cafeteria", "cafe em casa"], _extrair_cafeteria, _calcular_cafeteria)


def _extrair_petsitter(texto):
    if not combina(texto, [["petsitter", "pet sitter"]]):
        return None
    return ler(texto, [
        C("dias", ["dias", "dia"], "dia", True, solto=True),
        C("horas", ["horas", "hora"], "hora", True),
        C("sitter", ["por hora", "sitter"], "din", True),
        C("creche", ["creche"], "din", True),
        C("hotel", ["hotel"], "din", True),
    ])


def _calcular_petsitter(params):
    return _chamar(
        "petsitter-vs-creche", "pts_core", "comparar",
        {
            "dias": int(params["dias"]),
            "horas_dia": params["horas"],
            "preco_sitter_hora": params["sitter"],
            "preco_creche_dia": params["creche"],
            "preco_hotel_dia": params["hotel"],
        },
        "Mais barato", "melhor", False,
    )


_registrar("petsitter-vs-creche", ["petsitter", "creche"], _extrair_petsitter, _calcular_petsitter)


def _extrair_hotel_pet(texto):
    if not combina(texto, [["hotelzinho", "hospedagem"]], ["petsitter", "pet sitter"]):
        return None
    return ler(texto, [
        C("dias", ["dias", "dia"], "dia", True, solto=True),
        C("diaria", ["diaria", "dia a", "reais"], "din", True, solto=True),
    ])


def _calcular_hotel_pet(params):
    return _chamar(
        "hospedagem-pet", "hpv_core", "calcular",
        {"dias": int(params["dias"]), "preco_diaria": params["diaria"]},
        "Hotel do pet", "liquido", True,
        "1 pet, sem banho, transporte nem desconto.",
    )


_registrar("hospedagem-pet", ["hotelzinho", "hospedagem"], _extrair_hotel_pet, _calcular_hotel_pet)


def _extrair_horta(texto):
    if not combina(texto, [["horta"], ["colhi", "colheita"]]):
        return None
    return ler(texto, [
        C("kg", ["kg", "quilos", "colhi"], "num", True),
        C("preco", ["reais", "preco", "kg a"], "din", True),
        C("insumos", ["insumo", "insumos"], "din", True),
    ])


def _calcular_horta(params):
    return _chamar(
        "economia-horta-caseira", "hrt_core", "calcular",
        {
            "kg_colhido_mes": params["kg"],
            "preco_kg_mercado": params["preco"],
            "custo_insumos_mes": params["insumos"],
        },
        "Economia da horta", "economia", True,
        "Horas de trabalho ficaram 0 porque não foram ditas.",
    )


_registrar("economia-horta-caseira", ["horta", "colheita"], _extrair_horta, _calcular_horta)


def _extrair_reajuste(texto):
    if not combina(texto, [["reajuste"], ["plano"]]):
        return None
    return ler(texto, [
        C("anos", ["anos", "ano"], "int", False, 5, solto=True),
        C("pct", ["%", "reajuste", "ao ano"], "pct", True),
        C("mensalidade", ["reais", "mensalidade", "de"], "din", True, solto=True),
    ])


def _calcular_reajuste(params):
    return _chamar(
        "reajuste-plano-saude", "rps_core", "projetar",
        {"mensalidade": params["mensalidade"], "reajuste_pct": params["pct"], "anos": params["anos"]},
        "Mensalidade no fim", "mensal_final", True,
        "1 beneficiário, padrão da ferramenta.",
    )


_registrar("reajuste-plano-saude", ["reajuste", "plano de saude"], _extrair_reajuste, _calcular_reajuste)


def _extrair_reembolso(texto):
    if not combina(texto, [["reembolso"]]):
        return None
    return ler(texto, [
        C("cobertura", ["cobertura", "%"], "pct", True),
        C("tabela", ["tabela"], "din", True),
        C("pago", ["paguei", "pago", "reais"], "din", True, solto=True),
    ])


def _calcular_reembolso(params):
    return _chamar(
        "reembolso-plano-saude", "rms_core", "calcular",
        {
            "valor_pago": params["pago"],
            "valor_tabela": params["tabela"],
            "percentual_cobertura": params["cobertura"],
        },
        "Reembolso", "reembolso", True,
        "Sem coparticipação e sem teto, porque a frase não disse.",
    )


_registrar("reembolso-plano-saude", ["reembolso"], _extrair_reembolso, _calcular_reembolso)


def _extrair_lentes(texto):
    if not combina(texto, [["lente"]]):
        return None
    p = ler(texto, [
        C("caixa", ["caixa"], "int", True),
        C("preco", ["reais", "preco"], "din", True, solto=True),
    ])
    if not p:
        return None
    t = norm(texto)
    if "diaria" in t or "diária" in t:
        tipo = "diaria"
    elif "quinzenal" in t:
        tipo = "quinzenal"
    else:
        tipo = "mensal"
    p["tipo"] = tipo
    p["olhos"] = 1 if "um olho" in t else 2
    p["_disse_olhos"] = "olho" in t
    p["_disse_tipo"] = any(x in t for x in ("diaria", "quinzenal", "mensal"))
    return p


def _calcular_lentes(params):
    disse_olhos = params.pop("_disse_olhos")
    disse_tipo = params.pop("_disse_tipo")
    nota = []
    if not disse_tipo:
        nota.append("Tipo mensal, porque a frase não disse outro.")
    if not disse_olhos:
        nota.append("Dois olhos, porque a frase não disse outro.")
    return _chamar(
        "lentes-contato", "lct_core", "custo_mensal",
        {
            "preco_caixa": params["preco"],
            "lentes_por_caixa": params["caixa"],
            "olhos": params["olhos"],
            "tipo": params["tipo"],
        },
        "Custo das lentes", "custo", True,
        " ".join(nota),
    )


_registrar("lentes-contato", ["lente", "lentes"], _extrair_lentes, _calcular_lentes)


def _extrair_fumar(texto):
    if not combina(texto, [["sem fumar", "parei de fumar"]]):
        return None
    return ler(texto, [
        C("dias", ["dias", "dia"], "dia", True, solto=True),
        C("cigarros", ["cigarros", "cigarro"], "num", True),
        C("preco", ["maco", "reais"], "din", True),
    ])


def _calcular_fumar(params):
    return _chamar(
        "parar-fumar", "fum_core", "dinheiro_economizado",
        {
            "dias": int(params["dias"]),
            "cigarros_por_dia": params["cigarros"],
            "preco_maco": params["preco"],
        },
        "Economizado", "economizado", True,
        "Maço de 20 cigarros, padrão da ferramenta.",
    )


_registrar("parar-fumar", ["sem fumar", "cigarro"], _extrair_fumar, _calcular_fumar)


# T02: 15 chaves de casa que a cobertura ainda não ligava.

_MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}


def _extrair_glp(texto):
    if not combina(texto, [["glp"]], ["botijao", "p13", "p45"]):
        return None
    return ler(texto, [
        C("horas_por_dia", ["horas", "hora"], "hora", True),
        C("kg_botijao", ["kg"], "num", True),
        C("preco_botijao", ["reais"], "din", True),
        C("bocas_em_uso", ["bocas", "boca"], "int", True),
    ])


def _calcular_glp(params):
    mod = carregar("calculadora-botijao-gas", "glp_core")
    r = mod.estimar(params["kg_botijao"], params["preco_botijao"], params["bocas_em_uso"], 0.2, params["horas_por_dia"])
    return pacote(f"Dura {_num(r['dias'], 1)} dias", f"Custo por dia {_brl(r['custo_dia'])}. Consumo 0,2 kg por boca/hora, padrão do adaptador.")


def _extrair_agua_conta(texto):
    if not combina(texto, [["conta de agua"]]):
        return None
    return ler(texto, [
        C("m3", ["m3"], "num", True),
        C("tarifa", ["tarifa"], "din", True),
        C("taxa", ["taxa"], "din", True),
    ])


def _calcular_agua_conta(params):
    mod = carregar("estimativa-conta-agua", "agu_core")
    r = mod.custo(params["m3"], params["tarifa"], params["taxa"])
    return mostrar(mod, r, "Conta de água", "total_rs")


def _extrair_oleo(texto):
    if not combina(texto, [["troca de oleo", "oleo do carro"]]):
        return None
    return ler(texto, [
        C("litros", ["litros", "litro"], "num", True),
        C("preco_litro", ["reais"], "din", True),
        C("filtro_oleo", ["filtro"], "din", True),
    ])


def _calcular_oleo(params):
    mod = carregar("troca-oleo", "olo_core")
    r = mod.custo_estimado(params["litros"], params["preco_litro"], params["filtro_oleo"])
    return mostrar(mod, r, "Troca de óleo", "total")


def _extrair_app(texto):
    if not combina(texto, [["corrida de app"]]):
        return None
    return ler(texto, [
        C("minutos", ["minutos", "minuto"], "int", True),
        C("km", ["km"], "num", True),
        C("tarifa_base", ["base"], "din", True),
        C("por_km", ["por km"], "din", True),
        C("por_min", ["por minuto"], "din", True),
    ])


def _calcular_app(params):
    mod = carregar("carro-ou-app", "uba_core")
    r = mod.custo_corrida_app(params["km"], params["minutos"], params["tarifa_base"], params["por_km"], params["por_min"], 1)
    return mostrar(mod, r, "Corrida de app")


def _extrair_frasco(texto):
    if not combina(texto, [["protetor", "frasco"]]):
        return None
    if "protetor" not in norm(texto) and "frasco" not in norm(texto):
        return None
    if not combina(texto, [["protetor"]]):
        return None
    return ler(texto, [
        C("ml", ["frasco"], "num", True),
        C("dose_ml_dia", ["dose"], "num", True),
    ])


def _calcular_frasco(params):
    mod = carregar("rotina-skincare", "skn_core")
    dias = mod.duracao_frasco(params["ml"], params["dose_ml_dia"])
    return mostrar(mod, dias, "O frasco dura", None, False)


def _extrair_sono_bebe(texto):
    if not combina(texto, [["bebe"], ["sono"]]):
        return None
    return ler(texto, [C("meses", ["meses", "mes"], "mes", True)])


def _calcular_sono_bebe(params):
    mod = carregar("sono-bebe", "sbb_core")
    r = mod.recomendacao_sono(int(params["meses"]))
    return pacote(f"Sono do bebê: {_num(r['alvo'], 1)} h", f"Entre {_num(r['horas_min'], 1)} e {_num(r['horas_max'], 1)} h.")


def _extrair_pressao(texto):
    if not combina(texto, [["pressao"], ["diastolica"]]):
        return None
    return ler(texto, [
        C("sistolica", ["sistolica", "pressao"], "int", True),
        C("diastolica", ["diastolica"], "int", True),
    ])


def _calcular_pressao(params):
    mod = carregar("diario-pressao", "prs_core")
    classe = mod.classificar_pa(int(params["sistolica"]), int(params["diastolica"]))
    return pacote(f"Pressão: {classe}", f"{int(params['sistolica'])} por {int(params['diastolica'])}: {classe}.")


def _extrair_safra(texto):
    if not combina(texto, [["safra"]]):
        return None
    t = norm(texto)
    mes = next((n for nome, n in _MESES.items() if nome in t), None)
    if mes is None:
        return None
    mod = carregar("calendario-safra", "sfr_core")
    item = next((k for k in mod.ITENS if norm(k) in t), None)
    if item is None:
        return None
    return {"item": item, "mes": mes}


def _calcular_safra(params):
    mod = carregar("calendario-safra", "sfr_core")
    nivel = mod.nivel(params["item"], params["mes"])
    return pacote(f"Safra da {params['item']}: {nivel}", f"{params['item']} no mês {params['mes']}: {nivel}.")


def _extrair_rega(texto):
    if not combina(texto, [["vaso"], ["regar", "rega"]]):
        return None
    return ler(texto, [C("diametro_cm", ["cm"], "num", True)])


def _calcular_rega(params):
    mod = carregar("rega-plantas", "reg_core")
    ml = mod.volume_ml(params["diametro_cm"])
    return pacote(f"Rega: {_num(ml, 0)} ml", f"Vaso de {_num(params['diametro_cm'], 0)} cm: {_num(ml, 0)} ml.")


def _extrair_mesada(texto):
    if not combina(texto, [["mesada"]]):
        return None
    return ler(texto, [
        C("minimo_pct", ["minimo"], "pct", True),
        C("feitos", ["feitas"], "int", True),
        C("total", ["total"], "int", True),
        C("base", ["base"], "din", True),
        C("bonus_100", ["bonus"], "din", True),
    ])


def _calcular_mesada(params):
    mod = carregar("tarefas-casa", "tcs_core")
    valor = mod.mesada(params["feitos"], params["total"], params["base"], params["bonus_100"], params["minimo_pct"])
    return mostrar(mod, valor, "Mesada")


def _extrair_airbnb(texto):
    if not combina(texto, [["airbnb"]], ["hospedagem", "hotelzinho", "pet"]):
        return None
    return ler(texto, [
        C("noites", ["noites", "noite"], "int", True),
        C("pessoas", ["pessoas", "pessoa"], "int", True),
        C("diaria", ["diaria", "reais"], "din", True),
    ])


def _calcular_airbnb(params):
    mod = carregar("comparador-hospedagens", "hsp_core")
    op = mod.Opcao("estadia", params["diaria"])
    r = mod.total(op, int(params["noites"]), int(params["pessoas"]))
    return mostrar(mod, r, "Estadia", "total")


def _extrair_jet(texto):
    if not combina(texto, [["jet lag", "jetlag"]]):
        return None
    nums = re.findall(r"fuso\s*(-?\d+)", norm(texto))
    if len(nums) < 2:
        return None
    return {"origem": float(nums[0]), "destino": float(nums[1])}


def _calcular_jet(params):
    mod = carregar("adaptacao-jet-lag", "jtl_core")
    horas = mod.diferenca(params["origem"], params["destino"])
    return pacote(f"Fuso: {_num(horas, 0)} h", f"De {params['origem']:g} para {params['destino']:g}: {_num(horas, 1)} h.")


def _extrair_canteiro(texto):
    if not combina(texto, [["canteiro"], ["alface"]]):
        return None
    p = ler(texto, [
        C("length_m", ["comprimento"], "num", True),
        C("width_m", ["largura"], "num", True),
    ])
    if not p:
        return None
    p["crop"] = "Alface"
    return p


def _calcular_canteiro(params):
    mod = carregar("horta-jardim", "agr_core")
    r = mod.calculate_bed_fertilizer_and_plants(params["length_m"], params["width_m"], params["crop"])
    return pacote(f"Mudas: {r['estimated_plants']}", f"Canteiro de alface: {r['estimated_plants']} mudas em {_num(r['area_m2'], 1)} m².")


def _extrair_horta_cal(texto):
    if not combina(texto, [["calendario da horta"]]):
        return None
    t = norm(texto)
    mod = carregar("calendario-da-horta", "cpl_core")
    cultura = next((k for k in mod.CULTURAS if norm(k) in t), None)
    if cultura is None:
        return None
    return {"cultura": cultura}


def _calcular_horta_cal(params):
    mod = carregar("calendario-da-horta", "cpl_core")
    dias = mod.intervalo_ideal(params["cultura"])
    return pacote(f"Replante a cada {dias} dias", f"{params['cultura']}: intervalo ideal de {dias} dias.")


def _extrair_expresso(texto):
    if not combina(texto, [["expresso"]], ["cafeina", "v60", "coado"]):
        return None
    return ler(texto, [
        C("ml", ["ml"], "num", True),
        C("mg_por_ml", ["mg por ml", "mg/ml"], "num", True),
    ])


def _calcular_expresso(params):
    mod = carregar("controle-cafeina-doses-dia", "cfd_core")
    mg = mod.cafeina_por_volume(params["ml"], params["mg_por_ml"])
    return pacote(f"Cafeína: {_num(mg, 0)} mg", f"{_num(params['ml'], 0)} ml × {_num(params['mg_por_ml'], 1)} mg/ml.")


_registrar("calculadora-botijao-gas", ["glp"], _extrair_glp, _calcular_glp)
_registrar("estimativa-conta-agua", ["conta de agua"], _extrair_agua_conta, _calcular_agua_conta)
_registrar("troca-oleo", ["troca de oleo", "oleo do carro"], _extrair_oleo, _calcular_oleo)
_registrar("carro-ou-app", ["corrida de app"], _extrair_app, _calcular_app)
_registrar("rotina-skincare", ["protetor"], _extrair_frasco, _calcular_frasco)
_registrar("sono-bebe", ["bebe", "sono"], _extrair_sono_bebe, _calcular_sono_bebe)
_registrar("diario-pressao", ["pressao"], _extrair_pressao, _calcular_pressao)
_registrar("calendario-safra", ["safra"], _extrair_safra, _calcular_safra)
_registrar("rega-plantas", ["vaso", "regar"], _extrair_rega, _calcular_rega)
_registrar("tarefas-casa", ["mesada"], _extrair_mesada, _calcular_mesada)
_registrar("comparador-hospedagens", ["airbnb"], _extrair_airbnb, _calcular_airbnb)
_registrar("adaptacao-jet-lag", ["jet lag"], _extrair_jet, _calcular_jet)
_registrar("horta-jardim", ["canteiro", "alface"], _extrair_canteiro, _calcular_canteiro)
_registrar("calendario-da-horta", ["calendario da horta"], _extrair_horta_cal, _calcular_horta_cal)
_registrar("controle-cafeina-doses-dia", ["expresso"], _extrair_expresso, _calcular_expresso)
