# -*- coding: utf-8 -*-
"""Adaptadores da barra para conversões.

Cada calcular chama o módulo real da ferramenta. Não refaz a conta.
"""
from __future__ import annotations

import os
import re
import sys

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
pacote = af.pacote
_num = af._num

ADAPTADORES = []


def _registrar(chave, palavras, extrair, calcular):
    ADAPTADORES.append({
        "chave": chave,
        "palavras": list(palavras),
        "extrair": extrair,
        "calcular": calcular,
    })


# alias já sem acento -> uma ou mais (categoria, chave do cu_unidades)
_BRUTOS = [
    ("milhas nauticas", [("Comprimento", "nmi")]),
    ("milha nautica", [("Comprimento", "nmi")]),
    ("quilometros por hora", [("Velocidade", "kmh")]),
    ("kilometros por hora", [("Velocidade", "kmh")]),
    ("metros por segundo", [("Velocidade", "ms")]),
    ("milhas por hora", [("Velocidade", "mph")]),
    ("litros por 100 km", [("Combustível", "l100")]),
    ("km por litro", [("Combustível", "kml")]),
    ("graus celsius", [("Temperatura", "C")]),
    ("grau celsius", [("Temperatura", "C")]),
    ("graus fahrenheit", [("Temperatura", "F")]),
    ("grau fahrenheit", [("Temperatura", "F")]),
    ("graus kelvin", [("Temperatura", "K")]),
    ("metros quadrados", [("Área", "m2")]),
    ("metro quadrado", [("Área", "m2")]),
    ("metros cubicos", [("Volume", "m3")]),
    ("metro cubico", [("Volume", "m3")]),
    ("centimetros quadrados", [("Área", "cm2")]),
    ("centimetros cubicos", [("Volume", "cm3")]),
    ("quilometros quadrados", [("Área", "km2")]),
    ("colheres de sopa", [("Cozinha", "cs")]),
    ("colher de sopa", [("Cozinha", "cs")]),
    ("colheres de cha", [("Cozinha", "cc")]),
    ("colher de cha", [("Cozinha", "cc")]),
    ("onca fluida", [("Volume", "floz")]),
    ("oncas fluidas", [("Volume", "floz")]),
    ("milissegundos", [("Tempo", "ms")]),
    ("milissegundo", [("Tempo", "ms")]),
    ("microssegundos", [("Tempo", "ms")]),
    ("quilocalorias", [("Energia", "kcal")]),
    ("quilocaloria", [("Energia", "kcal")]),
    ("quilojoules", [("Energia", "kJ")]),
    ("quilojoule", [("Energia", "kJ")]),
    ("quilowatts", [("Potência", "kW")]),
    ("quilowatt", [("Potência", "kW")]),
    ("quilopascais", [("Pressão", "kPa")]),
    ("atmosferas", [("Pressão", "atm")]),
    ("atmosfera", [("Pressão", "atm")]),
    ("milimetros", [("Comprimento", "mm")]),
    ("milimetro", [("Comprimento", "mm")]),
    ("centimetros", [("Comprimento", "cm")]),
    ("centimetro", [("Comprimento", "cm")]),
    ("quilometros", [("Comprimento", "km")]),
    ("quilometro", [("Comprimento", "km")]),
    ("kilometros", [("Comprimento", "km")]),
    ("kilometro", [("Comprimento", "km")]),
    ("polegadas", [("Comprimento", "in")]),
    ("polegada", [("Comprimento", "in")]),
    ("micrômetro", [("Comprimento", "um")]),
    ("micrometros", [("Comprimento", "um")]),
    ("micrometro", [("Comprimento", "um")]),
    ("jardas", [("Comprimento", "yd")]),
    ("jarda", [("Comprimento", "yd")]),
    ("milhas", [("Comprimento", "mi")]),
    ("milha", [("Comprimento", "mi")]),
    ("hectares", [("Área", "ha")]),
    ("hectare", [("Área", "ha")]),
    ("alqueires", [("Área", "alq")]),
    ("alqueire", [("Área", "alq")]),
    ("celsius", [("Temperatura", "C")]),
    ("fahrenheit", [("Temperatura", "F")]),
    ("kelvin", [("Temperatura", "K")]),
    ("mililitros", [("Volume", "ml"), ("Cozinha", "ml")]),
    ("mililitro", [("Volume", "ml"), ("Cozinha", "ml")]),
    ("litros", [("Volume", "l"), ("Cozinha", "l")]),
    ("litro", [("Volume", "l"), ("Cozinha", "l")]),
    ("galao", [("Volume", "galus")]),
    ("gramas", [("Massa", "g")]),
    ("grama", [("Massa", "g")]),
    ("quilos", [("Massa", "kg")]),
    ("quilo", [("Massa", "kg")]),
    ("quilogramas", [("Massa", "kg")]),
    ("quilograma", [("Massa", "kg")]),
    ("miligramas", [("Massa", "mg")]),
    ("miligrama", [("Massa", "mg")]),
    ("toneladas", [("Massa", "t")]),
    ("tonelada", [("Massa", "t")]),
    ("libras", [("Massa", "lb")]),
    ("libra", [("Massa", "lb")]),
    ("arrobas", [("Massa", "arroba")]),
    ("arroba", [("Massa", "arroba")]),
    ("oncas", [("Massa", "oz")]),
    ("onca", [("Massa", "oz")]),
    ("segundos", [("Tempo", "s")]),
    ("segundo", [("Tempo", "s")]),
    ("minutos", [("Tempo", "min")]),
    ("minuto", [("Tempo", "min")]),
    ("horas", [("Tempo", "h")]),
    ("hora", [("Tempo", "h")]),
    ("semanas", [("Tempo", "sem")]),
    ("semana", [("Tempo", "sem")]),
    ("meses", [("Tempo", "mes")]),
    ("dias", [("Tempo", "d")]),
    ("anos", [("Tempo", "ano")]),
    ("radianos", [("Ângulo", "rad")]),
    ("radiano", [("Ângulo", "rad")]),
    ("graus", [("Ângulo", "deg")]),
    ("grau", [("Ângulo", "deg")]),
    ("gigabytes", [("Dados", "GB")]),
    ("gigabyte", [("Dados", "GB")]),
    ("megabytes", [("Dados", "MB")]),
    ("megabyte", [("Dados", "MB")]),
    ("kilobytes", [("Dados", "KB")]),
    ("kilobyte", [("Dados", "KB")]),
    ("terabytes", [("Dados", "TB")]),
    ("terabyte", [("Dados", "TB")]),
    ("gibibytes", [("Dados", "GiB")]),
    ("gibibyte", [("Dados", "GiB")]),
    ("mebibytes", [("Dados", "MiB")]),
    ("mebibyte", [("Dados", "MiB")]),
    ("kibibytes", [("Dados", "KiB")]),
    ("kibibyte", [("Dados", "KiB")]),
    ("calorias", [("Energia", "cal")]),
    ("caloria", [("Energia", "cal")]),
    ("joules", [("Energia", "J")]),
    ("joule", [("Energia", "J")]),
    ("xicaras", [("Cozinha", "xic")]),
    ("xicara", [("Cozinha", "xic")]),
    ("cavalos", [("Potência", "cv")]),
    ("cavalo", [("Potência", "cv")]),
    ("pascal", [("Pressão", "Pa")]),
    ("watts", [("Potência", "W")]),
    ("watt", [("Potência", "W")]),
    ("bytes", [("Dados", "B")]),
    ("byte", [("Dados", "B")]),
    ("km/h", [("Velocidade", "kmh")]),
    ("km/l", [("Combustível", "kml")]),
    ("l/100km", [("Combustível", "l100")]),
    ("l/100", [("Combustível", "l100")]),
    ("m/s", [("Velocidade", "ms")]),
    ("mmhg", [("Pressão", "mmHg")]),
    ("kcal", [("Energia", "kcal")]),
    ("kwh", [("Energia", "kWh")]),
    ("mib", [("Dados", "MiB")]),
    ("gib", [("Dados", "GiB")]),
    ("kib", [("Dados", "KiB")]),
    ("gbit", [("Dados", "Gbit")]),
    ("mbit", [("Dados", "Mbit")]),
    ("km2", [("Área", "km2")]),
    ("cm2", [("Área", "cm2")]),
    ("m2", [("Área", "m2")]),
    ("m3", [("Volume", "m3")]),
    ("cm3", [("Volume", "cm3")]),
    ("psi", [("Pressão", "psi")]),
    ("kpa", [("Pressão", "kPa")]),
    ("atm", [("Pressão", "atm")]),
    ("bar", [("Pressão", "bar")]),
    ("mph", [("Velocidade", "mph")]),
    ("kmh", [("Velocidade", "kmh")]),
    ("nmi", [("Comprimento", "nmi")]),
    ("cvs", [("Potência", "cv")]),
    ("btu", [("Energia", "BTU")]),
    ("rad", [("Ângulo", "rad")]),
    ("lbs", [("Massa", "lb")]),
    ("kgs", [("Massa", "kg")]),
    ("mm", [("Comprimento", "mm")]),
    ("cm", [("Comprimento", "cm")]),
    ("km", [("Comprimento", "km")]),
    ("ft", [("Comprimento", "ft")]),
    ("yd", [("Comprimento", "yd")]),
    ("mi", [("Comprimento", "mi")]),
    ("ha", [("Área", "ha")]),
    ("kg", [("Massa", "kg")]),
    ("mg", [("Massa", "mg")]),
    ("lb", [("Massa", "lb")]),
    ("oz", [("Massa", "oz")]),
    ("ml", [("Volume", "ml"), ("Cozinha", "ml")]),
    ("gb", [("Dados", "GB")]),
    ("mb", [("Dados", "MB")]),
    ("kb", [("Dados", "KB")]),
    ("tb", [("Dados", "TB")]),
    ("cv", [("Potência", "cv")]),
    ("hp", [("Potência", "hp")]),
    ("kw", [("Potência", "kW")]),
    ("pa", [("Pressão", "Pa")]),
    ("wh", [("Energia", "Wh")]),
    ("kj", [("Energia", "kJ")]),
    ("ms", [("Tempo", "ms"), ("Velocidade", "ms")]),
    ("min", [("Tempo", "min")]),
    ("pes", [("Comprimento", "ft")]),
    ("dia", [("Tempo", "d")]),
    ("mes", [("Tempo", "mes")]),
    ("ano", [("Tempo", "ano")]),
    ("nos", [("Velocidade", "kn")]),
    ("pol", [("Comprimento", "in")]),
    ("copo", [("Cozinha", "copo")]),
    ("copos", [("Cozinha", "copo")]),
    ("graus", [("Ângulo", "deg")]),
    ("c", [("Temperatura", "C")]),
    ("f", [("Temperatura", "F")]),
    ("k", [("Temperatura", "K")]),
    ("g", [("Massa", "g")]),
    ("l", [("Volume", "l"), ("Cozinha", "l")]),
    ("m", [("Comprimento", "m")]),
    ("h", [("Tempo", "h")]),
    ("s", [("Tempo", "s")]),
    ("t", [("Massa", "t")]),
    ("j", [("Energia", "J")]),
    ("w", [("Potência", "W")]),
]
_ALIASES = sorted(_BRUTOS, key=lambda item: len(item[0]), reverse=True)
_PREF = [
    "Comprimento", "Massa", "Temperatura", "Volume", "Área", "Velocidade",
    "Tempo", "Dados", "Energia", "Pressão", "Potência", "Ângulo",
    "Combustível", "Cozinha",
]
_EVITAR_CONV = ("epoch", "unix", "utm", "mired", "forno", "formatar", "coordenada")


