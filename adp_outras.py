# -*- coding: utf-8 -*-
"""Adaptadores da barra para a categoria Outras.

Cada calcular chama o modulo real. Nao refaz a conta. Ficam de fora geradores
de arquivo, inspetores, checklists e o que so varre disco ou guarda cadastro.
"""
from __future__ import annotations

import base64
import math
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
_brl = af._brl
tokens = af.tokens

ADAPTADORES = []


def _registrar(chave, palavras, extrair, calcular):
    ADAPTADORES.append({
        "chave": chave,
        "palavras": list(palavras),
        "extrair": extrair,
        "calcular": calcular,
    })


def _chamar(fn):
    try:
        return fn()
    except ValueError as e:
        return pacote(str(e).splitlines()[0], "A ferramenta recusou esses dados.")


def _sair(resposta, detalhe, titulo):
    d = pacote(resposta, detalhe)
    d["titulo"] = titulo
    return d


def _so(texto, gatilhos, spec):
    if isinstance(gatilhos, str):
        gatilhos = (gatilhos,)
    if not combina(texto, [tuple(gatilhos)]):
        return None
    params = ler(texto, spec)
    if not params:
        return None
    params["_confianca"] = 0.93
    return params


def _numero_depois(texto, marcas):
    if not combina(texto, [tuple(marcas)]):
        return None
    t = norm(texto)
    ini = None
    for marca in marcas:
        i = t.find(norm(marca))
        if i < 0:
            continue
        fim = i + len(norm(marca))
        if ini is None or fim < ini:
            ini = fim
    if ini is None:
        return None
    for tk in tokens(texto):
        if tk.ini >= ini:
            return tk.valor
    return None


def _extrair_iptu(texto):
    return _so(texto, ("iptu",), [
        C("venal", ["venal", "imovel"], "num", True),
        C("aliquota", ["aliquota"], "pct", True),
        C("desconto", ["desconto"], "pct", False, 0.0),
        C("parcelas", ["parcelas", "vezes"], "int", False, 1),
    ])


def _calcular_iptu(params):
    def fazer():
        mod = carregar("calculadora-iptu", "ipt_core")
        r = mod.calcular(
            params["venal"], params["aliquota"],
            params.get("desconto", 0.0), int(params.get("parcelas", 1)),
        )
        return _sair(_brl(r["liquido"]), "IPTU do ano, com a aliquota municipal.", "IPTU")
    return _chamar(fazer)


def _extrair_caucao(texto):
    return _so(texto, ("caucao",), [
        C("taxa", ["taxa", "cdi"], "pct", False, 0.8),
        C("meses", ["meses de caucao", "meses"], "int", False, 3),
        C("contrato", ["contrato"], "int", False, 30),
        C("aluguel", ["aluguel"], "num", True),
    ])


def _calcular_caucao(params):
    def fazer():
        mod = carregar("calculadora-caucao", "cau_core")
        r = mod.calcular(
            params["aluguel"], params.get("meses", 3),
            int(params.get("contrato", 30)), params.get("taxa", 0.8),
        )
        return _sair(_brl(r["deposito"]), "Deposito. O rendimento e o custo de deixar parado.", "Caucao")
    return _chamar(fazer)


def _extrair_caixa(texto):
    return _so(texto, ("caixa dagua", "caixa d'agua", "caixa d agua"), [
        C("volume", ["volume", "litros"], "num", True),
        C("pessoas", ["pessoas", "pessoa"], "int", True),
        C("por_pessoa", ["por pessoa", "cada"], "num", False, 150.0),
    ])


def _calcular_caixa(params):
    def fazer():
        mod = carregar("autonomia-caixa-dagua", "cda_core")
        r = mod.autonomia(
            params["volume"], int(params["pessoas"]), params.get("por_pessoa", 150.0),
        )
        return _sair(
            _num(r["dias"], 1) + " dias",
            "Autonomia com a caixa cheia.",
            "Caixa d'agua",
        )
    return _chamar(fazer)


def _extrair_limpeza(texto):
    return _so(texto, ("diluir limpeza", "diluicao de limpeza", "diluicao limpeza"), [
        C("produto", ["produto", "concentrado"], "pct", True),
        C("desejada", ["desejada", "final"], "pct", True),
        C("volume", ["volume", "ml"], "num", True),
    ])


def _calcular_limpeza(params):
    def fazer():
        mod = carregar("diluicao-limpeza", "dil_core")
        r = mod.diluir(params["produto"], params["desejada"], params["volume"])
        return _sair(
            _num(r["produto_ml"], 1) + " ml",
            "De produto. O resto e agua, ate o volume final.",
            "Diluicao de limpeza",
        )
    return _chamar(fazer)


def _extrair_extenso(texto):
    n = _numero_depois(texto, ("por extenso",))
    if n is None:
        return None
    return {"n": int(round(n)), "_confianca": 0.93}


def _calcular_extenso(params):
    def fazer():
        mod = carregar("numero-extenso", "ext_core")
        return _sair(mod.extenso(params["n"]), "Por extenso, em portugues.", "Numero por extenso")
    return _chamar(fazer)


def _extrair_romano(texto):
    n = _numero_depois(texto, ("algarismo romano", "algarismos romanos", "em romanos", "numero romano"))
    if n is None:
        return None
    return {"n": int(round(n)), "_confianca": 0.93}


def _calcular_romano(params):
    def fazer():
        mod = carregar("numero-extenso", "ext_core")
        return _sair(mod.to_roman(params["n"]), "Algarismo romano classico, de 1 a 3999.", "Numeros romanos")
    return _chamar(fazer)


def _extrair_reajuste(texto):
    return _so(texto, ("reajuste de aluguel", "reajuste do aluguel", "reajustar aluguel"), [
        C("percentual", ["percentual", "indice"], "pct", True),
        C("aluguel", ["aluguel", "valor"], "num", True),
    ])


def _calcular_reajuste(params):
    def fazer():
        mod = carregar("reajuste-aluguel", "alu_core")
        novo, aumento = mod.reajustar(params["aluguel"], params["percentual"])
        return _sair(_brl(novo), "Novo aluguel. Aumento de " + _brl(aumento) + ".", "Reajuste de aluguel")
    return _chamar(fazer)


def _extrair_btu(texto):
    return _so(texto, ("ar condicionado", "ar-condicionado"), [
        C("area", ["area", "m2"], "num", True),
        C("pessoas", ["pessoas", "pessoa"], "int", False, 1),
        C("aparelhos", ["aparelhos", "aparelho"], "int", False, 0),
    ])


def _calcular_btu(params):
    def fazer():
        mod = carregar("calculadora-ar-condicionado", "btu_core")
        bruto = mod.btu_necessario(
            params["area"], int(params.get("pessoas", 1)), int(params.get("aparelhos", 0)),
        )
        modelo = mod.modelo_comercial(bruto)
        if modelo:
            resp = _num(modelo, 0) + " BTU"
        else:
            resp = _num(bruto, 0) + " BTU"
        return _sair(resp, "Conta da ferramenta: " + _num(bruto, 0) + " BTU.", "Ar-condicionado")
    return _chamar(fazer)


def _extrair_chuveiro(texto):
    return _so(texto, ("conta do chuveiro", "chuveiro eletrico", "gasto do chuveiro"), [
        C("watts", ["watts", "w"], "num", True),
        C("minutos", ["minutos", "min"], "num", True),
        C("banhos", ["banhos", "banho"], "num", True),
        C("tarifa", ["tarifa", "kwh"], "num", True),
    ])


def _calcular_chuveiro(params):
    def fazer():
        mod = carregar("consumo-energia", "kwh_core")
        kwh, custo = mod.chuveiro(
            params["watts"], params["minutos"], params["banhos"], params["tarifa"],
        )
        return _sair(_brl(custo), _num(kwh, 1) + " kWh no mes.", "Conta do chuveiro")
    return _chamar(fazer)


def _extrair_das(texto):
    params = _so(texto, ("simples nacional", "das do mei"), [
        C("receita", ["receita", "faturamento"], "num", True),
        C("rbt12", ["rbt12"], "num", True),
    ])
    if not params:
        return None
    t = norm(texto)
    marcas = (
        ("intelectual", 4),
        ("anexo v", 4),
        ("anexo iv", 3),
        ("construcao", 3),
        ("anexo iii", 2),
        ("anexo 3", 2),
        ("anexo ii", 1),
        ("industria", 1),
        ("anexo i", 0),
        ("comercio", 0),
        ("servico", 2),
    )
    for marca, idx in marcas:
        if marca in t:
            params["anexo_idx"] = idx
            return params
    return None


def _calcular_das(params):
    def fazer():
        mod = carregar("calculadora-simples-nacional", "snl_core")
        anexo = list(mod.ANEXOS)[params["anexo_idx"]]
        das, ef = mod.das_mensal(params["receita"], params["rbt12"], anexo)
        return _sair(
            _brl(das),
            "Aliquota efetiva " + _num(ef * 100, 2) + "%.",
            "Simples Nacional",
        )
    return _chamar(fazer)


def _extrair_fila(texto):
    # "m/m/1" tem um 1 solto que o leitor gruda no primeiro campo.
    limpo = texto.replace("M/M/1", "mm1").replace("m/m/1", "mm1")
    return _so(limpo, ("fila mm1", "mm1"), [
        C("chegada", ["chegada", "lambda"], "num", True),
        C("atendimento", ["atendimento", "mi"], "num", True),
    ])


def _calcular_fila(params):
    def fazer():
        mod = carregar("teoria-filas", "qth_core")
        r = mod.mm1(params["chegada"], params["atendimento"])
        if not r.get("stable", False):
            return _sair(r.get("message", "Fila instavel."), "M/M/1.", "Teoria das filas")
        return _sair(
            _num(r["Wq"], 3) + " h",
            "Espera media na fila. As taxas sao por hora.",
            "Teoria das filas",
        )
    return _chamar(fazer)


def _extrair_calor(texto):
    return _so(texto, ("indice de calor", "heat index"), [
        C("umidade", ["umidade", "ur"], "pct", True),
        C("temperatura", ["temperatura", "temp"], "num", True),
    ])


def _calcular_calor(params):
    def fazer():
        mod = carregar("calculadora-indice-conforto", "wci_core")
        r = mod.heat_index_c(params["temperatura"], params["umidade"])
        return _sair(
            _num(r["heat_index_c"], 1) + " °C",
            "Sensacao. Categoria: " + str(r["category"]) + ".",
            "Indice de calor",
        )
    return _chamar(fazer)


def _extrair_engrenagem(texto):
    return _so(texto, ("engrenagem", "engrenagens"), [
        C("modulo", ["modulo"], "num", True),
        C("z1", ["z1", "pinhao"], "int", True),
        C("z2", ["z2", "coroa"], "int", True),
    ])


def _calcular_engrenagem(params):
    def fazer():
        mod = carregar("calculadora-engrenagens", "grs_core")
        r = mod.calculate_gear_pair(params["modulo"], int(params["z1"]), int(params["z2"]))
        return _sair(
            _num(r["center_distance_mm"], 1) + " mm",
            "Distancia entre centros. Relacao " + _num(r["ratio"], 2) + ".",
            "Engrenagens",
        )
    return _chamar(fazer)


def _extrair_cubado(texto):
    return _so(texto, ("frete cubado", "peso cubado"), [
        C("comp", ["comp", "comprimento"], "num", True),
        C("larg", ["larg", "largura"], "num", True),
        C("alt", ["alt", "altura"], "num", True),
        C("peso", ["peso", "kg"], "num", True),
    ])


def _calcular_cubado(params):
    def fazer():
        mod = carregar("cubagem-cargas", "cub_core")
        r = mod.calculate_volumetric_freight(
            params["comp"], params["larg"], params["alt"], params["peso"],
        )
        return _sair(
            _num(r["air_billable_kg"], 2) + " kg",
            "Peso taxavel aereo (IATA). Rodoviario: " + _num(r["road_billable_kg"], 2) + " kg.",
            "Frete cubado",
        )
    return _chamar(fazer)


def _extrair_gray(texto):
    n = _numero_depois(texto, ("codigo gray", "codigo de gray", "gray"))
    if n is None:
        return None
    return {"n": int(round(n)), "_confianca": 0.93}


def _calcular_gray(params):
    def fazer():
        mod = carregar("estudio-gray-code", "gry_core")
        return _sair(str(mod.bin_to_gray(params["n"])), "Binario refletido em codigo de Gray.", "Codigo de Gray")
    return _chamar(fazer)


def _extrair_cisterna(texto):
    return _so(texto, ("cisterna",), [
        C("area", ["area", "telhado"], "num", True),
        C("chuva", ["chuva", "mm"], "num", True),
    ])


def _calcular_cisterna(params):
    def fazer():
        mod = carregar("cisterna-chuva", "cis_core")
        r = mod.captacao_mensal(params["area"], params["chuva"])
        return _sair(
            _num(r["litros"], 0) + " L",
            "No mes, coeficiente 0,8 da ferramenta.",
            "Cisterna",
        )
    return _chamar(fazer)


def _extrair_eolica(texto):
    return _so(texto, ("potencia eolica", "energia eolica", "aerogerador"), [
        C("raio", ["raio"], "num", True),
        C("vento", ["vento"], "num", True),
    ])


def _calcular_eolica(params):
    def fazer():
        mod = carregar("calculadora-energia-eolica-aerogerador", "eoc_core")
        w = mod.potencia_vento_disponivel(params["raio"], params["vento"])
        return _sair(_num(w, 0) + " W", "Potencia do vento no rotor, antes do limite de Betz.", "Energia eolica")
    return _chamar(fazer)


def _extrair_dizimo(texto):
    return _so(texto, ("dizimo",), [
        C("percentual", ["percentual"], "pct", False, 10.0),
        C("renda", ["renda"], "num", True),
    ])


