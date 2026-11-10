# -*- coding: utf-8 -*-
"""Adaptadores da barra para Ciência & Engenharia.

Cada calcular chama a função do _core. Não refaz a conta.
Ficam de fora: n-corpos, grafos e imports circulares — não respondem
uma frase com número (só preset, amostra ou varredura de pasta).
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


def _sols(texto):
    return [tk.valor for tk in tokens(texto)]


def _escolha(texto, pares, padrao):
    t = norm(texto)
    for chaves, valor in pares:
        if any(c in t for c in chaves):
            return valor
    return padrao


def _tentar(fn, formatar):
    try:
        r = fn()
    except ValueError as e:
        return pacote(str(e), str(e))
    return formatar(r)


def _extrair_molar(texto):
    if not combina(texto, [["massa molar", "molar"]]):
        return None
    if combina(texto, [["balancear", "balanceie"]]):
        return None
    m = re.search(r"(?:[A-Z][a-z]?\d*){2,}|[A-Z][a-z]?\d+", texto)
    if not m:
        return None
    return {"formula": m.group(0)}


def _calcular_molar(params):
    mod = carregar("laboratorio-quimica", "chm_core")
    return _tentar(
        lambda: mod.calculate_molar_mass(params["formula"]),
        lambda r: pacote(
            f"Massa molar: {_num(r['molar_mass_g_mol'])} g/mol",
            f"{r['formula']}: {_num(r['molar_mass_g_mol'])} g/mol",
        ),
    )


_registrar("laboratorio-quimica", ["massa molar"], _extrair_molar, _calcular_molar)


def _extrair_balance(texto):
    if not combina(texto, [["balancear", "balanceie"]]):
        return None
    m = re.search(r"((?:[A-Z][a-z]?\d*)(?:\s*\+\s*[A-Z][a-z]?\d*)*.+)", texto)
    if not m:
        return None
    return {"equacao": m.group(1).strip()}


def _calcular_balance(params):
    mod = carregar("laboratorio-quimica", "chm_core")
    return _tentar(
        lambda: mod.balance_chemical_equation(params["equacao"]),
        lambda r: pacote(r["balanced"], r["balanced"]),
    )


_registrar("laboratorio-quimica", ["balancear equacao"], _extrair_balance, _calcular_balance)


def _extrair_divisor(texto):
    if not combina(texto, [["divisor"]]):
        return None
    return ler(texto, [
        C("vin", ["tensao", "vin"], "num", True),
        C("r1", ["r1"], "num", True),
        C("r2", ["r2"], "num", True),
    ])


def _calcular_divisor(params):
    mod = carregar("simulador-circuitos", "elt_core")
    return _tentar(
        lambda: mod.calc_voltage_divider(params["vin"], params["r1"], params["r2"]),
        lambda r: pacote(f"Saída: {_num(r['vout_unloaded'])} V", str(r["vout_unloaded"])),
    )


_registrar("simulador-circuitos", ["divisor de tensao"], _extrair_divisor, _calcular_divisor)


def _extrair_555(texto):
    if "555" not in norm(texto):
        return None
    return ler(texto, [
        C("r1", ["r1"], "num", True),
        C("r2", ["r2"], "num", True),
        C("c", ["capacitor", "uf"], "num", True),
    ])


def _calcular_555(params):
    mod = carregar("simulador-circuitos", "elt_core")
    return _tentar(
        lambda: mod.calc_ne555_astable(params["r1"], params["r2"], params["c"]),
        lambda r: pacote(
            f"Frequência: {_num(r['frequency_hz'])} Hz",
            "Capacitor lido em µF, como a função calc_ne555_astable espera.",
        ),
    )


_registrar("simulador-circuitos", ["ne555"], _extrair_555, _calcular_555)


def _extrair_serie(texto):
    if not combina(texto, [["resistor"], ["serie"]]):
        return None
    if combina(texto, [["divisor", "555"]]):
        return None
    p = ler(texto, [C("tensao", ["alimentacao", "volts"], "num", True)])
    if not p:
        return None
    ohms = [n for n in _sols(texto) if n != p["tensao"]]
    if len(ohms) < 2:
        return None
    p["ohms"] = ohms
    return p


def _calcular_serie(params):
    mod = carregar("simulador-circuitos", "elt_core")
    return _tentar(
        lambda: mod.solve_resistor_network(params["ohms"], params["tensao"]),
        lambda r: pacote(f"Série: {_num(r['r_series_ohms'])} ohm", str(r["r_series_ohms"])),
    )


_registrar("simulador-circuitos", ["resistores em serie"], _extrair_serie, _calcular_serie)


def _extrair_dna(texto):
    if not combina(texto, [["dna"]]):
        return None
    m = re.search(r"[ACGTUacgtu]{4,}", texto)
    if not m:
        return None
    return {"seq": m.group(0)}


def _calcular_dna(params):
    mod = carregar("laboratorio-dna", "dna_core")
    return _tentar(
        lambda: mod.analyze_dna(params["seq"]),
        lambda r: pacote(f"GC: {_num(r['gc_content_pct'])}%", r["codons_translated"]),
    )


_registrar("laboratorio-dna", ["dna"], _extrair_dna, _calcular_dna)


def _extrair_matriz(texto):
    if not combina(texto, [["matriz", "determinante"]]):
        return None
    i = norm(texto).find("matriz")
    bruto = texto[i + 6:] if i >= 0 else texto
    return {"texto": bruto.replace(";", "\n")}


def _calcular_matriz(params):
    mod = carregar("calculadora-matrizes", "mtx_core")
    return _tentar(
        lambda: mod.analyze_square_matrix(mod.parse_matrix_text(params["texto"])),
        lambda r: pacote(f"Determinante: {_num(r['determinant'])}", r.get("inverse_str", "")),
    )


_registrar("calculadora-matrizes", ["matriz", "determinante"], _extrair_matriz, _calcular_matriz)


def _extrair_stats(texto):
    if not combina(texto, [["estatistica"]]):
        return None
    nums = _sols(texto)
    if len(nums) < 2:
        return None
    return {"nums": nums}


def _calcular_stats(params):
    mod = carregar("laboratorio-estatistica", "stt_core")
    return _tentar(
        lambda: mod.descriptive_stats(params["nums"]),
        lambda r: pacote(f"Média: {_num(r['mean'])}", f"n={r['n']} desvio {_num(r['std_dev'])}"),
    )


_registrar("laboratorio-estatistica", ["estatistica"], _extrair_stats, _calcular_stats)


def _extrair_projetil(texto):
    if not combina(texto, [["projetil", "balistica"]]):
        return None
    return ler(texto, [
        C("v0", ["velocidade", "v0"], "num", True),
        C("angulo", ["angulo"], "num", True),
    ])


def _calcular_projetil(params):
    mod = carregar("simulador-fisica", "fsc_core")
    return _tentar(
        lambda: mod.simulate_projectile(params["v0"], params["angulo"]),
        lambda r: pacote(
            f"Alcance: {_num(r['max_range_m'])} m",
            "Gravidade e altura iniciais são o padrão da função.",
        ),
    )


_registrar("simulador-fisica", ["projetil"], _extrair_projetil, _calcular_projetil)


def _extrair_orbita(texto):
    if not combina(texto, [["orbita", "orbital"]]):
        return None
    return ler(texto, [C("altitude", ["altitude", "km"], "num", True)])


def _calcular_orbita(params):
    mod = carregar("simulador-fisica", "fsc_core")
    return _tentar(
        lambda: mod.calculate_orbital_mechanics(params["altitude"]),
        lambda r: pacote(
            f"Período: {_num(r['orbital_period_min'])} min",
            "Corpo central padrão da função (Terra).",
        ),
    )


_registrar("simulador-fisica", ["orbita"], _extrair_orbita, _calcular_orbita)


def _extrair_snell(texto):
    if not combina(texto, [["snell", "refracao"]]):
        return None
    return ler(texto, [
        C("n1", ["n1"], "num", True),
        C("n2", ["n2"], "num", True),
        C("angulo", ["angulo"], "num", True),
    ])


def _calcular_snell(params):
    mod = carregar("simulador-optica", "opt_core")
    return _tentar(
        lambda: mod.calculate_refraction(params["n1"], params["n2"], params["angulo"]),
        lambda r: pacote(f"Refração: {_num(r['angle_refraction_deg'])}°", str(r["angle_refraction_deg"])),
    )


_registrar("simulador-optica", ["snell"], _extrair_snell, _calcular_snell)


def _extrair_lente(texto):
    if not combina(texto, [["lente"]]):
        return None
    if combina(texto, [["contato", "caixa"]]):
        return None
    t = norm(texto)

    def pegar(rot):
        m = re.search(r"(?<!\w)" + rot + r"\s*([-+]?\d+(?:[.,]\d+)?)", t)
        if not m:
            return None
        return float(m.group(1).replace(",", "."))

    n, r1, r2 = pegar("n"), pegar("r1"), pegar("r2")
    if None in (n, r1, r2):
        return None
    return {"n": n, "r1": r1, "r2": r2}


def _calcular_lente(params):
    mod = carregar("simulador-optica", "opt_core")
    return _tentar(
        lambda: mod.calculate_lens_focal(params["n"], params["r1"], params["r2"]),
        lambda r: pacote(f"Dioptria: {_num(r['diopters'])}", r["lens_type"]),
    )


_registrar("simulador-optica", ["lente"], _extrair_lente, _calcular_lente)


def _extrair_comb(texto):
    if not combina(texto, [["combinacao", "arranjo", "permutacao"]]):
        return None
    if combina(texto, [["mega", "quina", "lotofacil", "loteria"]]):
        return None
    return ler(texto, [
        C("k", ["escolhe"], "int", True),
        C("n", ["combinacao", "arranjo", "permutacao"], "int", True),
    ])


def _calcular_comb(params):
    mod = carregar("calculadora-combinatoria", "cmb_core")
    return _tentar(
        lambda: mod.calculate_combinatorics(params["n"], params["k"]),
        lambda r: pacote(f"C(n,k): {r['combinations_c_n_k']}", str(r["arrangements_a_n_k"])),
    )


_registrar("calculadora-combinatoria", ["combinacao"], _extrair_comb, _calcular_comb)


def _extrair_loto(texto):
    if not combina(texto, [["mega", "quina", "lotofacil", "loteria"]]):
        return None
    t = norm(texto)
    if "lotofacil" in t:
        n, k, nome = 25, 15, "Lotofácil"
    elif "quina" in t:
        n, k, nome = 80, 5, "Quina"
    else:
        n, k, nome = 60, 6, "Mega-Sena"
    return {"n": n, "k": k, "nome": nome}


def _calcular_loto(params):
    mod = carregar("calculadora-combinatoria", "cmb_core")
    return _tentar(
        lambda: mod.calculate_lottery_odds(params["n"], params["k"]),
        lambda r: pacote(
            r["odds_ratio"],
            f"{params['nome']}: {params['n']} dezenas, {params['k']} sorteadas. Regra do jogo, não chute.",
        ),
    )


_registrar("calculadora-combinatoria", ["mega sena", "loteria"], _extrair_loto, _calcular_loto)


def _extrair_viga(texto):
    if not combina(texto, [["viga"]]):
        return None
    return ler(texto, [
        C("bw", ["bw"], "num", True),
        C("h", ["altura"], "num", True),
        C("d", ["cobrimento"], "num", True),
        C("fck", ["fck"], "num", True),
        C("fyk", ["fyk"], "num", True),
        C("mk", ["momento", "mk"], "num", True),
    ])


def _calcular_viga(params):
    mod = carregar("calculadora-concreto-armado", "cnc_core")
    return _tentar(
        lambda: mod.calculate_beam_flexure(
            params["bw"], params["h"], params["d"], params["fck"], params["fyk"], params["mk"]
        ),
        lambda r: pacote(f"As: {_num(r['as_adopted_cm2'])} cm²", r["domain"]),
    )


_registrar("calculadora-concreto-armado", ["viga"], _extrair_viga, _calcular_viga)


def _extrair_huff(texto):
    if not combina(texto, [["huffman"]]):
        return None
    m = re.search(r"texto\s+(.+)$", texto, re.I)
    if not m:
        return None
    return {"texto": m.group(1).strip()}


def _calcular_huff(params):
    mod = carregar("estudio-compressao-huffman", "huf_core")
    texto = params["texto"]

    def rodar():
        arvore = mod.build_huffman_tree(texto)
        codigos = mod.generate_huffman_codes(arvore)
        return mod.compute_entropy_and_metrics(texto, codigos)

    return _tentar(
        rodar,
        lambda r: pacote(f"Entropia: {_num(r['entropy'])} bit", f"Economia {_num(r['savings_pct'])}%"),
    )


_registrar("estudio-compressao-huffman", ["huffman"], _extrair_huff, _calcular_huff)


def _extrair_wolf(texto):
    if not combina(texto, [["wolfram", "automato"]]):
        return None
    return ler(texto, [C("regra", ["regra"], "int", True)])


def _calcular_wolf(params):
    mod = carregar("simulador-automato-celular", "cll_core")
    grade = mod.simulate_wolfram_1d(params["regra"])
    pop = sum(grade[-1])
    return pacote(
        f"Células vivas na última linha: {pop}",
        "Largura 101 e 60 passos, padrão da função simulate_wolfram_1d.",
    )


_registrar("simulador-automato-celular", ["wolfram"], _extrair_wolf, _calcular_wolf)


def _extrair_benford(texto):
    if not combina(texto, [["benford"]]):
        return None
    nums = _sols(texto)
    if len(nums) < 2:
        return None
    return {"nums": nums}


def _calcular_benford(params):
    mod = carregar("analisador-benford", "bnf_core")
    return _tentar(
        lambda: mod.analyze_benford(params["nums"]),
        lambda r: pacote(f"MAD: {r['mad']}", r.get("conformidade", r.get("mad_label", str(r["mad"])))),
    )


_registrar("analisador-benford", ["benford"], _extrair_benford, _calcular_benford)


def _extrair_zn(texto):
    if not combina(texto, [["ziegler"]]):
        return None
    return ler(texto, [
        C("ku", ["ku"], "num", True),
        C("pu", ["pu"], "num", True),
    ])


def _calcular_zn(params):
    mod = carregar("simulador-controle-pid", "pid_core")
    return _tentar(
        lambda: mod.ziegler_nichols_pid(params["ku"], params["pu"]),
        lambda r: pacote(f"Kp: {_num(r['kp'])}", f"Ki {_num(r['ki'])} Kd {_num(r['kd'])}"),
    )


_registrar("simulador-controle-pid", ["ziegler nichols"], _extrair_zn, _calcular_zn)


def _extrair_darcy(texto):
    if not combina(texto, [["darcy", "perda de carga"]]):
        return None
    return ler(texto, [
        C("vazao", ["vazao"], "num", True),
        C("diametro", ["diametro"], "num", True),
        C("comprimento", ["comprimento"], "num", True),
    ])


def _calcular_darcy(params):
    mod = carregar("calculadora-hidraulica-tubulacoes", "hdr_core")
    return _tentar(
        lambda: mod.calculate_darcy_weisbach(params["vazao"], params["diametro"], params["comprimento"]),
        lambda r: pacote(f"Regime: {r['regime']}", f"Perda {_num(r['head_loss_mca'])} mca"),
    )


_registrar("calculadora-hidraulica-tubulacoes", ["darcy"], _extrair_darcy, _calcular_darcy)


def _farad(texto, valor):
    t = norm(texto)
    if "micro" in t:
        return valor * 1e-6
    return valor


def _extrair_rc(texto):
    if not combina(texto, [["filtro"], ["rc"]]):
        return None
    if combina(texto, [["rlc"]]):
        return None
    p = ler(texto, [
        C("r", ["resistencia"], "num", True),
        C("c", ["capacitor"], "num", True),
    ])
    if not p:
        return None
    p["c"] = _farad(texto, p["c"])
    return p


def _calcular_rc(params):
    mod = carregar("simulador-circuitos-rc-rlc", "rlc_core")
    return _tentar(
        lambda: mod.calculate_rc_filter(params["r"], params["c"]),
        lambda r: pacote(f"Corte: {_num(r['cutoff_freq_hz'])} Hz", "Capacitor em farad. 'micro' vira µF."),
    )


_registrar("simulador-circuitos-rc-rlc", ["filtro rc"], _extrair_rc, _calcular_rc)


def _extrair_rlc(texto):
    if not combina(texto, [["rlc"]]):
        return None
    p = ler(texto, [
        C("r", ["resistencia"], "num", True),
        C("l", ["indutor"], "num", True),
        C("c", ["capacitor"], "num", True),
    ])
    if not p:
        return None
    p["c"] = _farad(texto, p["c"])
    return p


def _calcular_rlc(params):
    mod = carregar("simulador-circuitos-rc-rlc", "rlc_core")
    return _tentar(
        lambda: mod.calculate_rlc_series(params["r"], params["l"], params["c"]),
        lambda r: pacote(f"f0: {_num(r['f0_hz'])} Hz", r["damping_type"]),
    )


_registrar("simulador-circuitos-rc-rlc", ["rlc"], _extrair_rlc, _calcular_rlc)


def _extrair_pi(texto):
    if not combina(texto, [["monte carlo"]]):
        return None
    p = ler(texto, [C("n", ["amostras", "n"], "int", False, 100000)])
    return p or {"n": 100000}


def _calcular_pi(params):
    mod = carregar("simulador-monte-carlo", "mtc_core")
    r = mod.estimate_pi(int(params["n"]))
    return pacote(
        f"pi ≈ {_num(r['pi_estimate'], 4)}",
        "Semente 42, padrão da função estimate_pi.",
    )


_registrar("simulador-monte-carlo", ["monte carlo"], _extrair_pi, _calcular_pi)


def _extrair_quat(texto):
    if not combina(texto, [["quaternion", "quaternio"]]):
        return None
    t = norm(texto).replace(",", ".")
    nums = [float(x) for x in re.findall(r"[-+]?\d+(?:\.\d+)?", t)]
    if len(nums) < 4:
        return None
    return {"w": nums[0], "x": nums[1], "y": nums[2], "z": nums[3]}


def _calcular_quat(params):
    mod = carregar("calculadora-quaternions", "qtn_core")
    q = mod.q_new(params["w"], params["x"], params["y"], params["z"])
    r = mod.analyze(q)
    return pacote(f"Norma: {_num(r['norm'])}", r["text"])


_registrar("calculadora-quaternions", ["quaternion"], _extrair_quat, _calcular_quat)


def _cidades(texto):
    mod = carregar("planetario", "ast_core")
    t = norm(texto)
    achados = []
    for nome in mod.CITIES_BR:
        curto = norm(nome.split(",")[0])
        i = t.find(curto)
        if i >= 0:
            achados.append((i, nome))
    achados.sort()
    vistos = []
    for _, nome in achados:
        if nome not in vistos:
            vistos.append(nome)
    return vistos


def _extrair_nav(texto):
    if not combina(texto, [["distancia", "ortodromica", "haversine"]]):
        return None
    if combina(texto, [["focal", "lente"]]):
        return None
    cidades = _cidades(texto)
    if len(cidades) < 2:
        return None
    return {"origem": cidades[0], "destino": cidades[1]}


def _calcular_nav(params):
    astm = carregar("planetario", "ast_core")
    mod = carregar("navegacao", "nav_core")
    a = astm.CITIES_BR[params["origem"]]
    b = astm.CITIES_BR[params["destino"]]
    km = mod.haversine_km(a[0], a[1], b[0], b[1])
    return pacote(
        f"Distância: {_num(km)} km",
        f"{params['origem']} → {params['destino']}, coordenadas do planetário.",
    )


_registrar("navegacao", ["distancia", "ortodromica"], _extrair_nav, _calcular_nav)


def _extrair_ceu(texto):
    if not combina(texto, [["nascer do sol", "por do sol", "fase da lua"]]):
        return None
    cidades = _cidades(texto)
    if not cidades:
        return None
    return {"cidade": cidades[0]}


def _calcular_ceu(params):
    mod = carregar("planetario", "ast_core")
    lat, lon, tz = mod.CITIES_BR[params["cidade"]]
    r = mod.compute_sky_report(lat, lon, tz_offset=tz)
    return pacote(
        f"Nascer do sol: {r['sunrise']}",
        f"{params['cidade']}. Pôr {r['sunset']}. {r['moon']['phase_name']}.",
    )


_registrar("planetario", ["nascer do sol"], _extrair_ceu, _calcular_ceu)


def _extrair_trf(texto):
    if not combina(texto, [["transformador"]]):
        return None
    return ler(texto, [
        C("va", ["va", "potencia"], "num", True),
        C("vp", ["primario"], "num", True),
        C("vs", ["secundario"], "num", True),
    ])


def _calcular_trf(params):
    mod = carregar("calculadora-transformador-potencia", "trf_core")
    return _tentar(
        lambda: mod.design_transformer(params["va"], params["vp"], params["vs"]),
        lambda r: pacote(f"Espiras primário: {r['n_primary']}", f"Secundário {r['n_secondary']}"),
    )


_registrar("calculadora-transformador-potencia", ["transformador"], _extrair_trf, _calcular_trf)


def _extrair_parede(texto):
    if not combina(texto, [["parede", "valor u", "transmitancia"]]):
        return None
    p = ler(texto, [C("esp", ["espessura"], "num", True)])
    if not p:
        return None
    if "cm" in norm(texto):
        p["esp"] = p["esp"] / 100.0
    p["mat"] = _escolha(texto, [
        (("isopor", "eps"), "EPS Poliestireno Expandido (Isopor)"),
        (("poliuretano",), "Poliuretano Expandido (PU)"),
        (("la de vidro", "isolante"), "Lã de Vidro / Rocha (Isolante)"),
        (("reboco", "argamassa"), "Argamassa de Reboco"),
        (("gesso",), "Gesso Acartonado (Drywall)"),
        (("madeira",), "Madeira Compensada"),
        (("concreto",), "Concreto Armado"),
        (("vidro",), "Vidro Comum"),
        (("tijolo",), "Tijolo Cerâmico Furado"),
    ], "Tijolo Cerâmico Furado")
    return p


def _calcular_parede(params):
    mod = carregar("analisador-difusao-calor", "thm_core")
    k = mod.DEFAULT_MATERIALS[params["mat"]]
    camada = mod.WallLayer(params["mat"], params["esp"], k)
    return _tentar(
        lambda: mod.calculate_thermal_gradient([camada]),
        lambda r: pacote(
            f"U: {_num(r['u_value'], 4)} W/m²K",
            f"{params['mat']}, {params['esp']} m. Temperaturas e h são o padrão da função.",
        ),
    )


_registrar("analisador-difusao-calor", ["parede", "valor u"], _extrair_parede, _calcular_parede)


def _extrair_lorem(texto):
    if not combina(texto, [["lorem"]]):
        return None
    p = ler(texto, [C("n", ["palavras", "palavra"], "int", False, 8)])
    return p or {"n": 8}


def _calcular_lorem(params):
    mod = carregar("gerador-lorem", "lor_core")
    try:
        frase = mod.generate_words(int(params["n"]))
    except ValueError as e:
        return pacote(str(e), str(e))
    return pacote(frase, "Semente 42, padrão de generate_words.")


_registrar("gerador-lorem", ["lorem"], _extrair_lorem, _calcular_lorem)


def _extrair_naca(texto):
    if not combina(texto, [["naca"]]):
        return None
    m = re.search(r"(\d{4})", texto)
    if not m:
        return None
    return {"codigo": m.group(1)}


def _calcular_naca(params):
    mod = carregar("analisador-perfil-aerodinamico-naca", "nca_core")
    return _tentar(
        lambda: mod.generate_naca_airfoil(params["codigo"]),
        lambda r: pacote(
            f"Camber: {_num(r['max_camber_pct'])}%",
            f"NACA {r['code']}, espessura {_num(r['max_thickness_pct'])}%.",
        ),
    )


_registrar("analisador-perfil-aerodinamico-naca", ["naca"], _extrair_naca, _calcular_naca)


def _extrair_cinetica(texto):
    if not combina(texto, [["cinetica", "meia-vida", "meia vida"]]):
        return None
    if combina(texto, [["arrhenius"]]):
        return None
    return ler(texto, [
        C("ordem", ["ordem"], "int", True),
        C("conc", ["concentracao"], "num", True),
        C("k", ["k"], "num", True),
    ])


def _calcular_cinetica(params):
    mod = carregar("calculadora-cinetica-quimica", "knt_core")
    return _tentar(
        lambda: mod.calculate_reaction_kinetics(params["ordem"], params["conc"], params["k"]),
        lambda r: pacote(f"Meia-vida: {_num(r['t_half_s'])} s", r["integrated_equation"]),
    )


_registrar("calculadora-cinetica-quimica", ["cinetica"], _extrair_cinetica, _calcular_cinetica)


def _extrair_arr(texto):
    if not combina(texto, [["arrhenius"]]):
        return None
    return ler(texto, [
        C("k1", ["k"], "num", True),
        C("t1", ["t1"], "num", True),
        C("t2", ["t2"], "num", True),
        C("ea", ["ea"], "num", True),
    ])


def _calcular_arr(params):
    mod = carregar("calculadora-cinetica-quimica", "knt_core")
    return _tentar(
        lambda: mod.arrhenius_temperature_shift(params["k1"], params["t1"], params["t2"], params["ea"]),
        lambda r: pacote(f"k2: {_num(r)}", "Temperaturas em Celsius, Ea em kJ/mol."),
    )


_registrar("calculadora-cinetica-quimica", ["arrhenius"], _extrair_arr, _calcular_arr)


def _extrair_trelica(texto):
    if not combina(texto, [["trelica"]]):
        return None
    t = norm(texto)
    if "pratt" in t:
        tipo = "pratt"
    elif "howe" in t:
        tipo = "howe"
    elif "fink" in t:
        tipo = "fink"
    elif "balanco" in t or "cantilever" in t:
        tipo = "cantilever"
    else:
        tipo = "warren"
    p = ler(texto, [
        C("vao", ["vao"], "num", False, 12.0),
        C("altura", ["altura"], "num", False, 3.0),
        C("paineis", ["paineis", "painel"], "int", False, 4),
        C("carga", ["carga"], "num", False, 50.0),
    ])
    if p is None:
        return None
    p["tipo"] = tipo
    return p


def _calcular_trelica(params):
    mod = carregar("calculadora-trelicas-2d", "trs_core")
    tipo = params["tipo"]
    if tipo == "fink":
        tr = mod.create_fink_roof_truss(span=params["vao"], height=params["altura"], load_kn=params["carga"])
    elif tipo == "cantilever":
        tr = mod.create_cantilever_truss(
            length=params["vao"], height=params["altura"],
            panels=params["paineis"], tip_load_kn=params["carga"],
        )
    else:
        fn = {"warren": mod.create_warren_truss, "pratt": mod.create_pratt_truss, "howe": mod.create_howe_truss}[tipo]
        tr = fn(span=params["vao"], height=params["altura"], panels=params["paineis"], load_kn=params["carga"])
    r = tr.solve()
    return pacote(
        f"Treliça {tipo}: {r.static_determinacy}",
        "Vão, altura, painéis e carga omitidos usam o padrão da função (12 m, 3 m, 4, 50 kN).",
    )


_registrar("calculadora-trelicas-2d", ["trelica"], _extrair_trelica, _calcular_trelica)


_MAT_EUL = (
    (("aluminio",), "Alumínio Estrutural 6061-T6"),
    (("madeira",), "Madeira Estrutural (Paraju / Eucalipto)"),
    (("titanio",), "Titânio Grau 5 (Ti-6Al-4V)"),
    (("nodular", "fundido"), "Ferro Fundido Nodular"),
    (("alta resistencia",), "Aço de Alta Resistência (500 MPa)"),
    (("aco",), "Aço Estrutural ASTM A36"),
)


def _extrair_euler(texto):
    if not combina(texto, [["flambagem", "euler"]]):
        return None
    p = ler(texto, [
        C("comprimento", ["comprimento"], "num", True),
        C("diametro", ["diametro"], "num", True),
    ])
    if not p:
        return None
    t = norm(texto)
    if "tubo" in t or "tubular" in t:
        p["sec"] = "tubular_circular"
    elif "retang" in t:
        p["sec"] = "retangular"
    else:
        p["sec"] = "circular_macica"
    if "balanco" in t or "livre" in t:
        p["bc"] = "Engastada-Livre (Balanço)"
    elif "bi-engast" in t or "engaste-engaste" in t:
        p["bc"] = "Bi-engastada (Engaste-Engaste)"
    else:
        p["bc"] = "Bi-articulada (Pino-Pino)"
    p["mat"] = _escolha(texto, _MAT_EUL, "Aço Estrutural ASTM A36")
    return p


def _calcular_euler(params):
    mod = carregar("calculadora-flambagem-colunas-euler", "eul_core")
    e, sy = mod.STRUCTURAL_MATERIALS[params["mat"]]
    return _tentar(
        lambda: mod.calculate_buckling(
            params["comprimento"], params["bc"], e, sy, params["sec"], params["diametro"]
        ),
        lambda r: pacote(
            f"Pcr: {_num(r['p_cr_kn'])} kN",
            f"{params['mat']}. Vínculo {params['bc']}. Seção {params['sec']}.",
        ),
    )


_registrar("calculadora-flambagem-colunas-euler", ["flambagem"], _extrair_euler, _calcular_euler)


def _extrair_lc(texto):
    if not combina(texto, [["thomson"]]) and not combina(texto, [["circuito"], ["lc"]]):
        return None
    if combina(texto, [["rlc"]]):
        return None
    p = ler(texto, [
        C("l", ["indutor"], "num", True),
        C("c", ["capacitor"], "num", True),
    ])
    if not p:
        return None
    p["c"] = _farad(texto, p["c"])
    return p


def _calcular_lc(params):
    mod = carregar("analisador-circuito-ressonante-lc", "rls_core")
    return _tentar(
        lambda: mod.calculate_resonance(params["l"], params["c"]),
        lambda r: pacote(
            f"f0: {_num(r['f_0_hz'])} Hz",
            "Resistência 10 ohm, padrão da função. Q e banda saem dela.",
        ),
    )


_registrar("analisador-circuito-ressonante-lc", ["thomson", "circuito lc"], _extrair_lc, _calcular_lc)


_MAT_DLT = (
    (("inox",), "Aço Inoxidável AISI 304"),
    (("aluminio",), "Alumínio"),
    (("cobre",), "Cobre"),
    (("latao",), "Latão"),
    (("concreto",), "Concreto Armado"),
    (("pyrex", "borossilicato"), "Vidro Borossilicato (Pyrex)"),
    (("invar",), "Invar (Liga Fe-Ni 36)"),
    (("vidro",), "Vidro Comum (Janela)"),
    (("aco",), "Aço Estrutural / Carbono"),
)


def _extrair_dlt(texto):
    if not combina(texto, [["dilatacao"]]):
        return None
    p = ler(texto, [
        C("comp", ["comprimento"], "num", True),
        C("t1", ["inicial"], "num", True),
        C("t2", ["final"], "num", True),
    ])
    if not p:
        return None
    p["mat"] = _escolha(texto, _MAT_DLT, "Aço Estrutural / Carbono")
    return p


def _calcular_dlt(params):
    mod = carregar("calculadora-dilatacao-termica-tensao", "dlt_core")
    return _tentar(
        lambda: mod.calculate_thermal_expansion(params["mat"], params["comp"], params["t1"], params["t2"]),
        lambda r: pacote(
            f"Dilatação: {_num(r['delta_l_free_mm'])} mm",
            f"{params['mat']}. Área e folga são o padrão da função.",
        ),
    )


_registrar("calculadora-dilatacao-termica-tensao", ["dilatacao"], _extrair_dlt, _calcular_dlt)


def _extrair_bitola(texto):
    if not combina(texto, [["bitola", "disjuntor"]]):
        return None
    return ler(texto, [
        C("pot", ["watts", "watt"], "num", True),
        C("v", ["volts", "volt"], "num", True),
        C("m", ["metros", "metro"], "num", True),
    ])


def _calcular_bitola(params):
    mod = carregar("calculadora-eletrica-residencial", "ele_core")
    return _tentar(
        lambda: mod.dimensionar(params["pot"], params["v"], params["m"]),
        lambda r: pacote(
            f"Seção: {_num(r['secao'])} mm², disjuntor {r['disjuntor']} A",
            "Demais fatores são o padrão de dimensionar.",
        ),
    )


_registrar("calculadora-eletrica-residencial", ["bitola"], _extrair_bitola, _calcular_bitola)


def _extrair_ham(texto):
    if not combina(texto, [["hamming"]]):
        return None
    nums = [int(round(n)) for n in _sols(texto)]
    if len(nums) < 4:
        return None
    return {"bits": nums[:4]}


def _calcular_ham(params):
    mod = carregar("estudio-codigo-hamming-ecc", "ham_core")
    b = params["bits"]
    bloco = mod.codificar_bloco_74(*b)
    return pacote("Hamming: " + " ".join(str(x) for x in bloco), "Bloco (7,4).")


_registrar("estudio-codigo-hamming-ecc", ["hamming"], _extrair_ham, _calcular_ham)


def _extrair_reator(texto):
    if not combina(texto, [["reator", "cstr", "pfr"]]):
        return None
    return ler(texto, [
        C("x", ["conversao"], "num", True),
        C("ca0", ["ca0"], "num", True),
        C("vazao", ["vazao"], "num", True),
        C("k", ["constante"], "num", True),
    ])


def _calcular_reator(params):
    mod = carregar("simulador-reatores-quimicos", "rea_core")
    return _tentar(
        lambda: mod.calcular_reatores(params["x"], params["ca0"], params["vazao"], params["k"]),
        lambda r: pacote(
            f"CSTR: {_num(r['volume_cstr_l'])} L",
            "Ordem 1, padrão da função.",
        ),
    )


_registrar("simulador-reatores-quimicos", ["reator"], _extrair_reator, _calcular_reator)


def _extrair_manning(texto):
    if not combina(texto, [["manning"]]):
        return None
    return ler(texto, [
        C("base", ["base"], "num", True),
        C("talude", ["talude"], "num", True),
        C("decliv", ["declividade"], "num", True),
        C("n", ["rugosidade"], "num", True),
        C("vazao", ["vazao"], "num", True),
    ])


def _calcular_manning(params):
    mod = carregar("calculadora-canais-abertos-manning", "can_core")
    return _tentar(
        lambda: mod.analisar_canal_completo(
            params["base"], params["talude"], params["decliv"], params["n"],
            modo_entrada="vazao", valor_entrada=params["vazao"],
        ),
        lambda r: pacote(f"Regime: {r['regime']}", f"Lâmina {_num(r['profundidade_y_m'])} m"),
    )


_registrar("calculadora-canais-abertos-manning", ["manning"], _extrair_manning, _calcular_manning)


def _extrair_mola(texto):
    if not combina(texto, [["mola"]]):
        return None
    return ler(texto, [
        C("fio", ["fio"], "num", True),
        C("externo", ["externo"], "num", True),
        C("espiras", ["espiras"], "num", True),
        C("livre", ["livre"], "num", True),
        C("forca", ["forca"], "num", True),
    ])


def _calcular_mola(params):
    mod = carregar("projeto-molas-helicoidais", "mol_core")
    return _tentar(
        lambda: mod.calcular_mola_compressao(
            params["fio"], params["externo"], params["espiras"], params["livre"], params["forca"]
        ),
        lambda r: pacote(
            f"Rigidez: {_num(r['rigidez_k_n_mm'], 3)} N/mm",
            "Material e extremidade são o padrão da função.",
        ),
    )


_registrar("projeto-molas-helicoidais", ["mola"], _extrair_mola, _calcular_mola)


def _extrair_doppler(texto):
    if not combina(texto, [["doppler"]]):
        return None
    return ler(texto, [
        C("f", ["frequencia"], "num", True),
        C("vs", ["fonte"], "num", True),
    ])


def _calcular_doppler(params):
    mod = carregar("simulador-efeito-doppler-mach", "dop_core")
    return _tentar(
        lambda: mod.calcular_doppler_acustico(params["f"], params["vs"], 0),
        lambda r: pacote(
            f"Frequência: {_num(r['frequencia_percebida_hz'])} Hz",
            "Observador parado (0 m/s). Som no ar, padrão da função.",
        ),
    )


_registrar("simulador-efeito-doppler-mach", ["doppler"], _extrair_doppler, _calcular_doppler)


def _extrair_qol(texto):
    if not combina(texto, [["qualidade de vida"]]):
        return None
    return ler(texto, [
        C("saude_fisica", ["saude"], "int", True),
        C("sono", ["sono"], "int", True),
        C("humor", ["humor"], "int", True),
        C("relacoes", ["relacoes"], "int", True),
        C("lazer", ["lazer"], "int", True),
        C("sentido", ["sentido", "proposito"], "int", True),
    ])


def _calcular_qol(params):
    mod = carregar("indice-qualidade-vida-semanal", "qol_core")
    try:
        r = mod.calcular_indice_qol(params)
    except Exception as e:
        if type(e).__name__ in ("ErroQol", "ValueError"):
            return pacote(str(e), str(e))
        raise
    return pacote(r.resumo, r.dica)


_registrar("indice-qualidade-vida-semanal", ["qualidade de vida"], _extrair_qol, _calcular_qol)


def _extrair_glc(texto):
    if not combina(texto, [["glicemia"]]):
        return None
    nums = _sols(texto)
    if not nums:
        return None
    linhas = []
    for n in nums:
        linhas.append(str(int(n)) if float(n).is_integer() else str(n))
    return {"texto": "\n".join(linhas)}


def _calcular_glc(params):
    mod = carregar("media-glicemia-capilar", "glc_core")
    return _tentar(
        lambda: mod.analisar(params["texto"]),
        lambda r: pacote(
            f"Média: {_num(next(iter(r['grupos'].values()))['estatisticas']['media'])} mg/dL",
            "Medidas sem jejum/pós vão para o grupo indefinido da ferramenta.",
        ),
    )


_registrar("media-glicemia-capilar", ["glicemia"], _extrair_glc, _calcular_glc)


_MAT_FTR = (
    (("cobre",), "Cobre Eletrolitico Puro"),
    (("aluminio",), "Liga de Aluminio 2024-T6"),
    (("vidro",), "Vidro Comum (Janela)"),
    (("carne",), "Carne Bovina / Tecido Biologico"),
    (("aco",), "Aco Carbono AISI 1010"),
)


def _extrair_ftr(texto):
    if not combina(texto, [["transiente", "biot"]]):
        return None
    p = ler(texto, [
        C("dim", ["dimensao"], "num", True),
        C("h", ["conveccao"], "num", True),
        C("ti", ["inicial"], "num", True),
        C("tf", ["fluido"], "num", True),
        C("tempo", ["tempo"], "num", True),
    ])
    if not p:
        return None
    t = norm(texto)
    if "esfera" in t:
        p["geo"] = "esfera"
    elif "cilindro" in t:
        p["geo"] = "cilindro"
    else:
        p["geo"] = "placa"
    p["mat"] = _escolha(texto, _MAT_FTR, "Aco Carbono AISI 1010")
    return p


def _calcular_ftr(params):
    mod = carregar("conducao-termica-transiente-fourier", "ftr_core")
    return _tentar(
        lambda: mod.calcular_transiente_termico(
            params["mat"], params["geo"], params["dim"], params["h"],
            params["ti"], params["tf"], params["tempo"],
        ),
        lambda r: pacote(f"Centro: {_num(r['t_centro_c'])} °C", f"Biot {_num(r['biot_global'], 4)}"),
    )


_registrar("conducao-termica-transiente-fourier", ["transiente", "biot"], _extrair_ftr, _calcular_ftr)
