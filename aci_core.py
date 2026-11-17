# -*- coding: utf-8 -*-
"""Custo de academia/esporte infantil (mensalidade + extras)."""
from __future__ import annotations


def calcular(
    mensalidade: float,
    meses: int = 12,
    uniforme: float = 0.0,
    taxa_matricula: float = 0.0,
    competicoes: float = 0.0,
    transporte_mes: float = 0.0,
) -> dict:
    if min(mensalidade, uniforme, taxa_matricula, competicoes, transporte_mes) < 0 or meses < 1:
        raise ValueError("parametros invalidos")
    total = mensalidade * meses + uniforme + taxa_matricula + competicoes + transporte_mes * meses
    return {
        "total": round(total, 2),
        "media_mes": round(total / meses, 2),
        "mensalidades": round(mensalidade * meses, 2),
        "extras": round(uniforme + taxa_matricula + competicoes, 2),
        "transporte": round(transporte_mes * meses, 2),
    }


def formatar(r: dict) -> str:
    return (
        f"Mensalidades: R$ {r['mensalidades']:.2f}\n"
        f"Extras (uniforme/matricula/comps): R$ {r['extras']:.2f}\n"
        f"Transporte: R$ {r['transporte']:.2f}\n"
        f"Total no periodo: R$ {r['total']:.2f}\n"
        f"Media mensal real: R$ {r['media_mes']:.2f}"
    )