def _calcular_dizimo(params):
    def fazer():
        mod = carregar("dizimo-doacoes", "dzm_core")
        valor = mod.calcular_dizimo(params["renda"], params.get("percentual", 10.0))
        return _sair(_brl(valor), "Sobre a renda informada.", "Dizimo")
    return _chamar(fazer)


def _extrair_pensao(texto):
    return _so(texto, ("pensao alimenticia", "pensao"), [
        C("percentual", ["percentual"], "pct", False, 30.0),
        C("filhos", ["filhos", "filho"], "int", False, 1),
        C("renda", ["renda"], "num", True),
    ])


def _calcular_pensao(params):
    def fazer():
        mod = carregar("pensao-alimenticia", "pen_core")
        r = mod.calcular(
            params["renda"], params.get("percentual", 30.0), int(params.get("filhos", 1)),
        )
        return _sair(_brl(r["pensao"]), "Estimativa educativa, nao e decisao judicial.", "Pensao alimenticia")
    return _chamar(fazer)


def _extrair_cashback(texto):
    return _so(texto, ("cashback real", "cashback"), [
        C("percentual", ["percentual", "cashback"], "pct", True),
        C("gasto", ["gasto"], "num", True),
    ])


def _calcular_cashback(params):
    def fazer():
        mod = carregar("cashback-real", "csh_core")
        r = mod.calcular(params["gasto"], params["percentual"])
        return _sair(_brl(r["liquido"]), "Liquido, sem anuidade e sem IOF.", "Cashback")
    return _chamar(fazer)


def _extrair_prestacoes(texto):
    return _so(texto, ("saldo de prestacoes", "saldo das prestacoes", "prestacoes"), [
        C("parcela", ["parcela"], "num", True),
        C("totais", ["totais", "total"], "int", True),
        C("pagas", ["pagas", "paguei"], "int", True),
    ])


def _calcular_prestacoes(params):
    def fazer():
        mod = carregar("saldo-prestacoes", "pst_core")
        r = mod.saldo(params["parcela"], int(params["totais"]), int(params["pagas"]))
        return _sair(
            _brl(r["total_devido"]),
            str(r["restantes"]) + " parcelas restantes.",
            "Saldo de prestacoes",
        )
    return _chamar(fazer)


def _extrair_viagem(texto):
    return _so(texto, ("poupanca viagem", "poupanca de viagem", "guardar pra viagem"), [
        C("meses", ["meses"], "mes", True),
        C("guardado", ["guardado", "ja tenho"], "num", False, 0.0),
        C("meta", ["meta"], "num", True),
    ])


def _calcular_viagem(params):
    def fazer():
        mod = carregar("meta-poupanca-viagem", "rvg_core")
        r = mod.planejar(params["meta"], int(params["meses"]), params.get("guardado", 0.0))
        return _sair(_brl(r["parcela"]) + "/mes", "Sem rendimento. Ainda falta " + _brl(r["falta"]) + ".", "Poupanca da viagem")
    return _chamar(fazer)


def _extrair_km(texto):
    return _so(texto, ("custo por km", "custo do km"), [
        C("litro", ["litro", "preco"], "num", True),
        C("kml", ["kml", "consumo"], "num", True),
        C("rodados", ["rodados", "km mes"], "num", True),
    ])


def _calcular_km(params):
    def fazer():
        mod = carregar("custo-total-por-km", "ckm_core")
        r = mod.calcular(params["litro"], params["kml"], params["rodados"])
        return _sair(
            "R$ " + _num(r["total_km"], 3) + "/km",
            "So combustivel. No mes: " + _brl(r["total_mes"]) + ".",
            "Custo por km",
        )
    return _chamar(fazer)


def _extrair_frete(texto):
    return _so(texto, ("estimativa de frete", "estimar frete"), [
        C("peso", ["peso"], "num", True),
        C("distancia", ["distancia", "km"], "num", True),
    ])


def _calcular_frete(params):
    def fazer():
        mod = carregar("estimativa-frete", "fre_core")
        r = mod.estimar(params["peso"], params["distancia"])
        return _sair(
            _brl(r["total"]),
            "Modalidade economica da ferramenta. Prazo " + str(r["prazo_dias"]) + " dias.",
            "Estimativa de frete",
        )
    return _chamar(fazer)


def _extrair_tag(texto):
    return _so(texto, ("pedagio com tag", "pedagio tag", "tag de pedagio"), [
        C("desconto", ["desconto"], "pct", False, 0.0),
        C("valor", ["valor", "pedagio"], "num", True),
        C("viagens", ["viagens", "vezes"], "int", True),
    ])


def _calcular_tag(params):
    def fazer():
        mod = carregar("custo-pedagio-tag", "tag_core")
        r = mod.calcular(
            params["valor"], int(params["viagens"]), params.get("desconto", 0.0),
        )
        return _sair(
            _brl(r["com_tag"]),
            "No mes, ida e volta. Sem tag: " + _brl(r["sem_tag"]) + ".",
            "Pedagio com tag",
        )
    return _chamar(fazer)


def _extrair_dsr(texto):
    return _so(texto, ("dsr sobre hora extra", "dsr da hora extra", "dsr hora extra"), [
        C("valor", ["valor", "extras"], "num", True),
        C("uteis", ["uteis"], "int", True),
        C("domingos", ["domingos", "feriados"], "int", True),
    ])


def _calcular_dsr(params):
    def fazer():
        mod = carregar("calculadora-dsr-hora-extra", "dsr_core")
        r = mod.calcular_dsr(params["valor"], int(params["uteis"]), int(params["domingos"]))
        return _sair(mod.brl(r["dsr"]), "Reflexo estimado. Nao substitui a convencao coletiva.", "DSR da hora extra")
    return _chamar(fazer)


def _extrair_obra(texto):
    t = norm(texto)
    if "piso" not in t and "obra" not in t:
        return None
    m_piso = re.search(r"(\d+(?:,\d+)?)\s*(?:m2|metros?\s*quadrados?)\s*(?:de\s*)?piso\s*(\d+)\s*x\s*(\d+)", t)
    if not m_piso:
        m_piso = re.search(r"piso\s*(\d+)\s*x\s*(\d+).*?(\d+(?:,\d+)?)\s*(?:m2|metros?\s*quadrados?)", t)
        if m_piso:
            w = float(m_piso.group(1))
            h = float(m_piso.group(2))
            area = float(m_piso.group(3).replace(",", "."))
            return {"area": area, "w": w, "h": h}
        return None
    area = float(m_piso.group(1).replace(",", "."))
    w = float(m_piso.group(2))
    h = float(m_piso.group(3))
    return {"area": area, "w": w, "h": h}


def _calcular_obra(params):
    def fazer():
        mod = carregar("calculadora-obra", "obr_core")
        res = mod.floor(params["area"], params["w"], params["h"], 10.0)
        pecas = res["pecas"]
        area_c = res["area_compra"]
        return _sair(
            f"{pecas} peças ({area_c:g} m²)",
            f"Para {params['area']:g} m² com piso {params['w']:g}×{params['h']:g} cm (10% de perda sugerida).",
            "Calculadora de Obra & Piso",
        )
    return _chamar(fazer)


def _extrair_pneu(texto):
    t = norm(texto)
    if "calibragem" not in t and "pneu" not in t:
        return None
    m = re.search(r"(\d+(?:,\d+)?)\s*psi", t)
    if not m:
        return None
    psi = float(m.group(1).replace(",", "."))
    viagem = any(k in t for k in ("estrada", "viagem", "rodovia"))
    carregado = any(k in t for k in ("carregado", "carga", "cheio", "bagagem"))
    carga_pct = 50.0 if carregado else 0.0
    return {"psi": psi, "viagem": viagem, "carga_pct": carga_pct}


def _calcular_pneu(params):
    def fazer():
        mod = carregar("calibragem-pneus", "pnu_core")
        res = mod.pressao_ajustada(params["psi"], carga_extra_pct=params["carga_pct"], viagem_estrada=params["viagem"])
        rec = res["recomendada_psi"]
        bar = res["recomendada_bar"]
        motivo = []
        if params["viagem"]:
            motivo.append("+3 psi estrada")
        if params["carga_pct"] > 0:
            motivo.append(f"+{res['extra_carga_psi']:g} psi carga")
        det = " / ".join(motivo) if motivo else "pressão base"
        return _sair(
            f"{rec:g} PSI ({bar:.2f} bar)",
            f"Pressão recomendada ({det}). Base {params['psi']:g} PSI a frio.",
            "Calibragem de Pneus",
        )
    return _chamar(fazer)


def _extrair_aluguel_quartos(texto):
    t = norm(texto)
    if "aluguel" not in t or "quarto" not in t:
        return None
    m_val = re.search(r"aluguel\s*(?:de\s*)?([0-9.,]+)", t)
    if not m_val:
        return None
    val = float(m_val.group(1).replace(".", "").replace(",", "."))
    nums = [float(x.replace(",", ".")) for x in re.findall(r"\b(\d+(?:,\d+)?)\s*(?:m2|metros)?", t[m_val.end():])]
    if len(nums) < 2:
        return None
    a1, a2 = nums[0], nums[1]
    return {"aluguel": val, "a1": a1, "a2": a2}


def _calcular_aluguel_quartos(params):
    def fazer():
        mod = carregar("aluguel-quartos", "alq_core")
        quartos = [
            {"nome": f"Q1 ({params['a1']:g}m²)", "area_m2": params["a1"]},
            {"nome": f"Q2 ({params['a2']:g}m²)", "area_m2": params["a2"]},
        ]
        res = mod.dividir(params["aluguel"], 0.0, quartos)
        r1 = res["rateio"][0]["valor"]
        r2 = res["rateio"][1]["valor"]
        return _sair(
            f"Q1: {_brl(r1)} | Q2: {_brl(r2)}",
            f"Divisão proporcional de {_brl(params['aluguel'])} entre {params['a1']:g} m² e {params['a2']:g} m².",
            "Divisão de Aluguel por Quarto",
        )
    return _chamar(fazer)


def _extrair_desafio_poupanca(texto):
    t = norm(texto)
    if "52 semana" not in t and "desafio poupanca" not in t:
        return None
    m_base = re.search(r"(?:comecando\s+com|base|iniciando\s+com)\s*([0-9.,]+)", t)
    base = float(m_base.group(1).replace(",", ".")) if m_base else 1.0
    return {"base": base}


def _calcular_desafio_poupanca(params):
    def fazer():
        mod = carregar("desafio-poupanca", "cof_core")
        base = params.get("base", 1.0)
        plano = mod.plano_52(base=base)
        tot = sum(plano)
        ult = plano[-1]
        return _sair(
            f"Total acumulado: {_brl(tot)}",
            f"Desafio das 52 semanas (começando com {_brl(base)} até {_brl(ult)} na semana 52).",
            "Desafio da Poupança",
        )
    return _chamar(fazer)


def _extrair_renda_fixa(texto):
    t = norm(texto)
    if not any(k in t for k in ("renda fixa", "cdb", "lci", "lca", "tesouro direto")):
        return None
    m_val = re.search(r"(?:cdb|lci|lca|tesouro\s+direto|renda\s+fixa)\s*(?:de\s*)?([0-9.,]+(?:\s*mil)?)", t)
    if not m_val:
        return None
    val_str = m_val.group(1).strip()
    val = float(val_str.replace("mil", "").replace(".", "").replace(",", ".")) * (1000.0 if "mil" in val_str else 1.0)
    m_taxa = re.search(r"([0-9.,]+)\s*%\s*(?:a\.?a\.?|ao\s*ano)?", t)
    taxa = float(m_taxa.group(1).replace(",", ".")) if m_taxa else 12.0
    m_dias = re.search(r"(\d+)\s*dias?", t)
    if m_dias:
        dias = int(m_dias.group(1))
    elif any(k in t for k in ("1 ano", "um ano", "12 meses")):
        dias = 365
    elif any(k in t for k in ("2 anos", "dois anos", "24 meses")):
        dias = 730
    elif any(k in t for k in ("6 meses", "seis meses", "180 dias")):
        dias = 180
    else:
        dias = 365
    isento = "lci" in t or "lca" in t
    tipo = "LCI/LCA" if isento else ("CDB" if "cdb" in t else "Renda Fixa")
    return {"valor": val, "taxa": taxa, "dias": dias, "isento": isento, "rotulo": tipo}


def _calcular_renda_fixa(params):
    def fazer():
        mod = carregar("simulador-renda-fixa", "rfx_core")
        res = mod.simular(params["valor"], params["dias"], params["taxa"], isento=params["isento"])
        liq = res["liquido"]
        rend_l = res["rend_liquido"]
        ir = res["ir"]
        det_ir = f"IR ({res['aliq_ir']:g}%): {_brl(ir)}" if not params["isento"] else "Isento de IR"
        return _sair(
            f"Líquido: {_brl(liq)} (+{_brl(rend_l)})",
            f"{params['rotulo']} de {_brl(params['valor'])} a {params['taxa']:g}% a.a. por {params['dias']} dias. {det_ir}.",
            "Simulador de Renda Fixa",
        )
    return _chamar(fazer)


# --- TREINO DE ACADEMIA ---
def _extrair_treino(texto):
    t = norm(texto)
    # 1RM: "1rm 80kg 8 reps", "1rm 100kg 5 reps", "1rm de 70kg 10 repeticoes"
    if "1rm" in t or "uma repeticao maxima" in t:
        m_kg = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:kg|quilos?)", t)
        m_reps = re.search(r"(\d+)\s*(?:reps?|repeticoes|vezes)", t)
        if m_kg and m_reps:
            carga = float(m_kg.group(1).replace(",", "."))
            reps = int(m_reps.group(1))
            if carga > 0 and 1 <= reps < 37:
                return {"tipo": "1rm", "carga": carga, "reps": reps}
        numeros = [float(x.replace(",", ".")) for x in re.findall(r"\b\d+(?:[.,]\d+)?\b", t.replace("1rm", ""))]
        if len(numeros) >= 2:
            carga, reps = numeros[0], int(numeros[1])
            if carga > 0 and 1 <= reps < 37:
                return {"tipo": "1rm", "carga": carga, "reps": reps}

    # Anilhas: "anilhas para 80kg", "anilhas barra 100kg", "anilhas 90kg"
    if "anilha" in t or "anilhas" in t:
        m_kg = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:kg)?", t.replace("anilha", " ").replace("anilhas", " "))
        if m_kg:
            carga = float(m_kg.group(1).replace(",", "."))
            if carga >= 20.0:
                return {"tipo": "anilhas", "carga": carga}

    return None