def _achar_unidades(texto):
    t = norm(texto)
    ocupado = [False] * len(t)
    achados = []
    for alias, destinos in _ALIASES:
        ini = 0
        while True:
            i = t.find(alias, ini)
            if i < 0:
                break
            fim = i + len(alias)
            antes = i == 0 or not t[i - 1].isalnum()
            depois = fim >= len(t) or not t[fim].isalnum()
            livre = not any(ocupado[i:fim])
            if antes and depois and livre:
                for cat, chave in destinos:
                    achados.append((i, fim, cat, chave))
                for j in range(i, fim):
                    ocupado[j] = True
            ini = i + 1
    achados.sort()
    return achados


def _numero_antes(texto, pos):
    melhor = None
    for tk in tokens(texto):
        if tk.ini < pos and (melhor is None or tk.ini > melhor.ini):
            melhor = tk
    if melhor is None:
        return None
    return melhor.valor


def _extrair_converter(texto):
    t = norm(texto)
    if any(p in t for p in _EVITAR_CONV):
        return None
    uns = _achar_unidades(texto)
    if len(uns) < 2:
        return None
    for con in re.finditer(r"(?<!\w)(?:em|para|pra)(?!\w)", t):
        esq = [u for u in uns if u[1] <= con.start()]
        dire = [u for u in uns if u[0] >= con.end()]
        pares = [(a, b) for a in esq for b in dire if a[2] == b[2]]
        if not pares:
            continue
        pares.sort(key=lambda ab: _PREF.index(ab[0][2]) if ab[0][2] in _PREF else 99)
        a, b = pares[0]
        valor = _numero_antes(texto, a[0])
        if valor is None:
            continue
        return {"cat": a[2], "valor": valor, "de": a[3], "para": b[3]}
    return None


