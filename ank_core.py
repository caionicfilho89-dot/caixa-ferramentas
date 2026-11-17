"""Meta de Revisoes Anki — modelo estavel de carga diaria (sem FSRS completo).

Formula principal (regime estacionario aproximado):

    revisoes_dia ≈ novos_dia × fator_jovem + maduros / intervalo_medio_dias

- *fator_jovem*: carga media de revisoes na fila jovem/aprendizado por card novo/dia
  (base 8 + ajuste 21/intervalo — intervalos curtos elevam repeticoes iniciais).
- *maduros*: total_cards − min(novos_dia × 7, 25% do baralho) — pipeline jovem fixo em 7 dias.
- *intervalo_medio_dias*: informado pelo usuario OU derivado da retencao alvo R (0–1):
      intervalo = −1 / ln(R)   (modelo exponencial de esquecimento).

Minutos necessarios = revisoes_dia × (segundos_por_card / 60).
Cabe na meta se minutos_necessarios ≤ minutos_disponiveis.
Novo/dia sugerido: busca binaria no mesmo modelo para caber no teto de revisoes.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

PIPELINE_DIAS = 7.0
FATOR_JOVEM_BASE = 8.0
FRAC_MAX_PIPELINE = 0.25


def interval_from_retention(retention_percent: float) -> float:
    """Converte retencao alvo (%) em intervalo medio em dias."""
    if retention_percent <= 50.0 or retention_percent >= 99.95:
        raise ValueError("retencao alvo deve estar entre 50% e 99,9%")
    r = retention_percent / 100.0
    return -1.0 / math.log(r)


def fator_jovem(intervalo_dias: float) -> float:
    return FATOR_JOVEM_BASE + 21.0 / max(intervalo_dias, 3.0)


def cards_maduros(total_cards: int, novos_dia: float) -> float:
    if total_cards < 0:
        raise ValueError("total de cards invalido")
    if novos_dia < 0:
        raise ValueError("novos/dia nao pode ser negativo")
    limite = total_cards * FRAC_MAX_PIPELINE
    pipeline = min(novos_dia * PIPELINE_DIAS, limite)
    return max(0.0, float(total_cards) - pipeline)


def revisoes_estimadas_por_dia(
    novos_dia: float,
    intervalo_medio_dias: float,
    total_cards: int,
) -> tuple[float, float, float]:
    """Retorna (revisoes_dia, parte_jovem, parte_madura)."""
    if intervalo_medio_dias <= 0:
        raise ValueError("intervalo medio deve ser > 0")
    if total_cards <= 0:
        raise ValueError("total de cards deve ser > 0")
    mad = cards_maduros(total_cards, novos_dia)
    fj = fator_jovem(intervalo_medio_dias)
    parte_jovem = novos_dia * fj
    parte_madura = mad / intervalo_medio_dias
    return parte_jovem + parte_madura, parte_jovem, parte_madura


def sugerir_novos_por_dia(
    minutos_disponiveis: float,
    segundos_por_card: float,
    intervalo_medio_dias: float,
    total_cards: int,
) -> float:
    if minutos_disponiveis <= 0 or segundos_por_card <= 0:
        return 0.0
    teto_revisoes = (minutos_disponiveis * 60.0) / segundos_por_card
    lo, hi = 0.0, min(500.0, float(total_cards))
    for _ in range(60):
        mid = (lo + hi) / 2.0
        rev, _, _ = revisoes_estimadas_por_dia(mid, intervalo_medio_dias, total_cards)
        if rev <= teto_revisoes:
            lo = mid
        else:
            hi = mid
    return math.floor(lo * 10.0) / 10.0


@dataclass
class ResultadoCarga:
    revisoes_por_dia: float
    parte_jovem: float
    parte_madura: float
    minutos_necessarios: float
    cabe_na_meta: bool
    novos_sugeridos: float
    intervalo_medio_dias: float
    fator_jovem: float
    cards_maduros: float
    minutos_folga: float


def calcular_carga(
    novos_dia: float,
    total_cards: int,
    minutos_disponiveis: float,
    segundos_por_card: float,
    *,
    intervalo_medio_dias: float | None = None,
    retencao_alvo_percent: float | None = None,
    modo_intervalo: Literal["dias", "retencao"] = "dias",
) -> ResultadoCarga:
    if novos_dia < 0:
        raise ValueError("novos/dia invalido")
    if minutos_disponiveis < 0:
        raise ValueError("minutos disponiveis invalidos")
    if segundos_por_card <= 0:
        raise ValueError("segundos por card deve ser > 0")

    if modo_intervalo == "retencao":
        if retencao_alvo_percent is None:
            raise ValueError("informe retencao alvo")
        intervalo = interval_from_retention(retencao_alvo_percent)
    else:
        if intervalo_medio_dias is None or intervalo_medio_dias <= 0:
            raise ValueError("intervalo medio deve ser > 0")
        intervalo = float(intervalo_medio_dias)

    rev, pj, pm = revisoes_estimadas_por_dia(novos_dia, intervalo, total_cards)
    min_nec = rev * segundos_por_card / 60.0
    cabe = min_nec <= minutos_disponiveis + 1e-9
    sug = sugerir_novos_por_dia(minutos_disponiveis, segundos_por_card, intervalo, total_cards)
    fj = fator_jovem(intervalo)
    mad = cards_maduros(total_cards, novos_dia)
    folga = minutos_disponiveis - min_nec

    return ResultadoCarga(
        revisoes_por_dia=round(rev, 1),
        parte_jovem=round(pj, 1),
        parte_madura=round(pm, 1),
        minutos_necessarios=round(min_nec, 1),
        cabe_na_meta=cabe,
        novos_sugeridos=sug,
        intervalo_medio_dias=round(intervalo, 2),
        fator_jovem=round(fj, 2),
        cards_maduros=round(mad, 0),
        minutos_folga=round(folga, 1),
    )


def formatar_resultado(r: ResultadoCarga, novos_dia: float, minutos_disp: float) -> str:
    status = "SIM — cabe na sua meta de tempo" if r.cabe_na_meta else "NAO — estoura o tempo disponivel"
    linhas = [
        "=== Carga diaria estimada (modelo estavel) ===",
        f"Intervalo medio usado     : {r.intervalo_medio_dias:.2f} dias",
        f"Cards maduros (aprox.)    : {r.cards_maduros:.0f}",
        f"Fator jovem (por novo/dia): {r.fator_jovem:.2f}",
        "",
        f"Revisoes/dia (total)      : {r.revisoes_por_dia:.1f}",
        f"  · fila jovem (N×fator)  : {r.parte_jovem:.1f}",
        f"  · maduros / intervalo   : {r.parte_madura:.1f}",
        "",
        f"Minutos necessarios       : {r.minutos_necessarios:.1f}",
        f"Minutos disponiveis       : {minutos_disp:.1f}",
        f"Folga / deficit           : {r.minutos_folga:+.1f} min",
        f"Cabe na meta?             : {status}",
        "",
        f"Sugestao novos/dia        : {r.novos_sugeridos:.1f} "
        f"(para caber em ~{minutos_disp:.0f} min)",
    ]
    if not r.cabe_na_meta and novos_dia > r.novos_sugeridos:
        linhas.append(
            f"Dica: reduza novos/dia de {novos_dia:g} para ~{r.novos_sugeridos:g} "
            "ou aumente minutos/dia."
        )
    elif r.cabe_na_meta and r.novos_sugeridos > novos_dia + 0.5:
        linhas.append(
            f"Voce ainda pode subir novos/dia ate ~{r.novos_sugeridos:g} "
            "sem estourar o tempo."
        )
    return "\n".join(linhas)