def _calcular_treino(params):
    def fazer():
        mod = carregar("treino-academia", "rmx_core")
        tipo = params.get("tipo")
        if tipo == "1rm":
            carga = params["carga"]
            reps = params["reps"]
            rm = mod.media_1rm(carga, reps)
            ep = mod.epley(carga, reps)
            br = mod.brzycki(carga, reps)
            return _sair(
                f"1RM estimado: {rm:.1f} kg",
                f"Para {carga:g} kg e {reps} reps (Epley: {ep:.1f} kg, Brzycki: {br:.1f} kg).",
                "Treino de Academia",
            )
        elif tipo == "anilhas":
            carga = params["carga"]
            usadas, sobra = mod.anilhas_por_lado(carga)
            desc_anilhas = " + ".join(f"{a:g}kg" for a in usadas) if usadas else "nenhuma anilha"
            return _sair(
                f"Por lado: {desc_anilhas}",
                f"Barra de 20 kg + 2x {sum(usadas):g} kg = {carga:g} kg no total.",
                "Treino de Academia",
            )
        return pacote("Operação inválida", "Treino de Academia")
    return _chamar(fazer)


# --- FICHA MÉDICA / EXAMES / MEDICAMENTOS ---
_LAB_EXAMES = [
    ("glicemia em jejum", "Glicemia em Jejum (mg/dL)"),
    ("glicemia", "Glicemia em Jejum (mg/dL)"),
    ("hemoglobina glicada", "Hemoglobina Glicada HbA1c (%)"),
    ("hba1c", "Hemoglobina Glicada HbA1c (%)"),
    ("colesterol hdl", "Colesterol HDL (mg/dL)"),
    ("colesterol ldl", "Colesterol LDL (mg/dL)"),
    ("colesterol total", "Colesterol Total (mg/dL)"),
    ("colesterol", "Colesterol Total (mg/dL)"),
    ("triglicerideos", "Triglicerídeos (mg/dL)"),
    ("triglicerides", "Triglicerídeos (mg/dL)"),
    ("creatinina", "Creatinina Sérica (mg/dL)"),
    ("tsh", "TSH Ultra-sensível (mUI/L)"),
    ("vitamina d", "Vitamina D 25-OH (ng/mL)"),
    ("acido urico", "Ácido Úrico (mg/dL)"),
    ("hemoglobina", "Hemoglobina (g/dL)"),
]


def _extrair_ficha_medica(texto):
    t = norm(texto)
    # Remedio / estoque:
    if ("remedio" in t or "medicamento" in t or "comprimidos" in t) and ("estoque" in t or "duracao" in t or "dura" in t or "por dia" in t):
        m_tot = re.search(r"(\d+)\s*(?:comprimidos?|capsulas?|pilulas?)?", t.replace("estoque", "").replace("remedio", "").replace("medicamento", ""))
        m_dia = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:por\s+dia|ao\s+dia|diarios?|dia\b)", t)
        if m_tot and m_dia:
            total = int(m_tot.group(1))
            diario = float(m_dia.group(1).replace(",", "."))
            if total > 0 and diario > 0:
                return {"tipo": "medicamento", "total": total, "diario": diario}

    # Exame laboratorial:
    for termo, exam_key in _LAB_EXAMES:
        if termo in t:
            sem_termo = t.replace(termo, " ").replace("exame", " ").replace("de", " ").replace("mg/dl", " ").replace("ng/ml", " ").replace("g/dl", " ").replace("%", " ")
            m_val = re.search(r"\b(\d+(?:[.,]\d+)?)\b", sem_termo)
            if m_val:
                val = float(m_val.group(1).replace(",", "."))
                return {"tipo": "exame", "exame_chave": exam_key, "valor": val, "termo": termo.title()}

    return None


def _calcular_ficha_medica(params):
    def fazer():
        mod = carregar("ficha-medica", "med_core")
        tipo = params.get("tipo")
        if tipo == "exame":
            res = mod.evaluate_lab_exam(params["exame_chave"], params["valor"])
            return _sair(
                f"{res['status']}: {res['value']} {res['unit']}",
                f"{res['exam']} — Referência clínica: {res['ref_range']}.",
                "Prontuário & Exames",
            )
        elif tipo == "medicamento":
            res = mod.calculate_medication_stock(params["total"], params["diario"])
            return _sair(
                f"{res['days_left']} dias de estoque ({res['alert']})",
                f"{params['total']} comprimidos a {params['diario']:g}/dia.",
                "Prontuário & Exames",
            )
        return pacote("Operação inválida", "Prontuário & Exames")
    return _chamar(fazer)


# --- MALA DE VIAGEM ---
def _extrair_mala_viagem(texto):
    t = norm(texto)
    if "mala" not in t:
        return None
    if "mala direta" in t:
        return None
    if not any(k in t for k in ("viagem", "dias", "dia", "viajar")):
        return None
    m_dias = re.search(r"(\d+)\s*dias?", t)
    if m_dias:
        dias = int(m_dias.group(1))
    else:
        m_num = re.search(r"(?:mala|viagem)\s*(?:de|para)?\s*(\d+)", t)
        if m_num:
            dias = int(m_num.group(1))
        else:
            return None
    if dias < 1:
        return None

    clima = "Ameno"
    if any(k in t for k in ("calor", "praia", "verao")):
        clima = "Calor"
    elif any(k in t for k in ("frio", "inverno")):
        clima = "Frio"

    tipos = ["Lazer"]
    if any(k in t for k in ("trabalho", "negocios")):
        tipos.append("Negócios")
    if any(k in t for k in ("trilha", "camping")):
        tipos.append("Camping/trilha")
    if "internacional" in t:
        tipos.append("Internacional")

    return {"dias": dias, "clima": clima, "tipos": tipos}


def _calcular_mala_viagem(params):
    def fazer():
        mod = carregar("mala-viagem", "mal_core")
        dias = params["dias"]
        clima = params["clima"]
        tipos = tuple(params["tipos"])
        itens = mod.lista(dias, clima=clima, tipos=tipos)
        peso = mod.peso_total_kg(itens, mala="Mala de mão")
        ok, sobra = mod.cabe(peso, 10.0)
        status = "Cabe na mala de mão (10 kg)" if ok else "Excede mala de mão (10 kg)"
        tot_pecas = sum(q for q, _ in itens.values())
        return _sair(
            f"Mala {peso:.1f} kg ({tot_pecas} itens) — {status}",
            f"Sugestão para {dias} dias ({clima.lower()}, {', '.join(t.lower() for t in tipos)}): {tot_pecas} itens.",
            "Mala de Viagem",
        )
    return _chamar(fazer)


# --- MARMITAS DA SEMANA ---
def _extrair_marmitas(texto):
    t = norm(texto)
    if "marmita" not in t and "marmitas" not in t:
        return None
    m_qtd = re.search(r"(\d+)\s*(?:marmitas?|refeicoes|porcoes)", t)
    if m_qtd:
        n = int(m_qtd.group(1))
    else:
        m_dias = re.search(r"(\d+)\s*dias?", t)
        if m_dias:
            dias = int(m_dias.group(1))
            m_ref = re.search(r"(\d+)\s*(?:por\s+dia|ao\s+dia|refeicoes)", t)
            ref_dia = int(m_ref.group(1)) if m_ref else 1
            n = dias * ref_dia
        else:
            m_num = re.search(r"\b(\d+)\b", t)
            n = int(m_num.group(1)) if m_num else 5
    if n <= 0:
        return None
    return {"n": n}


def _calcular_marmitas(params):
    def fazer():
        mod = carregar("marmitas-semana", "mmt_core")
        n = params["n"]
        escolhas = {
            "Proteína": ["Peito de frango", "Carne moída"],
            "Carboidrato": ["Arroz branco", "Batata-doce"],
            "Leguminosa": ["Feijão"],
            "Legume": ["Brócolis", "Cenoura"],
        }
        card = mod.cardapio(escolhas, n)
        comp = mod.compras(card)
        res = mod.resumo(comp, n)
        dias_equiv = (n + 1) // 2
        gel, freez = mod.divisao_freezer(dias_equiv, 2)
        det_conserv = f"{min(gel, n)} na geladeira e {max(0, n - gel)} no freezer" if n > 3 else "consumir da geladeira em até 3-4 dias"
        return _sair(
            f"Total: {_brl(res['custo_total'])} ({_brl(res['por_marmita'])}/marmita)",
            f"{n} marmitas (~{res['peso_medio']:.0f}g cada). Conservação: {det_conserv}.",
            "Marmitas da Semana",
        )
    return _chamar(fazer)


# --- TRABALHO CLT: ADICIONAL NOTURNO ---
def _extrair_noturno(texto):
    t = norm(texto)
    if "noturno" not in t and "noturna" not in t:
        return None
    if not any(k in t for k in ("adicional noturno", "hora noturna", "horas noturnas", "noturno", "noturna")):
        return None
    # Horas noturnas trabalhadas:
    m_hn = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:horas?\s+noturnas?|h\s+noturnas?|horas?|h\b)", t.replace("adicional noturno", "").replace("hora noturna", ""))
    if not m_hn:
        m_hn = re.search(r"(\d+)\s*(?:horas?|h\b)", t)
    horas_noturnas = float(m_hn.group(1).replace(",", ".")) if m_hn else 40.0

    # Salario ou valor hora:
    m_vh = re.search(r"(?:hora\s*(?:diurna)?|valor\s*hora)\s*(?:de|r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_vh:
        hora_diurna = float(m_vh.group(1).replace(",", "."))
        salario = None
    else:
        m_sal = re.search(r"(?:salario|remuneracao|sal)\s*(?:de|r\$)?\s*(\d+(?:[.,]\d+)?)", t)
        if m_sal:
            salario = float(m_sal.group(1).replace(",", "."))
        else:
            nums = [float(x.replace(",", ".")) for x in re.findall(r"\b\d+(?:[.,]\d+)?\b", t)]
            nums = [x for x in nums if x != horas_noturnas]
            salario = nums[0] if nums else 2000.0
        hora_diurna = None

    jornada_red = any(k in t for k in ("reduzida", "ficta", "52"))
    return {
        "horas_noturnas": horas_noturnas,
        "salario": salario,
        "hora_diurna": hora_diurna,
        "jornada_reduzida": jornada_red,
    }


def _calcular_noturno(params):
    def fazer():
        mod = carregar("calculadora-adicional-noturno", "adt_core")
        hn = params["horas_noturnas"]
        if params.get("hora_diurna"):
            res = mod.calcular(hora_diurna=params["hora_diurna"], horas_noturnas_mes=hn, jornada_reduzida=params["jornada_reduzida"])
            base_txt = f"hora diurna de {_brl(params['hora_diurna'])}"
        else:
            sal = params["salario"] or 2000.0
            res = mod.calcular(salario_mensal=sal, horas_mes=220.0, horas_noturnas_mes=hn, jornada_reduzida=params["jornada_reduzida"])
            base_txt = f"salário de {_brl(sal)} (220h/mês)"

        red_txt = " (com hora reduzida)" if params["jornada_reduzida"] else ""
        return _sair(
            f"Adicional: {_brl(res['valor_adicional_mes'])}",
            f"{hn:g}h noturnas{red_txt} sobre {base_txt} (+{_brl(res['adicional_por_hora'])}/h, 20%). Total noturno: {_brl(res['total_noturno_mes'])}.",
            "Calculadora Adicional Noturno",
        )
    return _chamar(fazer)


# --- TRABALHO CLT: INSALUBRIDADE ---
def _extrair_insalubridade(texto):
    t = norm(texto)
    if "insalubridade" not in t:
        return None
    if any(k in t for k in ("maximo", "maxima", "40%")):
        grau = "maximo"
    elif any(k in t for k in ("minimo", "minima", "10%")):
        grau = "minimo"
    else:
        grau = "medio"

    m_sal = re.search(r"(?:salario|base|r\$)\s*(\d+(?:[.,]\d+)?)", t)
    base = float(m_sal.group(1).replace(",", ".")) if m_sal else None

    return {"grau": grau, "base": base}


def _calcular_insalubridade(params):
    def fazer():
        mod = carregar("calculadora-adicional-insalubridade", "ins_core")
        grau = params["grau"]
        sm = mod.SALARIO_MINIMO_PADRAO
        base_alt = params["base"]
        res = mod.calcular(grau, salario_minimo=sm, base_alternativa=base_alt, meses_anuais=12)
        base_efetiva = res["base_utilizada"]
        return _sair(
            f"Insalubridade: {_brl(res['adicional_mensal'])}/mês",
            f"Grau {grau} ({res['percentual']:g}%) sobre {_brl(base_efetiva)}. Impacto anual (12m): {_brl(res['impacto_anual'])}.",
            "Adicional de Insalubridade CLT",
        )
    return _chamar(fazer)


# --- IMPRESSÃO 3D ---
def _extrair_impressao_3d(texto):
    t = norm(texto)
    if not any(k in t for k in ("impressao 3d", "impressora 3d", "filamento 3d", "peca 3d")):
        return None

    m_g = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:g|gramas?)", t)
    gramas = float(m_g.group(1).replace(",", ".")) if m_g else 100.0

    m_h = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:horas?|h\b)", t)
    horas = float(m_h.group(1).replace(",", ".")) if m_h else 3.0

    m_rolo = re.search(r"(?:rolo|filamento|preco)\s*(?:de|r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    preco_rolo = float(m_rolo.group(1).replace(",", ".")) if m_rolo else 120.0

    return {"gramas": gramas, "horas": horas, "preco_rolo": preco_rolo}


def _calcular_impressao_3d(params):
    def fazer():
        mod = carregar("calculadora-impressao-3d", "p3d_core")
        g = params["gramas"]
        h = params["horas"]
        rolo = params["preco_rolo"]
        custo = mod.custo_peca(gramas=g, horas=h, preco_rolo=rolo)
        venda = mod.preco_venda(custo["total"], margem_pct=100.0)
        metros = mod.gramas_para_metros(g)
        return _sair(
            f"Custo: {_brl(custo['total'])} | Venda sugerida: {_brl(venda['preco'])}",
            f"Peça de {g:g}g (~{metros:.1f}m) e {h:g}h. Material: {_brl(custo['material'])}, Energia/depreciação: {_brl(custo['total'] - custo['material'])}.",
            "Calculadora de Impressão 3D",
        )
    return _chamar(fazer)


# --- CALCULADORA DE PISCINA ---
def _extrair_piscina(texto):
    t = norm(texto)
    if "piscina" not in t:
        return None

    m_dim = re.search(r"(\d+(?:[.,]\d+)?)\s*[xX*]\s*(\d+(?:[.,]\d+)?)(?:\s*[xX*]\s*(\d+(?:[.,]\d+)?))?", t)
    if m_dim:
        c = float(m_dim.group(1).replace(",", "."))
        l = float(m_dim.group(2).replace(",", "."))
        if m_dim.group(3):
            p = float(m_dim.group(3).replace(",", "."))
        else:
            m_prof = re.search(r"(?:profundidade|prof|fundo)\s*(?:de)?\s*(\d+(?:[.,]\d+)?)", t)
            p = float(m_prof.group(1).replace(",", ".")) if m_prof else 1.4
        vol_m3 = c * l * p
        return {"tipo": "dimensoes", "comp": c, "larg": l, "prof": p, "vol_m3": vol_m3}

    m_vol = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m3|mil\s*litros|litros?)", t)
    if m_vol:
        val = float(m_vol.group(1).replace(",", "."))
        if "mil litros" in t or ("litros" in t and val > 500):
            vol_m3 = val if "mil litros" in t else val / 1000.0
        else:
            vol_m3 = val
        choque = "choque" in t
        return {"tipo": "volume", "vol_m3": vol_m3, "choque": choque}

    return None