def _calcular_converter(params):
    mod = carregar("conversor-unidades", "cu_unidades")
    try:
        val = mod.convert(params["cat"], params["valor"], params["de"], params["para"])
    except (KeyError, ZeroDivisionError, OverflowError) as e:
        return pacote(str(e), str(e))
    origem = mod.get_unit(params["cat"], params["de"]).label
    destino = mod.get_unit(params["cat"], params["para"]).label
    resp = f"{mod.format_number(params['valor'])} {origem} = {mod.format_number(val)} {destino}"
    det = f"Categoria {params['cat']}, pela função convert de cu_unidades."
    return pacote(resp, det)


_registrar(
    "conversor-unidades",
    ["converter", "em", "quilometros", "celsius"],
    _extrair_converter, _calcular_converter,
)


def _extrair_tamanho(texto):
    if not combina(texto, [["formatar"], ["tamanho", "bytes", "byte"]]):
        return None
    t = norm(texto)
    m = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(bytes|byte|kib|mib|gib|tib|kb|mb|gb|tb|b)?",
        t,
    )
    if not m:
        return None
    return {"bruto": m.group(0).replace(",", ".").replace(" ", "")}


def _calcular_tamanho(params):
    mod = carregar("formatador-tamanho", "hsz_core")
    try:
        n = mod.parse_size(params["bruto"])
    except ValueError as e:
        return pacote(str(e), str(e))
    iec = mod.format_size(n, binary=True)
    si = mod.format_size(n, binary=False)
    return pacote(f"Tamanho: {iec}", f"Bytes exatos: {n}\nSI: {si}\n{mod.table(n)}")


