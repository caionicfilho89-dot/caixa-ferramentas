# -*- coding: utf-8 -*-
"""Adaptadores da barra para Arquivos & Sistema e o que caiu nessa categoria.

Cada calcular chama o modulo real. Nao refaz a conta. Ferramenta de arquivo,
pasta ou processo fica de fora: a barra nao varre disco.
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

_RE_DATA = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_RE_RATEIO = re.compile(
    r"([A-Za-zÀ-ÿ]+)\s+pagou\s+(\d+(?:[.,]\d+)?)\s+divide\s+(.+)$",
    re.IGNORECASE,
)
_CORTES = (
    ("frango inteiro", "Frango inteiro"),
    ("costela bovina", "Costela bovina"),
    ("lombo suino", "Lombo suino"),
    ("lombo", "Lombo suino"),
    ("peixe inteiro", "Peixe inteiro"),
    ("picanha", "Picanha"),
    ("pernil", "Pernil"),
    ("peru", "Peru"),
    ("lagarto", "Lagarto"),
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


def _depois_cru(texto, marca):
    """Tira so o espaco separador. O corpo pode comecar com quebra de linha."""
    t = norm(texto)
    i = t.find(norm(marca))
    if i < 0:
        return None
    return texto[i + len(norm(marca)):].lstrip(" ")


def _chamar(fn):
    try:
        return fn()
    except ValueError as e:
        return pacote(str(e).splitlines()[0], "A ferramenta recusou esses dados.")


def _fmt_data(d):
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def _datas(texto):
    achadas = []
    for dia, mes, ano in _RE_DATA.findall(texto):
        achadas.append(datetime.date(int(ano), int(mes), int(dia)))
    return achadas


def _extrair_bateria(texto):
    if not combina(texto, [("autonomia bateria",)]):
        return None
    return ler(texto, [
        C("ah", ["capacidade"], "num", True),
        C("tensao", ["tensao"], "num", True),
        C("carga", ["carga"], "num", True),
    ])


def _calcular_bateria(params):
    def fazer():
        mod = carregar("calculadora-baterias", "bat_core")
        horas = mod.autonomia_h(params["ah"], params["tensao"], params["carga"])
        return pacote(
            _num(horas, 2) + " h",
            "Descarga 80% e eficiência 90%, padrões da função.",
        )
    return _chamar(fazer)


def _extrair_hohmann(texto):
    if not combina(texto, [("transferencia hohmann",)]):
        return None
    return ler(texto, [
        C("baixa", ["baixa"], "num", True),
        C("alta", ["alta"], "num", True),
    ])


def _calcular_hohmann(params):
    def fazer():
        mod = carregar("calculadora-dinamica-orbital-hohmann", "hmn_core")
        r = mod.calculate_hohmann_transfer("Terra", params["baixa"], params["alta"])
        return pacote(
            _num(r["total_delta_v_m_s"], 1) + " m/s",
            "Terra, altitudes em km. Delta-v total da transferência.",
        )
    return _chamar(fazer)


def _extrair_zipf(texto):
    if not combina(texto, [("lei de zipf",)]):
        return None
    corpo = _depois(texto, "lei de zipf")
    if not corpo:
        return None
    return {"corpo": corpo}


def _calcular_zipf(params):
    def fazer():
        mod = carregar("analisador-zipf", "zpf_core")
        r = mod.zipf_analyze(params["corpo"])
        topo = r["rows"][0]
        return pacote(topo["word"], "Palavra mais frequente. " + str(topo["freq"]) + " vezes.")
    return _chamar(fazer)


def _extrair_espacos(texto):
    if not combina(texto, [("compactar espacos",)]):
        return None
    corpo = _depois_cru(texto, "compactar espacos")
    if corpo is None or corpo == "":
        return None
    return {"corpo": corpo}


def _calcular_espacos(params):
    def fazer():
        mod = carregar("compactador-whitespace", "wsp_core")
        depois = mod.normalize(params["corpo"])
        return pacote(mod.stats(params["corpo"], depois), "Tab vira 4 espaços e linhas em branco repetidas viram uma.")
    return _chamar(fazer)


def _extrair_nome(texto):
    if not combina(texto, [("normalizar arquivo",)]):
        return None
    corpo = _depois(texto, "normalizar arquivo")
    if not corpo:
        return None
    return {"nome": corpo}


def _calcular_nome(params):
    def fazer():
        mod = carregar("normalizador-nomes", "nfn_core")
        return pacote(mod.normalize_name(params["nome"]), "Minúsculo, underscore, sem acento. Extensão conservada.")
    return _chamar(fazer)


def _extrair_rateio(texto):
    if not combina(texto, [("acerto rateio",)]):
        return None
    m = _RE_RATEIO.search(texto.strip())
    if not m:
        return None
    nomes = m.group(3).split()
    if len(nomes) < 2:
        return None
    return {
        "pagou": m.group(1),
        "valor": float(m.group(2).replace(",", ".")),
        "nomes": nomes,
    }


def _calcular_rateio(params):
    def fazer():
        mod = carregar("rateio", "rct_core")
        despesas = [{
            "desc": "conta",
            "valor": params["valor"],
            "pagou": params["pagou"],
            "entre": params["nomes"],
        }]
        bal = mod.saldos(params["nomes"], despesas)
        trans = mod.acertar(bal)
        if not trans:
            return pacote("todos quites", "Nenhuma transferência.")
        texto = "; ".join(a + " paga " + mod.brl(v) + " para " + b for a, b, v in trans)
        return pacote(texto, "Menor número de transferências.")
    return _chamar(fazer)


def _extrair_ciclo(texto):
    if not combina(texto, [("ciclo menstrual",)]):
        return None
    datas = _datas(texto)
    if not datas:
        return None
    return {"inicios": datas}


def _calcular_ciclo(params):
    def fazer():
        mod = carregar("ciclo-menstrual", "cic_core")
        prev = mod.previsoes(params["inicios"])
        return pacote(
            _fmt_data(prev[0]["inicio"]),
            "Próximo início. Duração 5 dias e ciclo 28 se faltar histórico, padrões da função. Estimativa, não é diagnóstico.",
        )
    return _chamar(fazer)


def _extrair_pausas(texto):
    if not combina(texto, [("pausas da jornada",)]):
        return None
    return ler(texto, [C("horas", ["horas"], "num", True)])


def _calcular_pausas(params):
    def fazer():
        mod = carregar("ergonomia-pausas-trabalho", "erg_core")
        r = mod.calcular_cronograma_jornada(params["horas"])
        return pacote(
            str(r["num_pausas_sugeridas"]) + " pausas",
            "A cada 50 min, pausa de 5 min, padrões da função.",
        )
    return _chamar(fazer)


def _extrair_liquido(texto):
    # "liquido" dispara o salario e "distracao" contem "racao".
    if not combina(texto, [("foco de estudo",)]):
        return None
    return ler(texto, [
        C("bruto", ["bruto"], "num", True),
        C("interrupcoes", ["interrupcoes"], "int", True),
        C("cada", ["cada"], "num", True),
        C("perda", ["perda"], "num", True),
    ])


def _calcular_liquido(params):
    def fazer():
        mod = carregar("tempo-liquido-estudo", "tnr_core")
        r = mod.calcular_tempo_liquido(
            params["bruto"], params["interrupcoes"], params["cada"], params["perda"],
        )
        return pacote(
            _num(r.tempo_liquido, 2) + " min",
            "Pausas planejadas 0. " + r.rotulo + ".",
        )
    return _chamar(fazer)


def _extrair_roi(texto):
    if not combina(texto, [("roi da pos",)]):
        return None
    return ler(texto, [
        C("mensalidade", ["mensalidade"], "num", True),
        C("prazo", ["prazo"], "int", True),
        C("atual", ["atual"], "num", True),
        C("projetado", ["projetado"], "num", True),
    ])


def _calcular_roi(params):
    def fazer():
        mod = carregar("calculadora-roi-educacao-pos", "cbf_core")
        r = mod.calcular_roi_educacao(
            params["mensalidade"], params["prazo"], 0.0,
            params["atual"], params["projetado"],
        )
        return pacote(
            _num(r["mes_payback_simples"], 1) + " meses",
            "Extras 0. Desconto 10% ao ano e horizonte de 60 meses, padrões da função.",
        )
    return _chamar(fazer)


def _extrair_pendulo(texto):
    if not combina(texto, [("periodo do pendulo",)]):
        return None
    return ler(texto, [
        C("comprimento", ["comprimento"], "num", True),
        C("gravidade", ["gravidade"], "num", True),
    ])


def _calcular_pendulo(params):
    def fazer():
        mod = carregar("simulador-pendulo-duplo", "pdl_core")
        t = mod.periodo_pequenas_osc(params["comprimento"], params["gravidade"])
        return pacote(_num(t, 3) + " s", "Pêndulo simples, pequenas oscilações.")
    return _chamar(fazer)


def _corte(texto):
    t = norm(texto)
    for gatilho, oficial in _CORTES:
        if gatilho in t:
            return oficial
    return None


def _extrair_forno(texto):
    if not combina(texto, [("tempo de forno",)]):
        return None
    corte = _corte(texto)
    if not corte:
        return None
    p = ler(texto, [C("peso", ["peso"], "num", True)])
    if not p:
        return None
    p["corte"] = corte
    return p


def _calcular_forno(params):
    def fazer():
        mod = carregar("forno-carnes", "asd_core")
        r = mod.tempo_forno(params["corte"], params["peso"])
        return pacote(
            str(r["minutos"]) + " min",
            params["corte"] + " a " + str(r["temp_C"]) + " °C, ponto " + r["ponto"] + " da ficha.",
        )
    return _chamar(fazer)


def _metodo_gelo(texto):
    t = norm(texto)
    if "agua fria" in t:
        return "Água fria"
    if "micro" in t:
        return "Micro-ondas"
    if "geladeira" in t:
        return "Geladeira"
    return None


def _extrair_gelo(texto):
    if not combina(texto, [("descongelar",)]):
        return None
    metodo = _metodo_gelo(texto)
    if not metodo:
        return None
    p = ler(texto, [C("peso", ["peso"], "num", True)])
    if not p:
        return None
    p["metodo"] = metodo
    return p


def _calcular_gelo(params):
    def fazer():
        mod = carregar("descongelar-com-seguranca", "dsc_core")
        horas = mod.horas_descongelar(params["peso"], params["metodo"])
        return pacote(_num(horas, 2) + " h", params["metodo"] + ", espessura média, padrão da função.")
    return _chamar(fazer)


def _extrair_cozinha(texto):
    if not combina(texto, [("tempo de cozimento",)]):
        return None
    corpo = _depois(texto, "tempo de cozimento")
    if not corpo:
        return None
    return {"alimento": corpo}


def _calcular_cozinha(params):
    def fazer():
        mod = carregar("cozimento-alimentos", "coz_core")
        r = mod.tempo(params["alimento"])
        return pacote(str(r["minutos"]) + " min", r["nota"] + " Uma porção, padrão da função.")
    return _chamar(fazer)


def _extrair_composto(texto):
    if not combina(texto, [("volume composteira",)]):
        return None
    return ler(texto, [C("pessoas", ["pessoas"], "int", True)])


def _calcular_composto(params):
    def fazer():
        mod = carregar("compostagem", "cmp_core")
        r = mod.volume_composteira(params["pessoas"])
        return pacote(
            str(r["volume_l"]) + " L",
            "0,5 kg de resto por pessoa ao dia, conta de dentro da função.",
        )
    return _chamar(fazer)


def _extrair_prova(texto):
    if not combina(texto, [("estrategia de prova",)]):
        return None
    return ler(texto, [
        C("minutos", ["minutos"], "int", True),
        C("questoes", ["questoes"], "int", True),
    ])


def _calcular_prova(params):
    def fazer():
        mod = carregar("planejador-tempo-estrategia-prova", "etp_core")
        r = mod.calcular_estrategia_prova(params["minutos"], params["questoes"])
        return pacote(
            r["tempo_formatado"],
            "Com redação de 70 min, gabarito de 25 min e lanche de 15 min, padrões da função.",
        )
    return _chamar(fazer)


def _extrair_nuvem(texto):
    if not combina(texto, [("crescimento nuvem",)]):
        return None
    return ler(texto, [
        C("fotos", ["fotos"], "num", True),
        C("foto", ["foto"], "num", True),
        C("video", ["video"], "num", True),
        C("minuto", ["minuto"], "num", True),
    ])


def _calcular_nuvem(params):
    def fazer():
        mod = carregar("plano-nuvem-backup", "nuv_core")
        gb = mod.crescimento_gb(params["fotos"], params["foto"], params["video"], params["minuto"])
        return pacote(_num(gb, 2) + " GB/mês", "Fotos no mês, MB de cada foto, minutos de vídeo e MB por minuto.")
    return _chamar(fazer)


_registrar("calculadora-baterias", ["autonomia bateria"], _extrair_bateria, _calcular_bateria)
_registrar("calculadora-dinamica-orbital-hohmann", ["transferencia hohmann"], _extrair_hohmann, _calcular_hohmann)
_registrar("analisador-zipf", ["lei de zipf"], _extrair_zipf, _calcular_zipf)
_registrar("compactador-whitespace", ["compactar espacos"], _extrair_espacos, _calcular_espacos)
_registrar("normalizador-nomes", ["normalizar arquivo"], _extrair_nome, _calcular_nome)
_registrar("rateio", ["acerto rateio"], _extrair_rateio, _calcular_rateio)
_registrar("ciclo-menstrual", ["ciclo menstrual"], _extrair_ciclo, _calcular_ciclo)
_registrar("ergonomia-pausas-trabalho", ["pausas da jornada"], _extrair_pausas, _calcular_pausas)
_registrar("tempo-liquido-estudo", ["foco de estudo"], _extrair_liquido, _calcular_liquido)
_registrar("calculadora-roi-educacao-pos", ["roi da pos"], _extrair_roi, _calcular_roi)
_registrar("simulador-pendulo-duplo", ["periodo do pendulo"], _extrair_pendulo, _calcular_pendulo)
_registrar("forno-carnes", ["tempo de forno"], _extrair_forno, _calcular_forno)
_registrar("descongelar-com-seguranca", ["descongelar"], _extrair_gelo, _calcular_gelo)
_registrar("cozimento-alimentos", ["tempo de cozimento"], _extrair_cozinha, _calcular_cozinha)
_registrar("compostagem", ["volume composteira"], _extrair_composto, _calcular_composto)
_registrar("planejador-tempo-estrategia-prova", ["estrategia de prova"], _extrair_prova, _calcular_prova)
_registrar("plano-nuvem-backup", ["crescimento nuvem"], _extrair_nuvem, _calcular_nuvem)