def _calcular_piscina(params):
    def fazer():
        mod = carregar("calculadora-piscina", "psc_core")
        vol_m3 = params["vol_m3"]
        litros = vol_m3 * 1000
        dose_dia = mod.dose_cloro(vol_m3, ppm_alvo=3.0, ppm_atual=1.0)
        dose_chq = mod.cloro_choque(vol_m3, ppm_choque=10.0)
        if params.get("choque"):
            return _sair(
                f"Cloro de choque: {dose_chq:.0f}g de cloro granulado",
                f"Piscina de {vol_m3:.1f} m³ ({litros:,.0f} L). Dosagem de choque (10 ppm).",
                "Calculadora de Piscina",
            )
        return _sair(
            f"Volume: {vol_m3:.1f} m³ ({litros:,.0f} L) | Cloro: {dose_dia:.0f}g/dia",
            f"Manutenção diária: ~{dose_dia:.0f}g de cloro (elevar 2 ppm). Choque: ~{dose_chq:.0f}g.",
            "Calculadora de Piscina",
        )
    return _chamar(fazer)


# --- ADICIONAL DE PERICULOSIDADE CLT ---
def _extrair_periculosidade(texto):
    t = norm(texto)
    if "periculosidade" not in t:
        return None
    m_sal = re.search(r"(\d+(?:[.,]\d+)?)", t.replace("periculosidade", " ").replace("adicional", " "))
    salario = float(m_sal.group(1).replace(",", ".")) if m_sal else 2000.0

    m_prop = re.search(r"(\d+(?:[.,]\d+)?)\s*%\s*(?:proporcional|jornada)?", t)
    prop = float(m_prop.group(1).replace(",", ".")) if m_prop and "%" in t and "30%" not in t else 100.0

    return {"salario": salario, "proporcionalidade": prop}


def _calcular_periculosidade(params):
    def fazer():
        mod = carregar("calculadora-adicional-periculosidade", "per_core")
        sal = params["salario"]
        prop = params.get("proporcionalidade", 100.0)
        res = mod.calcular(sal, percentual=30.0, proporcionalidade=prop, meses_anuais=12)
        return _sair(
            f"Periculosidade (30%): {_brl(res['adicional_mensal'])}/mês",
            f"Salário final: {_brl(res['salario_com_adicional'])} (base {_brl(sal)}). Total anual (12m): {_brl(res['adicional_anual'])}.",
            "Adicional de Periculosidade CLT",
        )
    return _chamar(fazer)


# --- CALCULADORA DE SEGURO-DESEMPREGO ---
def _extrair_seguro_desemprego(texto):
    t = norm(texto)
    if not any(k in t for k in ("seguro desemprego", "seguro-desemprego")):
        return None

    m_meses = re.search(r"(\d+)\s*(?:meses|m\b)", t)
    meses = int(m_meses.group(1)) if m_meses else 14

    txt_sem = t.replace("seguro desemprego", " ").replace("seguro-desemprego", "")
    if m_meses:
        txt_sem = txt_sem.replace(m_meses.group(0), " ")
    m_sal = re.search(r"(\d+(?:[.,]\d+)?)", txt_sem)
    sal = float(m_sal.group(1).replace(",", ".")) if m_sal else 2500.0

    if "2" in t and any(k in t for k in ("segunda", "2a", "2ª")):
        sol = 2
    elif "3" in t and any(k in t for k in ("terceira", "3a", "3ª")):
        sol = 3
    else:
        sol = 1

    return {"salario": sal, "meses": meses, "solicitacao": sol}


def _calcular_seguro_desemprego(params):
    def fazer():
        mod = carregar("calculadora-seguro-desemprego", "csd_core")
        sal = params["salario"]
        meses = params["meses"]
        sol = params["solicitacao"]
        res = mod.simular_seguro_desemprego([sal, sal, sal], numero_solicitacao=sol, meses_trabalhados=meses)
        if not res["aprovado"]:
            return _sair(
                "Ineligível ao seguro-desemprego",
                res["motivo_elegibilidade"],
                "Calculadora de Seguro-Desemprego",
            )
        return _sair(
            f"{res['num_parcelas']} parcelas de {_brl(res['valor_parcela'])} (Total: {_brl(res['total_beneficio'])})",
            f"Média salarial: {_brl(sal)} com {meses} meses trabalhados ({sol}ª solicitação).",
            "Calculadora de Seguro-Desemprego",
        )
    return _chamar(fazer)


# --- CALCULADORA DE AQUÁRIO ---
def _extrair_aquario(texto):
    t = norm(texto)
    if "aquario" not in t:
        return None

    m_dim = re.search(r"(\d+(?:[.,]\d+)?)\s*[xX*]\s*(\d+(?:[.,]\d+)?)\s*[xX*]\s*(\d+(?:[.,]\d+)?)", t)
    if m_dim:
        c = float(m_dim.group(1).replace(",", "."))
        l = float(m_dim.group(2).replace(",", "."))
        a = float(m_dim.group(3).replace(",", "."))
        return {"tipo": "dimensoes", "comp": c, "larg": l, "alt": a}

    m_litros = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:litros?|l\b)", t)
    if m_litros:
        litros = float(m_litros.group(1).replace(",", "."))
        return {"tipo": "litros", "litros": litros}

    return None


def _calcular_aquario(params):
    def fazer():
        mod = carregar("calculadora-aquario", "aqu_core")
        tipo = params.get("tipo")
        if tipo == "dimensoes":
            c = params["comp"]
            l = params["larg"]
            a = params["alt"]
            bruto = mod.volume_retangular(c, l, a)
        else:
            bruto = params["litros"]

        real = mod.volume_real(bruto)
        f_min, f_max = mod.filtragem(real, tipo="Comunitário")
        term_w = mod.aquecedor_comercial(mod.aquecedor_w(real, 26, 21))
        return _sair(
            f"Aquário: {bruto:.0f}L bruto (~{real:.1f}L real)",
            f"Filtro sugerido: {f_min:.0f} a {f_max:.0f} L/h (comunitário). Termostato: ~{term_w}W.",
            "Calculadora de Aquário",
        )
    return _chamar(fazer)


# --- CALCULADORA HIDRÁULICA DE TUBULAÇÕES ---
def _extrair_hidraulica(texto):
    t = norm(texto)
    if not any(k in t for k in ("perda de carga", "hidraulica tubo", "tubulacao", "tubulacoes")):
        return None

    m_vaz = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:l/s|litros?\s*(?:por|/)\s*s(?:egundo)?)", t)
    if m_vaz:
        flow_lps = float(m_vaz.group(1).replace(",", "."))
    else:
        m_m3h = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m3/h|m3\s*(?:por|/)\s*h)", t)
        flow_lps = float(m_m3h.group(1).replace(",", ".")) / 3.6 if m_m3h else 2.0

    m_diam = re.search(r"(\d+(?:[.,]\d+)?)\s*mm\b", t)
    if m_diam:
        diam_mm = float(m_diam.group(1).replace(",", "."))
    else:
        m_pol = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:pol|polegadas?|\")", t)
        diam_mm = float(m_pol.group(1).replace(",", ".")) * 25.4 if m_pol else 50.0

    m_comp = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:metros?|m\b)", t.replace(f"{diam_mm:g} mm" if m_diam else "", ""))
    length_m = float(m_comp.group(1).replace(",", ".")) if m_comp else 50.0

    return {"flow_lps": flow_lps, "diam_mm": diam_mm, "length_m": length_m}


def _calcular_hidraulica(params):
    def fazer():
        mod = carregar("calculadora-hidraulica-tubulacoes", "hdr_core")
        flow = params["flow_lps"]
        diam = params["diam_mm"]
        length = params["length_m"]
        res = mod.calculate_darcy_weisbach(flow_lps=flow, diameter_mm=diam, length_m=length)
        return _sair(
            f"Perda de carga: {res['head_loss_mca']:.2f} mca ({res['head_loss_bar']:.3f} bar)",
            f"Vazão: {flow:g} L/s ({res['flow_m3h']:g} m³/h) em tubo {diam:g}mm x {length:g}m. Velocidade: {res['velocity_ms']:.2f} m/s ({res['regime']}).",
            "Calculadora Hidráulica de Tubulações",
        )
    return _chamar(fazer)


# --- RESCISÃO TRABALHISTA CLT ---
def _extrair_rescisao(texto):
    t = norm(texto)
    if "rescisao" not in t:
        return None

    m_sal = re.search(r"(\d+(?:[.,]\d+)?)", t.replace("rescisao", " ").replace("clt", " "))
    sal = float(m_sal.group(1).replace(",", ".")) if m_sal else 2500.0

    m_anos = re.search(r"(\d+)\s*(?:anos?|a\b)", t)
    anos = int(m_anos.group(1)) if m_anos else 1

    m_meses = re.search(r"(\d+)\s*(?:meses|m\b)", t)
    meses = int(m_meses.group(1)) if m_meses else 6

    if any(k in t for k in ("pedido", "pedi demissao")):
        mod = "pedido_demissao"
    elif any(k in t for k in ("acordo", "mutuo")):
        mod = "acordo_mutuo"
    elif any(k in t for k in ("justa causa", "com justa causa")) and "sem" not in t:
        mod = "com_justa_causa"
    else:
        mod = "sem_justa_causa"

    return {"salario": sal, "anos": anos, "meses": meses, "modalidade": mod}


def _calcular_rescisao(params):
    def fazer():
        mod = carregar("calculadora-rescisao-trabalhista", "rst_core")
        sal = params["salario"]
        anos = params["anos"]
        meses = params["meses"]
        modalidade = params["modalidade"]
        res = mod.calcular_rescisao_clt(
            salario_bruto=sal,
            anos_trabalhados=anos,
            meses_trabalhados_ano_atual=meses,
            dias_trabalhados_mes_rescisao=30,
            modalidade=modalidade,
            aviso_previo_indenizado=True,
            tem_ferias_vencidas=False,
            meses_ferias_proporcionais=meses,
            saldo_fgts_acumulado=sal * 0.08 * 12 * anos,
        )
        mod_rotulo = {
            "sem_justa_causa": "Sem justa causa",
            "pedido_demissao": "Pedido de demissão",
            "acordo_mutuo": "Acordo mútuo (Art. 484-A)",
            "com_justa_causa": "Com justa causa",
        }.get(modalidade, modalidade)
        return _sair(
            f"Rescisão ({mod_rotulo}): Líquido TRCT {_brl(res['liquido_rescisao_trct'])}",
            f"Bruto: {_brl(res['total_proventos_brutos'])}, Descontos: {_brl(res['total_descontos'])}, FGTS+Multa: {_brl(res['saque_fgts_liberado'])}. Total disponível: {_brl(res['total_liquido_disponivel'])}.",
            "Calculadora de Rescisão Trabalhista CLT",
        )
    return _chamar(fazer)


# --- CALCULADORA CHMOD ---
def _extrair_chmod(texto):
    t = norm(texto)
    if "chmod" not in t and "permissao" not in t and "permissoes" not in t:
        return None

    m_oct = re.search(r"\b([0-7]{3,4})\b", t)
    if m_oct:
        return {"tipo": "octal", "valor": m_oct.group(1)}

    m_sym = re.search(r"[-dlbcps]?[r-][w-][xstST-][r-][w-][xstST-][r-][w-][xstST-]", t)
    if m_sym:
        return {"tipo": "simbolico", "valor": m_sym.group(0)}

    return None


