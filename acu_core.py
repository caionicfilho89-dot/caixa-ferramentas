# -*- coding: utf-8 -*-
"""
acu_core.py - Núcleo de Engenharia Acústica de Salas e Reverberação
Cálculo de tempo de reverberação RT60 pelas equações de Sabine e Eyring,
modos próprios de ressonância (ondas estacionárias), frequência de Schroeder e velocidade do som.
"""
import math
from typing import Dict, List, Any, Tuple

# Coeficientes de absorção sonora típicos alpha por banda de 500 Hz / 1 kHz
MATERIAL_ABSORPTION = {
    "Espuma Acústica Perfilada (50mm)": 0.85,
    "Lã de Rocha / Painel Fonoabsorvente": 0.80,
    "Carpete sobre Concreto": 0.35,
    "Gesso Acartonado (Drywall)": 0.10,
    "Piso de Madeira / Parquet": 0.10,
    "Vidro Comum (Janela)": 0.05,
    "Concreto Aparente / Alvenaria": 0.02,
}

ROOM_PRESETS = [
    ("Estúdio de Gravação / Podcast (Seco, RT60 ~0.3s)", 5.0, 4.0, 2.8, 0.65),
    ("Home Theater / Cinema em Casa (RT60 ~0.4s)", 6.0, 4.5, 2.8, 0.45),
    ("Auditório / Sala de Conferências (RT60 ~0.7s)", 12.0, 8.0, 3.5, 0.25),
    ("Sala de Aula Padrão (RT60 ~0.6s)", 8.0, 6.0, 3.0, 0.20),
    ("Quarto Residencial sem Tratamento (Eco)", 4.0, 3.5, 2.7, 0.08),
]

def speed_of_sound(temperature_c: float = 20.0) -> float:
    """Calcula a velocidade do som no ar em função da temperatura (m/s)."""
    return 331.3 * math.sqrt(1.0 + (temperature_c / 273.15))

def calculate_room_acoustics(
    length_m: float,
    width_m: float,
    height_m: float,
    avg_absorption_coeff: float = 0.20,
    temperature_c: float = 20.0
) -> Dict[str, Any]:
    """
    Calcula tempo de reverberação RT60 e frequência de Schroeder.
    length_m, width_m, height_m: dimensões da sala em metros
    avg_absorption_coeff: coeficiente médio de absorção das superfícies (0.0 a 1.0)
    temperature_c: temperatura do ar em Celsius
    """
    if length_m <= 0 or width_m <= 0 or height_m <= 0:
        raise ValueError("Dimensões da sala devem ser estritamente positivas.")

    c_sound = speed_of_sound(temperature_c)
    volume_m3 = length_m * width_m * height_m
    surface_area_m2 = 2.0 * (length_m * width_m + length_m * height_m + width_m * height_m)

    alpha_clamped = max(0.01, min(0.99, avg_absorption_coeff))
    absorption_area_a = surface_area_m2 * alpha_clamped

    # Tempo de Reverberação de Sabine: RT60 = 0.161 * V / A
    rt60_sabine = (0.161 * volume_m3) / absorption_area_a

    # Tempo de Reverberação de Eyring (mais preciso para salas com alta absorção alpha > 0.2)
    rt60_eyring = (0.161 * volume_m3) / (-surface_area_m2 * math.log(1.0 - alpha_clamped))

    # Frequência limite de Schroeder fs = 2000 * sqrt(RT60 / V)
    schroeder_freq = 2000.0 * math.sqrt(rt60_sabine / volume_m3)

    # Classificação do uso acústico recomendado
    if rt60_sabine < 0.35:
        recommendation = "Ideal para Gravação de Voz, Podcasts e Estúdios de Mixagem."
    elif rt60_sabine < 0.60:
        recommendation = "Excelente para Salas de Home Theater e Videoconferências."
    elif rt60_sabine < 0.90:
        recommendation = "Adequado para Salas de Aula e Discursos (Boa Inteligibilidade da Fala)."
    elif rt60_sabine < 1.40:
        recommendation = "Recomendado para Apresentações de Música Acústica e Corais."
    else:
        recommendation = "Ambiente excessivamente reverberante (eco / borrão sonoro perceptível)."

    # Cálculo dos 12 primeiros modos axiais e tangenciais da sala (até 250 Hz)
    modes = []
    for nx in range(4):
        for ny in range(4):
            for nz in range(4):
                if nx == 0 and ny == 0 and nz == 0:
                    continue
                # f = (c/2) * sqrt((nx/L)^2 + (ny/W)^2 + (nz/H)^2)
                f_mode = (c_sound / 2.0) * math.sqrt((nx / length_m) ** 2 + (ny / width_m) ** 2 + (nz / height_m) ** 2)
                if f_mode <= 250.0:
                    # Classificação do modo
                    non_zero = sum(1 for n in (nx, ny, nz) if n > 0)
                    m_type = "Axial (Forte)" if non_zero == 1 else ("Tangencial" if non_zero == 2 else "Oblíquo")
                    modes.append({
                        "freq_hz": round(f_mode, 1),
                        "indices": f"({nx}, {ny}, {nz})",
                        "type": m_type
                    })

    modes.sort(key=lambda m: m["freq_hz"])

    return {
        "volume_m3": round(volume_m3, 2),
        "surface_area_m2": round(surface_area_m2, 2),
        "speed_of_sound_ms": round(c_sound, 1),
        "absorption_area_sabins": round(absorption_area_a, 2),
        "rt60_sabine_s": round(rt60_sabine, 3),
        "rt60_eyring_s": round(rt60_eyring, 3),
        "schroeder_freq_hz": round(schroeder_freq, 1),
        "recommendation": recommendation,
        "room_modes": modes[:15]
    }
