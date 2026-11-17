"""Cartela do Anticoncepcional — lógica pura (orientação geral informativa)."""
from __future__ import annotations
from datetime import date, timedelta
import json
import os

ARQ = os.path.join(os.path.expanduser("~"), ".caixa_cartela_anticoncepcional.json")

TIPOS = {
    "21": {"ativos": 21, "pausa": 7, "ciclo": 28, "rotulo": "21 ativos + 7 de pausa"},
    "24": {"ativos": 24, "pausa": 4, "ciclo": 28, "rotulo": "24 ativos + 4 placebos"},
    "28": {"ativos": 28, "pausa": 0, "ciclo": 28, "rotulo": "28 comprimidos (com placebos)"},
    "continuo": {"ativos": 84, "pausa": 7, "ciclo": 91, "rotulo": "Uso contínuo (84 ativos + 7 pausa)"},
}


def tipo_info(tipo: str) -> dict:
    t = tipo.strip().lower()
    if t not in TIPOS:
        raise ValueError("Tipo deve ser 21, 24, 28 ou continuo.")
    return dict(TIPOS[t])


def dia_na_cartela(inicio: date, hoje: date | None = None, tipo: str = "21") -> dict:
    """Retorna o dia atual na cartela (1-based) e se está em pausa."""
    hoje = hoje or date.today()
    info = tipo_info(tipo)
    if hoje < inicio:
        raise ValueError("Data de hoje anterior ao início da cartela.")
    decorridos = (hoje - inicio).days
    pos = decorridos % info["ciclo"]  # 0 .. ciclo-1
    dia = pos + 1
    em_pausa = dia > info["ativos"]
    comprimido = None if em_pausa else dia
    pausa_dia = (dia - info["ativos"]) if em_pausa else 0
    return {
        "dia": dia,
        "ciclo": info["ciclo"],
        "ativos": info["ativos"],
        "em_pausa": em_pausa,
        "comprimido": comprimido,
        "pausa_dia": pausa_dia,
        "rotulo": info["rotulo"],
    }


def proxima_cartela(inicio: date, tipo: str = "21") -> date:
    info = tipo_info(tipo)
    return inicio + timedelta(days=info["ciclo"])


def dias_para_proxima(inicio: date, hoje: date | None = None, tipo: str = "21") -> int:
    hoje = hoje or date.today()
    prox = proxima_cartela(inicio, tipo)
    # se já passou, avança ciclos
    info = tipo_info(tipo)
    while prox <= hoje:
        prox = prox + timedelta(days=info["ciclo"])
        inicio = inicio + timedelta(days=info["ciclo"])
    return (prox - hoje).days


def orientacao_esquecimento(horas_atraso: float, dia_ativo: int, tipo: str = "21") -> dict:
    """
    Orientação GERAL informativa (não substitui bula nem profissional de saúde).
    Base simplificada: <12h tomar assim que lembrar; 12-24h; >24h.
    """
    if horas_atraso < 0:
        raise ValueError("Horas de atraso inválidas.")
    info = tipo_info(tipo)
    if dia_ativo < 1 or dia_ativo > info["ativos"]:
        raise ValueError("Dia ativo fora da faixa da cartela.")
    if horas_atraso < 12:
        nivel = "leve"
        texto = (
            "Menos de 12 horas: tome o comprimido assim que lembrar e siga o horário normal. "
            "Em geral a proteção se mantém. Confirme sempre a bula do seu medicamento."
        )
    elif horas_atraso <= 24:
        nivel = "moderado"
        texto = (
            "Entre 12 e 24 horas: tome o comprimido esquecido assim que lembrar "
            "(mesmo que sejam dois no mesmo dia) e use proteção adicional (camisinha) "
            "pelos próximos 7 dias. Consulte a bula."
        )
    else:
        nivel = "alto"
        texto = (
            "Mais de 24 horas: a proteção pode estar comprometida. "
            "Tome o comprimido mais recente, descarte os anteriores esquecidos do mesmo período, "
            "use proteção adicional por 7 dias e considere anticoncepcional de emergência "
            "se houve relação de risco. Procure orientação de um profissional de saúde."
        )
    return {
        "nivel": nivel,
        "horas_atraso": horas_atraso,
        "dia_ativo": dia_ativo,
        "texto": texto,
        "aviso": "Orientação geral informativa — não substitui bula nem consulta médica.",
    }


def calendario_ciclo(inicio: date, tipo: str = "21") -> list[dict]:
    info = tipo_info(tipo)
    out = []
    for i in range(info["ciclo"]):
        d = inicio + timedelta(days=i)
        dia = i + 1
        out.append({
            "data": d.isoformat(),
            "dia": dia,
            "ativo": dia <= info["ativos"],
        })
    return out


def salvar(dados, arq=ARQ):
    with open(arq, "w", encoding="utf-8") as fh:
        json.dump(dados, fh, ensure_ascii=False, indent=1)


def carregar(arq=ARQ):
    try:
        with open(arq, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"cartelas": []}