_registrar("formatador-tamanho", ["formatar tamanho", "bytes"], _extrair_tamanho, _calcular_tamanho)


def _data_literal(texto):
    m = re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", texto)
    return m.group(0) if m else None


def _extrair_epoch_num(texto):
    if not combina(texto, [["epoch", "unix"]]):
        return None
    if _data_literal(texto):
        return None
    nums = [tk.valor for tk in tokens(texto)]
    if not nums:
        return None
    return {"valor": int(round(nums[0]))}


def _calcular_epoch_num(params):
    mod = carregar("conversor-epoch", "epc_core")
    try:
        r = mod.epoch_to_datetimes(params["valor"])
    except (ValueError, OSError, OverflowError) as e:
        return pacote(str(e), str(e))
    resp = f"UTC: {r['utc_iso']}"
    det = f"Unidade lida: {r['unit']}. Segundos: {r['seconds']}."
    return pacote(resp, det)


_registrar("conversor-epoch", ["epoch", "unix"], _extrair_epoch_num, _calcular_epoch_num)


def _extrair_epoch_data(texto):
    if not combina(texto, [["epoch", "unix"]]):
        return None
    data = _data_literal(texto)
    if not data:
        return None
    return {"data": data}


def _calcular_epoch_data(params):
    mod = carregar("conversor-epoch", "epc_core")
    try:
        r = mod.datetime_to_epoch(params["data"])
    except ValueError as e:
        return pacote(str(e), str(e))
    return pacote(
        f"Epoch: {r['epoch']}",
        f"Data lida como UTC: {r['datetime']}. Segundos: {r['seconds']}.",
    )


