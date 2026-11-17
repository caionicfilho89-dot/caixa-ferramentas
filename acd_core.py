# -*- coding: utf-8 -*-
"""Compara academia mensal vs comprar equipamentos em casa."""
from __future__ import annotations


def comparar(
    mensalidade: float,
    meses_horizonte: int,
    custo_equipamentos: float,
    manutencao_mes: float = 0.0,
    taxa_matricula_mes: float = 0.0,
) -> dict:
    if min(mensalidade, custo_equipamentos, manutencao_mes, taxa_matricula_mes) < 0 or meses_horizonte < 1:
        raise ValueError("parametros invalidos")
    acad = round(mensalidade * meses_horizonte + taxa_matricula_mes * meses_horizonte, 2)
    casa = round(custo_equipamentos + manutencao_mes * meses_horizonte, 2)
    break_even = None
    if mensalidade + taxa_matricula_mes > manutencao_mes:
        # meses para academia = custo_equip / (mensal_acad - manut_casa)
        diff = (mensalidade + taxa_matricula_mes) - manutencao_mes
        break_even = round(custo_equipamentos / diff, 1) if diff > 0 else None
    return {
        "academia": acad,
        "casa": casa,
        "economia": round(acad - casa, 2),
        "melhor": "casa" if casa < acad else ("academia" if casa > acad else "empate"),
        "break_even_meses": break_even,
        "meses": meses_horizonte,
    }


def formatar(r: dict) -> str:
    linhas = [
        f"Horizonte: {r['meses']} meses",
        f"Academia: R$ {r['academia']:.2f}",
        f"Equipamentos em casa: R$ {r['casa']:.2f}",
        f"Economia (acad - casa): R$ {r['economia']:.2f}",
        f"Mais barato: {r['melhor']}",
    ]
    if r["break_even_meses"] is not None:
        linhas.append(f"Payback dos equipamentos: ~{r['break_even_meses']:.1f} meses")
    return "\n".join(linhas)