def _calcular_chmod(params):
    def fazer():
        mod = carregar("calculadora-chmod", "rwx_core")
        tipo = params.get("tipo")
        if tipo == "octal":
            code = params["valor"]
            mode = mod.parse_octal(code)
            sym = mod.to_symbolic(mode)
            oct_fmt = mod.to_octal(mode)
            return _sair(
                f"chmod {oct_fmt} = {sym}",
                f"Permissões Unix: dono={sym[0:3]}, grupo={sym[3:6]}, outros={sym[6:9]}.",
                "Calculadora chmod",
            )
        elif tipo == "simbolico":
            s = params["valor"]
            mode = mod.parse_symbolic(s)
            oct_fmt = mod.to_octal(mode)
            sym = mod.to_symbolic(mode)
            return _sair(
                f"{sym} = chmod {oct_fmt}",
                f"Permissões Unix em octal: {oct_fmt} (dono={sym[0:3]}, grupo={sym[3:6]}, outros={sym[6:9]}).",
                "Calculadora chmod",
            )
        return pacote("Operação inválida", "Calculadora chmod")
    return _chamar(fazer)


# --- MOTORES ELÉTRICOS DE INDUÇÃO ---
def _extrair_motor(texto):
    t = norm(texto)
    if "motor" not in t and "motores" not in t:
        return None
    if not any(k in t for k in ("motor eletrico", "motores eletricos", "motor trifasico", "motor monofasico", "motor de inducao", "cv", "hp")):
        if not any(k in t for k in ("220v", "380v", "440v", "110v", "polos", "torque")):
            return None

    m_cv = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:cv|hp)", t)
    if m_cv:
        power_cv = float(m_cv.group(1).replace(",", "."))
    else:
        m_num = re.search(r"motor\s*(?:eletrico)?\s*(\d+(?:[.,]\d+)?)", t)
        power_cv = float(m_num.group(1).replace(",", ".")) if m_num else 5.0

    m_v = re.search(r"(\d+)\s*v\b", t)
    voltage_v = float(m_v.group(1)) if m_v else 220.0

    m_polos = re.search(r"(\d+)\s*polos?", t)
    if m_polos:
        polos = int(m_polos.group(1))
        if polos not in (2, 4, 6, 8):
            polos = 4
    else:
        polos = 4

    is_three = "monofasico" not in t

    return {"power_cv": power_cv, "voltage_v": voltage_v, "poles": polos, "is_three_phase": is_three}


def _calcular_motor(params):
    def fazer():
        mod = carregar("calculadora-motores-eletricos", "mot_core")
        cv = params["power_cv"]
        v = params["voltage_v"]
        poles = params["poles"]
        three = params["is_three_phase"]
        res = mod.calculate_electric_motor(power_cv=cv, voltage_v=v, poles=poles, is_three_phase=three)
        fase_txt = "trifásico" if three else "monofásico"
        return _sair(
            f"Motor {cv:g} CV ({res['power_kw']:.2f} kW) {fase_txt} {v:g}V: In = {res['i_nominal']:.1f}A",
            f"Torque nominal: {res['torque_nm']:.1f} N.m ({res['torque_kgfm']:.2f} kgf.m). Rotação: {res['rated_rpm']} RPM ({poles} polos, s={res['slip_pct']:.1f}%). Cabo: {res['recommended_cable_mm2']} mm², Disjuntor: {res['recommended_breaker_a']}A.",
            "Calculadora de Motores Elétricos",
        )
    return _chamar(fazer)


# --- FILTRO DE BLOOM ---
def _extrair_bloom(texto):
    t = norm(texto)
    if "bloom" not in t:
        return None

    m_itens = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:mil\s*itens|mil\s*elementos|itens|elementos|chaves?)", t)
    if m_itens:
        val_str = m_itens.group(1).replace(",", ".")
        n = int(float(val_str) * 1000 if "mil" in t else float(val_str))
    else:
        nums = [int(x) for x in re.findall(r"\b\d+\b", t)]
        n = nums[0] if nums else 10000

    m_pct = re.search(r"(\d+(?:[.,]\d+)?)\s*%", t)
    if m_pct:
        p = float(m_pct.group(1).replace(",", ".")) / 100.0
    else:
        m_dec = re.search(r"(?:erro|taxa|falso\s*positivo|p)\s*(?:de)?\s*(0[.,]\d+)", t)
        if m_dec:
            p = float(m_dec.group(1).replace(",", "."))
        else:
            p = 0.01

    if n < 1 or not (0 < p < 1):
        return None

    return {"n": n, "p": p}


def _calcular_bloom(params):
    def fazer():
        mod = carregar("filtro-bloom", "blm_core")
        n = params["n"]
        p = params["p"]
        res = mod.size_report(n, p)
        pct_txt = f"{p * 100:g}%"
        kb_txt = f"{res['m_kib']} KiB" if res["m_kib"] >= 1.0 else f"{res['m_bytes']} B"
        return _sair(
            f"Filtro de Bloom: {res['m_bits']:,} bits ({kb_txt}), k = {res['k_hashes']} hashes".replace(",", "."),
            f"Para {n:,} itens com {pct_txt} de falso positivo ({res['bits_per_item']:.1f} bits/item). Erro real: {res['p_actual'] * 100:.3f}%.".replace(",", "."),
            "Filtro de Bloom",
        )
    return _chamar(fazer)


def _formatar_hora_solar(h_float):
    h = int(h_float) % 24
    m = int(round((h_float - int(h_float)) * 60))
    if m >= 60:
        h = (h + 1) % 24
        m = 0
    return f"{h:02d}:{m:02d}"


def _extrair_posicao_solar(texto):
    t = norm(texto)
    if not any(k in t for k in ["posicao solar", "azimute solar", "elevacao solar", "spa solar"]):
        return None

    lat = None
    lon = None
    utc = -3.0
    cidade_nome = None

    cidades = {
        "sao paulo": (-23.5505, -46.6333, -3.0, "São Paulo"),
        "sp": (-23.5505, -46.6333, -3.0, "São Paulo"),
        "brasilia": (-15.7975, -47.8919, -3.0, "Brasília"),
        "rio": (-22.9068, -43.1729, -3.0, "Rio de Janeiro"),
        "recife": (-8.0476, -34.8770, -3.0, "Recife"),
        "manaus": (-3.1190, -60.0217, -4.0, "Manaus"),
        "lisboa": (38.7223, -9.1393, 0.0, "Lisboa"),
        "londres": (51.5074, -0.1278, 0.0, "Londres"),
        "toquio": (35.6762, 139.6503, 9.0, "Tóquio"),
        "tokyo": (35.6762, 139.6503, 9.0, "Tóquio"),
        "nova york": (40.7128, -74.0060, -5.0, "Nova York"),
    }

    for c_key, c_vals in cidades.items():
        if re.search(r"\b" + re.escape(c_key) + r"\b", t):
            lat, lon, utc, cidade_nome = c_vals
            break

    m_lat = re.search(r"lat(?:itude)?\s*[:=]?\s*(-?\d+(?:\.\d+)?)", t)
    if m_lat:
        lat = float(m_lat.group(1))

    m_lon = re.search(r"lon(?:gitude)?\s*[:=]?\s*(-?\d+(?:\.\d+)?)", t)
    if m_lon:
        lon = float(m_lon.group(1))

    m_utc = re.search(r"utc\s*([+-]?\d+(?:\.\d+)?)", t)
    if m_utc:
        utc = float(m_utc.group(1))

    if lat is None:
        lat, lon, utc, cidade_nome = cidades["sao paulo"]

    dia = 15
    mes = 3
    m_data = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", t)
    if m_data:
        dia = int(m_data.group(1))
        mes = int(m_data.group(2))

    hora = 12.0
    m_hora = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(?:h|horas?)\b", t)
    if m_hora:
        h = float(m_hora.group(1))
        minuto = float(m_hora.group(2)) if m_hora.group(2) else 0.0
        hora = h + minuto / 60.0
    else:
        m_h_simples = re.search(r"hora\s*[:=]?\s*(\d{1,2}(?:\.\d+)?)", t)
        if m_h_simples:
            hora = float(m_h_simples.group(1))

    return {
        "lat": lat,
        "lon": lon,
        "utc": utc,
        "dia": dia,
        "mes": mes,
        "hora": hora,
        "cidade": cidade_nome,
    }


def _calcular_posicao_solar(params):
    def fazer():
        mod = carregar("calculadora-posicao-solar-astronomia", "spa_core")
        lat = params["lat"]
        lon = params["lon"]
        utc = params["utc"]
        dia = params["dia"]
        mes = params["mes"]
        hora = params["hora"]
        cidade = params.get("cidade")

        res = mod.calcular_posicao_solar(lat, lon, utc, dia, mes, hora)

        h_fmt = _formatar_hora_solar(hora)
        nascer = _formatar_hora_solar(res.hora_nascer_sol)
        por = _formatar_hora_solar(res.hora_por_sol)
        local_str = f" em {cidade}" if cidade else f" (lat {lat:.2f}, lon {lon:.2f})"

        return _sair(
            f"Posição Solar às {h_fmt}{local_str}: Elevação {res.elevacao_deg:.1f}°, Azimute {res.azimute_deg:.1f}°",
            f"Zenite: {res.zenite_deg:.1f}°. Nascer: {nascer}, Pôr: {por} (duração: {res.duracao_dia_horas:.1f}h). Irradiância: {res.irradiancia_direta_w_m2:.0f} W/m².",
            "Posição Solar e Astronomia",
        )
    return _chamar(fazer)


def _extrair_spline(texto):
    t = norm(texto)
    if not any(k in t for k in ["spline", "splines", "catmull rom"]):
        return None

    x_eval = None
    m_eval = re.search(r"(?:em|para|avaliar|x\s*[:=])\s*(-?\d+(?:\.\d+)?)", t)
    if m_eval:
        try:
            x_eval = float(m_eval.group(1))
        except ValueError:
            pass

    t_clean = re.sub(r"\b(splines?|catmull\s*rom|interpolacao|pontos?|em|para|avaliar|x|y)\b", " ", t)
    nums = [float(v) for v in re.findall(r"[-+]?\d*\.?\d+", t_clean)]

    xs = []
    ys = []
    if len(nums) >= 4 and len(nums) % 2 == 0:
        for i in range(0, len(nums), 2):
            xs.append(nums[i])
            ys.append(nums[i + 1])
    elif len(nums) >= 5 and x_eval is not None:
        for val in nums:
            if abs(val - x_eval) < 1e-9:
                nums.remove(val)
                break
        if len(nums) >= 4 and len(nums) % 2 == 0:
            for i in range(0, len(nums), 2):
                xs.append(nums[i])
                ys.append(nums[i + 1])

    if len(xs) < 2:
        xs = [0.0, 1.0, 2.0, 3.0]
        ys = [0.0, 2.0, 1.0, 3.0]

    pts = sorted(zip(xs, ys), key=lambda p: p[0])
    xs_ord = []
    ys_ord = []
    for x_val, y_val in pts:
        if not xs_ord or x_val > xs_ord[-1]:
            xs_ord.append(x_val)
            ys_ord.append(y_val)

    if len(xs_ord) < 2:
        xs_ord = [0.0, 1.0, 2.0, 3.0]
        ys_ord = [0.0, 2.0, 1.0, 3.0]

    if x_eval is None:
        x_eval = (xs_ord[0] + xs_ord[-1]) / 2.0

    return {"xs": xs_ord, "ys": ys_ord, "x_eval": x_eval}


def _calcular_spline(params):
    def fazer():
        mod = carregar("estudio-splines", "spl_core")
        xs = params["xs"]
        ys = params["ys"]
        x_eval = params["x_eval"]

        spline = mod.natural_cubic_spline(xs, ys)
        y_eval = mod.evaluate_spline(spline, x_eval)

        return _sair(
            f"Spline Cúbico em x = {x_eval:g}: y = {y_eval:.4f}",
            f"{len(xs)} pontos interpolados [{xs[0]:g} a {xs[-1]:g}]. {len(spline['segments'])} segmentos cúbicos (condição natural S''=0).",
            "Estúdio de Splines",
        )
    return _chamar(fazer)