_registrar("conversor-epoch", ["data epoch"], _extrair_epoch_data, _calcular_epoch_data)


def _extrair_cor(texto):
    if not combina(texto, [["mired", "de cor"]]):
        return None
    nums = [tk.valor for tk in tokens(texto)]
    if not nums:
        return None
    return {"kelvin": nums[0]}


def _calcular_cor(params):
    mod = carregar("conversor-temperatura-cor", "ctk_core")
    try:
        r = mod.report(params["kelvin"])
    except (ValueError, ZeroDivisionError) as e:
        return pacote(str(e), str(e))
    resp = f"Mired: {_num(r['mired'])} — {r['label']}"
    return pacote(resp, f"Kelvin {params['kelvin']}. RGB {r.get('rgb')}.")


_registrar("conversor-temperatura-cor", ["mired", "temperatura de cor"], _extrair_cor, _calcular_cor)


def _extrair_forno(texto):
    if not combina(texto, [["forno"]]):
        return None
    nums = [tk.valor for tk in tokens(texto) if tk.tipo in ("solto", "din", "min", "hora")]
    if len(nums) < 3:
        return None
    return {"tempo": nums[0], "antes": nums[1], "depois": nums[2]}


def _calcular_forno(params):
    mod = carregar("formas-bolo", "bol_core")
    try:
        minutos = mod.tempo_forno(params["tempo"], params["antes"], params["depois"])
    except ValueError as e:
        return pacote(str(e), str(e))
    return pacote(
        f"Forno: {minutos} min",
        "Tempo proporcional à raiz da altura, pela função tempo_forno. "
        "Ordem lida: minutos, altura de origem, altura nova.",
    )


_registrar("formas-bolo", ["forno", "forma"], _extrair_forno, _calcular_forno)


def _assinados(texto):
    t = norm(texto).replace(",", ".")
    return [float(x) for x in re.findall(r"[-+]?\d+(?:\.\d+)?", t)]


def _extrair_utm(texto):
    if not combina(texto, [["utm"]]):
        return None
    nums = _assinados(texto)
    if len(nums) < 2:
        return None
    return {"lat": nums[0], "lon": nums[1]}


def _calcular_utm(params):
    mod = carregar("conversor-coordenadas", "geo_core")
    try:
        r = mod.dd_to_utm(params["lat"], params["lon"])
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"UTM {r['zone']}: E {_num(r['easting_m'])} m, N {_num(r['northing_m'])} m"
    return pacote(resp, resp)


_registrar("conversor-coordenadas", ["utm"], _extrair_utm, _calcular_utm)


def _extrair_gms(texto):
    if not combina(texto, [["grau", "graus"], ["minuto", "minutos"]]):
        return None
    if not combina(texto, [["sul", "norte", "leste", "oeste", "coordenada", "latitude", "longitude"]]):
        return None
    nums = [tk.valor for tk in tokens(texto)]
    if len(nums) < 3:
        return None
    t = norm(texto)
    if "sul" in t:
        dire = "S"
    elif "norte" in t:
        dire = "N"
    elif "oeste" in t:
        dire = "W"
    elif "leste" in t:
        dire = "E"
    else:
        dire = "N"
    return {"g": nums[0], "m": nums[1], "s": nums[2], "dire": dire}


def _calcular_gms(params):
    mod = carregar("conversor-coordenadas", "geo_core")
    dd = mod.dms_to_dd(params["g"], params["m"], params["s"], params["dire"])
    return pacote(
        f"Graus decimais: {_num(dd, 6)}",
        f"{int(params['g'])}° {int(params['m'])}' {params['s']}\" {params['dire']}",
    )


_registrar("conversor-coordenadas", ["coordenada", "graus minutos"], _extrair_gms, _calcular_gms)
