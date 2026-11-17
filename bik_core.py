"""Calculadora de Marchas de Bicicleta — lógica pura (relações, desenvolvimento, velocidade, cadência, sobreposição)."""
import math

ARO_MM = {"700c / 29\"": 622, "27,5\" / 650b": 584, "26\"": 559, "24\"": 507, "20\" (BMX)": 406, "16\"": 305}
CASSETES = {
    "11-28 (11v estrada)": [11, 12, 13, 14, 15, 17, 19, 21, 23, 25, 28],
    "11-32 (11v)": [11, 12, 13, 14, 16, 18, 20, 22, 25, 28, 32],
    "11-34 (12v estrada)": [11, 12, 13, 14, 15, 17, 19, 21, 24, 27, 30, 34],
    "10-51 (12v MTB)": [10, 12, 14, 16, 18, 21, 24, 28, 33, 39, 45, 51],
    "11-42 (11v MTB)": [11, 13, 15, 17, 19, 21, 24, 28, 32, 37, 42],
    "14-28 (7v urbana)": [14, 16, 18, 20, 22, 24, 28],
}
PEDIVELAS = {"50/34 (compacta)": [34, 50], "52/36 (semi)": [36, 52], "53/39 (padrão)": [39, 53], "32 (1x MTB)": [32],
             "42/32/22 (tripla)": [22, 32, 42], "48/31 (gravel)": [31, 48]}


def circunferencia(aro, largura_mm):
    """Circunferência da roda (mm) = pi × (diâmetro do aro + 2 × altura do pneu ≈ largura)."""
    return math.pi * (ARO_MM[aro] + 2 * largura_mm)


def relacao(coroa, pinhao):
    if coroa <= 0 or pinhao <= 0:
        raise ValueError("Dentes precisam ser positivos.")
    return coroa / pinhao


def desenvolvimento_m(coroa, pinhao, circ_mm):
    return relacao(coroa, pinhao) * circ_mm / 1000


def gear_inches(coroa, pinhao, circ_mm):
    return relacao(coroa, pinhao) * circ_mm / math.pi / 25.4


def velocidade_kmh(coroa, pinhao, circ_mm, cadencia_rpm):
    return desenvolvimento_m(coroa, pinhao, circ_mm) * cadencia_rpm * 60 / 1000


def cadencia_para(vel_kmh, coroa, pinhao, circ_mm):
    return vel_kmh * 1000 / 60 / desenvolvimento_m(coroa, pinhao, circ_mm)


def cruzada(i_coroa, n_coroas, i_pinhao, n_pinhoes):
    """Corrente cruzada: coroa menor com os 2 menores pinhões ou coroa maior com os 2 maiores."""
    if n_coroas < 2:
        return False
    menor = i_coroa == 0
    maior = i_coroa == n_coroas - 1
    return (menor and i_pinhao <= 1) or (maior and i_pinhao >= n_pinhoes - 2)


def matriz(coroas, cassete, circ_mm, cadencia):
    out = []
    for ic, c in enumerate(coroas):
        linha = []
        for ip, p in enumerate(cassete):
            linha.append({"coroa": c, "pinhao": p, "relacao": relacao(c, p), "desenv": desenvolvimento_m(c, p, circ_mm),
                          "vel": velocidade_kmh(c, p, circ_mm, cadencia),
                          "cruzada": cruzada(ic, len(coroas), ip, len(cassete))})
        out.append(linha)
    return out


def marchas_uteis(coroas, cassete, tolerancia_pct=3.0):
    """Relações únicas (sem cruzadas), descartando as que diferem menos que a tolerância."""
    rel = sorted(relacao(c, p) for ic, c in enumerate(coroas) for ip, p in enumerate(cassete)
                 if not cruzada(ic, len(coroas), ip, len(cassete)))
    uteis = []
    for r in rel:
        if not uteis or (r / uteis[-1] - 1) * 100 >= tolerancia_pct:
            uteis.append(r)
    return uteis


def amplitude(coroas, cassete):
    return (max(coroas) / min(cassete)) / (min(coroas) / max(cassete)) * 100


def saltos_cassete(cassete):
    return [round((b / a - 1) * 100, 1) for a, b in zip(cassete, cassete[1:])]
