"""Calculadora de Baterias — lógica pura."""
import math

QUIMICAS = {
    # nome: (tensão nominal, tensão cheia, tensão mínima, profundidade de descarga recomendada, expoente de Peukert)
    "Chumbo-ácido (estacionária)": (2.0, 2.4, 1.75, 0.5, 1.25),
    "AGM": (2.0, 2.45, 1.75, 0.6, 1.15),
    "Gel": (2.0, 2.35, 1.75, 0.6, 1.12),
    "Li-ion (NMC)": (3.6, 4.2, 3.0, 0.8, 1.05),
    "LiFePO4": (3.2, 3.65, 2.5, 0.9, 1.03),
    "NiMH": (1.2, 1.45, 1.0, 0.8, 1.1),
}

CELULAS = {
    "18650 2500 mAh": ("Li-ion (NMC)", 2.5, 20.0, 45.0),
    "18650 3500 mAh": ("Li-ion (NMC)", 3.5, 10.0, 48.0),
    "21700 5000 mAh": ("Li-ion (NMC)", 5.0, 10.0, 69.0),
    "LiFePO4 32700 6000 mAh": ("LiFePO4", 6.0, 18.0, 145.0),
    "LiFePO4 prismática 100 Ah": ("LiFePO4", 100.0, 100.0, 2000.0),
    "NiMH AA 2000 mAh": ("NiMH", 2.0, 4.0, 27.0),
}  # nome: (química, capacidade Ah, corrente máx. A, massa g)


def energia_wh(tensao, ah):
    return tensao * ah


def autonomia_h(capacidade_ah, tensao, carga_w, dod=0.8, eficiencia=0.9):
    """Autonomia simples: energia útil / potência."""
    if carga_w <= 0:
        raise ValueError("Carga precisa ser maior que zero.")
    if not 0 < dod <= 1 or not 0 < eficiencia <= 1:
        raise ValueError("Profundidade de descarga e eficiência devem estar entre 0 e 100%.")
    return capacidade_ah * tensao * dod * eficiencia / carga_w


def autonomia_peukert_h(capacidade_ah, horas_nominais, corrente_a, k):
    """Lei de Peukert: t = H * (C / (I*H))^k."""
    if corrente_a <= 0:
        raise ValueError("Corrente precisa ser maior que zero.")
    return horas_nominais * (capacidade_ah / (corrente_a * horas_nominais)) ** k


def capacidade_efetiva_ah(capacidade_ah, horas_nominais, corrente_a, k):
    return corrente_a * autonomia_peukert_h(capacidade_ah, horas_nominais, corrente_a, k)


def pack(serie, paralelo, celula):
    if serie < 1 or paralelo < 1:
        raise ValueError("Série e paralelo devem ser pelo menos 1.")
    quim, ah, imax, g = CELULAS[celula]
    vn, vmax, vmin, _, _ = QUIMICAS[quim]
    return {
        "celulas": serie * paralelo,
        "v_nominal": vn * serie, "v_max": vmax * serie, "v_min": vmin * serie,
        "ah": ah * paralelo, "wh": vn * serie * ah * paralelo,
        "i_max": imax * paralelo, "p_max_w": imax * paralelo * vn * serie,
        "massa_kg": g * serie * paralelo / 1000,
        "wh_kg": vn * ah / (g / 1000),
    }


def sugerir_pack(tensao_alvo, wh_alvo, celula):
    quim, ah, _, _ = CELULAS[celula]
    vn = QUIMICAS[quim][0]
    s = max(1, round(tensao_alvo / vn))
    p = max(1, math.ceil(wh_alvo / (vn * s * ah)))
    return s, p


def banco_offgrid(consumo_wh_dia, dias_autonomia, tensao_banco, dod, ah_bateria, v_bateria, eficiencia=0.85):
    """Dimensiona banco de baterias de sistema isolado."""
    if min(consumo_wh_dia, dias_autonomia, tensao_banco, ah_bateria, v_bateria) <= 0 or not 0 < dod <= 1:
        raise ValueError("Valores precisam ser positivos.")
    if tensao_banco % v_bateria:
        raise ValueError("A tensão do banco precisa ser múltipla da tensão da bateria.")
    ah_necessario = consumo_wh_dia * dias_autonomia / (tensao_banco * dod * eficiencia)
    serie = int(tensao_banco // v_bateria)
    paralelo = math.ceil(ah_necessario / ah_bateria)
    return {"ah_necessario": ah_necessario, "serie": serie, "paralelo": paralelo,
            "total": serie * paralelo, "wh_instalado": serie * paralelo * v_bateria * ah_bateria}


def tempo_recarga_h(capacidade_ah, corrente_carga_a, soc_ini=0.2, soc_fim=1.0, eficiencia=0.85, quimica="LiFePO4"):
    """Tempo de recarga com fase de absorção estimada (CC/CV)."""
    if corrente_carga_a <= 0:
        raise ValueError("Corrente de carga precisa ser maior que zero.")
    if not 0 <= soc_ini < soc_fim <= 1:
        raise ValueError("Carga inicial deve ser menor que a final.")
    lítio = quimica in ("LiFePO4", "Li-ion (NMC)")
    limite_cc = 0.9 if lítio else 0.8
    cc = max(0.0, min(soc_fim, limite_cc) - soc_ini) * capacidade_ah / (corrente_carga_a * eficiencia)
    cv = 0.0
    if soc_fim > limite_cc:
        trecho = soc_fim - max(soc_ini, limite_cc)
        cv = trecho * capacidade_ah / (corrente_carga_a * eficiencia) * (1.5 if lítio else 3.0)
    return cc + cv


def taxa_c(corrente_a, capacidade_ah):
    return corrente_a / capacidade_ah