def _extrair_agua_filtro(texto):
    t = norm(texto)
    if "caixa dagua" in t:
        return None
    if not any(k in t for k in ["agua mineral", "mineral vs filtro", "galao ou filtro", "galao vs filtro"]):
        if not ("galao" in t and "filtro" in t):
            return None

    preco_galao = 14.0
    litros_galao = 20.0
    consumo_litros_mes = 60.0
    preco_filtro = 350.0
    vida_filtro_meses = 12.0
    energia_mes = 0.0
    manutencao_mes = 0.0

    m_galao = re.search(r"galao\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_galao:
        preco_galao = float(m_galao.group(1).replace(",", "."))

    m_litros = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:l|litros)\s*(?:por\s*mes|ao\s*mes|/mes|mes)", t)
    if m_litros:
        consumo_litros_mes = float(m_litros.group(1).replace(",", "."))
    else:
        m_cons = re.search(r"consumo\s*[:=]?\s*(\d+(?:[.,]\d+)?)", t)
        if m_cons:
            consumo_litros_mes = float(m_cons.group(1).replace(",", "."))

    m_filtro = re.search(r"filtro\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_filtro:
        preco_filtro = float(m_filtro.group(1).replace(",", "."))

    m_vida = re.search(r"(\d+(?:[.,]\d+)?)\s*meses", t)
    if m_vida:
        vida_filtro_meses = float(m_vida.group(1).replace(",", "."))

    return {
        "preco_galao": preco_galao,
        "litros_galao": litros_galao,
        "consumo_litros_mes": consumo_litros_mes,
        "preco_filtro": preco_filtro,
        "vida_filtro_meses": vida_filtro_meses,
        "energia_mes": energia_mes,
        "manutencao_mes": manutencao_mes,
    }


def _calcular_agua_filtro(params):
    def fazer():
        mod = carregar("agua-mineral-vs-filtro", "agm_core")
        res = mod.calcular(
            params["preco_galao"],
            params["litros_galao"],
            params["consumo_litros_mes"],
            params["preco_filtro"],
            params["vida_filtro_meses"],
            params["energia_mes"],
            params["manutencao_mes"],
        )
        venc = "Filtro" if res["vencedor"] == "filtro" else ("Água Mineral" if res["vencedor"] == "mineral" else "Empate")
        pay_str = f" Payback: {res['payback_meses']:.1f} meses." if res.get("payback_meses") else ""
        return _sair(
            f"Água Mineral × Filtro: mais econômico é {venc} (diferença de {_brl(res['diferenca'])}/mês)",
            f"Mineral: {_brl(res['mensal_mineral'])}/mês ({_brl(res['custo_litro_mineral'])}/L) vs Filtro: {_brl(res['mensal_filtro'])}/mês ({_brl(res['custo_litro_filtro'])}/L). Economia anual: {_brl(res['economia_anual'])}.{pay_str}",
            "Água Mineral × Filtro",
        )
    return _chamar(fazer)


def _extrair_acustica(texto):
    t = norm(texto)
    if any(k in t for k in ["aquario", "piscina"]):
        return None
    if not any(k in t for k in ["acustica", "rt60", "reverberacao", "sabine"]):
        return None

    l, w, h = 5.0, 4.0, 2.8
    m_dim = re.search(r"(\d+(?:[.,]\d+)?)\s*[xX*]\s*(\d+(?:[.,]\d+)?)\s*[xX*]\s*(\d+(?:[.,]\d+)?)", t)
    if m_dim:
        l = float(m_dim.group(1).replace(",", "."))
        w = float(m_dim.group(2).replace(",", "."))
        h = float(m_dim.group(3).replace(",", "."))
    else:
        m_l = re.search(r"(?:comprimento|comp)\s*[:=]?\s*(\d+(?:[.,]\d+)?)", t)
        m_w = re.search(r"(?:largura|larg)\s*[:=]?\s*(\d+(?:[.,]\d+)?)", t)
        m_h = re.search(r"(?:altura|alt|pe\s*direito)\s*[:=]?\s*(\d+(?:[.,]\d+)?)", t)
        if m_l:
            l = float(m_l.group(1).replace(",", "."))
        if m_w:
            w = float(m_w.group(1).replace(",", "."))
        if m_h:
            h = float(m_h.group(1).replace(",", "."))

    alpha = 0.20
    if "estudio" in t or "podcast" in t:
        alpha = 0.65
    elif "cinema" in t or "home theater" in t:
        alpha = 0.45
    elif "aula" in t:
        alpha = 0.20
    elif "eco" in t or "vazio" in t:
        alpha = 0.08
    else:
        m_abs = re.search(r"(?:absorcao|alpha|alfa)\s*[:=]?\s*(0[.,]\d+)", t)
        if m_abs:
            alpha = float(m_abs.group(1).replace(",", "."))

    return {"length_m": l, "width_m": w, "height_m": h, "alpha": alpha}


def _calcular_acustica(params):
    def fazer():
        mod = carregar("calculadora-acustica-salas", "acu_core")
        res = mod.calculate_room_acoustics(
            params["length_m"],
            params["width_m"],
            params["height_m"],
            params["alpha"],
        )
        l, w, h = params["length_m"], params["width_m"], params["height_m"]
        return _sair(
            f"Acústica da Sala ({l:.1f}x{w:.1f}x{h:.1f}m, {res['volume_m3']} m³): RT60 Sabine = {res['rt60_sabine_s']:.2f}s (Eyring = {res['rt60_eyring_s']:.2f}s)",
            f"Frequência de Schroeder: {res['schroeder_freq_hz']:.0f} Hz. Área: {res['surface_area_m2']} m². {res['recommendation']}",
            "Acústica de Salas",
        )
    return _chamar(fazer)


def _extrair_academia_casa(texto):
    t = norm(texto)
    if any(k in t for k in ["1rm", "anilhas"]):
        return None
    if not any(k in t for k in ["academia vs equipamentos", "academia vs casa", "home gym", "academia ou home gym", "treinar em casa"]):
        if not ("academia" in t and ("equipamento" in t or "casa" in t or "home" in t)):
            return None

    mensalidade = 150.0
    meses_horizonte = 24
    custo_equipamentos = 2000.0
    manutencao_mes = 10.0

    m_mensal = re.search(r"(?:mensalidade|mensal|academia)\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_mensal:
        mensalidade = float(m_mensal.group(1).replace(",", "."))

    m_equip = re.search(r"(?:equipamentos?|compra|investimento|casa)\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_equip:
        custo_equipamentos = float(m_equip.group(1).replace(",", "."))

    m_meses = re.search(r"(\d+)\s*(?:meses|mes)", t)
    if m_meses:
        meses_horizonte = int(m_meses.group(1))

    m_manut = re.search(r"manutencao\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_manut:
        manutencao_mes = float(m_manut.group(1).replace(",", "."))

    return {
        "mensalidade": mensalidade,
        "meses_horizonte": meses_horizonte,
        "custo_equipamentos": custo_equipamentos,
        "manutencao_mes": manutencao_mes,
        "taxa_matricula_mes": 0.0,
    }


def _calcular_academia_casa(params):
    def fazer():
        mod = carregar("academia-vs-equipamentos", "acd_core")
        res = mod.comparar(
            params["mensalidade"],
            params["meses_horizonte"],
            params["custo_equipamentos"],
            params["manutencao_mes"],
            params["taxa_matricula_mes"],
        )
        melhor_str = "Equipamentos em Casa" if res["melhor"] == "casa" else ("Academia" if res["melhor"] == "academia" else "Empate")
        pay_str = f" Payback: ~{res['break_even_meses']:.1f} meses." if res.get("break_even_meses") else ""
        return _sair(
            f"Academia × Home Gym: mais econômico é {melhor_str} em {res['meses']} meses",
            f"Academia: {_brl(res['academia'])} vs Casa: {_brl(res['casa'])}. Diferença: {_brl(abs(res['economia']))}.{pay_str}",
            "Academia × Equipamentos",
        )
    return _chamar(fazer)


def _extrair_anki(texto):
    t = norm(texto)
    if not any(k in t for k in ["anki", "flashcard", "flashcards"]):
        return None

    novos_dia = 15.0
    total_cards = 1500
    minutos_disp = 25.0
    segundos_por_card = 8.0
    retencao = 85.0

    m_novos = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:novos?|novos/dia|novos\s*por\s*dia|cards?\s*novos?)", t)
    if m_novos:
        novos_dia = float(m_novos.group(1).replace(",", "."))

    m_total = re.search(r"(\d+)\s*(?:cards?|cartoes|flashcards?|total)", t)
    if m_total:
        total_cards = int(m_total.group(1))

    m_min = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:min|minutos|minutos/dia|tempo)", t)
    if m_min:
        minutos_disp = float(m_min.group(1).replace(",", "."))

    m_ret = re.search(r"(\d+(?:[.,]\d+)?)\s*%", t)
    if m_ret:
        val = float(m_ret.group(1).replace(",", "."))
        if 50.0 <= val <= 99.0:
            retencao = val

    return {
        "novos_dia": novos_dia,
        "total_cards": total_cards,
        "minutos_disp": minutos_disp,
        "segundos_por_card": segundos_por_card,
        "retencao": retencao,
    }


def _calcular_anki(params):
    def fazer():
        mod = carregar("meta-revisoes-anki-diarias", "ank_core")
        novos = params["novos_dia"]
        minutos = params["minutos_disp"]
        res = mod.calcular_carga(
            novos,
            params["total_cards"],
            minutos,
            params["segundos_por_card"],
            retencao_alvo_percent=params["retencao"],
            modo_intervalo="retencao",
        )
        status_meta = f"CABE (folga {res.minutos_folga:+.1f} min)" if res.cabe_na_meta else f"ESTOURA ({res.minutos_folga:+.1f} min)"
        return _sair(
            f"Meta Anki: {res.revisoes_por_dia:.0f} revisões/dia ({res.minutos_necessarios:.1f} min para {novos:g} novos/dia)",
            f"Fila jovem: {res.parte_jovem:.0f}, maduros: {res.parte_madura:.0f}. Meta {minutos:.0f} min: {status_meta}. Sugestão: ~{res.novos_sugeridos:g} novos/dia.",
            "Meta de Revisões Anki",
        )
    return _chamar(fazer)


def _extrair_aerodinamica(texto):
    t = norm(texto)
    if not any(k in t for k in ["aerodinamica", "arrasto", "sustentacao", "estol", "planeio", "cessna", "boeing", "drone"]):
        return None

    aero = "Cessna 172 Skyhawk"
    if "boeing" in t or "737" in t:
        aero = "Boeing 737-800"
    elif "drone" in t or "vtol" in t:
        aero = "Drone VTOL Asa Fixa"
    elif "planador" in t:
        aero = "Planador de Alta Performance"

    v_kmh = 220.0 if aero == "Cessna 172 Skyhawk" else (820.0 if aero == "Boeing 737-800" else (70.0 if aero == "Drone VTOL Asa Fixa" else 110.0))
    alt_m = 1500.0

    m_vel = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:km/h|kmh)", t)
    if m_vel:
        v_kmh = float(m_vel.group(1).replace(",", "."))
    else:
        m_v_simples = re.search(r"velocidade\s*[:=]?\s*(\d+(?:[.,]\d+)?)", t)
        if m_v_simples:
            v_kmh = float(m_v_simples.group(1).replace(",", "."))

    m_alt = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m\b|metros)", t)
    if m_alt:
        alt_m = float(m_alt.group(1).replace(",", "."))
    else:
        m_alt_simples = re.search(r"altitude\s*[:=]?\s*(\d+(?:[.,]\d+)?)", t)
        if m_alt_simples:
            alt_m = float(m_alt_simples.group(1).replace(",", "."))

    return {
        "aeronave": aero,
        "velocidade_kmh": v_kmh,
        "altitude_m": alt_m,
    }


def _calcular_aerodinamica(params):
    def fazer():
        mod = carregar("calculadora-aerodinamica-arrasto-sustentacao", "aer_core")
        nome = params["aeronave"]
        spec = mod.AERONAVES_PREDEFINIDAS[nome]
        v_kmh = params["velocidade_kmh"]
        alt_m = params["altitude_m"]

        res = mod.calcular_desempenho_voo(
            spec["massa_kg"],
            spec["area_asa_m2"],
            spec["envergadura_m"],
            spec["cd0"],
            spec["oswald_e"],
            spec["cl_max"],
            v_kmh,
            alt_m,
        )

        return _sair(
            f"Aerodinâmica ({nome} a {res.velocidade_kmh:.0f} km/h, {res.altitude_m:.0f}m): L/D = {res.razao_planeio_ld:.1f}, Estol = {res.velocidade_estol_kmh:.0f} km/h",
            f"CL: {res.cl_operacao:.3f}, CD: {res.cd_total:.4f} (parasita {res.cd_parasita:.3f} + induzido {res.cd_induzido:.4f}). Potência: {res.potencia_requerida_hp:.1f} HP ({res.potencia_requerida_kw:.1f} kW).",
            "Aerodinâmica & Arrasto",
        )
    return _chamar(fazer)


def _extrair_anticoncepcional(texto):
    t = norm(texto)
    if not any(k in t for k in ["anticoncepcional", "cartela", "pilula"]):
        return None

    tipo = "21"
    if "24" in t:
        tipo = "24"
    elif "28" in t:
        tipo = "28"
    elif "continuo" in t:
        tipo = "continuo"

    m_horas = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:h|horas?)\s*(?:de\s*atraso|atrasada|esquecida)?", t)
    m_esqueci = re.search(r"esquec(?:i|eu|imento)", t)
    if m_esqueci or ("atraso" in t and m_horas):
        horas = float(m_horas.group(1).replace(",", ".")) if m_horas else 8.0
        m_dia = re.search(r"(?:dia|comprimido)\s*[:=]?\s*(\d+)", t)
        dia = int(m_dia.group(1)) if m_dia else 10
        return {"modo": "esquecimento", "horas": horas, "dia": dia, "tipo": tipo}

    from datetime import date
    m_data = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", t)
    hoje = date.today()
    if m_data:
        d = int(m_data.group(1))
        m = int(m_data.group(2))
        y = int(m_data.group(3)) if m_data.group(3) else hoje.year
        if y < 100:
            y += 2000
        inicio = date(y, m, d)
    else:
        from datetime import timedelta
        inicio = hoje - timedelta(days=10)

    return {"modo": "ciclo", "inicio": inicio, "tipo": tipo}


def _calcular_anticoncepcional(params):
    def fazer():
        mod = carregar("cartela-anticoncepcional", "acp_core")
        tipo = params["tipo"]
        if params["modo"] == "esquecimento":
            res = mod.orientacao_esquecimento(params["horas"], params["dia"], tipo)
            return _sair(
                f"Esquecimento de Pílula ({res['horas_atraso']:.0f}h atraso, dia {res['dia_ativo']}): Nível {res['nivel'].upper()}",
                f"{res['texto']} ({res['aviso']})",
                "Cartela Anticoncepcional",
            )
        else:
            from datetime import date
            res = mod.dia_na_cartela(params["inicio"], date.today(), tipo)
            if res["em_pausa"]:
                rep = f"Cartela Anticoncepcional: Em PAUSA (dia {res['pausa_dia']} de pausa)"
            else:
                rep = f"Cartela Anticoncepcional: Comprimido {res['comprimido']} de {res['ativos']}"
            return _sair(
                rep,
                f"Dia {res['dia']} do ciclo ({res['rotulo']}). Faltam {max(0, res['ativos'] - res['dia'] + 1)} dias para início da pausa.",
                "Cartela Anticoncepcional",
            )
    return _chamar(fazer)


