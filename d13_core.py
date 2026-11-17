# -*- coding: utf-8 -*-
"""Calcula 13o salario proporcional (CLT)."""
from __future__ import annotations

import math


def calcular(salario: float, meses_trabalhados: float, adiantamento: float = 0.0) -> dict:
    if salario < 0 or meses_trabalhados < 0 or adiantamento < 0:
        raise ValueError("valores nao podem ser negativos")
    if meses_trabalhados > 12:
        raise ValueError("meses trabalhados maximo 12")
    # Regra CLT: mes conta se >= 15 dias (~0.5). Aqui o usuario informa meses ja convertidos.
    meses_inteiros = math.floor(meses_trabalhados + 1e-9)
    fracao = meses_trabalhados - meses_inteiros
    # se fracao >= 0.5, conta o mes cheio na pratica comum
    meses_contados = meses_inteiros + (1 if fracao >= 0.5 else 0)
    meses_contados = min(12, meses_contados)
    bruto = round(salario * (meses_contados / 12.0), 2)
    liquido = round(max(0.0, bruto - adiantamento), 2)
    return {
        "meses_contados": meses_contados,
        "bruto": bruto,
        "adiantamento": round(adiantamento, 2),
        "a_receber": liquido,
    }


def formatar(r: dict) -> str:
    return (
        f"Meses contados: {r['meses_contados']}/12\n"
        f"13o bruto proporcional: R$ {r['bruto']:.2f}\n"
        f"Adiantamento ja recebido: R$ {r['adiantamento']:.2f}\n"
        f"A receber: R$ {r['a_receber']:.2f}\n"
        "\nNao inclui INSS/IR — ajuste conforme o holerite."
    )
