"""
aer_core.py - Núcleo de aerodinâmica, sustentação, arrasto e mecânica de voo.
Implementa modelo atmosférico ISA, polar de arrasto parabólica (arrasto induzido e parasita),
velocidade de estol, razão de planeio (L/D) e potência requerida de voo nivelado.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Constantes físicas
G_PADRAO = 9.80665  # m/s^2
R_AR = 287.058      # J/(kg*K)
T0_ISA = 288.15     # K (15 °C ao nível do mar)
P0_ISA = 101325.0   # Pa
RHO0_ISA = 1.225    # kg/m^3
GRAD_TEMP = 0.0065  # K/m (troposfera até 11.000 m)

# Predefinições de aeronaves
AERONAVES_PREDEFINIDAS = {
    "Cessna 172 Skyhawk": {
        "massa_kg": 1111.0,
        "area_asa_m2": 16.2,
        "envergadura_m": 11.0,
        "cd0": 0.027,
        "oswald_e": 0.75,
        "cl_max": 1.60,
    },
    "Boeing 737-800": {
        "massa_kg": 70000.0,
        "area_asa_m2": 125.0,
        "envergadura_m": 34.3,
        "cd0": 0.020,
        "oswald_e": 0.82,
        "cl_max": 2.20,
    },
    "Planador de Alta Performance": {
        "massa_kg": 380.0,
        "area_asa_m2": 10.5,
        "envergadura_m": 18.0,
        "cd0": 0.012,
        "oswald_e": 0.90,
        "cl_max": 1.45,
    },
    "Drone VTOL Asa Fixa": {
        "massa_kg": 4.5,
        "area_asa_m2": 0.38,
        "envergadura_m": 1.60,
        "cd0": 0.035,
        "oswald_e": 0.70,
        "cl_max": 1.30,
    },
}


@dataclass
class EstadoVoo:
    altitude_m: float
    velocidade_ms: float
    velocidade_kmh: float
    densidade_ar: float
    pressao_dinamica_pa: float
    peso_n: float
    cl_operacao: float
    cd_parasita: float
    cd_induzido: float
    cd_total: float
    sustentacao_n: float
    arrasto_n: float
    razao_planeio_ld: float
    velocidade_estol_ms: float
    velocidade_estol_kmh: float
    potencia_requerida_kw: float
    potencia_requerida_hp: float
    alongamento_ar: float


def atmosfera_isa(altitude_m: float) -> Tuple[float, float, float]:
    """
    Retorna (temperatura_K, pressao_Pa, densidade_kg_m3) na troposfera (0 a 11000m).
    """
    alt = max(0.0, min(altitude_m, 11000.0))
    temp = T0_ISA - GRAD_TEMP * alt
    pressao = P0_ISA * ((temp / T0_ISA) ** (G_PADRAO / (R_AR * GRAD_TEMP)))
    densidade = pressao / (R_AR * temp)
    return temp, pressao, densidade


def calcular_desempenho_voo(
    massa_kg: float,
    area_asa_m2: float,
    envergadura_m: float,
    cd0: float,
    oswald_e: float,
    cl_max: float,
    velocidade_kmh: float,
    altitude_m: float = 0.0,
) -> EstadoVoo:
    """
    Calcula parâmetros de voo nivelado e sustentação/arrasto para a condição dada.
    """
    if massa_kg <= 0 or area_asa_m2 <= 0 or envergadura_m <= 0 or velocidade_kmh <= 0:
        raise ValueError("Valores de massa, geometria e velocidade devem ser positivos.")

    v_ms = velocidade_kmh / 3.6
    _, _, rho = atmosfera_isa(altitude_m)

    # Alongamento da asa (Aspect Ratio): AR = b^2 / S
    ar = (envergadura_m ** 2) / area_asa_m2

    peso_n = massa_kg * G_PADRAO
    q = 0.5 * rho * (v_ms ** 2)

    # Em voo nivelado de cruzeiro: Sustentação L = Peso W
    # CL = W / (q * S)
    cl_operacao = peso_n / (q * area_asa_m2)

    # Coeficiente de arrasto induzido: CDi = CL^2 / (pi * e * AR)
    k_induzido = 1.0 / (math.pi * oswald_e * ar)
    cd_induzido = k_induzido * (cl_operacao ** 2)
    cd_total = cd0 + cd_induzido

    sustentacao_n = peso_n
    arrasto_n = q * area_asa_m2 * cd_total

    razao_ld = cl_operacao / cd_total if cd_total > 1e-6 else 0.0

    # Velocidade de estol: v_stall = sqrt(2 * W / (rho * S * CL_max))
    v_stall_ms = math.sqrt((2.0 * peso_n) / (rho * area_asa_m2 * cl_max))
    v_stall_kmh = v_stall_ms * 3.6

    # Potência requerida: P = Drag * Velocity (Watts)
    pot_w = arrasto_n * v_ms
    pot_kw = pot_w / 1000.0
    pot_hp = pot_w / 745.699872

    return EstadoVoo(
        altitude_m=altitude_m,
        velocidade_ms=v_ms,
        velocidade_kmh=velocidade_kmh,
        densidade_ar=rho,
        pressao_dinamica_pa=q,
        peso_n=peso_n,
        cl_operacao=cl_operacao,
        cd_parasita=cd0,
        cd_induzido=cd_induzido,
        cd_total=cd_total,
        sustentacao_n=sustentacao_n,
        arrasto_n=arrasto_n,
        razao_planeio_ld=razao_ld,
        velocidade_estol_ms=v_stall_ms,
        velocidade_estol_kmh=v_stall_kmh,
        potencia_requerida_kw=pot_kw,
        potencia_requerida_hp=pot_hp,
        alongamento_ar=ar,
    )


def gerar_polar_arrasto(
    cd0: float,
    oswald_e: float,
    ar: float,
    cl_max: float = 1.6,
    num_pontos: int = 50,
) -> Tuple[List[float], List[float]]:
    """Gera pontos (CD, CL) da curva polar parabólica do aerofólio/aeronave."""
    k = 1.0 / (math.pi * oswald_e * ar)
    cls = []
    cds = []
    passo = cl_max / (num_pontos - 1)
    for i in range(num_pontos):
        cl = i * passo
        cd = cd0 + k * (cl ** 2)
        cls.append(cl)
        cds.append(cd)
    return cds, cls


def gerar_curva_potencia(
    massa_kg: float,
    area_asa_m2: float,
    envergadura_m: float,
    cd0: float,
    oswald_e: float,
    cl_max: float,
    altitude_m: float = 0.0,
    num_pontos: int = 50,
) -> Tuple[List[float], List[float]]:
    """
    Gera curva de potência requerida (HP) em função da velocidade (km/h) a partir da velocidade de estol.
    """
    v_stall_ms = math.sqrt((2.0 * massa_kg * G_PADRAO) / (atmosfera_isa(altitude_m)[2] * area_asa_m2 * cl_max))
    v_min_kmh = v_stall_ms * 3.6 * 1.05
    v_max_kmh = v_min_kmh * 2.8

    vels = []
    pots = []
    passo = (v_max_kmh - v_min_kmh) / (num_pontos - 1)
    for i in range(num_pontos):
        v = v_min_kmh + i * passo
        try:
            est = calcular_desempenho_voo(massa_kg, area_asa_m2, envergadura_m, cd0, oswald_e, cl_max, v, altitude_m)
            vels.append(v)
            pots.append(est.potencia_requerida_hp)
        except Exception:
            pass
    return vels, pots