def _extrair_sessao_foco(texto):
    t = norm(texto)
    if not any(k in t for k in ["sessao de foco", "blocos de foco", "planejar foco", "foco profundo", "planejador de foco", "sessao foco"]):
        return None

    minutos_totais = 180
    bloco_foco_min = 50
    pausa_min = 10
    horario_inicio = "09:00"

    m_h = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:h|horas)\b", t)
    if m_h:
        minutos_totais = int(float(m_h.group(1).replace(",", ".")) * 60)
    else:
        m_min = re.search(r"(\d+)\s*(?:min|minutos)\b", t)
        if m_min:
            minutos_totais = int(m_min.group(1))

    m_bloco = re.search(r"bloco\s*[:=]?\s*(\d+)", t)
    if m_bloco:
        bloco_foco_min = int(m_bloco.group(1))

    m_pausa = re.search(r"pausa\s*[:=]?\s*(\d+)", t)
    if m_pausa:
        pausa_min = int(m_pausa.group(1))

    m_inicio = re.search(r"\b(\d{1,2}:\d{2})\b", t)
    if m_inicio:
        horario_inicio = m_inicio.group(1)

    return {
        "minutos_totais": minutos_totais,
        "bloco_foco_min": bloco_foco_min,
        "pausa_min": pausa_min,
        "horario_inicio": horario_inicio,
    }


def _calcular_sessao_foco(params):
    def fazer():
        mod = carregar("planejador-sessao-foco", "fcs_core")
        res = mod.montar_plano(
            params["minutos_totais"],
            params["bloco_foco_min"],
            params["pausa_min"],
            "",
            params["horario_inicio"],
        )
        ini = res.agenda[0].inicio if res.agenda else params["horario_inicio"]
        fim = res.agenda[-1].fim if res.agenda else ini
        return _sair(
            f"Sessão de Foco: {res.blocos_foco} blocos ({res.minutos_foco_total} min foco + {res.minutos_pausa_total} min pausas, aproveitamento {res.aproveitamento_pct:.0f}%)",
            f"Agenda: {ini} às {fim} (ciclos {params['bloco_foco_min']}m foco + {params['pausa_min']}m pausa). Janela {params['minutos_totais']} min (sobra {res.minutos_sobra} min).",
            "Planejador de Sessão de Foco",
        )
    return _chamar(fazer)


