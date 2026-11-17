# -*- coding: utf-8 -*-
"""Compara custo de agua mineral (galao) vs filtro/purificador."""
from __future__ import annotations


def calcular(
    preco_galao: float,
    litros_galao: float,
    consumo_litros_mes: float,
    preco_filtro: float,
    vida_filtro_meses: float,
    energia_mes: float = 0.0,
    manutencao_mes: float = 0.0,
) -> dict:
    if any(x < 0 for x in (
        preco_galao, litros_galao, consumo_litros_mes,
        preco_filtro, vida_filtro_meses, energia_mes, manutencao_mes,
    )):
        raise ValueError("valores nao podem ser negativos")
    if litros_galao <= 0:
        raise ValueError("litros_galao deve ser > 0")
    if vida_filtro_meses <= 0:
        raise ValueError("vida_filtro_meses deve ser > 0")

    galoes = consumo_litros_mes / litros_galao if litros_galao else 0.0
    mensal_mineral = galoes * preco_galao
    mensal_filtro = (
        preco_filtro / vida_filtro_meses + energia_mes + manutencao_mes
    )
    diff = mensal_mineral - mensal_filtro
    if abs(diff) < 0.01:
        vencedor = "empate"
    elif diff > 0:
        vencedor = "filtro"
    else:
        vencedor = "mineral"
    # Payback do filtro em meses (se mineral for mais caro)
    if diff > 0:
        payback = preco_filtro / diff if diff else None
    else:
        payback = None

    return {
        "galoes_mes": round(galoes, 2),
        "mensal_mineral": round(mensal_mineral, 2),
        "mensal_filtro": round(mensal_filtro, 2),
        "diferenca": round(abs(diff), 2),
        "economia_anual": round(abs(diff) * 12, 2),
        "vencedor": vencedor,
        "payback_meses": round(payback, 1) if payback is not None else None,
        "custo_litro_mineral": round(preco_galao / litros_galao, 4),
        "custo_litro_filtro": round(
            mensal_filtro / consumo_litros_mes, 4
        ) if consumo_litros_mes else 0.0,
    }


def formatar(r: dict) -> str:
    linhas = [
        f"Mineral: {r['galoes_mes']:.1f} galoes/mes → R$ {r['mensal_mineral']:.2f} "
        f"(R$ {r['custo_litro_mineral']:.3f}/L)",
        f"Filtro/purificador: R$ {r['mensal_filtro']:.2f}/mes "
        f"(R$ {r['custo_litro_filtro']:.3f}/L)",
        f"Diferenca: R$ {r['diferenca']:.2f}/mes (~R$ {r['economia_anual']:.2f}/ano)",
    ]
    if r["vencedor"] == "empate":
        linhas.append("Resultado: custos equivalentes.")
    elif r["vencedor"] == "filtro":
        linhas.append("Mais barato: filtro/purificador.")
        if r["payback_meses"] is not None:
            linhas.append(f"Payback do equipamento: ~{r['payback_meses']:.0f} meses.")
    else:
        linhas.append("Mais barato: agua mineral.")
    return "\n".join(linhas)
