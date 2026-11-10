# -*- coding: utf-8 -*-
"""Adaptadores da barra para a categoria Outras.

Cada calcular chama o modulo real. Nao refaz a conta. Ficam de fora geradores
de arquivo, inspetores, checklists e o que so varre disco ou guarda cadastro.
"""
from __future__ import annotations

import os
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
