"""
spa_core.py - Núcleo astronômico de algoritmo de posição solar (SPA) e radiação solar.
Calcula declinação solar, equação do tempo (EoT), ângulo horário, azimute e elevação solar,
horários de nascer/pôr do sol, massa de ar atmosférica AM e irradiância solar direta.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Predefinições de cidades (Latitude, Longitude, Fuso Horário UTC)
CIDADES_PREDEFINIDAS = {
    "São Paulo, Brasil": {"lat": -23.5505, "lon": -46.6333, "utc": -3.0},
    "Brasília, Brasil": {"lat": -15.7975, "lon": -47.8919, "utc": -3.0},
    "Rio de Janeiro, Brasil": {"lat": -22.9068, "lon": -43.1729, "utc": -3.0},
    "Recife, Brasil": {"lat": -8.0476, "lon": -34.8770, "utc": -3.0},
    "Manaus, Brasil": {"lat": -3.1190, "lon": -60.0217, "utc": -4.0},
    "Lisboa, Portugal": {"lat": 38.7223, "lon": -9.1393, "utc": 0.0},
    "Londres, Reino Unido": {"lat": 51.5074, "lon": -0.1278, "utc": 0.0},
    "Tóquio, Japão": {"lat": 35.6762, "lon": 139.6503, "utc": 9.0},
    "Nova York, EUA": {"lat": 40.7128, "lon": -74.0060, "utc": -5.0},
}


@dataclass
class PosicaoSolar:
    dia_ano: int
    hora_solar_verdadeira: float
    equacao_do_tempo_min: float
    declinacao_deg: float
    angulo_horario_deg: float
    elevacao_deg: float
    zenite_deg: float
    azimute_deg: float
    hora_nascer_sol: float
    hora_por_sol: float
    duracao_dia_horas: float
    massa_de_ar: float
    irradiancia_direta_w_m2: float


def dia_do_ano(dia: int, mes: int, ano: int = 2026) -> int:
    """Calcula o dia juliano ordinal do ano N (1 a 365/366)."""
    dias_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    bissexto = (ano % 4 == 0 and ano % 100 != 0) or (ano % 400 == 0)
    if bissexto:
        dias_mes[1] = 29
    return sum(dias_mes[: mes - 1]) + dia


def equacao_do_tempo_e_declinacao(n_dia: int, hora_frac: float = 12.0) -> Tuple[float, float]:
    """
    Fórmula analítica de Spencer para Equação do Tempo (EoT em min) e Declinação solar (em graus).
    """
    gamma = 2.0 * math.pi / 365.0 * (n_dia - 1 + (hora_frac - 12.0) / 24.0)

    # EoT em minutos
    eot = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2.0 * gamma)
        - 0.040849 * math.sin(2.0 * gamma)
    )

    # Declinação em radianos convertida para graus
    dec_rad = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2.0 * gamma)
        + 0.000907 * math.sin(2.0 * gamma)
        - 0.002697 * math.cos(3.0 * gamma)
        + 0.00148 * math.sin(3.0 * gamma)
    )
    return eot, math.degrees(dec_rad)


def calcular_posicao_solar(
    latitude_deg: float,
    longitude_deg: float,
    utc_offset: float,
    dia: int,
    mes: int,
    hora: float,
    ano: int = 2026,
) -> PosicaoSolar:
    """
    Calcula azimute, elevação, zenite e parâmetros solares completos para dado local e instante.
    """
    n_dia = dia_do_ano(dia, mes, ano)
    eot, declinacao_deg = equacao_do_tempo_e_declinacao(n_dia, hora)

    # Correção de longitude em relação ao meridiano padrão do fuso
    meridiano_padrao = utc_offset * 15.0
    deslocamento_tempo_min = eot + 4.0 * (longitude_deg - meridiano_padrao)
    hora_solar_verdadeira = hora + deslocamento_tempo_min / 60.0
    if hora_solar_verdadeira < 0:
        hora_solar_verdadeira += 24.0
    elif hora_solar_verdadeira >= 24.0:
        hora_solar_verdadeira -= 24.0

    # Ângulo horário omega (0° ao meio-dia solar, -15°/h de manhã, +15°/h à tarde)
    omega_deg = (hora_solar_verdadeira - 12.0) * 15.0

    lat_rad = math.radians(latitude_deg)
    dec_rad = math.radians(declinacao_deg)
    om_rad = math.radians(omega_deg)

    # Ângulo de Elevação alfa
    sin_elev = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(om_rad)
    sin_elev = max(-1.0, min(1.0, sin_elev))
    elev_rad = math.asin(sin_elev)
    elevacao_deg = math.degrees(elev_rad)
    zenite_deg = 90.0 - elevacao_deg

    # Azimute solar (0° ao Norte, 90° Leste, 180° Sul, 270° Oeste)
    cos_azim = (math.sin(elev_rad) * math.sin(lat_rad) - math.sin(dec_rad)) / (
        math.cos(elev_rad) * math.cos(lat_rad) + 1e-9
    )
    cos_azim = max(-1.0, min(1.0, cos_azim))
    azim_bruto = math.degrees(math.acos(cos_azim))

    if omega_deg > 0:
        azimute_deg = (azim_bruto + 180.0) % 360.0
    else:
        azimute_deg = (540.0 - azim_bruto) % 360.0

    # Nascer e pôr do sol
    cos_omega_s = -math.tan(lat_rad) * math.tan(dec_rad)
    if cos_omega_s >= 1.0:
        # Noite polar permanente
        nascer = 0.0
        por = 0.0
        duracao = 0.0
    elif cos_omega_s <= -1.0:
        # Sol da meia-noite permanente
        nascer = 0.0
        por = 24.0
        duracao = 24.0
    else:
        omega_s_deg = math.degrees(math.acos(cos_omega_s))
        duracao = (2.0 * omega_s_deg) / 15.0
        meio_dia_padrao = 12.0 - deslocamento_tempo_min / 60.0
        nascer = (meio_dia_padrao - duracao / 2.0) % 24.0
        por = (meio_dia_padrao + duracao / 2.0) % 24.0

    # Massa de Ar (Kasten-Young)
    if elevacao_deg > 0:
        z = zenite_deg
        am = 1.0 / (math.cos(math.radians(z)) + 0.50572 * ((96.07995 - z) ** (-1.6364)))
    else:
        am = 0.0

    # Irradiância solar direta extraterrestre e de feixe direto claro (W/m^2)
    i_sc = 1361.0 * (1.0 + 0.033 * math.cos(2.0 * math.pi * n_dia / 365.0))
    if elevacao_deg > 0 and am > 0:
        i_dir = i_sc * (0.7 ** (am ** 0.678)) * math.sin(elev_rad)
    else:
        i_dir = 0.0

    return PosicaoSolar(
        dia_ano=n_dia,
        hora_solar_verdadeira=hora_solar_verdadeira,
        equacao_do_tempo_min=eot,
        declinacao_deg=declinacao_deg,
        angulo_horario_deg=omega_deg,
        elevacao_deg=elevacao_deg,
        zenite_deg=zenite_deg,
        azimute_deg=azimute_deg,
        hora_nascer_sol=nascer,
        hora_por_sol=por,
        duracao_dia_horas=duracao,
        massa_de_ar=am,
        irradiancia_direta_w_m2=i_dir,
    )


def gerar_trajetoria_solar_diurna(
    latitude_deg: float,
    longitude_deg: float,
    utc_offset: float,
    dia: int,
    mes: int,
    ano: int = 2026,
    num_pontos: int = 96,
) -> Tuple[List[float], List[float], List[float]]:
    """
    Gera curva horária (horas, azimutes, elevações) ao longo de 24 horas.
    """
    horas = []
    azimutes = []
    elevacoes = []

    for i in range(num_pontos):
        h = i * (24.0 / num_pontos)
        pos = calcular_posicao_solar(latitude_deg, longitude_deg, utc_offset, dia, mes, h, ano)
        horas.append(h)
        azimutes.append(pos.azimute_deg)
        elevacoes.append(pos.elevacao_deg)

    return horas, azimutes, elevacoes
