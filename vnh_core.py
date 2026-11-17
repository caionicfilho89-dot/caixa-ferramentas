"""Harmonização de Vinhos e Queijos — lógica pura."""
VINHOS = {
    "Cabernet Sauvignon": {"corpo": 5, "acidez": 3, "tanino": 5, "docura": 1, "estilo": "tinto", "temp_C": 18},
    "Merlot": {"corpo": 4, "acidez": 3, "tanino": 3, "docura": 1, "estilo": "tinto", "temp_C": 17},
    "Pinot Noir": {"corpo": 3, "acidez": 4, "tanino": 2, "docura": 1, "estilo": "tinto", "temp_C": 15},
    "Malbec": {"corpo": 5, "acidez": 3, "tanino": 4, "docura": 1, "estilo": "tinto", "temp_C": 18},
    "Chardonnay": {"corpo": 4, "acidez": 3, "tanino": 0, "docura": 1, "estilo": "branco", "temp_C": 11},
    "Sauvignon Blanc": {"corpo": 2, "acidez": 5, "tanino": 0, "docura": 1, "estilo": "branco", "temp_C": 8},
    "Riesling": {"corpo": 2, "acidez": 5, "tanino": 0, "docura": 3, "estilo": "branco", "temp_C": 8},
    "Prosecco": {"corpo": 2, "acidez": 4, "tanino": 0, "docura": 2, "estilo": "espumante", "temp_C": 6},
    "Champagne": {"corpo": 3, "acidez": 5, "tanino": 0, "docura": 1, "estilo": "espumante", "temp_C": 7},
    "Porto": {"corpo": 5, "acidez": 2, "tanino": 3, "docura": 5, "estilo": "fortificado", "temp_C": 16},
}

QUEIJOS = {
    "Brie": {"gordura": 5, "sal": 2, "docura": 2, "intensidade": 3},
    "Camembert": {"gordura": 5, "sal": 2, "docura": 2, "intensidade": 3},
    "Gorgonzola": {"gordura": 4, "sal": 4, "docura": 1, "intensidade": 5},
    "Parmesão": {"gordura": 3, "sal": 5, "docura": 1, "intensidade": 5},
    "Gouda": {"gordura": 4, "sal": 3, "docura": 2, "intensidade": 3},
    "Cheddar": {"gordura": 4, "sal": 3, "docura": 1, "intensidade": 4},
    "Mussarela": {"gordura": 3, "sal": 2, "docura": 1, "intensidade": 2},
    "Goat (chevre)": {"gordura": 3, "sal": 2, "docura": 1, "intensidade": 3},
    "Manchego": {"gordura": 4, "sal": 3, "docura": 1, "intensidade": 4},
    "Provolone": {"gordura": 4, "sal": 3, "docura": 1, "intensidade": 3},
}

# ml por convidado por estilo (jantar ~2,5 h)
ML_POR_CONV = {"tinto": 375, "branco": 300, "espumante": 250, "fortificado": 120}


def pontuar(vinho_nome, queijo_nome):
    """Regras classicas: corpo~intensidade, acidez corta gordura, tanino com sal/gordura, doce com salgado."""
    if vinho_nome not in VINHOS or queijo_nome not in QUEIJOS:
        raise ValueError("Vinho ou queijo desconhecido.")
    v, q = VINHOS[vinho_nome], QUEIJOS[queijo_nome]
    score = 10.0
    # corpo vs intensidade: diferenca penaliza
    score -= abs(v["corpo"] - q["intensidade"]) * 1.2
    # acidez equilibra gordura
    score += min(v["acidez"], q["gordura"]) * 0.8
    # tanino com gordura/sal
    if v["tanino"]:
        score += min(v["tanino"], q["gordura"]) * 0.6
        score += min(v["tanino"], q["sal"]) * 0.3
    # doce com salgado (ex. porto + gorgonzola)
    score += min(v["docura"], q["sal"]) * 0.9
    # espumante com queijos leves
    if v["estilo"] == "espumante" and q["intensidade"] <= 3:
        score += 1.5
    return round(max(0.0, score), 2)


def top_vinhos_para(queijo_nome, n=3):
    if queijo_nome not in QUEIJOS:
        raise ValueError("Queijo desconhecido.")
    ranked = sorted(((pontuar(v, queijo_nome), v) for v in VINHOS), reverse=True)
    return [{"vinho": v, "nota": s, "temp_C": VINHOS[v]["temp_C"], "estilo": VINHOS[v]["estilo"]}
            for s, v in ranked[:n]]


def quantidade_vinho(convidados, estilo, garrafa_ml=750):
    if convidados <= 0 or garrafa_ml <= 0:
        raise ValueError("Valores inválidos.")
    if estilo not in ML_POR_CONV:
        raise ValueError("Estilo desconhecido.")
    ml = convidados * ML_POR_CONV[estilo]
    garrafas = -(-ml // garrafa_ml)  # ceil
    return {"ml_total": ml, "garrafas": int(garrafas), "ml_por_pessoa": ML_POR_CONV[estilo]}


def temperatura_servico(vinho_nome):
    if vinho_nome not in VINHOS:
        raise ValueError("Vinho desconhecido.")
    return VINHOS[vinho_nome]["temp_C"]
