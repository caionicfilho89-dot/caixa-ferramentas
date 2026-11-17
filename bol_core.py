"""Conversor de Formas de Bolo — área/volume, escala de receita, tempo de forno."""
import math
import re

FORMAS = ["Redonda", "Quadrada", "Retangular", "Redonda com furo", "Quadrada com furo"]


def area(forma, a, b=0.0, furo=0.0):
    """a = diâmetro (redonda) ou lado (quadrada) ou largura (retangular).
    b = comprimento (retangular). furo = diâmetro/lado do furo central."""
    if a <= 0:
        raise ValueError("Dimensão precisa ser positiva.")
    if forma == "Redonda":
        return math.pi * (a / 2) ** 2
    if forma == "Quadrada":
        return a * a
    if forma == "Retangular":
        if b <= 0:
            raise ValueError("Retangular precisa de comprimento.")
        return a * b
    if forma == "Redonda com furo":
        if furo < 0 or furo >= a:
            raise ValueError("Furo inválido.")
        return math.pi * ((a / 2) ** 2 - (furo / 2) ** 2)
    if forma == "Quadrada com furo":
        if furo < 0 or furo >= a:
            raise ValueError("Furo inválido.")
        return a * a - furo * furo
    raise ValueError("Forma desconhecida.")


def volume(forma, a, altura, b=0.0, furo=0.0):
    if altura <= 0:
        raise ValueError("Altura precisa ser positiva.")
    return area(forma, a, b, furo) * altura


def fator_escala(origem, destino):
    """origem/destino: dicts com forma, a, b, furo, altura. Escala por volume."""
    vo = volume(origem["forma"], origem["a"], origem["altura"], origem.get("b", 0), origem.get("furo", 0))
    vd = volume(destino["forma"], destino["a"], destino["altura"], destino.get("b", 0), destino.get("furo", 0))
    if vo <= 0:
        raise ValueError("Volume de origem zero.")
    return vd / vo


def parse_ingredientes(texto):
    """Linhas tipo '200 g farinha' ou '2 xicaras açúcar'. Retorna [(qtd, unidade, nome)]."""
    out = []
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        m = re.match(r"^([\d.,]+)\s*([A-Za-z\u00C0-\u00FF]+)?\s+(.+)$", linha)
        if not m:
            raise ValueError(f"Não entendi: {linha}")
        qtd = float(m.group(1).replace(",", "."))
        uni = (m.group(2) or "un").strip()
        nome = m.group(3).strip()
        out.append((qtd, uni, nome))
    return out


def escalar_receita(ings, fator):
    return [(round(q * fator, 2), u, n) for q, u, n in ings]


def tempo_forno(tempo_orig_min, altura_orig, altura_nova):
    """Ajuste aproximado: tempo proporcional a altura^0.5 (forno conduz pelo centro)."""
    if tempo_orig_min <= 0 or altura_orig <= 0 or altura_nova <= 0:
        raise ValueError("Tempos/alturas inválidos.")
    return round(tempo_orig_min * math.sqrt(altura_nova / altura_orig))