def _extrair_amortizacao(texto):
    t = norm(texto)
    if not any(k in t for k in ["amortizacao extra", "amortizar", "reduzir prazo", "financiamento vs consorcio", "sac vs price"]):
        return None

    principal = 200000.0
    annual_rate = 10.5
    months = 360
    system = "PRICE" if "price" in t else "SAC"
    extra = 500.0

    m_val = re.search(r"(?:valor|saldo|financiamento|divida|de)\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_val:
        v = float(m_val.group(1).replace(",", "."))
        if v >= 1000.0:
            principal = v

    m_taxa = re.search(r"(\d+(?:[.,]\d+)?)\s*%", t)
    if m_taxa:
        annual_rate = float(m_taxa.group(1).replace(",", "."))

    m_meses = re.search(r"(\d+)\s*(?:meses|mes|parcelas)\b", t)
    if m_meses:
        months = int(m_meses.group(1))

    m_extra = re.search(r"(?:extra|amortizacao|amortizar|aporte)\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_extra:
        extra = float(m_extra.group(1).replace(",", "."))

    return {
        "principal": principal,
        "annual_rate": annual_rate,
        "months": months,
        "system": system,
        "extra": extra,
    }


def _calcular_amortizacao(params):
    def fazer():
        mod = carregar("comparador-credito", "crd_core")
        res = mod.simulate_loan_with_extra_amort(
            params["principal"],
            params["annual_rate"],
            params["months"],
            params["system"],
            params["extra"],
            "prazo",
        )
        return _sair(
            f"Amortização Extra {res['system']}: Economia de {_brl(res['interest_saved'])} em juros (corta {res['months_saved']} meses)",
            f"Prazo reduz de {res['original_months']} para {res['optimized_months']} meses. Juros caem de {_brl(res['original_interest'])} para {_brl(res['optimized_interest'])} com aporte de {_brl(params['extra'])}/mês.",
            "Amortização Extra SAC/PRICE",
        )
    return _chamar(fazer)


def _extrair_esporte_infantil(texto):
    t = norm(texto)
    if not any(k in t for k in ["esporte infantil", "academia infantil", "natacao infantil", "judo infantil", "futebol infantil", "ballet infantil"]):
        return None

    mensalidade = 200.0
    meses = 12
    uniforme = 150.0
    taxa_matricula = 100.0
    transporte_mes = 50.0

    m_mensal = re.search(r"(?:mensalidade|mensal)\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_mensal:
        mensalidade = float(m_mensal.group(1).replace(",", "."))

    m_unif = re.search(r"uniforme\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_unif:
        uniforme = float(m_unif.group(1).replace(",", "."))

    m_matr = re.search(r"matricula\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_matr:
        taxa_matricula = float(m_matr.group(1).replace(",", "."))

    m_trans = re.search(r"transporte\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_trans:
        transporte_mes = float(m_trans.group(1).replace(",", "."))

    m_meses = re.search(r"(\d+)\s*(?:meses|mes)\b", t)
    if m_meses:
        meses = int(m_meses.group(1))

    return {
        "mensalidade": mensalidade,
        "meses": meses,
        "uniforme": uniforme,
        "taxa_matricula": taxa_matricula,
        "competicoes": 0.0,
        "transporte_mes": transporte_mes,
    }


def _calcular_esporte_infantil(params):
    def fazer():
        mod = carregar("custo-academia-infantil", "aci_core")
        res = mod.calcular(
            params["mensalidade"],
            params["meses"],
            params["uniforme"],
            params["taxa_matricula"],
            params["competicoes"],
            params["transporte_mes"],
        )
        return _sair(
            f"Custo de Esporte Infantil: Média real de {_brl(res['media_mes'])}/mês (Total {_brl(res['total'])} em {params['meses']} meses)",
            f"Mensalidades: {_brl(res['mensalidades'])}, Extras (uniforme/matrícula): {_brl(res['extras'])}, Transporte: {_brl(res['transporte'])}.",
            "Custo de Esporte Infantil",
        )
    return _chamar(fazer)


def _extrair_decimo_terceiro(texto):
    t = norm(texto)
    if "rescisao" in t:
        return None
    if not any(k in t for k in ["decimo terceiro", "13o", "13 salario"]):
        return None

    salario = 3000.0
    meses = 12.0
    adiantamento = 0.0

    m_sal = re.search(r"(?:salario|base|de)\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_sal:
        v = float(m_sal.group(1).replace(",", "."))
        if v >= 100.0:
            salario = v

    m_meses = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:meses|mes)\b", t)
    if m_meses:
        meses = float(m_meses.group(1).replace(",", "."))

    m_adiant = re.search(r"(?:adiantamento|adiantado|1a\s*parcela)\s*[:=]?\s*(?:r\$)?\s*(\d+(?:[.,]\d+)?)", t)
    if m_adiant:
        adiantamento = float(m_adiant.group(1).replace(",", "."))

    return {
        "salario": salario,
        "meses": meses,
        "adiantamento": adiantamento,
    }


def _calcular_decimo_terceiro(params):
    def fazer():
        mod = carregar("decimo-terceiro", "d13_core")
        res = mod.calcular(params["salario"], params["meses"], params["adiantamento"])
        return _sair(
            f"13º Salário ({res['meses_contados']}/12 avos): Bruto {_brl(res['bruto'])}, a receber {_brl(res['a_receber'])}",
            f"Base: {_brl(params['salario'])}, Adiantamento já recebido: {_brl(res['adiantamento'])}. Não inclui deduções de INSS/IRRF.",
            "13º Salário Proporcional",
        )
    return _chamar(fazer)


def _extrair_acl(texto):
    t = norm(texto)
    if not any(k in t for k in ["acl ntfs", "inspetor acl", "permissoes ntfs", "dono ntfs", "regras ntfs"]):
        return None

    path = os.getcwd()
    m_path = re.search(r"([a-zA-Z]:\\[^\s\"'\n\r\t]+)", texto)
    if m_path:
        cand = m_path.group(1).strip()
        if os.path.exists(cand):
            path = cand

    return {"path": path}


def _calcular_acl(params):
    def fazer():
        mod = carregar("inspetor-acl-ntfs", "acl_core")
        info = mod.ler_acl(params["path"])
        base = os.path.basename(info["path"]) or info["path"]
        prot = "sim" if info["protegido"] else "não"
        return _sair(
            f"ACL NTFS ({base}): Dono {info['dono']}, {len(info['regras'])} regras",
            f"Herança bloqueada: {prot}. Grupo: {info['grupo']}. Caminho: {info['path']}.",
            "Inspetor ACL NTFS",
        )
    return _chamar(fazer)


def _extrair_marchas_bike(texto):
    t = norm(texto)
    if "engrenagem" in t or "modulo" in t:
        return None
    if not any(k in t for k in ["marcha", "coroa", "pinhao", "bike", "bicicleta", "cadencia"]):
        return None
    if not any(k in t for k in ["coroa", "pinhao", "marchas bike", "relacao", "pedalada", "desenvolvimento"]):
        if not re.search(r"\b\d{2}\s*[xX/]\s*\d{1,2}\b", t):
            return None

    coroa = 34
    pinhao = 15
    cadencia = 80.0

    m_par = re.search(r"\b(\d{2})\s*[xX/]\s*(\d{1,2})\b", t)
    if m_par:
        coroa = int(m_par.group(1))
        pinhao = int(m_par.group(2))
    else:
        m_c = re.search(r"coroa\s*[:=]?\s*(\d+)", t)
        if m_c:
            coroa = int(m_c.group(1))
        m_p = re.search(r"pinhao\s*[:=]?\s*(\d+)", t)
        if m_p:
            pinhao = int(m_p.group(1))

    m_cad = re.search(r"(?:cadencia|rpm)\s*[:=]?\s*(\d+(?:[.,]\d+)?)", t)
    if m_cad:
        cadencia = float(m_cad.group(1).replace(",", "."))

    return {
        "coroa": coroa,
        "pinhao": pinhao,
        "cadencia": cadencia,
    }


def _calcular_marchas_bike(params):
    def fazer():
        mod = carregar("calculadora-marchas-bike", "bik_core")
        c = params["coroa"]
        p = params["pinhao"]
        cad = params["cadencia"]
        circ_mm = mod.circunferencia("700c / 29\"", 25)
        rel = mod.relacao(c, p)
        desenv = mod.desenvolvimento_m(c, p, circ_mm)
        vel = mod.velocidade_kmh(c, p, circ_mm, cad)
        gi = mod.gear_inches(c, p, circ_mm)

        return _sair(
            f"Marcha {c}x{p}: Relação {rel:.2f}, {desenv:.2f} m/pedalada ({vel:.1f} km/h a {cad:.0f} rpm)",
            f"Gear inches: {gi:.1f}\". Circunferência roda (700x25c): {circ_mm:.0f} mm.",
            "Marchas de Bicicleta",
        )
    return _chamar(fazer)


def _extrair_forma_bolo(texto):
    t = norm(texto)
    if not any(k in t for k in ["forma de bolo", "formas de bolo", "conversor de forma", "forma redonda", "forma bolo"]):
        return None

    orig = {"forma": "Redonda", "a": 20.0, "altura": 6.0, "b": 0.0, "furo": 0.0}
    dest = {"forma": "Redonda", "a": 25.0, "altura": 6.0, "b": 0.0, "furo": 0.0}

    partes = re.split(r"\b(?:para|pra|->)\b", t)
    t_orig = partes[0]
    t_dest = partes[1] if len(partes) > 1 else ""

    m_ret_o = re.search(r"(\d+(?:[.,]\d+)?)\s*[xX*]\s*(\d+(?:[.,]\d+)?)", t_orig)
    if m_ret_o:
        orig["forma"] = "Retangular"
        orig["a"] = float(m_ret_o.group(1).replace(",", "."))
        orig["b"] = float(m_ret_o.group(2).replace(",", "."))
    else:
        m_num_o = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:cm)?", t_orig)
        if m_num_o:
            orig["a"] = float(m_num_o.group(1).replace(",", "."))

    if t_dest:
        m_ret_d = re.search(r"(\d+(?:[.,]\d+)?)\s*[xX*]\s*(\d+(?:[.,]\d+)?)", t_dest)
        if m_ret_d:
            dest["forma"] = "Retangular"
            dest["a"] = float(m_ret_d.group(1).replace(",", "."))
            dest["b"] = float(m_ret_d.group(2).replace(",", "."))
        else:
            m_num_d = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:cm)?", t_dest)
            if m_num_d:
                dest["a"] = float(m_num_d.group(1).replace(",", "."))

    return {"origem": orig, "destino": dest}


def _calcular_forma_bolo(params):
    def fazer():
        mod = carregar("conversor-formas-bolo", "bol_core")
        orig = params["origem"]
        dest = params["destino"]
        fator = mod.fator_escala(orig, dest)
        vo = mod.volume(orig["forma"], orig["a"], orig["altura"], orig.get("b", 0), orig.get("furo", 0))
        vd = mod.volume(dest["forma"], dest["a"], dest["altura"], dest.get("b", 0), dest.get("furo", 0))

        nome_o = f"{orig['forma']} {orig['a']:.0f}" + (f"x{orig['b']:.0f}" if orig['b'] > 0 else "") + "cm"
        nome_d = f"{dest['forma']} {dest['a']:.0f}" + (f"x{dest['b']:.0f}" if dest['b'] > 0 else "") + "cm"

        return _sair(
            f"Forma de Bolo ({nome_o} → {nome_d}): Escala = {fator:.2f}x receita",
            f"Volume original: {vo:.0f} cm³ vs novo: {vd:.0f} cm³. Multiplique os ingredientes da receita por {fator:.2f}.",
            "Conversor de Formas de Bolo",
        )
    return _chamar(fazer)


def _extrair_cronometro(texto):
    t = norm(texto)
    if not any(k in t for k in ["cronometro", "relogio de xadrez", "xadrez fischer", "cronometragem", "tempo laps"]):
        return None

    m_fischer = re.search(r"\b(\d{1,2})\s*\+\s*(\d{1,2})\b", t)
    if m_fischer or "xadrez" in t or "fischer" in t:
        mins = int(m_fischer.group(1)) if m_fischer else 5
        inc = int(m_fischer.group(2)) if m_fischer else 3
        m_m = re.search(r"(\d+)\s*(?:min|minutos)", t)
        if m_m and not m_fischer:
            mins = int(m_m.group(1))
        m_inc = re.search(r"(?:incremento|inc)\s*[:=]?\s*(\d+)", t)
        if m_inc:
            inc = int(m_inc.group(1))
        return {"modo": "xadrez", "mins": mins, "inc": inc}

    ms = 75420
    m_ms = re.search(r"(\d+)\s*(?:ms|milissegundos)", t)
    if m_ms:
        ms = int(m_ms.group(1))
    else:
        m_s = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:s|segundos)", t)
        if m_s:
            ms = int(float(m_s.group(1).replace(",", ".")) * 1000)

    return {"modo": "tempo", "ms": ms}


def _calcular_cronometro(params):
    def fazer():
        mod = carregar("estudio-cronometro", "crn_core")
        if params["modo"] == "xadrez":
            mins = params["mins"]
            inc = params["inc"]
            clock = mod.ChessClockState(mins, inc)
            t_w = mod.format_milliseconds(clock.white_ms)
            t_b = mod.format_milliseconds(clock.black_ms)
            return _sair(
                f"Relógio de Xadrez ({mins}+{inc} Fischer): Brancas {t_w} vs Pretas {t_b}",
                f"Tempo inicial: {mins} min, incremento: +{inc}s por lance (Fischer). Vez: Brancas.",
                "Estúdio de Cronometragem",
            )
        else:
            ms = params["ms"]
            fmt = mod.format_milliseconds(ms)
            return _sair(
                f"Cronômetro: {fmt} ({ms:,} ms)".replace(",", "."),
                "Formato padrão MM:SS.mmm para tomada de tempo e voltas/laps.",
                "Estúdio de Cronometragem",
            )
    return _chamar(fazer)


def _extrair_base64(texto):
    t = norm(texto)
    if not any(k in t for k in ["base64", "b64"]):
        return None

    m_exp = re.search(r"(\d+)\s*(?:bytes?|kb|mb)", t)
    if "expansao" in t or ("tamanho" in t and m_exp):
        n = int(m_exp.group(1)) if m_exp else 1024
        return {"modo": "expansao", "bytes": n}

    if any(k in t for k in ["decode", "decodificar", "descodificar"]):
        limpo = re.sub(r"(?i)\b(?:decodificar\s+base64|decode\s+base64|base64\s+decod(?:ificar)?|base64\s+decode|decodificar|decode|descodificar)\b", "", texto).strip()
        alvo = limpo if limpo else "b2xhIG11bmRv"
        return {"modo": "decode", "texto": alvo}

    limpo = re.sub(r"(?i)\b(?:codificar\s+base64|encode\s+base64|base64\s+cod(?:ificar)?|base64\s+encode|codificar|encode|base64|b64)\b", "", texto).strip()
    alvo = limpo if limpo else "olá mundo"
    return {"modo": "encode", "texto": alvo}


def _calcular_base64(params):
    def fazer():
        mod = carregar("conversor-base64", "b64_core")
        modo = params["modo"]
        if modo == "expansao":
            n = params["bytes"]
            exp = mod.expansao(n)
            return _sair(
                f"Base64 Expansão: {exp['original']:,} B → {exp['base64']:,} B (+{exp['overhead_pct']:.1f}%)".replace(",", "."),
                f"Razão de crescimento: {exp['razao']:.2f}x (overhead de ~4/3 do Base64).",
                "Conversor Base64",
            )
        elif modo == "decode":
            raw = params["texto"]
            b = mod.decode_to_bytes(raw)
            try:
                dec_str = b.decode("utf-8")
            except UnicodeDecodeError:
                dec_str = f"<{len(b)} bytes binários>"
            return _sair(
                f"Base64 Decode: {dec_str}",
                f"{len(raw)} caracteres decodificados em {len(b)} bytes.",
                "Conversor Base64",
            )
        else:
            raw = params["texto"]
            enc = base64.b64encode(raw.encode("utf-8")).decode("ascii")
            return _sair(
                f"Base64 Encode: {enc}",
                f"{len(raw.encode('utf-8'))} bytes codificados em {len(enc)} caracteres Base64.",
                "Conversor Base64",
            )
    return _chamar(fazer)


_registrar("calculadora-iptu", ["iptu"], _extrair_iptu, _calcular_iptu)
_registrar("calculadora-caucao", ["caucao"], _extrair_caucao, _calcular_caucao)
_registrar("autonomia-caixa-dagua", ["caixa dagua"], _extrair_caixa, _calcular_caixa)
_registrar("diluicao-limpeza", ["diluir limpeza"], _extrair_limpeza, _calcular_limpeza)
_registrar("numero-extenso", ["por extenso"], _extrair_extenso, _calcular_extenso)
_registrar("numero-extenso", ["romano"], _extrair_romano, _calcular_romano)
_registrar("reajuste-aluguel", ["reajuste de aluguel"], _extrair_reajuste, _calcular_reajuste)
_registrar("calculadora-ar-condicionado", ["ar condicionado"], _extrair_btu, _calcular_btu)
_registrar("consumo-energia", ["chuveiro"], _extrair_chuveiro, _calcular_chuveiro)
_registrar("calculadora-simples-nacional", ["simples nacional"], _extrair_das, _calcular_das)
_registrar("teoria-filas", ["fila mm1"], _extrair_fila, _calcular_fila)
_registrar("calculadora-indice-conforto", ["indice de calor"], _extrair_calor, _calcular_calor)
_registrar("calculadora-engrenagens", ["engrenagem"], _extrair_engrenagem, _calcular_engrenagem)
_registrar("cubagem-cargas", ["frete cubado"], _extrair_cubado, _calcular_cubado)
_registrar("estudio-gray-code", ["gray"], _extrair_gray, _calcular_gray)
_registrar("cisterna-chuva", ["cisterna"], _extrair_cisterna, _calcular_cisterna)
_registrar("calculadora-energia-eolica-aerogerador", ["eolica"], _extrair_eolica, _calcular_eolica)
_registrar("dizimo-doacoes", ["dizimo"], _extrair_dizimo, _calcular_dizimo)
_registrar("pensao-alimenticia", ["pensao"], _extrair_pensao, _calcular_pensao)
_registrar("cashback-real", ["cashback"], _extrair_cashback, _calcular_cashback)
_registrar("saldo-prestacoes", ["prestacoes"], _extrair_prestacoes, _calcular_prestacoes)
_registrar("meta-poupanca-viagem", ["poupanca viagem"], _extrair_viagem, _calcular_viagem)
_registrar("custo-total-por-km", ["custo por km"], _extrair_km, _calcular_km)
_registrar("estimativa-frete", ["estimativa de frete"], _extrair_frete, _calcular_frete)
_registrar("custo-pedagio-tag", ["pedagio"], _extrair_tag, _calcular_tag)
_registrar("calculadora-dsr-hora-extra", ["dsr"], _extrair_dsr, _calcular_dsr)
_registrar("calculadora-obra", ["obra", "piso"], _extrair_obra, _calcular_obra)
_registrar("calibragem-pneus", ["calibragem", "pneu"], _extrair_pneu, _calcular_pneu)
_registrar("aluguel-quartos", ["aluguel quarto", "quartos"], _extrair_aluguel_quartos, _calcular_aluguel_quartos)
_registrar("desafio-poupanca", ["desafio", "52 semanas"], _extrair_desafio_poupanca, _calcular_desafio_poupanca)
_registrar("simulador-renda-fixa", ["renda fixa", "cdb", "lci", "lca"], _extrair_renda_fixa, _calcular_renda_fixa)
_registrar("treino-academia", ["1rm", "anilhas", "treino"], _extrair_treino, _calcular_treino)
_registrar("ficha-medica", ["glicemia", "colesterol", "triglicerideos", "creatinina", "vitamina d", "acido urico", "hemoglobina", "estoque de remedio", "comprimidos"], _extrair_ficha_medica, _calcular_ficha_medica)
_registrar("mala-viagem", ["mala de viagem", "mala"], _extrair_mala_viagem, _calcular_mala_viagem)
_registrar("marmitas-semana", ["marmita", "marmitas"], _extrair_marmitas, _calcular_marmitas)
_registrar("calculadora-adicional-noturno", ["adicional noturno", "hora noturna", "noturno"], _extrair_noturno, _calcular_noturno)
_registrar("calculadora-adicional-insalubridade", ["insalubridade", "adicional de insalubridade"], _extrair_insalubridade, _calcular_insalubridade)
_registrar("calculadora-impressao-3d", ["impressao 3d", "filamento 3d"], _extrair_impressao_3d, _calcular_impressao_3d)
_registrar("calculadora-piscina", ["piscina", "cloro piscina"], _extrair_piscina, _calcular_piscina)
_registrar("calculadora-adicional-periculosidade", ["periculosidade", "adicional de periculosidade"], _extrair_periculosidade, _calcular_periculosidade)
_registrar("calculadora-seguro-desemprego", ["seguro desemprego", "seguro-desemprego"], _extrair_seguro_desemprego, _calcular_seguro_desemprego)
_registrar("calculadora-aquario", ["aquario", "aquário"], _extrair_aquario, _calcular_aquario)
_registrar("calculadora-hidraulica-tubulacoes", ["perda de carga", "hidraulica tubo", "tubulacao"], _extrair_hidraulica, _calcular_hidraulica)
_registrar("calculadora-rescisao-trabalhista", ["rescisao", "rescisao clt"], _extrair_rescisao, _calcular_rescisao)
_registrar("calculadora-chmod", ["chmod", "permissao", "permissoes"], _extrair_chmod, _calcular_chmod)
_registrar("calculadora-motores-eletricos", ["motor eletrico", "motores eletricos", "motor"], _extrair_motor, _calcular_motor)
_registrar("filtro-bloom", ["filtro de bloom", "bloom", "filtro bloom"], _extrair_bloom, _calcular_bloom)
_registrar("calculadora-posicao-solar-astronomia", ["posicao solar", "azimute solar", "elevacao solar", "spa solar"], _extrair_posicao_solar, _calcular_posicao_solar)
_registrar("estudio-splines", ["spline", "splines", "catmull rom"], _extrair_spline, _calcular_spline)
_registrar("agua-mineral-vs-filtro", ["agua mineral vs filtro", "mineral vs filtro", "galao ou filtro", "galao vs filtro", "agua mineral"], _extrair_agua_filtro, _calcular_agua_filtro)
_registrar("calculadora-acustica-salas", ["acustica de salas", "acustica sala", "acustica", "rt60", "reverberacao", "sabine"], _extrair_acustica, _calcular_acustica)
_registrar("academia-vs-equipamentos", ["academia vs equipamentos", "academia vs casa", "home gym", "academia ou home gym", "treinar em casa"], _extrair_academia_casa, _calcular_academia_casa)
_registrar("meta-revisoes-anki-diarias", ["anki", "revisoes anki", "flashcards anki", "cards anki", "meta anki"], _extrair_anki, _calcular_anki)
_registrar("calculadora-aerodinamica-arrasto-sustentacao", ["aerodinamica", "arrasto e sustentacao", "sustentacao e arrasto", "velocidade de estol", "razao de planeio", "polar de arrasto"], _extrair_aerodinamica, _calcular_aerodinamica)
_registrar("cartela-anticoncepcional", ["anticoncepcional", "cartela anticoncepcional", "esqueci anticoncepcional", "pilula anticoncepcional", "pausa anticoncepcional"], _extrair_anticoncepcional, _calcular_anticoncepcional)
_registrar("planejador-sessao-foco", ["sessao de foco", "blocos de foco", "planejar foco", "foco profundo", "planejador de foco", "sessao foco"], _extrair_sessao_foco, _calcular_sessao_foco)
_registrar("comparador-credito", ["amortizacao extra", "amortizar", "reduzir prazo", "financiamento vs consorcio", "sac vs price"], _extrair_amortizacao, _calcular_amortizacao)
_registrar("custo-academia-infantil", ["esporte infantil", "academia infantil", "natacao infantil", "judo infantil", "futebol infantil", "ballet infantil"], _extrair_esporte_infantil, _calcular_esporte_infantil)
_registrar("decimo-terceiro", ["decimo terceiro", "13o", "13 salario"], _extrair_decimo_terceiro, _calcular_decimo_terceiro)
_registrar("inspetor-acl-ntfs", ["acl ntfs", "inspetor acl", "permissoes ntfs", "dono ntfs", "regras ntfs"], _extrair_acl, _calcular_acl)
_registrar("calculadora-marchas-bike", ["marcha de bicicleta", "marchas bike", "coroa e pinhao", "cadencia bike", "desenvolvimento marcha", "relacao de marcha"], _extrair_marchas_bike, _calcular_marchas_bike)
_registrar("conversor-formas-bolo", ["forma de bolo", "formas de bolo", "conversor de forma", "forma redonda para retangular", "escala de bolo", "forma bolo"], _extrair_forma_bolo, _calcular_forma_bolo)
_registrar("estudio-cronometro", ["cronometro", "relogio de xadrez", "xadrez fischer", "cronometragem", "tempo laps"], _extrair_cronometro, _calcular_cronometro)
_registrar("conversor-base64", ["base64", "b64", "codificar base64", "decodificar base64"], _extrair_base64, _calcular_base64)
