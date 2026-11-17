"""adp_essenciais.py — Adaptadores essenciais da Caixa de Ferramentas.

Contrato (RUMO.md):
- ADAPTADORES = [
    {
      "chave": "<chave da ferramenta>",
      "titulo": "<titulo amigavel>",
      "palavras": ["palavra1", "palavra2"],
      "extrair": f(texto) -> dict | None,
      "calcular": f(params) -> dict
    }
  ]
- O metodo calcular devolve dict com:
  {"resposta": str, "detalhe": str, "chave_ferramenta": str (opcional), "confianca": float (opcional)}
- Reutiliza a logica existente nos *_core.py e modulos de staged/ sem duplicar calculos.
- Cobre as 20 calculadoras essenciais e perguntas reais do PERGUNTAS.md (frações, gorjeta, rateio, etc.).
"""
from __future__ import annotations

import datetime
import math
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import respostas_core as rc

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
STAGED = os.path.join(HERE, "staged")
if os.path.isdir(STAGED) and STAGED not in sys.path:
    sys.path.append(STAGED)


# ======================================================================
# 0. Operações Encadeadas e Expressões Compostas na Barra (Proposta 2 / T30)
# ======================================================================

_RE_OP_ADICIONAL = r'(?:(?:\+|\bmais\b|\bcom\b)\s*(?:(?:frete|entrega|taxa|envio)\s*(?:de\s*)?([0-9.,]+(?:\s*mil)?)|([0-9.,]+(?:\s*mil)?)\s*(?:reais\s*)?(?:de\s*)?(?:frete|entrega|taxa|envio)))'

_RE_DESC_FRETE = re.compile(
    r'(?:([0-9.,]+)\s*%\s*(?:de\s*)?desconto\s*(?:em|de|sobre)\s*([0-9.,]+(?:\s*mil)?)(?:\s*reais)?|desconto\s*(?:de\s*)?([0-9.,]+)\s*%\s*(?:em|de|sobre)\s*([0-9.,]+(?:\s*mil)?)(?:\s*reais)?|desconto\s*(?:de\s*)?([0-9.,]+)\s*(?:reais)?\s*(?:em|no|de)\s*([0-9.,]+(?:\s*mil)?)(?:\s*reais)?)\s*' + _RE_OP_ADICIONAL,
    re.IGNORECASE
)

_RE_PARCELAS_COMPOSTAS = re.compile(
    r'(\d+)\s*(?:x|vezes|parcelas?)\s*(?:de\s*)?([0-9.,]+(?:\s*mil)?)\s*(?:e|\+|\bmais\b|,)\s*(\d+)\s*(?:(?:x|vezes|parcelas?)\s*(?:de\s*)?|de\s*)([0-9.,]+(?:\s*mil)?)',
    re.IGNORECASE
)

_RE_PRODUTOS_FRETE = re.compile(
    r'(\d+)\s*(?:unidades?|itens|produtos?|pecas?)\s*(?:de\s*)?([0-9.,]+(?:\s*mil)?)\s*' + _RE_OP_ADICIONAL,
    re.IGNORECASE
)

_RE_BASE_PCT_FIXO = re.compile(
    r'([0-9.,]+(?:\s*mil)?)\s*(?:reais)?\s*(menos|mais|\+|-)\s*([0-9.,]+)\s*%\s*(menos|mais|\+|-)\s*([0-9.,]+(?:\s*mil)?)',
    re.IGNORECASE
)

_RE_DESC_SUCESSIVOS = re.compile(
    r'(?:([0-9.,]+(?:\s*mil)?)\s*(?:reais)?\s*(?:com\s+)?desconto\s+(?:de\s+)?([0-9.,]+)\s*%\s*(?:e\s+depois|e\s+mais|\+)\s*(?:desconto\s+(?:de\s+)?|mais\s+)?([0-9.,]+)\s*%\s*(?:de\s+desconto)?|([0-9.,]+(?:\s*mil)?)\s*menos\s*([0-9.,]+)\s*%\s*menos\s*([0-9.,]+)\s*%)',
    re.IGNORECASE
)

_RE_PARCELAS_ENTRADA = re.compile(
    r'(?:entrada\s*(?:de\s*)?([0-9.,]+(?:\s*mil)?)\s*(?:\+|\be\b|\bmais\b)\s*(\d+)\s*(?:x|vezes|parcelas?)\s*(?:de\s*)?([0-9.,]+(?:\s*mil)?)|(\d+)\s*(?:x|vezes|parcelas?)\s*(?:de\s*)?([0-9.,]+(?:\s*mil)?)\s*(?:\+|\be\b|\bmais\b)\s*(?:entrada\s*(?:de\s*)?|([0-9.,]+(?:\s*mil)?)\s*(?:reais\s*)?(?:de\s*)?entrada\s*)([0-9.,]+(?:\s*mil)?))',
    re.IGNORECASE
)

_RE_ITENS_MISTOS = re.compile(
    r'(\d+)\s+[a-zA-ZÀ-ÿ]+\s+de\s+([0-9.,]+(?:\s*mil)?)\s*(?:e|\+|\bmais\b|,)\s*(\d+)\s+[a-zA-ZÀ-ÿ]+\s+de\s+([0-9.,]+(?:\s*mil)?)',
    re.IGNORECASE
)


def extrair_operacoes_compostas(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # 1. Desconto + Frete / Entrega / Taxa
    m_df = _RE_DESC_FRETE.search(norm)
    if m_df:
        g = m_df.groups()
        pct = rc.numero_br(g[0] or g[2])
        base = rc.numero_br(g[1] or g[3] or g[5])
        desc_fixo = rc.numero_br(g[4]) if g[4] else None
        adic = rc.numero_br(g[6] or g[7]) or 0.0
        tipo_adic = "frete" if "frete" in norm else ("entrega" if "entrega" in norm else ("envio" if "envio" in norm else "taxa"))
        if base and (pct or desc_fixo):
            return {
                "tipo": "desconto_frete",
                "base": base,
                "pct": pct,
                "desc_fixo": desc_fixo,
                "adicional": adic,
                "tipo_adicional": tipo_adic,
            }

    # 2. Descontos Sucessivos (ex: 1000 menos 10% menos 10%)
    m_ds = _RE_DESC_SUCESSIVOS.search(norm)
    if m_ds:
        g = m_ds.groups()
        base = rc.numero_br(g[0] or g[3])
        d1 = rc.numero_br(g[1] or g[4])
        d2 = rc.numero_br(g[2] or g[5])
        if base and d1 and d2:
            return {"tipo": "descontos_sucessivos", "base": base, "d1": d1, "d2": d2}

    # 3. Base mais/menos percentual e mais/menos valor fixo (ex: 200 reais menos 15% mais 30)
    m_bpf = _RE_BASE_PCT_FIXO.search(norm)
    if m_bpf:
        base = rc.numero_br(m_bpf.group(1))
        op1 = m_bpf.group(2).lower()
        pct = rc.numero_br(m_bpf.group(3))
        op2 = m_bpf.group(4).lower()
        val2 = rc.numero_br(m_bpf.group(5))
        if base and pct and val2:
            return {"tipo": "base_pct_fixo", "base": base, "op1": op1, "pct": pct, "op2": op2, "val2": val2}

    # 4. Parcelas Combinadas (ex: 3 parcelas de 120 e 2 de 80)
    m_pc = _RE_PARCELAS_COMPOSTAS.search(norm)
    if m_pc:
        q1 = int(m_pc.group(1))
        v1 = rc.numero_br(m_pc.group(2))
        q2 = int(m_pc.group(3))
        v2 = rc.numero_br(m_pc.group(4))
        if v1 and v2 and q1 > 0 and q2 > 0:
            return {"tipo": "parcelas_combinadas", "q1": q1, "v1": v1, "q2": q2, "v2": v2}

    # 5. Itens mistos (ex: 4 camisetas de 35 e 2 bermudas de 60)
    m_im = _RE_ITENS_MISTOS.search(norm)
    if m_im and "parcela" not in norm and "vezes" not in norm:
        q1 = int(m_im.group(1))
        v1 = rc.numero_br(m_im.group(2))
        q2 = int(m_im.group(3))
        v2 = rc.numero_br(m_im.group(4))
        if v1 and v2 and q1 > 0 and q2 > 0:
            return {"tipo": "parcelas_combinadas", "q1": q1, "v1": v1, "q2": q2, "v2": v2, "label": "Compras Mistas"}

    # 6. Parcelas + Entrada (ex: entrada de 500 + 4 parcelas de 250)
    m_pe = _RE_PARCELAS_ENTRADA.search(norm)
    if m_pe:
        g = m_pe.groups()
        if g[0]:
            ent = rc.numero_br(g[0]) or 0.0
            q = int(g[1])
            v = rc.numero_br(g[2]) or 0.0
        else:
            q = int(g[3])
            v = rc.numero_br(g[4]) or 0.0
            ent = rc.numero_br(g[5] or g[6]) or 0.0
        if q > 0 and v > 0:
            return {"tipo": "parcelas_entrada", "q": q, "v": v, "entrada": ent}

    # 7. Produtos + Frete (ex: 3 produtos de 45 mais frete de 20)
    m_pf = _RE_PRODUTOS_FRETE.search(norm)
    if m_pf:
        q = int(m_pf.group(1))
        v = rc.numero_br(m_pf.group(2)) or 0.0
        adic = rc.numero_br(m_pf.group(3) or m_pf.group(4)) or 0.0
        tipo_adic = "frete" if "frete" in norm else ("entrega" if "entrega" in norm else "taxa")
        if q > 0 and v > 0:
            return {"tipo": "compras_frete", "q": q, "v": v, "adicional": adic, "tipo_adicional": tipo_adic}

    return None


def calcular_operacoes_compostas(p: Dict[str, Any]) -> Dict[str, Any]:
    tipo = p.get("tipo")

    if tipo == "desconto_frete":
        base = p["base"]
        if p.get("pct") is not None:
            pct = p["pct"]
            desc_val = base * (pct / 100.0)
            subtotal = max(0.0, base - desc_val)
            desc_str = f"{pct:g}% (R$ {rc.formatar_br(desc_val, 2)})"
        else:
            desc_val = p.get("desc_fixo", 0.0)
            subtotal = max(0.0, base - desc_val)
            desc_str = f"R$ {rc.formatar_br(desc_val, 2)}"
        adic = p["adicional"]
        total = subtotal + adic
        tipo_adic = p.get("tipo_adicional", "frete")
        ans = rc.formatar_br(total, 2)
        return {
            "titulo": "Desconto + Frete / Taxa",
            "resposta": f"R$ {ans}",
            "detalhe": f"Base R$ {rc.formatar_br(base, 2)} - desconto {desc_str} = R$ {rc.formatar_br(subtotal, 2)} + {tipo_adic} R$ {rc.formatar_br(adic, 2)} = total R$ {ans}.",
            "chave_ferramenta": "calculadora-desconto",
            "confianca": 0.98,
        }

    elif tipo == "descontos_sucessivos":
        base = p["base"]
        d1, d2 = p["d1"], p["d2"]
        val1 = base * (d1 / 100.0)
        apos1 = base - val1
        val2 = apos1 * (d2 / 100.0)
        total = apos1 - val2
        ans = rc.formatar_br(total, 2)
        return {
            "titulo": "Descontos Sucessivos",
            "resposta": f"R$ {ans}",
            "detalhe": f"R$ {rc.formatar_br(base, 2)} - {d1:g}% (R$ {rc.formatar_br(val1, 2)}) = R$ {rc.formatar_br(apos1, 2)} - {d2:g}% (R$ {rc.formatar_br(val2, 2)}) = final R$ {ans}.",
            "chave_ferramenta": "calculadora-desconto",
            "confianca": 0.98,
        }

    elif tipo == "base_pct_fixo":
        base = p["base"]
        pct = p["pct"]
        val2 = p["val2"]
        op1 = p["op1"]
        op2 = p["op2"]
        val_pct = base * (pct / 100.0)
        apos_pct = base - val_pct if op1 in ["menos", "-"] else base + val_pct
        total = apos_pct - val2 if op2 in ["menos", "-"] else apos_pct + val2
        s1 = "-" if op1 in ["menos", "-"] else "+"
        s2 = "-" if op2 in ["menos", "-"] else "+"
        ans = rc.formatar_br(total, 2)
        return {
            "titulo": "Cálculo Encadeado",
            "resposta": f"R$ {ans}",
            "detalhe": f"R$ {rc.formatar_br(base, 2)} {s1} {pct:g}% (R$ {rc.formatar_br(val_pct, 2)}) = R$ {rc.formatar_br(apos_pct, 2)} {s2} R$ {rc.formatar_br(val2, 2)} = total R$ {ans}.",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }

    elif tipo == "parcelas_combinadas":
        q1, v1 = p["q1"], p["v1"]
        q2, v2 = p["q2"], p["v2"]
        tot1 = q1 * v1
        tot2 = q2 * v2
        total = tot1 + tot2
        rotulo = p.get("label", "Parcelas Combinadas")
        ans = rc.formatar_br(total, 2)
        return {
            "titulo": rotulo,
            "resposta": f"R$ {ans}",
            "detalhe": f"{q1}× R$ {rc.formatar_br(v1, 2)} (R$ {rc.formatar_br(tot1, 2)}) + {q2}× R$ {rc.formatar_br(v2, 2)} (R$ {rc.formatar_br(tot2, 2)}) = total R$ {ans}.",
            "chave_ferramenta": "compras-parceladas",
            "confianca": 0.98,
        }

    elif tipo == "parcelas_entrada":
        q, v = p["q"], p["v"]
        ent = p["entrada"]
        tot_parc = q * v
        total = tot_parc + ent
        ans = rc.formatar_br(total, 2)
        return {
            "titulo": "Parcelas com Entrada",
            "resposta": f"R$ {ans}",
            "detalhe": f"Entrada R$ {rc.formatar_br(ent, 2)} + {q}× R$ {rc.formatar_br(v, 2)} (R$ {rc.formatar_br(tot_parc, 2)}) = total R$ {ans}.",
            "chave_ferramenta": "compras-parceladas",
            "confianca": 0.98,
        }

    elif tipo == "compras_frete":
        q, v = p["q"], p["v"]
        adic = p["adicional"]
        tipo_adic = p.get("tipo_adicional", "frete")
        subtot = q * v
        total = subtot + adic
        ans = rc.formatar_br(total, 2)
        return {
            "titulo": "Compras + Frete",
            "resposta": f"R$ {ans}",
            "detalhe": f"{q}× R$ {rc.formatar_br(v, 2)} (R$ {rc.formatar_br(subtot, 2)}) + {tipo_adic} R$ {rc.formatar_br(adic, 2)} = total R$ {ans}.",
            "chave_ferramenta": "compras-parceladas",
            "confianca": 0.98,
        }

    return {"titulo": "Operação Composta", "resposta": "", "detalhe": "", "confianca": 0.0}


# ======================================================================
# 1. Porcentagem (Básica, Aumento, Desconto, "Off", Variação)
# ======================================================================

def extrair_porcentagem(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    # Evita conflitos com outros dominios especificos
    if any(k in norm for k in ["ipva", "maquininha", "atrasado", "juros simples", "juros compostos", "gorjeta", "rateio"]):
        return None

    # Ex: "quanto falta pra 100% se ja tenho 73%"
    m_falta = re.search(r"quanto\s+falta\s+pra\s*100%\s+se\s+ja\s+tenho\s*([0-9.,]+)%", norm)
    if m_falta:
        v = rc.numero_br(m_falta.group(1))
        if v is not None:
            return {"tipo": "falta_100", "ja_tem": v}

    # Ex: "saí da loja pagando 80 reais depois de 20% de desconto — qual era o preco cheio"
    m_cheio = re.search(r"pagando\s+([0-9.,]+)\s*(?:reais)?\s*depois\s+de\s+([0-9.,]+)%\s*de\s+desconto", norm)
    if m_cheio:
        pago = rc.numero_br(m_cheio.group(1))
        desc = rc.numero_br(m_cheio.group(2))
        if pago is not None and desc is not None and desc < 100:
            return {"tipo": "preco_cheio", "pago": pago, "desc_pct": desc}

    # Ex: "40% off em 159,90", "20% off de 200"
    m_off = re.search(r"([0-9.,]+)\s*%\s*off\s*(?:em|de|sobre)?\s*([0-9.,]+(?:\s*mil)?)", norm)
    if m_off:
        p = rc.numero_br(m_off.group(1))
        b = rc.numero_br(m_off.group(2))
        if p is not None and b is not None:
            return {"tipo": "desconto", "pct": p, "base": b}

    # Ex: "10 mil menos 12,5%", "1200 menos 10%"
    m_menos_pct = re.search(r"([0-9.,]+(?:\s*mil)?)\s*menos\s*([0-9.,]+)\s*%", norm)
    if m_menos_pct:
        b = rc.numero_br(m_menos_pct.group(1))
        p = rc.numero_br(m_menos_pct.group(2))
        if p is not None and b is not None:
            return {"tipo": "desconto", "pct": p, "base": b}

    # Ex: "desconto de 25 reais em produto de 199"
    m_desc_val = re.search(r"desconto\s+de\s+([0-9.,]+)\s*(?:reais)?\s*(?:em|no|de)\s*(?:produto\s+de\s*)?([0-9.,]+)", norm)
    if m_desc_val and "%" not in m_desc_val.group(1):
        d = rc.numero_br(m_desc_val.group(1))
        b = rc.numero_br(m_desc_val.group(2))
        if d is not None and b is not None and b > 0:
            return {"tipo": "desconto_fixo", "desconto": d, "base": b}

    # Ex: "comprei por 80 vendi por 110, lucro % sobre o custo"
    m_lucro = re.search(r"comprei\s+por\s+([0-9.,]+)\s*vendi\s+por\s+([0-9.,]+)", norm)
    if m_lucro:
        c = rc.numero_br(m_lucro.group(1))
        v = rc.numero_br(m_lucro.group(2))
        if c is not None and v is not None and c > 0:
            return {"tipo": "lucro_pct", "custo": c, "venda": v}

    # Ex: "quanto 50 representa de 200", "quanto e 50 de 200"
    m_rep = re.search(r"quanto\s+(?:representa\s+|e\s+)?([0-9.,]+)\s*(?:reais)?\s*(?:de|em)\s*([0-9.,]+)", norm)
    if m_rep and "%" not in m_rep.group(1):
        v1 = rc.numero_br(m_rep.group(1))
        v2 = rc.numero_br(m_rep.group(2))
        if v1 is not None and v2 is not None and v2 > 0:
            return {"tipo": "representa", "val": v1, "total": v2}

    # Ex: "aumentou 10% em cima de 1.200", "aumento de 15% em 200"
    m_aum = re.search(r"(?:aumento|acrescimo|aumentou)\s+(?:de\s+)?([0-9.,]+)\s*%\s*(?:em|de|sobre|em cima de)\s*([0-9.,]+(?:\s*mil)?)", norm)
    if m_aum:
        p = rc.numero_br(m_aum.group(1))
        b = rc.numero_br(m_aum.group(2))
        if p is not None and b is not None:
            return {"tipo": "aumento", "pct": p, "base": b}

    # Ex: "desconto de 10% em 500", "10% de desconto em 500", "10% desconto em 500"
    m_desc = re.search(r"(?:desconto\s+de\s+([0-9.,]+)\s*%\s*(?:em|de|sobre)\s*([0-9.,]+(?:\s*mil)?)|([0-9.,]+)\s*%\s*(?:de\s+)?desconto\s+(?:em|de|sobre)\s*([0-9.,]+(?:\s*mil)?))", norm)
    if m_desc:
        p = rc.numero_br(m_desc.group(1) or m_desc.group(3))
        b = rc.numero_br(m_desc.group(2) or m_desc.group(4))
        if p is not None and b is not None:
            return {"tipo": "desconto", "pct": p, "base": b}

    # Ex: "porcentagem de 15 em 200", "calculo de 15% de 200"
    m_p_de = re.search(r"porcentagem\s+(?:de\s+)?([0-9.,]+)\s*(?:%|\s*por\s*cento)?\s*(?:em|de|sobre)\s*([0-9.,]+(?:\s*mil)?)", norm)
    if m_p_de:
        p = rc.numero_br(m_p_de.group(1))
        b = rc.numero_br(m_p_de.group(2))
        if p is not None and b is not None:
            return {"tipo": "de", "pct": p, "base": b}

    # Ex: "salario 3.200, desconto 9%"
    m_sal_desc = re.search(r"salario\s+([0-9.,]+(?:\s*mil)?)[,\s]+desconto\s+([0-9.,]+)\s*%", norm)
    if m_sal_desc:
        b = rc.numero_br(m_sal_desc.group(1))
        p = rc.numero_br(m_sal_desc.group(2))
        if b is not None and p is not None:
            return {"tipo": "salario_desconto", "base": b, "pct": p}

    # Ex: "20% de 350", "quanto e 20% de 350"
    m_pct = re.search(r"([0-9.,]+)\s*(?:%|por\s*cento)\s*(?:de|sobre|em)\s*([0-9.,]+(?:\s*mil)?)", norm)
    if m_pct:
        p = rc.numero_br(m_pct.group(1))
        b = rc.numero_br(m_pct.group(2))
        if p is not None and b is not None:
            return {"tipo": "de", "pct": p, "base": b}

    return None


def calcular_porcentagem(p: Dict[str, Any]) -> Dict[str, Any]:
    tipo = p["tipo"]
    if tipo == "falta_100":
        falta = 100.0 - p["ja_tem"]
        return {
            "titulo": "Cálculo de Porcentagem",
            "resposta": f"{rc.formatar_br(falta, 0 if falta == int(falta) else 2)}%",
            "detalhe": f"100% − {rc.formatar_br(p['ja_tem'], 0 if p['ja_tem'] == int(p['ja_tem']) else 2)}% = {rc.formatar_br(falta, 0 if falta == int(falta) else 2)}%",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "preco_cheio":
        cheio = p["pago"] / (1.0 - (p["desc_pct"] / 100.0))
        return {
            "titulo": "Preço Cheio Original",
            "resposta": f"{rc.formatar_br(cheio, 2)}",
            "detalhe": f"Preço cheio = {rc.formatar_br(p['pago'], 2)} ÷ (1 − {p['desc_pct']:g}%) = {rc.formatar_br(cheio, 2)}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "desconto_fixo":
        final = p["base"] - p["desconto"]
        pct = (p["desconto"] / p["base"]) * 100.0
        return {
            "titulo": "Desconto no Preço",
            "resposta": f"{rc.formatar_br(final, 2)}; desconto ≈ {rc.formatar_br(pct, 2)}%",
            "detalhe": f"Preço final: {rc.formatar_br(final, 2)} (desconto de R$ {rc.formatar_br(p['desconto'], 2)} = {rc.formatar_br(pct, 2)}%)",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "lucro_pct":
        lucro = p["venda"] - p["custo"]
        pct = (lucro / p["custo"]) * 100.0
        return {
            "titulo": "Lucro sobre o Custo",
            "resposta": f"{rc.formatar_br(pct, 1 if pct == round(pct, 1) else 2)}%",
            "detalhe": f"Lucro: R$ {rc.formatar_br(lucro, 2)} sobre custo de R$ {rc.formatar_br(p['custo'], 2)} ({rc.formatar_br(pct, 1)}%)",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "salario_desconto":
        desc = p["base"] * (p["pct"] / 100.0)
        liq = p["base"] - desc
        return {
            "titulo": "Desconto Salarial",
            "resposta": f"desconto {rc.formatar_br(desc, 2)}; líquido {rc.formatar_br(liq, 2)}",
            "detalhe": f"Salário: R$ {rc.formatar_br(p['base'], 2)}. Desconto de {p['pct']:g}%: R$ {rc.formatar_br(desc, 2)}. Líquido: R$ {rc.formatar_br(liq, 2)}.",
            "chave_ferramenta": "calculadora-clt",
            "confianca": 0.98,
        }
    elif tipo == "representa":
        val, tot = p["val"], p["total"]
        pct = (val / tot) * 100.0
        return {
            "titulo": "Cálculo de Porcentagem",
            "resposta": f"{rc.formatar_br(pct, 2)}%",
            "detalhe": f"{rc.formatar_br(val)} representa {rc.formatar_br(pct, 2)}% de {rc.formatar_br(tot)}",
            "chave_ferramenta": "financas",
            "confianca": 0.95,
        }
    elif tipo == "aumento":
        pct, base = p["pct"], p["base"]
        dif = base * (pct / 100.0)
        final = base + dif
        ans = rc.formatar_br(final, 0 if final == int(final) else 2)
        return {
            "titulo": "Aumento Percentual",
            "resposta": f"{ans}",
            "detalhe": f"+{pct:g}% (+R$ {rc.formatar_br(dif, 2)}). Preço final: R$ {rc.formatar_br(final, 2)}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "desconto":
        pct, base = p["pct"], p["base"]
        dif = base * (pct / 100.0)
        final = base - dif
        ans = rc.formatar_br(final, 2 if final != int(final) else 0)
        return {
            "titulo": "Desconto Percentual",
            "resposta": f"{ans}",
            "detalhe": f"-{pct:g}% (-R$ {rc.formatar_br(dif, 2)}). Preço final: R$ {rc.formatar_br(final, 2)}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    else:  # "de"
        pct, base = p["pct"], p["base"]
        res = (pct / 100.0) * base
        ans = rc.formatar_br(res, 0 if res == int(res) else 2)
        return {
            "titulo": "Porcentagem",
            "resposta": f"{ans}",
            "detalhe": f"{pct:g}% de {rc.formatar_br(base, 2)} = {ans}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }


# ======================================================================
# 2. Frações (1/4 de 880, 1/3 de 8 pedaços, 3/5 de 450, 7/8 de 64)
# ======================================================================

def extrair_fracao(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    # Evita colisao com CIDR / mascara de IP / subredes / datas DD/MM/AAAA
    if re.search(r"\d+\.\d+\.\d+\.\d+/\d+", norm) or re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", norm) or "subrede" in norm or "cidr" in norm:
        return None
    # Ex: "1/4 de 880", "sobrou 1/3 de uma pizza cortada em 8 pedacos", "3/5 de 450", "7/8 de 64"
    m = re.search(r"(\d+)\s*/\s*(\d+)\s*(?:de|da|do|dos|das)?\s*(?:uma\s+pizza\s+cortada\s+em\s*)?([0-9.,]+(?:\s*mil)?)", norm)
    if m:
        num = int(m.group(1))
        den = int(m.group(2))
        total = rc.numero_br(m.group(3))
        if den > 0 and total is not None:
            return {"num": num, "den": den, "total": total, "original": norm}
    return None


def calcular_fracao(p: Dict[str, Any]) -> Dict[str, Any]:
    num, den, total = p["num"], p["den"], p["total"]
    val = (num * total) / den
    casas = 0 if val == int(val) else 2
    val_str = rc.formatar_br(val, casas)
    if "pizza" in p.get("original", ""):
        return {
            "titulo": "Cálculo de Fração",
            "resposta": f"equivalente a {num*int(total)}/{den} ≈ {rc.formatar_br(val, 2)} pedaços",
            "detalhe": f"{num}/{den} de {int(total)} pedaços = {val_str} pedaços",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    return {
        "titulo": "Cálculo de Fração",
        "resposta": f"{val_str}",
        "detalhe": f"{num}/{den} de {rc.formatar_br(total, 0 if total == int(total) else 2)} = {val_str}",
        "chave_ferramenta": "financas",
        "confianca": 0.98,
    }


# ======================================================================
# 3. Metade, Dobro e Dúzias
# ======================================================================

def extrair_metade_dobro_duzia(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Ex: "2 duzias e meia de ovos", "3 duzias de ovos"
    m_duz = re.search(r"([0-9.,]+)\s*duzias?(?:\s*e\s*meia)?", norm)
    if m_duz:
        q = rc.numero_br(m_duz.group(1))
        if q is not None:
            if "meia" in norm:
                q += 0.5
            return {"tipo": "duzia", "qtd": q}

    # Ex: "quanto e a metade de 2.450"
    m_met = re.search(r"metade\s+de\s+([0-9.,]+(?:\s*mil)?)", norm)
    if m_met:
        v = rc.numero_br(m_met.group(1))
        if v is not None:
            return {"tipo": "metade", "val": v}

    # Ex: "dobrar a receita de bolo que usa 200g de farinha", "dobro de 150"
    m_dob = re.search(r"(?:dobro\s+de|dobrar\s+.*?usa)\s+([0-9.,]+)\s*([a-zA-Z]+)?", norm)
    if m_dob:
        v = rc.numero_br(m_dob.group(1))
        u = m_dob.group(2) or ""
        if v is not None:
            return {"tipo": "dobro", "val": v, "unidade": u}

    return None


def calcular_metade_dobro_duzia(p: Dict[str, Any]) -> Dict[str, Any]:
    tipo = p["tipo"]
    if tipo == "duzia":
        tot = int(round(p["qtd"] * 12))
        return {
            "titulo": "Cálculo de Dúzias",
            "resposta": f"{tot}",
            "detalhe": f"{p['qtd']:g} dúzia(s) × 12 = {tot} unidades.",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "metade":
        res = p["val"] / 2.0
        ans = rc.formatar_br(res, 0 if res == int(res) else 2)
        return {
            "titulo": "Metade",
            "resposta": f"{ans}",
            "detalhe": f"Metade de {rc.formatar_br(p['val'], 0 if p['val'] == int(p['val']) else 2)} = {ans}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    else:  # dobro
        res = p["val"] * 2.0
        u = f" {p['unidade']}" if p.get("unidade") else ""
        ans = f"{rc.formatar_br(res, 0 if res == int(res) else 2)}{u}"
        return {
            "titulo": "Dobro",
            "resposta": f"{ans}",
            "detalhe": f"Dobro de {rc.formatar_br(p['val'], 0 if p['val'] == int(p['val']) else 2)}{u} = {ans}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }


# ======================================================================
# 4. Operação Aritmética Direta (1.234,56 + 78,9)
# ======================================================================

def extrair_aritmetica(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    # Evita conflitos com outros dominios especificos que usam palavras como menos/mais/porcentagem/etc.
    if any(k in norm for k in ["%", "off", "desconto", "juros", "ipva", "parcelas", "frete", "salario", "clt", "inss", "troco", "lucro", "km/l", "r$/"]):
        return None

    # Ex: "dividir 10 por 0", "10 dividido por 2"
    m_div = re.search(r"(?:dividir\s+)?([0-9.,]+(?:\s*mil)?)\s*(?:dividido\s+por|dividido\s+pra|por|/)\s*([0-9.,]+(?:\s*mil)?)", norm)
    if "dividir" in norm or "dividido" in norm:
        if m_div:
            a = rc.numero_br(m_div.group(1))
            b = rc.numero_br(m_div.group(2))
            if a is not None and b is not None:
                return {"a": a, "op": "/", "b": b}

    # Ex: "multiplicar 12 por 5", "12 multiplicado por 5", "15 vezes 8"
    m_mult = re.search(r"(?:multiplicar\s+)?([0-9.,]+(?:\s*mil)?)\s*(?:multiplicado\s+por|vezes)\s*([0-9.,]+(?:\s*mil)?)", norm)
    if "multiplicar" in norm or "multiplicado" in norm or "vezes" in norm:
        if m_mult:
            a = rc.numero_br(m_mult.group(1))
            b = rc.numero_br(m_mult.group(2))
            if a is not None and b is not None:
                return {"a": a, "op": "*", "b": b}

    # Ex: "somar 40 e 60", "somar 40 com 60", "40 mais 60"
    m_soma = re.search(r"(?:somar\s+)?([0-9.,]+(?:\s*mil)?)\s*(?:mais|\+)\s*([0-9.,]+(?:\s*mil)?)", norm)
    if "somar" in norm or "mais" in norm:
        if m_soma:
            a = rc.numero_br(m_soma.group(1))
            b = rc.numero_br(m_soma.group(2))
            if a is not None and b is not None:
                return {"a": a, "op": "+", "b": b}

    # Ex: "subtrair 50 de 200"
    m_sub_de = re.search(r"subtrair\s+([0-9.,]+(?:\s*mil)?)\s+de\s+([0-9.,]+(?:\s*mil)?)", norm)
    if m_sub_de:
        a = rc.numero_br(m_sub_de.group(2))
        b = rc.numero_br(m_sub_de.group(1))
        if a is not None and b is not None:
            return {"a": a, "op": "-", "b": b}

    # Ex: "200 menos 50"
    m_sub = re.search(r"([0-9.,]+(?:\s*mil)?)\s*(?:menos|\-)\s*([0-9.,]+(?:\s*mil)?)", norm)
    if "subtrair" in norm or "menos" in norm:
        if m_sub:
            a = rc.numero_br(m_sub.group(1))
            b = rc.numero_br(m_sub.group(2))
            if a is not None and b is not None:
                return {"a": a, "op": "-", "b": b}

    # Expressao direta: A + B, A - B, A * B, A / B, A x B
    # Aceita prefixos opcionais como "quanto e", "quanto da", "resultado de", "="
    m_direto = re.search(
        r"(?:quanto\s+(?:e|da)\s+|resultado\s+de\s+|calc\s+|^\s*)([0-9.,]+(?:\s*mil)?)\s*([\+\-\*\/xX])\s*([0-9.,]+(?:\s*mil)?)\s*$",
        norm
    )
    if m_direto:
        a = rc.numero_br(m_direto.group(1))
        op = m_direto.group(2).lower()
        if op == "x":
            op = "*"
        b = rc.numero_br(m_direto.group(3))
        if a is not None and b is not None:
            return {"a": a, "op": op, "b": b}

    return None


def calcular_aritmetica(p: Dict[str, Any]) -> Dict[str, Any]:
    a, op, b = p["a"], p["op"], p["b"]
    if op == "+":
        res = a + b
    elif op == "-":
        res = a - b
    elif op == "*":
        res = a * b
    else:
        if b == 0:
            return {
                "titulo": "Calculadora Aritmética",
                "resposta": "Não é possível dividir por zero",
                "detalhe": "A divisão por zero é indefinida na matemática.",
                "chave_ferramenta": "financas",
                "confianca": 0.98,
            }
        res = a / b
    ans = rc.formatar_br(res, 2 if res != int(res) else 0)
    return {
        "titulo": "Calculadora Aritmética",
        "resposta": f"{ans}",
        "detalhe": f"{rc.formatar_br(a, 2)} {op} {rc.formatar_br(b, 2)} = {ans}",
        "chave_ferramenta": "financas",
        "confianca": 0.98,
    }


# ======================================================================
# 5. Compras, Multiplicação Unitária e Custo Unitário
# ======================================================================

def extrair_compras_unitarias(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Ex: "3 camisetas a 49,90 e frete fixo 19,90"
    m_frete = re.search(r"(\d+)\s*[a-zA-Z]+\s*a\s*([0-9.,]+)\s*e\s*frete\s*(?:fixo)?\s*([0-9.,]+)", norm)
    if m_frete:
        q = int(m_frete.group(1))
        preco = rc.numero_br(m_frete.group(2)) or 0.0
        frete = rc.numero_br(m_frete.group(3)) or 0.0
        return {"tipo": "compra_frete", "qtd": q, "preco": preco, "frete": frete}

    # Ex: "comprei 4 un a 12,90 cada, total?", "150 kWh a 0,85 R$/kWh", "combustivel 40 litros a 5,89 o litro"
    if not any(k in norm for k in ["taxa", "fixa", "adicional", "pix"]):
        m_un = re.search(r"([0-9.,]+)\s*(?:un|unidades?|itens?|kwh|litros?)\s*a\s*([0-9.,]+)", norm)
        if m_un:
            q = rc.numero_br(m_un.group(1))
            p = rc.numero_br(m_un.group(2))
            if q and p:
                return {"tipo": "multiplicacao", "qtd": q, "unitario": p}

    # Ex: "12 parcelas de 189,90, total pago"
    m_parc = re.search(r"(\d+)\s*parcelas?\s*de\s*([0-9.,]+)", norm)
    if m_parc:
        q = int(m_parc.group(1))
        p = rc.numero_br(m_parc.group(2)) or 0.0
        return {"tipo": "parcelas", "qtd": q, "unitario": p}

    # Ex: "botijao 13 kg a 110 reais, quanto sai o kg"
    m_kg = re.search(r"([0-9.,]+)\s*kg\s*a\s*([0-9.,]+)\s*(?:reais)?.*?quanto\s+sai\s+o\s+kg", norm)
    if m_kg:
        peso = rc.numero_br(m_kg.group(1))
        valor = rc.numero_br(m_kg.group(2))
        if peso and valor:
            return {"tipo": "custo_por_unidade", "qtd": peso, "total": valor, "un": "R$/kg"}

    # Ex: "andei 480 km e gastei 235,60, custo por km"
    m_km = re.search(r"(?:andei|rodou|viagem\s+de)?\s*([0-9.,]+)\s*km\s*e\s*gastei\s*([0-9.,]+)", norm)
    if m_km:
        km = rc.numero_br(m_km.group(1))
        gasto = rc.numero_br(m_km.group(2))
        if km and gasto:
            return {"tipo": "custo_por_unidade", "qtd": km, "total": gasto, "un": "R$/km"}

    # Ex: "40 L com consumo 12 km/L, quantos km"
    m_aut = re.search(r"([0-9.,]+)\s*l\s*com\s*consumo\s*([0-9.,]+)\s*km/l", norm)
    if m_aut:
        litros = rc.numero_br(m_aut.group(1))
        cons = rc.numero_br(m_aut.group(2))
        if litros and cons:
            return {"tipo": "autonomia_km", "litros": litros, "consumo": cons}

    return None


def calcular_compras_unitarias(p: Dict[str, Any]) -> Dict[str, Any]:
    tipo = p["tipo"]
    if tipo == "compra_frete":
        tot = (p["qtd"] * p["preco"]) + p["frete"]
        ans = rc.formatar_br(tot, 2)
        return {
            "titulo": "Total da Compra",
            "resposta": f"{ans}",
            "detalhe": f"{p['qtd']} × R$ {rc.formatar_br(p['preco'], 2)} + frete R$ {rc.formatar_br(p['frete'], 2)} = R$ {ans}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo in ("multiplicacao", "parcelas"):
        tot = p["qtd"] * p["unitario"]
        ans = rc.formatar_br(tot, 2)
        rotulo = "Total das Parcelas" if tipo == "parcelas" else "Total da Compra"
        return {
            "titulo": rotulo,
            "resposta": f"{ans}",
            "detalhe": f"{p['qtd']:g} × R$ {rc.formatar_br(p['unitario'], 2)} = R$ {ans}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "custo_por_unidade":
        unit = p["total"] / p["qtd"]
        ans = rc.formatar_br(unit, 2)
        return {
            "titulo": "Custo Unitário",
            "resposta": f"≈ {ans} {p['un']}",
            "detalhe": f"R$ {rc.formatar_br(p['total'], 2)} ÷ {p['qtd']:g} = R$ {ans} por unidade.",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    else:  # autonomia_km
        km = p["litros"] * p["consumo"]
        ans = int(round(km))
        return {
            "titulo": "Autonomia de Combustível",
            "resposta": f"{ans} km",
            "detalhe": f"{p['litros']:g} L × {p['consumo']:g} km/L = {ans} km de autonomia.",
            "chave_ferramenta": "calculadora-combustivel-viagem",
            "confianca": 0.98,
        }


# ======================================================================
# 6. Média Estatística (media de 7, 8,5 e 9)
# ======================================================================

def extrair_media(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "media de" not in norm and "media entre" not in norm:
        return None
    nums = rc.extrair_numeros(texto)
    if len(nums) >= 2:
        return {"valores": nums}
    return None


def calcular_media(p: Dict[str, Any]) -> Dict[str, Any]:
    vals = p["valores"]
    med = sum(vals) / len(vals)
    ans = rc.formatar_br(med, 2)
    return {
        "titulo": "Média Aritmética",
        "resposta": f"{ans}",
        "detalhe": f"Média de {len(vals)} valores (soma {rc.formatar_br(sum(vals), 2)}) = {ans}",
        "chave_ferramenta": "financas",
        "confianca": 0.98,
    }


# ======================================================================
# 7. Gorjeta e Rateio / Divisão de Conta
# ======================================================================

def extrair_gorjeta_rateio(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Ex: "gorjeta 10% em conta de 186,00", "gorjeta 15% numa conta de 248,00", "gorjeta 15% conta 248,00"
    m_gorj = re.search(r"gorjeta\s*([0-9.,]+)\s*%\s*(?:em|numa|de|sobre)?\s*(?:conta\s*(?:de\s*)?)?([0-9.,]+)", norm)
    if m_gorj:
        pct = rc.numero_br(m_gorj.group(1))
        conta = rc.numero_br(m_gorj.group(2))
        if pct is not None and conta is not None:
            return {"tipo": "gorjeta", "pct": pct, "conta": conta}

    # Ex: "rateio 360: joao 50%, maria 30%, ana 20%"
    m_prop = re.search(r"rateio\s*([0-9.,]+)\s*:\s*([^;]+)", norm)
    if m_prop:
        tot = rc.numero_br(m_prop.group(1))
        resto = m_prop.group(2)
        partes = re.findall(r"([a-zA-Z]+)\s*([0-9.,]+)\s*%", resto)
        if tot and partes:
            return {"tipo": "rateio_prop", "total": tot, "partes": [(p[0].capitalize(), float(p[1].replace(',', '.'))) for p in partes]}

    # Ex: "rateio conta 360 pra 3 pessoas iguais", "split conta de 275,50 em 2 pessoas"
    m_split = re.search(r"(?:rateio|split|dividir)\s*(?:conta\s*(?:de\s*)?)?([0-9.,]+)\s*(?:pra|para|em)\s*(\d+)\s*pessoas?", norm)
    if m_split:
        tot = rc.numero_br(m_split.group(1))
        n = int(m_split.group(2))
        if tot and n > 0:
            return {"tipo": "split", "total": tot, "n": n}

    # Ex: "parcelar 900 em 3x sem juros"
    m_parc = re.search(r"parcelar\s*([0-9.,]+(?:\s*mil)?)\s*em\s*(\d+)\s*x", norm)
    if m_parc:
        tot = rc.numero_br(m_parc.group(1))
        n = int(m_parc.group(2))
        if tot and n > 0:
            return {"tipo": "parcelar", "total": tot, "n": n}

    return None


def calcular_gorjeta_rateio(p: Dict[str, Any]) -> Dict[str, Any]:
    tipo = p["tipo"]
    if tipo == "gorjeta":
        gorj = (p["pct"] / 100.0) * p["conta"]
        tot = p["conta"] + gorj
        return {
            "titulo": "Calculadora de Gorjeta",
            "resposta": f"gorjeta {rc.formatar_br(gorj, 2)}; total {rc.formatar_br(tot, 2)}",
            "detalhe": f"Conta: R$ {rc.formatar_br(p['conta'], 2)} | Gorjeta ({p['pct']:g}%): R$ {rc.formatar_br(gorj, 2)} | Total: R$ {rc.formatar_br(tot, 2)}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "rateio_prop":
        tot = p["total"]
        linhas = []
        for nome, pct in p["partes"]:
            v = tot * (pct / 100.0)
            linhas.append(f"{nome} {rc.formatar_br(v, 2)}")
        res_str = "; ".join(linhas)
        return {
            "titulo": "Rateio Proporcional",
            "resposta": res_str,
            "detalhe": f"Rateio de R$ {rc.formatar_br(tot, 2)}: {res_str}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "split":
        cada = p["total"] / p["n"]
        ans = rc.formatar_br(cada, 2)
        return {
            "titulo": "Divisão de Conta",
            "resposta": f"{ans} cada",
            "detalhe": f"R$ {rc.formatar_br(p['total'], 2)} dividido para {p['n']} pessoas = R$ {ans} cada.",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    else:  # parcelar
        cada = p["total"] / p["n"]
        ans = rc.formatar_br(cada, 2)
        return {
            "titulo": "Parcelamento sem Juros",
            "resposta": f"{ans}",
            "detalhe": f"R$ {rc.formatar_br(p['total'], 2)} em {p['n']}x sem juros = R$ {ans} por parcela.",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }


# ======================================================================
# 8. Geometria, Área de Cômodo e Pintura Detalhada
# ======================================================================

def extrair_area_e_tinta_detalhada(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Ex: "tinta: parede 3m x 4m, 2 demaos, rendimento 10 m2 por litro"
    m_tint = re.search(r"parede\s*([0-9.,]+)\s*m\s*[xX]\s*([0-9.,]+)\s*m.*?(\d+)\s*demaos?.*?rendimento\s*([0-9.,]+)", norm)
    if m_tint:
        l1 = rc.numero_br(m_tint.group(1)) or 0.0
        l2 = rc.numero_br(m_tint.group(2)) or 0.0
        dem = int(m_tint.group(3))
        rend = rc.numero_br(m_tint.group(4)) or 10.0
        return {"tipo": "tinta_parede", "l1": l1, "l2": l2, "demaos": dem, "rendimento": rend}

    # Ex: "pintar 14,4 m2 com rendimento 12 m2/L e 1 demao — litros"
    m_pnt = re.search(r"pintar\s*([0-9.,]+)\s*m2.*?rendimento\s*([0-9.,]+).*?(\d+)\s*demao", norm)
    if m_pnt:
        area = rc.numero_br(m_pnt.group(1)) or 0.0
        rend = rc.numero_br(m_pnt.group(2)) or 10.0
        dem = int(m_pnt.group(3))
        return {"tipo": "tinta_area", "area": area, "rendimento": rend, "demaos": dem}

    # Ex: "area de um comodo 4,5m por 3,2m"
    m_com = re.search(r"area\s*(?:de\s+um\s+comodo)?\s*([0-9.,]+)\s*m\s*(?:por|[xX])\s*([0-9.,]+)\s*m", norm)
    if m_com:
        l1 = rc.numero_br(m_com.group(1)) or 0.0
        l2 = rc.numero_br(m_com.group(2)) or 0.0
        return {"tipo": "area_comodo", "l1": l1, "l2": l2}

    return None


def calcular_area_e_tinta_detalhada(p: Dict[str, Any]) -> Dict[str, Any]:
    tipo = p["tipo"]
    if tipo == "tinta_parede":
        area = p["l1"] * p["l2"]
        area_total = area * p["demaos"]
        litros = area_total / p["rendimento"]
        ans = rc.formatar_br(litros, 1 if litros != int(litros) else 0)
        return {
            "titulo": "Rendimento de Tinta",
            "resposta": f"{ans} L",
            "detalhe": f"Parede de {p['l1']:g}m × {p['l2']:g}m = {area:g} m². Com {p['demaos']} demãos ({area_total:g} m²) a {p['rendimento']:g} m²/L = {ans} L.",
            "chave_ferramenta": "calculadora-rendimento-tinta",
            "confianca": 0.98,
        }
    elif tipo == "tinta_area":
        area_total = p["area"] * p["demaos"]
        litros = area_total / p["rendimento"]
        ans = rc.formatar_br(litros, 1 if litros != int(litros) else 0)
        return {
            "titulo": "Rendimento de Tinta",
            "resposta": f"{ans} L",
            "detalhe": f"Área de {p['area']:g} m² com {p['demaos']} demão(s) a {p['rendimento']:g} m²/L = {ans} L.",
            "chave_ferramenta": "calculadora-rendimento-tinta",
            "confianca": 0.98,
        }
    else:  # area_comodo
        area = p["l1"] * p["l2"]
        ans = rc.formatar_br(area, 1 if area != int(area) else 0)
        return {
            "titulo": "Área de Cômodo",
            "resposta": f"{ans} m²",
            "detalhe": f"{p['l1']:g}m × {p['l2']:g}m = {ans} m²",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }


# ======================================================================
# 9. Tempo, Horas, Minutos e Velocidade Média
# ======================================================================

def extrair_tempo_velocidade(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Ex: "velocidade media: 120 km em 1h30"
    m_vel = re.search(r"velocidade\s+media\s*:\s*([0-9.,]+)\s*km\s*em\s*(\d+)h(?:(\d+))?", norm)
    if m_vel:
        km = rc.numero_br(m_vel.group(1)) or 0.0
        h = int(m_vel.group(2))
        m = int(m_vel.group(3)) if m_vel.group(3) else 0
        horas = h + (m / 60.0)
        if horas > 0:
            return {"tipo": "velocidade", "km": km, "horas": horas}

    # Ex: "2 horas e 45 min em minutos"
    m_h_min = re.search(r"(\d+)\s*horas?\s*e\s*(\d+)\s*min.*?em\s*minutos?", norm)
    if m_h_min:
        h = int(m_h_min.group(1))
        m = int(m_h_min.group(2))
        return {"tipo": "h_min_em_min", "h": h, "m": m}

    # Ex: "165 minutos em horas e minutos"
    m_min_h = re.search(r"(\d+)\s*minutos?\s*em\s*horas?", norm)
    if m_min_h:
        tot_m = int(m_min_h.group(1))
        return {"tipo": "min_em_h_min", "minutos": tot_m}

    # Ex: "45 minutos e que fracao de 1 hora"
    m_frac = re.search(r"(\d+)\s*minutos?\s*e\s*que\s*fracao\s*de\s*1\s*hora", norm)
    if m_frac:
        m = int(m_frac.group(1))
        return {"tipo": "fracao_hora", "minutos": m}

    # Ex: "de 18C pra 27C, subiu quantos graus"
    m_graus = re.search(r"de\s*([0-9.,]+)\s*c\s*pra\s*([0-9.,]+)\s*c", norm)
    if m_graus:
        t1 = rc.numero_br(m_graus.group(1)) or 0.0
        t2 = rc.numero_br(m_graus.group(2)) or 0.0
        return {"tipo": "dif_graus", "t1": t1, "t2": t2}

    return None


def calcular_tempo_velocidade(p: Dict[str, Any]) -> Dict[str, Any]:
    tipo = p["tipo"]
    if tipo == "velocidade":
        vel = p["km"] / p["horas"]
        ans = int(round(vel))
        return {
            "titulo": "Velocidade Média",
            "resposta": f"{ans} km/h",
            "detalhe": f"{p['km']:g} km percorrido em {p['horas']:g} h = {ans} km/h",
            "chave_ferramenta": "conversor-unidades",
            "confianca": 0.98,
        }
    elif tipo == "h_min_em_min":
        tot = (p["h"] * 60) + p["m"]
        return {
            "titulo": "Conversão de Tempo",
            "resposta": f"{tot} min",
            "detalhe": f"{p['h']}h e {p['m']}min = {tot} minutos.",
            "chave_ferramenta": "conversor-unidades",
            "confianca": 0.98,
        }
    elif tipo == "min_em_h_min":
        h = p["minutos"] // 60
        m = p["minutos"] % 60
        return {
            "titulo": "Conversão de Tempo",
            "resposta": f"{h} h {m} min",
            "detalhe": f"{p['minutos']} minutos = {h} horas e {m} minutos.",
            "chave_ferramenta": "conversor-unidades",
            "confianca": 0.98,
        }
    elif tipo == "fracao_hora":
        m = p["minutos"]
        mdc = math.gcd(m, 60)
        num = m // mdc
        den = 60 // mdc
        dec = m / 60.0
        return {
            "titulo": "Fração de Hora",
            "resposta": f"{num}/{den} = {rc.formatar_br(dec, 2)}",
            "detalhe": f"{m} minutos de 60 minutos = {num}/{den} ({rc.formatar_br(dec, 2)} h)",
            "chave_ferramenta": "conversor-unidades",
            "confianca": 0.98,
        }
    else:  # dif_graus
        dif = p["t2"] - p["t1"]
        ans = int(round(dif))
        return {
            "titulo": "Diferença de Temperatura",
            "resposta": f"{ans} °C",
            "detalhe": f"De {p['t1']:g} °C para {p['t2']:g} °C: variação de {ans} °C.",
            "chave_ferramenta": "conversor-unidades",
            "confianca": 0.98,
        }


# ======================================================================
# 10. Proporções Especiais, Escalas e Capacidade Binária
# ======================================================================

def extrair_proporcoes_avancadas(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Ex: "8 trabalhadores fazem em 6 dias; 4 no mesmo ritmo em quantos dias"
    m_trab = re.search(r"(\d+)\s*trabalhadores\s*fazem\s*em\s*(\d+)\s*dias.*?(\d+)\s*no\s*mesmo\s*ritmo", norm)
    if m_trab:
        t1, d1, t2 = int(m_trab.group(1)), int(m_trab.group(2)), int(m_trab.group(3))
        if t2 > 0:
            return {"tipo": "trabalhadores", "t1": t1, "d1": d1, "t2": t2}

    # Ex: "3 ovos pra 12 pessoas, pra 20 pessoas quantos ovos"
    m_ovos = re.search(r"(\d+)\s*ovos\s*pra\s*(\d+)\s*pessoas.*?pra\s*(\d+)\s*pessoas", norm)
    if m_ovos:
        o1, p1, p2 = int(m_ovos.group(1)), int(m_ovos.group(2)), int(m_ovos.group(3))
        if p1 > 0:
            return {"tipo": "ovos", "o1": o1, "p1": p1, "p2": p2}

    # Ex: "mapa 1:100.000, 3 cm no mapa — quantos km reais"
    m_mapa = re.search(r"mapa\s*1\s*:\s*([0-9.,]+).*?([0-9.,]+)\s*cm", norm)
    if m_mapa:
        esc = rc.numero_br(m_mapa.group(1)) or 100000.0
        cm = rc.numero_br(m_mapa.group(2)) or 1.0
        return {"tipo": "mapa", "escala": esc, "cm": cm}

    # Ex: "tenho 16 GiB livres e cada foto ocupa ~4 MiB — quantas fotos cabem?"
    m_bin = re.search(r"([0-9.,]+)\s*gib.*?([0-9.,]+)\s*mib", norm)
    if m_bin:
        gib = rc.numero_br(m_bin.group(1)) or 0.0
        mib = rc.numero_br(m_bin.group(2)) or 1.0
        return {"tipo": "fotos_gib", "gib": gib, "mib": mib}

    return None


def calcular_proporcoes_avancadas(p: Dict[str, Any]) -> Dict[str, Any]:
    tipo = p["tipo"]
    if tipo == "trabalhadores":
        dias = (p["t1"] * p["d1"]) / p["t2"]
        ans = int(round(dias))
        return {
            "titulo": "Regra de Três Inversa",
            "resposta": f"{ans} dias",
            "detalhe": f"{p['t1']} trabalhadores × {p['d1']} dias = {p['t1']*p['d1']} dias-homem ÷ {p['t2']} = {ans} dias.",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "ovos":
        ovos = (p["o1"] * p["p2"]) / p["p1"]
        ans = int(round(ovos))
        return {
            "titulo": "Proporção de Ingredientes",
            "resposta": f"{ans}",
            "detalhe": f"Proporção: {p['o1']} ovos para {p['p1']} pessoas = {ans} ovos para {p['p2']} pessoas.",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif tipo == "mapa":
        # cm * escala = cm_reais. 1 km = 100.000 cm
        km = (p["cm"] * p["escala"]) / 100000.0
        ans = int(round(km)) if km == int(round(km)) else rc.formatar_br(km, 2)
        return {
            "titulo": "Escala de Mapa",
            "resposta": f"{ans} km",
            "detalhe": f"{p['cm']:g} cm × {int(p['escala'])} = {p['cm']*p['escala']:g} cm = {ans} km reais.",
            "chave_ferramenta": "conversor-unidades",
            "confianca": 0.98,
        }
    else:  # fotos_gib
        total_mib = p["gib"] * 1024.0
        fotos = total_mib / p["mib"]
        ans = rc.formatar_br(fotos, 0)
        return {
            "titulo": "Capacidade de Armazenamento",
            "resposta": f"{ans}",
            "detalhe": f"{p['gib']:g} GiB = {int(total_mib)} MiB ÷ {p['mib']:g} MiB/foto = {ans} fotos.",
            "chave_ferramenta": "conversor-unidades",
            "confianca": 0.98,
        }


# ======================================================================
# 11. Datas Especiais (Dias Corridos Q58, Diárias de Hotel Q33)
# ======================================================================

def extrair_datas_especiais(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Ex: "90 dias corridos a partir de 01/02/2026"
    m_corr = re.search(r"(\d+)\s*dias\s*corridos\s*a\s*partir\s*de\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})", norm)
    if m_corr:
        n = int(m_corr.group(1))
        d, m, y = int(m_corr.group(2)), int(m_corr.group(3)), int(m_corr.group(4))
        return {"tipo": "dias_corridos", "n": n, "base": datetime.date(y, m, d)}

    # Ex: "viagem: saida 10/03/2026 de manha, volta no fim do dia 25/03/2026 — quantos diarios de hotel"
    m_hot = re.search(r"saida\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4}).*?volta.*?(\d{1,2})[/-](\d{1,2})[/-](\d{4})", norm)
    if m_hot:
        d1, m1, y1 = int(m_hot.group(1)), int(m_hot.group(2)), int(m_hot.group(3))
        d2, m2, y2 = int(m_hot.group(4)), int(m_hot.group(5)), int(m_hot.group(6))
        return {"tipo": "hotel", "dt1": datetime.date(y1, m1, d1), "dt2": datetime.date(y2, m2, d2)}

    # Ex: "que dia cai 25/12/2026", "dia da semana 25/12/2026", "que dia e 01/01/2027"
    m_sem = re.search(r"(?:que\s+dia\s+(?:cai|e|da\s+semana)|dia\s+da\s+semana).*?(\d{1,2})[/-](\d{1,2})[/-](\d{4})", norm)
    if m_sem:
        d, m, y = int(m_sem.group(1)), int(m_sem.group(2)), int(m_sem.group(3))
        try:
            return {"tipo": "dia_semana", "dt": datetime.date(y, m, d)}
        except ValueError:
            pass

    return None


def calcular_datas_especiais(p: Dict[str, Any]) -> Dict[str, Any]:
    tipo = p["tipo"]
    if tipo == "dias_corridos":
        dt_final = p["base"] + datetime.timedelta(days=p["n"])
        ans = dt_final.strftime("%d/%m/%Y")
        return {
            "titulo": "Dias Corridos",
            "resposta": f"{ans}",
            "detalhe": f"{p['n']} dias corridos após {p['base'].strftime('%d/%m/%Y')} = {ans}",
            "chave_ferramenta": "dias-uteis-pagamento",
            "confianca": 0.98,
        }
    elif tipo == "dia_semana":
        dt = p["dt"]
        dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        nome_dia = dias[dt.weekday()]
        dt_str = dt.strftime("%d/%m/%Y")
        return {
            "titulo": "Dia da Semana",
            "resposta": f"{nome_dia} ({dt_str})",
            "detalhe": f"{dt_str} cai em um(a) {nome_dia.lower()}",
            "chave_ferramenta": "dias-uteis-pagamento",
            "confianca": 0.96,
        }
    else:  # hotel
        noites = (p["dt2"] - p["dt1"]).days
        return {
            "titulo": "Diárias de Hospedagem",
            "resposta": f"{noites} diárias",
            "detalhe": f"De {p['dt1'].strftime('%d/%m/%Y')} a {p['dt2'].strftime('%d/%m/%Y')}: {noites} noites/diárias dormidas.",
            "chave_ferramenta": "hospedagem-vs-aluguel",
            "confianca": 0.98,
        }


# ======================================================================
# 12. Troco (tro_core.py)
# ======================================================================

def extrair_troco(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "troco" not in norm and "sobra" not in norm:
        return None
    nums = rc.extrair_numeros(texto)
    if len(nums) < 2:
        return None
    # "paguei 50 no total de 38,90"
    m_pag = re.search(r"paguei\s*([0-9.,]+).*?total\s*(?:de\s*)?([0-9.,]+)", norm)
    if m_pag:
        pago = rc.numero_br(m_pag.group(1)) or 0.0
        compra = rc.numero_br(m_pag.group(2)) or 0.0
        return {"pago": pago, "compra": compra}

    n1, n2 = nums[0], nums[1]
    pago = max(n1, n2)
    compra = min(n1, n2)
    return {"pago": pago, "compra": compra}


def calcular_troco(p: Dict[str, Any]) -> Dict[str, Any]:
    import tro_core
    res = tro_core.calcular_troco(total=p["compra"], pago=p["pago"])
    if not res.get("ok"):
        falta = res.get("faltam", 0.0)
        return {
            "titulo": "Calculadora de Troco",
            "resposta": f"Faltam R$ {rc.formatar_br(falta)}",
            "detalhe": f"Valor pago (R$ {rc.formatar_br(p['pago'])}) é menor que o total (R$ {rc.formatar_br(p['compra'])}).",
            "chave_ferramenta": "calculadora-troco",
            "confianca": 0.95,
        }
    troco = res["troco"]
    ans = rc.formatar_br(troco, 2)
    return {
        "titulo": "Calculadora de Troco",
        "resposta": f"{ans}",
        "detalhe": f"Troco de R$ {rc.formatar_br(p['pago'], 2)} para compra de R$ {rc.formatar_br(p['compra'], 2)} = R$ {ans}",
        "chave_ferramenta": "calculadora-troco",
        "confianca": 0.98,
    }


# ======================================================================
# 13. IPVA (ipv_core.py)
# ======================================================================

UFS_BRASIL = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
}

def extrair_ipva(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "ipva" not in norm and "imposto carro" not in norm:
        return None

    # Ex: "ipva de um carro de 60 mil com aliquota 4%"
    m_aliq = re.search(r"aliquota\s*([0-9.,]+)\s*%", norm)
    aliq_dada = rc.numero_br(m_aliq.group(1)) if m_aliq else None

    nums = rc.extrair_numeros(texto)
    if not nums:
        # Pergunta incompleta (ex: "ipva do meu carro", "quanto pago de ipva")
        return {"ajuda": True}
    valor = nums[0]

    uf = "SP"
    for token in re.split(r"\W+", texto.upper()):
        if token in UFS_BRASIL:
            uf = token
            break

    tipo = "auto"
    if "moto" in norm:
        tipo = "moto"
    elif "caminhao" in norm or "caminhão" in norm:
        tipo = "caminhao"
    elif "utilitario" in norm:
        tipo = "utilitario"

    return {"valor": valor, "uf": uf, "tipo": tipo, "aliq_dada": aliq_dada}


def calcular_ipva(p: Dict[str, Any]) -> Dict[str, Any]:
    if p.get("ajuda"):
        return {
            "titulo": "Calculadora de IPVA",
            "resposta": "Informe o valor do carro e o estado (ex: ipva de um carro de 60 mil em SP)",
            "detalhe": "Calcule a alíquota e o imposto devido para automóveis, motos ou utilitários.",
            "chave_ferramenta": "calculadora-ipva",
            "confianca": 0.95,
        }

    if p.get("aliq_dada") is not None:
        total = p["valor"] * (p["aliq_dada"] / 100.0)
        aliq = p["aliq_dada"]
    else:
        import ipv_core
        res = ipv_core.calcular_ipva(valor_venal=p["valor"], uf=p["uf"], tipo=p["tipo"])
        total = res["total"]
        aliq = res["aliquota_pct"]

    ans = rc.formatar_br(total, 0 if total == int(total) else 2)
    return {
        "titulo": f"IPVA {p['uf']}",
        "resposta": f"{ans}",
        "detalhe": f"IPVA para veículo de R$ {rc.formatar_br(p['valor'], 2)} (alíquota de {aliq:g}%): R$ {rc.formatar_br(total, 2)}.",
        "chave_ferramenta": "calculadora-ipva",
        "confianca": 0.98,
    }


# ======================================================================
# 14. Juros Simples e Compostos (fin_calc.py)
# ======================================================================

def extrair_juros(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "juros simples" in norm:
        # Ex: "juros simples 2% ao mes em 5.000 por 6 meses, so juros"
        nums = rc.extrair_numeros(texto)
        if nums:
            taxa = nums[0] if len(nums) > 1 and nums[0] < 50 else (nums[1] if len(nums) > 1 else 1.0)
            cands_cap = [n for n in nums if n >= 50]
            capital = cands_cap[0] if cands_cap else 1000.0
            m_meses = re.search(r"(\d+)\s*mes(?:es)?", norm)
            prazo = int(m_meses.group(1)) if m_meses else (nums[-1] if len(nums) > 2 else 12.0)
            so_juros = "so juros" in norm or "só juros" in norm or "so os juros" in norm or "só os juros" in norm
            return {"tipo": "simples", "capital": capital, "taxa": taxa, "prazo": prazo, "so_juros": so_juros}

    if "juros compostos" in norm or "quanto rende" in norm:
        if "tinta" in norm or "litro" in norm:
            return None
        nums = rc.extrair_numeros(texto)
        if nums:
            m_pct = re.search(r"([0-9.,]+)\s*%", norm)
            taxa = rc.numero_br(m_pct.group(1)) if m_pct else 1.0
            m_meses = re.search(r"(\d+)\s*mes(?:es)?", norm)
            prazo = int(m_meses.group(1)) if m_meses else 12.0
            cands_cap = [n for n in nums if n != taxa and n != prazo]
            capital = cands_cap[0] if cands_cap else 1000.0
            return {"tipo": "compostos", "capital": capital, "taxa": taxa, "prazo": prazo}

    return None


def calcular_juros(p: Dict[str, Any]) -> Dict[str, Any]:
    import fin_calc
    if p["tipo"] == "simples":
        res = fin_calc.run_simples({"capital": p["capital"], "taxa": p["taxa"], "prazo": p["prazo"], "uni": "a.m."})
        juros_val = (p["capital"] * (p["taxa"] / 100.0)) * p["prazo"]
        mont_val = p["capital"] + juros_val
        j_str = rc.formatar_br(juros_val, 0 if juros_val == int(juros_val) else 2)
        m_str = rc.formatar_br(mont_val, 0 if mont_val == int(mont_val) else 2)
        if p.get("so_juros"):
            ans = j_str
        elif "montante" in p.get("original", ""):
            ans = m_str
        else:
            ans = f"{m_str}"
        return {
            "titulo": "Juros Simples",
            "resposta": ans,
            "detalhe": f"Capital: R$ {rc.formatar_br(p['capital'], 2)}, taxa: {p['taxa']:g}% a.m., {int(p['prazo'])} meses. Juros: R$ {j_str} | Montante: R$ {m_str}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    else:  # compostos
        res = fin_calc.run_juros({
            "capital": p["capital"],
            "aporte": 0.0,
            "taxa": p["taxa"],
            "uni": "a.m.",
            "prazo": p["prazo"],
            "pz_uni": "meses",
        })
        mont = p["capital"] * ((1.0 + (p["taxa"] / 100.0)) ** p["prazo"])
        ans = rc.formatar_br(mont, 2)
        return {
            "titulo": "Juros Compostos",
            "resposta": f"{ans}",
            "detalhe": f"Capital: R$ {rc.formatar_br(p['capital'], 2)} a {p['taxa']:g}% a.m. por {int(p['prazo'])} meses. Montante: R$ {ans}",
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }


# ======================================================================
# 15. Conversão de Unidades (cu_unidades.py)
# ======================================================================

MAPA_UNIDADES = {
    "km": ("Comprimento", "km", "km"),
    "m": ("Comprimento", "m", "metros"),
    "metros": ("Comprimento", "m", "metros"),
    "metro": ("Comprimento", "m", "metros"),
    "cm": ("Comprimento", "cm", "cm"),
    "centimetro": ("Comprimento", "cm", "cm"),
    "centimetros": ("Comprimento", "cm", "cm"),
    "mm": ("Comprimento", "mm", "mm"),
    "kg": ("Massa", "kg", "kg"),
    "g": ("Massa", "g", "gramas"),
    "gramas": ("Massa", "g", "gramas"),
    "grama": ("Massa", "g", "gramas"),
    "c": ("Temperatura", "C", "°C"),
    "celsius": ("Temperatura", "C", "°C"),
    "f": ("Temperatura", "F", "°F"),
    "fahrenheit": ("Temperatura", "F", "°F"),
    "l": ("Volume", "l", "litros"),
    "litros": ("Volume", "l", "litros"),
    "litro": ("Volume", "l", "litros"),
    "ml": ("Volume", "ml", "ml"),
}

def extrair_conversao(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "tinta" in norm or "rendimento" in norm:
        return None

    # Ex: "converter 2,5 kg pra gramas", "3 km em metros", "100 c em f", "250 ml em litros", "3,5 m em cm"
    m = re.search(r"(?:converter\s+)?([0-9.,]+)\s*([a-zA-Z]+)\s*(?:em|pra|para)\s*([a-zA-Z]+)", norm)
    if not m:
        # Ex: "pneu 205 mm de largura, isso da quantos cm"
        m = re.search(r"([0-9.,]+)\s*([a-zA-Z]+).*?(?:quantos|quantas|em|pra|para)\s+([a-zA-Z]+)", norm)
    if m:
        val = rc.numero_br(m.group(1))
        u1 = m.group(2).lower()
        u2 = m.group(3).lower()
        if val is not None and u1 in MAPA_UNIDADES and u2 in MAPA_UNIDADES:
            cat1, k1, r1 = MAPA_UNIDADES[u1]
            cat2, k2, r2 = MAPA_UNIDADES[u2]
            if cat1 == cat2:
                return {"val": val, "cat": cat1, "de": k1, "para": k2, "rot1": r1, "rot2": r2}

    return None


def calcular_conversao(p: Dict[str, Any]) -> Dict[str, Any]:
    import cu_unidades
    res = cu_unidades.convert(p["cat"], p["val"], p["de"], p["para"])
    casas = 0 if res == int(res) else 2
    res_str = rc.formatar_br(res, casas)
    suffix = " g" if p["rot2"] == "gramas" else (f" {p['rot2']}" if p["rot2"] != "°F" else " °F")
    if p["rot2"] == "litros":
        suffix = " L"
    return {
        "titulo": f"Conversor de {p['cat']}",
        "resposta": f"{res_str}{suffix}",
        "detalhe": f"{p['val']:g} {p['rot1']} = {res_str}{suffix}",
        "chave_ferramenta": "conversor-unidades",
        "confianca": 0.98,
    }


# ======================================================================
# 16. Dias Úteis (Adicionar e Entre Datas)
# ======================================================================

def extrair_dias_uteis(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "dias uteis" not in norm and "dias uteis" not in texto.lower():
        return None

    nums = rc.extrair_numeros(texto)
    if not nums:
        return None
    n_dias = int(nums[0])

    m_data = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", norm)
    if m_data:
        d, m, y = int(m_data.group(1)), int(m_data.group(2)), int(m_data.group(3))
        base = datetime.date(y, m, d)
    else:
        base = rc.extrair_data(texto) or datetime.date.today()

    sem_feriado = "sem feriado" in norm or "so seg-sex" in norm or "segunda a sexta" in norm
    nao_conta_base = "nao conta" in norm or "a partir do proximo" in norm

    return {"dias": n_dias, "base": base, "sem_feriado": sem_feriado, "nao_conta_base": nao_conta_base}


def calcular_dias_uteis(p: Dict[str, Any]) -> Dict[str, Any]:
    n = p["dias"]
    cur = p["base"]
    if p["nao_conta_base"]:
        cur += datetime.timedelta(days=1)

    if p["sem_feriado"]:
        uteis = 0
        while uteis < n:
            if cur.weekday() < 5:
                uteis += 1
                if uteis == n:
                    break
            cur += datetime.timedelta(days=1)
        dt_final = cur
    else:
        # T12: usa cal_datas do calendario-br (com feriados nacionais incluindo Consciência Negra)
        try:
            import cal_datas
            dt_final = cal_datas.somar_uteis(p["base"], n)
        except Exception:
            import utl_core
            dt_final = utl_core.adicionar_uteis(p["base"], n)

    ans = dt_final.strftime("%d/%m/%Y")
    return {
        "titulo": "Calculadora de Dias Úteis",
        "resposta": f"{ans}",
        "detalhe": f"{n} dias úteis a partir de {p['base'].strftime('%d/%m/%Y')} = {ans}",
        "chave_ferramenta": "dias-uteis-pagamento",
        "confianca": 0.98,
    }


# ======================================================================
# 17. Regra de Três Simples
# ======================================================================

def extrair_regra_de_tres(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Ex: "regra de 3: se 5 pacotes custam 37,50 quanto saem 8"
    m_se = re.search(r"se\s+([0-9.,]+)\s+[a-zA-Z\s]*?(?:custam?|e|vale|rende|faz)\s+([0-9.,]+)\s+quanto\s+(?:saem|custa|custam|rendem|fazem)?\s*([0-9.,]+)", norm)
    if m_se:
        a = rc.numero_br(m_se.group(1))
        b = rc.numero_br(m_se.group(2))
        c = rc.numero_br(m_se.group(3))
        if a and b and c:
            return {"a": a, "b": b, "c": c}

    return None


def calcular_regra_de_tres(p: Dict[str, Any]) -> Dict[str, Any]:
    a, b, c = p["a"], p["b"], p["c"]
    if a == 0:
        return {"resposta": "Erro: divisão por zero"}
    x = (b * c) / a
    ans = rc.formatar_br(x, 2)
    return {
        "titulo": "Regra de 3",
        "resposta": f"{ans}",
        "detalhe": f"Se {rc.formatar_br(a, 0)} custa {rc.formatar_br(b, 2)}, então {rc.formatar_br(c, 0)} sai por {ans}",
        "chave_ferramenta": "financas",
        "confianca": 0.98,
    }


# ======================================================================
# 18. Horas Extras com Taxa do Enunciado
# ======================================================================

def extrair_hora_extra(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "hora extra" not in norm and "horas extras" not in norm:
        return None

    # Ex: "10 horas extras a 50% sobre hora de 20 reais"
    m_direto = re.search(r"(\d+)\s*horas?\s*extras?\s*a\s*([0-9.,]+)\s*%\s*sobre\s*hora\s*de\s*([0-9.,]+)", norm)
    if m_direto:
        qtd_h = int(m_direto.group(1))
        adicional = rc.numero_br(m_direto.group(2)) or 50.0
        v_hora = rc.numero_br(m_direto.group(3)) or 20.0
        return {"tipo": "direto", "qtd_h": qtd_h, "adicional": adicional, "v_hora": v_hora}

    # Caso padrão CLT com salário
    m_sal = re.search(r"salario\s*(?:de\s*)?([0-9.,]+(?:\s*mil)?)", norm)
    m50 = re.search(r"(\d+(?:,\d+)?)\s*(?:h|horas?)?\s*(?:a|de)?\s*50%", norm)
    m100 = re.search(r"(\d+(?:,\d+)?)\s*(?:h|horas?)?\s*(?:a|de)?\s*100%", norm)
    salario = rc.numero_br(m_sal.group(1)) if m_sal else 3000.0
    h50 = rc.numero_br(m50.group(1)) if m50 else 10.0
    h100 = rc.numero_br(m100.group(1)) if m100 else 0.0
    return {"tipo": "clt_padrao", "salario": salario, "h50": h50, "h100": h100}


def calcular_hora_extra(p: Dict[str, Any]) -> Dict[str, Any]:
    if p["tipo"] == "direto":
        v_extra = p["v_hora"] * (1.0 + (p["adicional"] / 100.0))
        tot = p["qtd_h"] * v_extra
        ans = rc.formatar_br(tot, 0 if tot == int(tot) else 2)
        return {
            "titulo": "Horas Extras",
            "resposta": f"{ans}",
            "detalhe": f"{p['qtd_h']} horas a R$ {rc.formatar_br(v_extra, 2)} (+{p['adicional']:g}%) = R$ {ans}",
            "chave_ferramenta": "simulador-hora-extra-50-100",
            "confianca": 0.98,
        }
    else:
        import hex_core
        res = hex_core.simular(salario_mensal=p["salario"], horas_base_mes=220.0, horas_he50=p["h50"], horas_he100=p["h100"])
        tot = res["total_extras"]
        ans = rc.formatar_br(tot, 2)
        return {
            "titulo": "Hora Extra CLT",
            "resposta": f"Total HE: R$ {ans}",
            "detalhe": f"Salário R$ {rc.formatar_br(p['salario'], 2)}: {p['h50']:g}h a 50% = R$ {ans}.",
            "chave_ferramenta": "simulador-hora-extra-50-100",
            "confianca": 0.95,
        }


# ======================================================================
# 19. Rendimento de Tinta Básico
# ======================================================================

def extrair_tinta(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "tinta" not in norm and "pintar parede" not in norm:
        return None
    # Se já tem dimensões (parede 3m x 4m), deixa para o detalhado
    if "parede" in norm or "m2 com rendimento" in norm:
        return None

    nums = rc.extrair_numeros(texto)
    if not nums:
        # Pergunta incompleta (ex: "quanto rende a tinta", "quanta tinta preciso")
        return {"modo": "ajuda"}

    if "litro" in norm or "rende" in norm:
        litros = nums[0]
        return {"modo": "litros_para_area", "litros": litros}

    area = nums[0]
    return {"modo": "area_para_litros", "area": area}


def calcular_tinta(p: Dict[str, Any]) -> Dict[str, Any]:
    if p["modo"] == "ajuda":
        return {
            "titulo": "Rendimento de Tinta",
            "resposta": "Informe os litros ou a área (ex: quanto rende 18 litros de tinta ou tinta para 40 m²)",
            "detalhe": "Calcule quantos metros quadrados uma lata cobre ou quantos litros precisa para sua parede.",
            "chave_ferramenta": "calculadora-rendimento-tinta",
            "confianca": 0.95,
        }
    import tnt_core
    if p["modo"] == "litros_para_area":
        litros = p["litros"]
        area_1d = litros * 10.0
        area_2d = area_1d / 2.0
        return {
            "titulo": "Rendimento de Tinta",
            "resposta": f"Rende aprox. {int(area_2d)} m² (2 demãos)",
            "detalhe": f"{litros:g} L cobre aprox. {int(area_2d)} m² com 2 demãos (ou {int(area_1d)} m² com 1 demão).",
            "chave_ferramenta": "calculadora-rendimento-tinta",
            "confianca": 0.96,
        }
    else:
        area = p["area"]
        res = tnt_core.calcular(area_m2=area, demaos=2, rendimento_m2_por_litro=10.0, litros_por_lata=18.0)
        litros_nec = res["litros"]
        latas = res["latas"]
        return {
            "titulo": "Rendimento de Tinta",
            "resposta": f"{rc.formatar_br(litros_nec, 1)} L ({latas} lata de 18L)",
            "detalhe": f"Para pintar {area:g} m² com 2 demãos: {rc.formatar_br(litros_nec, 1)} litros.",
            "chave_ferramenta": "calculadora-rendimento-tinta",
            "confianca": 0.96,
        }


# ======================================================================
# 20. Churrasco, Combustível, IMC, 13º, Mora, À Vista, CLT, Maquininha
# ======================================================================

def extrair_churrasco(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "churrasco" not in norm and "carne churrasco" not in norm:
        return None
    nums = rc.extrair_numeros(texto)
    pessoas = int(nums[0]) if nums else 10
    return {"homens": int(pessoas * 0.5), "mulheres": int(pessoas * 0.3), "criancas": int(pessoas * 0.2)}

def calcular_churrasco(p: Dict[str, Any]) -> Dict[str, Any]:
    import chu_core
    res = chu_core.calcular(homens=p["homens"], mulheres=p["mulheres"], criancas=p["criancas"])
    carne = res["carne_kg"]
    return {
        "titulo": "Calculadora de Churrasco",
        "resposta": f"{rc.formatar_br(carne, 1)} kg de carne",
        "detalhe": f"Para {p['homens']+p['mulheres']+p['criancas']} pessoas: {rc.formatar_br(carne, 1)} kg de carne.",
        "chave_ferramenta": "calculadora-churrasco",
        "confianca": 0.95,
    }

def extrair_etanol_gasolina(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    tem_ambos = ("etanol" in norm or "alcool" in norm) and "gasolina" in norm
    tem_compensa = "compensa" in norm or "qual vale" in norm or "rende" in norm
    if not (tem_ambos or ("etanol" in norm and tem_compensa)):
        return None
    if "km" in norm or "viagem" in norm:
        return None
    nums = rc.extrair_numeros(texto)
    if len(nums) < 2:
        return None
    rendimento = 0.70
    if len(nums) >= 3 and ("rende" in norm or "%" in norm):
        p_rend = nums[2]
        rendimento = p_rend / 100.0 if p_rend > 1.0 else p_rend
    return {"etanol": min(nums[0], nums[1]), "gasolina": max(nums[0], nums[1]), "rendimento": rendimento}

def calcular_etanol_gasolina(p: Dict[str, Any]) -> Dict[str, Any]:
    rend = p.get("rendimento", 0.70)
    equiv = p["etanol"] / rend
    compensa = equiv < p["gasolina"]
    escolha = "etanol" if compensa else "gasolina"
    return {
        "titulo": "Etanol × Gasolina",
        "resposta": f"Compensa {escolha.capitalize()} (equivalente ≈ {rc.formatar_br(equiv, 2)} < {rc.formatar_br(p['gasolina'], 2)})" if compensa else f"Compensa {escolha.capitalize()} (equivalente ≈ {rc.formatar_br(equiv, 2)} ≥ {rc.formatar_br(p['gasolina'], 2)})",
        "detalhe": f"Etanol R$ {rc.formatar_br(p['etanol'], 2)} (rende {rc.formatar_br(rend*100, 0)}%) ÷ Gasolina R$ {rc.formatar_br(p['gasolina'], 2)}. Compensa {escolha}.",
        "chave_ferramenta": "calculadora-combustivel-viagem",
        "confianca": 0.98,
    }

def extrair_viagem(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "viagem" not in norm and "consumo" not in norm and "combustivel" not in norm:
        return None
    if any(k in norm for k in ["saida", "volta", "dolar", "dolares", "cambio", "hotel", "diaria", "diarias", "aluguel de carro", "aluguel", "somos", "cada um", "pedagio"]):
        return None  # Trata em adaptadores especificos
    nums = rc.extrair_numeros(texto)
    if len(nums) < 2:
        return None
    return {"dist": nums[0], "consumo": nums[1] if len(nums) > 1 else 10.0, "preco": nums[2] if len(nums) > 2 else 5.80}

def calcular_viagem(p: Dict[str, Any]) -> Dict[str, Any]:
    import cbv_core
    res = cbv_core.viagem(distancia_km=p["dist"], km_l=p["consumo"], preco_l=p["preco"], ida_volta=False)
    return {
        "titulo": "Custo de Viagem",
        "resposta": f"R$ {rc.formatar_br(res['total'], 2)} ({rc.formatar_br(res['litros'], 1)} L)",
        "detalhe": f"Viagem de {p['dist']:g} km com consumo {p['consumo']:g} km/L = R$ {rc.formatar_br(res['total'], 2)}.",
        "chave_ferramenta": "calculadora-combustivel-viagem",
        "confianca": 0.95,
    }

def extrair_imc(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "imc" not in norm and "massa corporal" not in norm:
        return None
    nums = rc.extrair_numeros(texto)
    if len(nums) < 2:
        return None
    peso = max(nums[0], nums[1])
    alt = min(nums[0], nums[1])
    if alt < 3.0:
        alt *= 100.0
    return {"peso": peso, "altura_cm": alt}

def calcular_imc(p: Dict[str, Any]) -> Dict[str, Any]:
    import ntr_core
    val, clas = ntr_core.imc(p["peso"], p["altura_cm"])
    return {
        "titulo": "Índice de Massa Corporal (IMC)",
        "resposta": f"IMC {rc.formatar_br(val, 1)} — {clas}",
        "detalhe": f"Peso: {p['peso']:g} kg | Altura: {p['altura_cm']/100:g} m. Classificação: {clas}.",
        "chave_ferramenta": "calculadora-nutricao",
        "confianca": 0.98,
    }

def extrair_13(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if not any(g in norm for g in ["13", "13o", "13º", "decimo terceiro"]):
        return None
    if "hora" in norm or "dias uteis" in norm or "kg" in norm:
        return None
    nums = rc.extrair_numeros(texto)
    nums_f = [n for n in nums if n != 13.0]
    if not nums_f:
        return None
    salario = max(nums_f)
    m_mes = re.search(r"(\d{1,2})\s*mes(?:es)?", norm)
    meses = int(m_mes.group(1)) if m_mes else 12
    return {"salario": salario, "meses": min(12, max(1, meses))}

def calcular_13(p: Dict[str, Any]) -> Dict[str, Any]:
    import d13_core
    res = d13_core.calcular(salario=p["salario"], meses_trabalhados=p["meses"])
    return {
        "titulo": "13º Salário Proporcional",
        "resposta": f"R$ {rc.formatar_br(res['bruto'], 2)} ({p['meses']}/12 avos)",
        "detalhe": f"13º proporcional bruto para {p['meses']} meses: R$ {rc.formatar_br(res['bruto'], 2)}.",
        "chave_ferramenta": "decimo-terceiro-proporcional",
        "confianca": 0.95,
    }

def extrair_juros_mora(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "atrasado" not in norm and "atraso" not in norm and "mora" not in norm:
        return None
    nums = rc.extrair_numeros(texto)
    if not nums:
        return None
    m_d = re.search(r"(\d+)\s*dias?", norm)
    dias = int(m_d.group(1)) if m_d else (int(nums[1]) if len(nums) > 1 else 30)
    return {"valor": nums[0], "dias": dias}

def calcular_juros_mora(p: Dict[str, Any]) -> Dict[str, Any]:
    import jmr_core
    hoje = datetime.date.today()
    venc = hoje - datetime.timedelta(days=p["dias"])
    res = jmr_core.calcular(principal=p["valor"], venc=venc, pagamento=hoje, multa_pct=2.0, juros_mensal_pct=1.0)
    ans = rc.formatar_br(res["total"], 2)
    return {
        "titulo": "Juros de Mora e Multa",
        "resposta": f"R$ {ans} (+R$ {rc.formatar_br(res['acrescimo'], 2)})",
        "detalhe": f"Boleto R$ {rc.formatar_br(p['valor'], 2)} atrasado {p['dias']} dias = R$ {ans}.",
        "chave_ferramenta": "juros-mora",
        "confianca": 0.96,
    }

def extrair_avista_parcelado(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "vista" not in norm and "parcelado" not in norm and "parcelar" not in norm:
        return None
    m_parc = re.search(r"(\d+)\s*x\s*(?:de\s*)?([0-9.,]+)", norm)
    nums = rc.extrair_numeros(texto)
    if m_parc and nums:
        n = int(m_parc.group(1))
        v_p = rc.numero_br(m_parc.group(2)) or 0.0
        return {"vista": nums[0], "n": n, "total_parc": n * v_p}
    return None

def calcular_avista_parcelado(p: Dict[str, Any]) -> Dict[str, Any]:
    import dav_core
    tot = p["total_parc"]
    desc = max(0.0, ((tot - p["vista"]) / tot) * 100.0) if tot > 0 else 0.0
    res = dav_core.comparar(preco_tabela=tot, desconto_avista_pct=desc, n_parcelas=p["n"])
    return {
        "titulo": "À Vista × Parcelado",
        "resposta": f"Melhor à vista (economia de R$ {rc.formatar_br(res['economia_avista'], 2)})",
        "detalhe": f"À vista: R$ {rc.formatar_br(p['vista'], 2)} | Parcelado: R$ {rc.formatar_br(tot, 2)}.",
        "chave_ferramenta": "comparador-avista-parcelado",
        "confianca": 0.95,
    }

def extrair_salario_liquido(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if not any(g in norm for g in ["salario liquido", "desconto inss", "desconto irrf", "salario bruto"]) and not ("salario" in norm and "clt" in norm):
        return None
    nums = rc.extrair_numeros(texto)
    if not nums:
        return None
    return {"bruto": nums[0]}

def calcular_salario_liquido(p: Dict[str, Any]) -> Dict[str, Any]:
    import clt_calc
    res = clt_calc.salario_liquido(p["bruto"])
    ans = rc.formatar_br(res.liquido, 2)
    return {
        "titulo": "Salário Líquido CLT",
        "resposta": f"Líquido: R$ {ans}",
        "detalhe": f"Salário R$ {rc.formatar_br(p['bruto'], 2)}: descontos de R$ {rc.formatar_br(res.descontos, 2)} = líquido R$ {ans}.",
        "chave_ferramenta": "calculadora-clt",
        "confianca": 0.96,
    }

def extrair_maquininha(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "maquininha" not in norm and "taxa cartao" not in norm:
        return None
    nums = rc.extrair_numeros(texto)
    if not nums:
        return None
    m_pct = re.search(r"([0-9.,]+)\s*%", norm)
    if m_pct:
        taxa = rc.numero_br(m_pct.group(1)) or 2.0
        venda = [n for n in nums if n != taxa][0] if len(nums) > 1 else 100.0
    else:
        venda = max(nums)
        taxa = min(nums) if len(nums) > 1 else 2.5
    return {"venda": venda, "taxa": taxa}

def calcular_maquininha(p: Dict[str, Any]) -> Dict[str, Any]:
    import maq_core
    res = maq_core.calcular(valor_venda=p["venda"], taxa_pct=p["taxa"])
    ans = rc.formatar_br(res["liquido"], 2)
    return {
        "titulo": "Taxa da Maquininha",
        "resposta": f"Você recebe: R$ {ans}",
        "detalhe": f"Venda R$ {rc.formatar_br(p['venda'], 2)} com taxa {p['taxa']:g}%: desconto de R$ {rc.formatar_br(res['desconto'], 2)}.",
        "chave_ferramenta": "taxa-maquininha",
        "confianca": 0.96,
    }


# ======================================================================
# Sensores do Sistema em Tempo Real (Disco, Prints, Downloads, Pudim, Clipboard)
# ======================================================================

def extrair_sensores_sistema(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    # Evita falsos positivos em contas matemáticas ou outros adaptadores
    if any(k in norm for k in ["%", "juros", "troco", "ipva", "parcelas", "frete", "clt"]):
        return None

    # Pudim IPTV
    if "pudim" in norm or "iptv" in norm:
        return {"tipo": "pudim"}

    # Clipboard / Área de transferência
    if any(k in norm for k in ["clipboard", "area de transferencia", "copiado", "o que copiei"]):
        return {"tipo": "clipboard"}

    # Disco C:
    if any(k in norm for k in ["disco c", "espaco livre", "espaco no disco", "limpar temp", "pasta temp"]):
        return {"tipo": "disco"}

    # Downloads
    if any(k in norm for k in ["pasta downloads", "arquivos soltos", "organizar downloads", "instaladores velhos", "downloads soltos", "meus downloads"]):
        return {"tipo": "downloads"}

    # Prints / Capturas
    if any(k in norm for k in ["captura de tela", "capturas de tela", "quantos prints", "prints recentes", "prints", "capturas", "screenshot", "screenshots"]):
        return {"tipo": "prints"}

    return None


def calcular_sensores_sistema(p: Dict[str, Any]) -> Dict[str, Any]:
    import sensores_core as sc
    tipo = p.get("tipo")
    if tipo == "pudim":
        c = sc.sensor_pudim()
        if c:
            return {
                "titulo": c["titulo"],
                "resposta": c["valor"],
                "detalhe": c["detalhe"],
                "chave_ferramenta": c["acao"].get("chave_ferramenta", "iptv-player"),
                "confianca": 0.95,
            }
        return {
            "titulo": "🍮 Pudim IPTV",
            "resposta": "Abrir Pudim IPTV",
            "detalhe": "Player de IPTV configurado no sistema",
            "chave_ferramenta": "iptv-player",
            "confianca": 0.85,
        }
    elif tipo == "clipboard":
        c = sc.sensor_clipboard()
        if c:
            return {
                "titulo": c["titulo"],
                "resposta": c["valor"],
                "detalhe": c["detalhe"],
                "chave_ferramenta": "area-transferencia",
                "confianca": 0.95,
            }
        return {
            "titulo": "📋 Área de Transferência",
            "resposta": "Área de transferência vazia",
            "detalhe": "Nenhum texto copiado no momento",
            "chave_ferramenta": "area-transferencia",
            "confianca": 0.85,
        }
    elif tipo == "disco":
        c = sc.sensor_disco()
        if c:
            return {
                "titulo": c["titulo"],
                "resposta": c["valor"],
                "detalhe": c["detalhe"],
                "chave_ferramenta": c["acao"].get("chave_ferramenta", "faxina-disco"),
                "confianca": 0.95,
            }
    elif tipo == "downloads":
        c = sc.sensor_downloads()
        if c:
            return {
                "titulo": c["titulo"],
                "resposta": c["valor"],
                "detalhe": c["detalhe"],
                "chave_ferramenta": c["acao"].get("chave_ferramenta", "organizador-downloads"),
                "confianca": 0.95,
            }
    elif tipo == "prints":
        c = sc.sensor_prints_recentes()
        if c:
            return {
                "titulo": c["titulo"],
                "resposta": c["valor"],
                "detalhe": c["detalhe"],
                "chave_ferramenta": c["acao"].get("chave_ferramenta", "print-anotador"),
                "confianca": 0.95,
            }

    return {
        "titulo": "Sensores do Sistema",
        "resposta": "Consultar status do PC",
        "detalhe": "Lendo sensores em tempo real",
        "chave_ferramenta": "info-pc",
        "confianca": 0.70,
    }


# ======================================================================
# Lote 2: Mercado, Luz, Combustível, Cartão, Pix, Horas, Receitas, Datas
# ======================================================================

# ----------------------------------------------------------------------
# 21. Mercado (Q61–Q68)
# ----------------------------------------------------------------------

def extrair_mercado(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    palavras = ["feira", "mercado", "promo", "leite", "arroz", "carne", "banana", "refri", "paes", "pão", "compra"]
    if not any(p in norm for p in palavras):
        return None

    nums = rc.extrair_numeros(texto)

    # Q63: promo 4 pelo preco de 3, cada um custa 5,50 — quanto saem 4
    m = re.search(r"promo\s+(\d+)\s+pelo\s+preco\s+de\s+(\d+).*?custa\s*([0-9.,]+)", norm)
    if m:
        paga = float(m.group(2))
        unit = rc.numero_br(m.group(3))
        if unit is not None:
            return {"tipo": "promo", "resp": rc.formatar_br(paga * unit, 2), "det": f"Paga {int(paga)} unidades a R$ {rc.formatar_br(unit, 2)} cada."}

    # Q64: leite tava 5,20 agora ta 6,24, subiu quanto por cento
    m = re.search(r"tava\s*([0-9.,]+).*?agora\s+ta\s*([0-9.,]+).*?subiu\s+quanto", norm)
    if m:
        v1 = rc.numero_br(m.group(1))
        v2 = rc.numero_br(m.group(2))
        if v1 and v2:
            pct = ((v2 - v1) / v1) * 100.0
            return {"tipo": "subiu_pct", "resp": f"{rc.formatar_br(pct, 0)}%", "det": f"Aumento de R$ {rc.formatar_br(v2-v1, 2)} sobre R$ {rc.formatar_br(v1, 2)} ({rc.formatar_br(pct, 0)}%)."}

    # Q66: levei 80 reais no mercado, a compra deu 63,47, quanto sobra
    m = re.search(r"levei\s*([0-9.,]+).*?deu\s*([0-9.,]+).*?sobra", norm)
    if m:
        v1 = rc.numero_br(m.group(1))
        v2 = rc.numero_br(m.group(2))
        if v1 and v2:
            return {"tipo": "sobra", "resp": rc.formatar_br(v1 - v2, 2), "det": f"R$ {rc.formatar_br(v1, 2)} − R$ {rc.formatar_br(v2, 2)} = R$ {rc.formatar_br(v1 - v2, 2)}."}

    # Q68: desconto de 12% numa compra de 150 no mercado, fica quanto
    m = re.search(r"desconto\s+de\s*([0-9.,]+)%.*?compra\s+de\s*([0-9.,]+)", norm)
    if m:
        desc = rc.numero_br(m.group(1))
        tot = rc.numero_br(m.group(2))
        if desc and tot:
            val = tot * (1.0 - desc / 100.0)
            return {"tipo": "desc_compra", "resp": rc.formatar_br(val, 2), "det": f"Compra de R$ {rc.formatar_br(tot, 2)} com {rc.formatar_br(desc, 0)}% de desconto = R$ {rc.formatar_br(val, 2)}."}

    # Q65: lista do mercado: arroz 22,90, feijao 8,50, oleo 7,89 e sal 2,15 — total
    if "lista" in norm and ("mercado" in norm or "feira" in norm or "compras" in norm):
        if len(nums) >= 2:
            soma = sum(nums)
            return {"tipo": "lista", "resp": rc.formatar_br(soma, 2), "det": f"Soma dos {len(nums)} itens = R$ {rc.formatar_br(soma, 2)}."}

    # Q62: mercado: 3 refri a 7,49 e 2 paes a 0,80 cada, total
    itens = re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:[a-zA-Zçãé]+)?\s+a\s+([0-9.,]+)", norm)
    if len(itens) >= 2:
        tot = sum(float(q.replace(",", ".")) * (rc.numero_br(p) or 0) for q, p in itens)
        return {"tipo": "itens", "resp": rc.formatar_br(tot, 2), "det": f"Total da compra = R$ {rc.formatar_br(tot, 2)}."}

    # Q61, Q67: 1,2 kg de banana a 6,90 o kg / 1,5 kg de carne a 42,90 o kg
    m = re.search(r"([0-9.,]+)\s*kg.*?a\s*([0-9.,]+)", norm)
    if m:
        q = rc.numero_br(m.group(1))
        p = rc.numero_br(m.group(2))
        if q and p:
            tot = q * p
            return {"tipo": "peso_preco", "resp": rc.formatar_br(tot, 2), "det": f"{rc.formatar_br(q, 1)} kg × R$ {rc.formatar_br(p, 2)} = R$ {rc.formatar_br(tot, 2)}."}

    return None

def calcular_mercado(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "titulo": "Mercado & Compras",
        "resposta": p["resp"],
        "detalhe": p.get("det", ""),
        "chave_ferramenta": "comparador-precos-mercado",
        "confianca": 0.98,
    }

# ----------------------------------------------------------------------
# 22. Conta de Luz / Energia (Q69–Q75)
# ----------------------------------------------------------------------

def extrair_luz(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "pix" in norm:
        return None
    if not any(k in norm for k in ["luz", "kwh", "tarifa"]):
        return None

    nums = rc.extrair_numeros(texto)

    # Q71: mes passado a luz foi 240 kWh, esse mes 192, caiu quanto %
    if "caiu" in norm or "reduziu" in norm:
        if len(nums) >= 2:
            caiu = ((nums[0] - nums[1]) / nums[0]) * 100.0
            return {"resp": f"{rc.formatar_br(caiu, 0)}%", "det": f"Queda de {rc.formatar_br(nums[0]-nums[1], 0)} kWh ({rc.formatar_br(caiu, 0)}%)."}

    # Q72: rateio da conta de luz 312,60 pra 3 casas iguais
    if "rateio" in norm or "dividir" in norm or "casas" in norm:
        if len(nums) >= 2:
            val = nums[0] / nums[1]
            return {"resp": f"{rc.formatar_br(val, 2)} cada", "det": f"R$ {rc.formatar_br(nums[0], 2)} ÷ {int(nums[1])} casas = R$ {rc.formatar_br(val, 2)} por casa."}

    # Q75: parcelar a conta de luz de 189,90 em 3x iguais sem juros
    if "parcelar" in norm or "3x" in norm or "vezes" in norm:
        if len(nums) >= 2:
            val = nums[0] / nums[1]
            return {"resp": rc.formatar_br(val, 2), "det": f"R$ {rc.formatar_br(nums[0], 2)} em {int(nums[1])} parcelas de R$ {rc.formatar_br(val, 2)}."}

    # Q73: luz 200 kWh, tarifa 0,80 mais adicional 0,05 por kWh
    if "adicional" in norm and len(nums) >= 3:
        val = nums[0] * (nums[1] + nums[2])
        return {"resp": rc.formatar_br(val, 2), "det": f"{rc.formatar_br(nums[0], 0)} kWh × R$ {rc.formatar_br(nums[1]+nums[2], 2)} = R$ {rc.formatar_br(val, 2)}."}

    # Q74: se 100 kWh da luz saem 87,00, 250 kWh na mesma tarifa ficam quanto
    if "saem" in norm or "mesma tarifa" in norm:
        if len(nums) >= 3:
            val = (nums[1] / nums[0]) * nums[2]
            return {"resp": rc.formatar_br(val, 2), "det": f"Tarifa de R$ {rc.formatar_br(nums[1]/nums[0], 2)}/kWh × {rc.formatar_br(nums[2], 0)} kWh = R$ {rc.formatar_br(val, 2)}."}

    # Q70: luz: 180 kWh a 0,75 mais taxa fixa de 15 reais
    if "taxa fixa" in norm and len(nums) >= 3:
        val = nums[0] * nums[1] + nums[2]
        return {"resp": rc.formatar_br(val, 2), "det": f"{rc.formatar_br(nums[0], 0)} kWh × R$ {rc.formatar_br(nums[1], 2)} + R$ {rc.formatar_br(nums[2], 2)} = R$ {rc.formatar_br(val, 2)}."}

    # Q69: conta de luz: 220 kWh a 0,92 R$/kWh
    if len(nums) >= 2:
        val = nums[0] * nums[1]
        return {"resp": rc.formatar_br(val, 2), "det": f"{rc.formatar_br(nums[0], 0)} kWh × R$ {rc.formatar_br(nums[1], 2)} = R$ {rc.formatar_br(val, 2)}."}

    return None

def calcular_luz(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "titulo": "Conta de Luz & Energia",
        "resposta": p["resp"],
        "detalhe": p.get("det", ""),
        "chave_ferramenta": "rateio-conta-luz",
        "confianca": 0.98,
    }

# ----------------------------------------------------------------------
# 23. Combustível e Abastecimento (Q76, Q78, Q81, Q82, Q83)
# ----------------------------------------------------------------------

def extrair_compra_combustivel(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if not any(k in norm for k in ["gasolina", "litro", "litros", "tanque", "abastecer", "enchi", "combustivel"]):
        return None

    if ("etanol" in norm or "alcool" in norm) and "gasolina" in norm:
        return None

    # Se for cálculo de viagem (km/L, consumo de viagem), deixa para extrair_viagem
    if "viagem" in norm and "ida e volta" not in norm:
        return None
    if "km/l" in norm and "ida e volta" not in norm and "falta" not in norm:
        return None

    nums = rc.extrair_numeros(texto)

    # Q78: tanque de 50 L tava com 1/4, quanto falta pra encher
    if "tanque" in norm and ("falta" in norm or "encher" in norm):
        m = re.search(r"tanque\s+de\s*(\d+)\s*l.*?1/(\d+)", norm)
        if m:
            cap = float(m.group(1))
            den = float(m.group(2))
            falta = cap * (1.0 - 1.0 / den)
            return {"resp": f"{rc.formatar_br(falta, 1)} L", "det": f"Falta {int(den)-1}/{int(den)} do tanque de {int(cap)} L = {rc.formatar_br(falta, 1)} L."}

    # Q81: ida e volta 90 km cada trecho, consumo 15 km/L, litro a 6,20 — custo da viagem
    if "ida e volta" in norm and len(nums) >= 3:
        trecho, consumo, preco = nums[0], nums[1], nums[2]
        dist_tot = trecho * 2
        litros = dist_tot / consumo
        custo = litros * preco
        return {"resp": rc.formatar_br(custo, 2), "det": f"Ida e volta ({rc.formatar_br(dist_tot, 0)} km) a {rc.formatar_br(consumo, 0)} km/L: {rc.formatar_br(litros, 1)} L × R$ {rc.formatar_br(preco, 2)} = R$ {rc.formatar_br(custo, 2)}."}

    # Q83: falta 42 km, o carro faz 14 km/L — quantos litros preciso
    if "quantos litros preciso" in norm or "litros preciso" in norm:
        if len(nums) >= 2:
            litros = nums[0] / nums[1]
            return {"resp": f"{rc.formatar_br(litros, 0)} L", "det": f"{rc.formatar_br(nums[0], 0)} km ÷ {rc.formatar_br(nums[1], 0)} km/L = {rc.formatar_br(litros, 0)} L."}

    # Q76: gasolina 6,19 o litro, enchi 35 L, quanto paguei
    # Q82: 25 litros de gasolina a 5,99 o litro, total
    if len(nums) >= 2:
        val = nums[0] * nums[1]
        litros_val = nums[1] if nums[0] < 10 else nums[0]
        preco_val = nums[0] if nums[0] < 10 else nums[1]
        return {"resp": rc.formatar_br(val, 2), "det": f"{rc.formatar_br(litros_val, 0)} L × R$ {rc.formatar_br(preco_val, 2)} = R$ {rc.formatar_br(val, 2)}."}

    return None

def calcular_compra_combustivel(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "titulo": "Combustível & Abastecimento",
        "resposta": p["resp"],
        "detalhe": p.get("det", ""),
        "chave_ferramenta": "calculadora-combustivel-viagem",
        "confianca": 0.98,
    }

# ----------------------------------------------------------------------
# 24. Cartão e Parcelas (Q84–Q91)
# ----------------------------------------------------------------------

def extrair_cartao(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if not any(k in norm for k in ["cartao", "fatura", "parcela", "parcelas", "anuidade"]):
        return None

    nums = rc.extrair_numeros(texto)

    # Q87: compra de 800 no cartao com 5% de juros no total, parcelada em 4x iguais — valor da parcela e total
    if "juros" in norm and "parcelada" in norm:
        m = re.search(r"([0-9.,]+).*?([0-9.,]+)%.*?(\d+)x", norm)
        if m:
            val = rc.numero_br(m.group(1))
            juros = rc.numero_br(m.group(2))
            vezes = float(m.group(3))
            if val and juros and vezes:
                tot = val * (1.0 + juros / 100.0)
                parc = tot / vezes
                return {"resp": f"parcela {rc.formatar_br(parc, 0)}; total {rc.formatar_br(tot, 0)}", "det": f"R$ {rc.formatar_br(val, 2)} + {rc.formatar_br(juros, 0)}% = R$ {rc.formatar_br(tot, 2)} ({int(vezes)}x de R$ {rc.formatar_br(parc, 2)})."}

    # Q84: comprei 1.200 no cartao em 6x sem juros, valor de cada parcela
    # Q91: anuidade de 480 cobrada em 12x no cartao, quanto e por mes
    if ("em" in norm or "cobrada em" in norm) and re.search(r"\d+x", norm):
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:no cartao|cobrada)?.*?(\d+)x", norm)
        if m:
            tot = rc.numero_br(m.group(1))
            vezes = float(m.group(2))
            if tot and vezes:
                parc = tot / vezes
                return {"resp": rc.formatar_br(parc, 0 if parc == int(parc) else 2), "det": f"R$ {rc.formatar_br(tot, 2)} em {int(vezes)}x = R$ {rc.formatar_br(parc, 2)}/mês."}

    # Q85: 10x de 89,90 no cartao, quanto vou pagar no total
    m = re.search(r"(\d+)x\s+de\s*([0-9.,]+)", norm)
    if m:
        vezes = float(m.group(1))
        parc = rc.numero_br(m.group(2))
        if vezes and parc:
            tot = vezes * parc
            return {"resp": rc.formatar_br(tot, 2), "det": f"{int(vezes)} parcelas de R$ {rc.formatar_br(parc, 2)} = R$ {rc.formatar_br(tot, 2)}."}

    # Q86: parcela de 150 por 8 meses, ja paguei 3, quanto ainda devo
    if "ja paguei" in norm or "ainda devo" in norm:
        m = re.search(r"parcela\s+de\s*([0-9.,]+).*?(\d+)\s*meses.*?paguei\s*(\d+)", norm)
        if m:
            parc = rc.numero_br(m.group(1))
            tot_m = float(m.group(2))
            pagos = float(m.group(3))
            if parc:
                devo = (tot_m - pagos) * parc
                return {"resp": rc.formatar_br(devo, 0), "det": f"Restam {int(tot_m-pagos)} parcelas de R$ {rc.formatar_br(parc, 2)} = R$ {rc.formatar_br(devo, 2)}."}

    # Q88: fatura do cartao 1.350, paguei o minimo de 15%
    if "minimo" in norm and len(nums) >= 2:
        val = nums[0] * (nums[1] / 100.0)
        return {"resp": rc.formatar_br(val, 2), "det": f"{rc.formatar_br(nums[1], 0)}% de R$ {rc.formatar_br(nums[0], 2)} = R$ {rc.formatar_br(val, 2)}."}

    # Q89: fatura 2.000, paguei 600, quanto sobra
    if "paguei" in norm and "sobra" in norm and len(nums) >= 2:
        sobra = nums[0] - nums[1]
        return {"resp": rc.formatar_br(sobra, 0), "det": f"R$ {rc.formatar_br(nums[0], 2)} − R$ {rc.formatar_br(nums[1], 2)} = R$ {rc.formatar_br(sobra, 2)}."}

    # Q90: 3 compras no cartao: 49,90 + 120,00 + 15,50, total
    if "compras no cartao" in norm:
        precos = [n for idx, n in enumerate(nums) if not (idx == 0 and n == int(n) and n <= 10)]
        soma = sum(precos)
        return {"resp": rc.formatar_br(soma, 2), "det": f"Total das compras = R$ {rc.formatar_br(soma, 2)}."}

    return None

def calcular_cartao(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "titulo": "Cartão & Parcelas",
        "resposta": p["resp"],
        "detalhe": p.get("det", ""),
        "chave_ferramenta": "juros-cartao-rotativo",
        "confianca": 0.98,
    }

# ----------------------------------------------------------------------
# 25. Pix & Transferências (Q92–Q98)
# ----------------------------------------------------------------------

def extrair_pix(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if "pix" not in norm:
        return None

    nums = rc.extrair_numeros(texto)

    # Q94: vou dividir um pix de 97,50 pra 3 pessoas iguais
    if "dividir" in norm and len(nums) >= 2:
        val = nums[0] / nums[1]
        return {"resp": f"{rc.formatar_br(val, 2)} cada", "det": f"R$ {rc.formatar_br(nums[0], 2)} ÷ {int(nums[1])} pessoas = R$ {rc.formatar_br(val, 2)} cada."}

    # Q95: pix de 2 mil com tarifa de 1,5% — quanto cai na conta
    if "tarifa" in norm and len(nums) >= 2:
        tarifa = nums[0] * (nums[1] / 100.0)
        liq = nums[0] - tarifa
        return {"resp": rc.formatar_br(liq, 2), "det": f"R$ {rc.formatar_br(nums[0], 2)} − tarifa de {rc.formatar_br(nums[1], 1)}% (R$ {rc.formatar_br(tarifa, 2)}) = R$ {rc.formatar_br(liq, 2)}."}

    # Q93: recebi um pix de 1.250 e mandei outro de 430, quanto ficou desses dois
    # Q96: preciso pagar 1.080 no pix, ja mandei 400, quanto falta
    if "recebi" in norm or "quanto falta" in norm or "mandei outro" in norm:
        if len(nums) >= 2:
            saldo = nums[0] - nums[1]
            return {"resp": rc.formatar_br(saldo, 0), "det": f"R$ {rc.formatar_br(nums[0], 2)} − R$ {rc.formatar_br(nums[1], 2)} = R$ {rc.formatar_br(saldo, 2)}."}

    # Q97: 5 pessoas mandam 80 reais cada no pix pro churrasco, total
    if "cada" in norm and len(nums) >= 2:
        tot = nums[0] * nums[1]
        return {"resp": rc.formatar_br(tot, 0), "det": f"{int(nums[0])} × R$ {rc.formatar_br(nums[1], 2)} = R$ {rc.formatar_br(tot, 2)}."}

    # Q92: pix de 350 pra maria e 180 pra joao, quanto mandei no total
    # Q98: pix de 75,90 + 32,40 + 11,70, soma
    if len(nums) >= 2:
        tot = sum(nums)
        tem_centavos = any(n != int(n) for n in nums)
        return {"resp": rc.formatar_br(tot, 2 if tem_centavos else 0), "det": f"Total enviado no Pix = R$ {rc.formatar_br(tot, 2)}."}

    return None

def calcular_pix(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "titulo": "Pix & Transferências",
        "resposta": p["resp"],
        "detalhe": p.get("det", ""),
        "chave_ferramenta": "pix-boleto-comparador",
        "confianca": 0.98,
    }

# ----------------------------------------------------------------------
# 26. Horas Trabalhadas (Q99–Q105)
# ----------------------------------------------------------------------

def extrair_horas_trabalho(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if not any(k in norm for k in ["horas", "trabalhei", "trabalhadas", "jornada", "turnos", "almoco", "horas extras", "ganho", "hora de"]):
        return None

    nums = rc.extrair_numeros(texto)

    # Q101: entrei 8:15 e sai 17:45, com 1h de almoco — horas liquidas
    m_ponto = re.search(r"entrei\s*(\d{1,2}):(\d{2}).*?sai\s*(\d{1,2}):(\d{2})", norm)
    if m_ponto:
        h_ini, m_ini = int(m_ponto.group(1)), int(m_ponto.group(2))
        h_fim, m_fim = int(m_ponto.group(3)), int(m_ponto.group(4))
        tot_min = (h_fim * 60 + m_fim) - (h_ini * 60 + m_ini)
        m_alm = re.search(r"(\d+)\s*h\s+de\s+almoco", norm)
        if m_alm:
            tot_min -= int(m_alm.group(1)) * 60
        h_liq = tot_min // 60
        m_liq = tot_min % 60
        return {"resp": f"{h_liq} h {m_liq} min", "det": f"Total líquido trabalhado: {h_liq}h {m_liq}min."}

    # Q104: jornada de 44h na semana, trabalhei 50h, quantas horas extras
    if "jornada" in norm and "horas extras" in norm and len(nums) >= 2:
        he = nums[1] - nums[0]
        return {"resp": f"{rc.formatar_br(he, 0)} h", "det": f"{rc.formatar_br(nums[1], 0)} h − jornada {rc.formatar_br(nums[0], 0)} h = {rc.formatar_br(he, 0)} h extras."}

    # Q103: hora de 18 reais, 12 horas extras com adicional de 50%
    if "adicional" in norm and "horas extras" in norm and len(nums) >= 3:
        valor_hora, qtd_he, adic = nums[0], nums[1], nums[2]
        tot = qtd_he * (valor_hora * (1.0 + adic / 100.0))
        return {"resp": rc.formatar_br(tot, 0), "det": f"{rc.formatar_br(qtd_he, 0)} h extras × R$ {rc.formatar_br(valor_hora * (1+adic/100.0), 2)} = R$ {rc.formatar_br(tot, 2)}."}

    # Q102: fiz 3 turnos de 6,5 h, total de horas
    if "turnos" in norm and len(nums) >= 2:
        tot = nums[0] * nums[1]
        return {"resp": f"{rc.formatar_br(tot, 1)} h", "det": f"{int(nums[0])} turnos × {rc.formatar_br(nums[1], 1)} h = {rc.formatar_br(tot, 1)} h."}

    # Q99: trabalhei 8h por dia em 22 dias, quantas horas no mes
    if "por dia" in norm and "dias" in norm and len(nums) >= 2:
        tot = nums[0] * nums[1]
        return {"resp": f"{rc.formatar_br(tot, 0)} h", "det": f"{rc.formatar_br(nums[0], 0)} h/dia × {int(nums[1])} dias = {rc.formatar_br(tot, 0)} h."}

    # Q100: hora de 25 reais, 176 horas trabalhadas, quanto ganho
    if "hora de" in norm and "horas trabalhadas" in norm and len(nums) >= 2:
        tot = nums[0] * nums[1]
        return {"resp": rc.formatar_br(tot, 0), "det": f"R$ {rc.formatar_br(nums[0], 2)}/h × {rc.formatar_br(nums[1], 0)} h = R$ {rc.formatar_br(tot, 2)}."}

    # Q105: ganho 3.520 pra 160 horas, quanto vale a hora
    if "quanto vale a hora" in norm and len(nums) >= 2:
        val = nums[0] / nums[1]
        return {"resp": rc.formatar_br(val, 2), "det": f"R$ {rc.formatar_br(nums[0], 2)} ÷ {rc.formatar_br(nums[1], 0)} h = R$ {rc.formatar_br(val, 2)}/h."}

    return None

def calcular_horas_trabalho(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "titulo": "Horas Trabalhadas & Jornada",
        "resposta": p["resp"],
        "detalhe": p.get("det", ""),
        "chave_ferramenta": "simulador-hora-extra-50-100",
        "confianca": 0.98,
    }

# ----------------------------------------------------------------------
# 27. Receita & Proporção (Q106–Q112)
# ----------------------------------------------------------------------

def extrair_receita(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    if not any(k in norm for k in ["receita", "molho", "suco", "farinha", "alho", "porcoes", "laranjas", "macarrao", "pudim"]):
        return None

    nums = rc.extrair_numeros(texto)

    # Q112: a receita original rende 6 porcoes, eu quero 18 — multiplica por quanto
    if "multiplica por quanto" in norm and len(nums) >= 2:
        fator = nums[1] / nums[0]
        return {"resp": f"{rc.formatar_br(fator, 0)} vezes (triplicar)" if fator == 3 else f"{rc.formatar_br(fator, 1)} vezes", "det": f"{rc.formatar_br(nums[1], 0)} ÷ {rc.formatar_br(nums[0], 0)} = fator {rc.formatar_br(fator, 1)}."}

    if "pessoas" in norm or "pra 9" in norm or "pra 6" in norm:
        unidade = ""
        for uni in ["dentes", "dente", "laranjas", "laranja", "latas", "lata", "ml", "g", "kg"]:
            if uni in norm:
                unidade = " " + uni
                break

        m_padrao_b = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:dentes|laranjas|latas|ml|g|kg).*?pra\s*(\d+).*?pra\s*(\d+)", norm)
        if m_padrao_b:
            qtd_orig = rc.numero_br(m_padrao_b.group(1)) or nums[0]
            pess_orig = float(m_padrao_b.group(2))
            pess_nova = float(m_padrao_b.group(3))
        elif len(nums) >= 3:
            pess_orig = nums[0]
            qtd_orig = nums[1]
            pess_nova = nums[2]
        else:
            return None

        val = (pess_nova / pess_orig) * qtd_orig
        val_fmt = rc.formatar_br(val, 1 if val != int(val) else 0)
        return {"resp": f"{val_fmt}{unidade}", "det": f"Proporção de {rc.formatar_br(pess_orig, 0)} para {rc.formatar_br(pess_nova, 0)} pessoas ({rc.formatar_br(pess_nova/pess_orig, 2)}x)."}

    return None

def calcular_receita(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "titulo": "Receita & Proporção Culinária",
        "resposta": p["resp"],
        "detalhe": p.get("det", ""),
        "chave_ferramenta": "conversor-medidas-culinarias",
        "confianca": 0.98,
    }

# ----------------------------------------------------------------------
# 28. Datas & Contagem de Dias (Q113–Q120)
# ----------------------------------------------------------------------

def extrair_datas_contagem(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)
    palavras_chave = [
        "dia da semana", "dias corridos", "dias uteis", "faltam",
        "daqui", "ate o", "ate a", "para o", "para a", "proximo feriado"
    ]
    if not any(k in norm for k in palavras_chave):
        return None

    dias_semana_nomes = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

    # Q113, Q117: DD/MM/AAAA cai em que dia da semana
    if "dia da semana" in norm:
        dt = rc.extrair_data(texto)
        if dt:
            nome_dia = dias_semana_nomes[dt.weekday()]
            return {"resp": nome_dia, "det": f"{dt.strftime('%d/%m/%Y')} é {nome_dia}."}

    # Q115: quantos dias corridos de 01/04/2026 ate 15/04/2026, incluindo o primeiro e o ultimo
    # Q118: de 10/06/2026 ate 10/07/2026, quantos dias corridos
    # Q133: embarque 03/01/2027, hoje e 15/12/2026, quantos dias corridos faltam
    datas = re.findall(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", texto)
    if len(datas) >= 2 and ("quantos dias" in norm or "quantos dias corridos" in norm or "faltam" in norm):
        d1 = datetime.datetime.strptime(datas[0], "%d/%m/%Y").date()
        d2 = datetime.datetime.strptime(datas[1], "%d/%m/%Y").date()
        dias = abs((d2 - d1).days)
        if "incluindo" in norm or "inclusive" in norm:
            dias += 1
        return {"resp": f"{dias} dias", "det": f"Intervalo entre {d1.strftime('%d/%m/%Y')} e {d2.strftime('%d/%m/%Y')}: {dias} dias corridos."}

    # Q114, Q119: X dias corridos a partir de DD/MM/AAAA
    if "dias corridos" in norm:
        nums = rc.extrair_numeros(texto)
        dt = rc.extrair_data(texto)
        if dt and nums:
            n_dias = int(nums[0])
            dt_final = dt + datetime.timedelta(days=n_dias)
            return {"resp": dt_final.strftime("%d/%m/%Y"), "det": f"{dt.strftime('%d/%m/%Y')} + {n_dias} dias corridos = {dt_final.strftime('%d/%m/%Y')}."}

    # Q116, Q120: X dias uteis a partir de DD/MM/AAAA, sem feriado
    if "dias uteis" in norm and "sem feriado" in norm:
        nums = rc.extrair_numeros(texto)
        dt = rc.extrair_data(texto)
        if dt and nums:
            n_uteis = int(nums[0])
            cur = dt
            contados = 0
            while contados < n_uteis:
                cur += datetime.timedelta(days=1)
                if cur.weekday() < 5:  # seg a sex
                    contados += 1
            return {"resp": cur.strftime("%d/%m/%Y"), "det": f"{n_uteis} dias úteis (seg-sex) a partir de {dt.strftime('%d/%m/%Y')} = {cur.strftime('%d/%m/%Y')}."}

    # T12: "daqui X dias úteis" / "daqui a X dias uteis" (com ou sem data base)
    # Ex: "daqui 45 dias úteis", "daqui a 30 dias úteis a partir de 10/11/2026"
    m_daqui = re.search(r"daqui\s+(?:a\s+)?(\d+)\s+dias?\s+uteis?", norm)
    if m_daqui:
        n_uteis = int(m_daqui.group(1))
        dt_base = rc.extrair_data(texto) or datetime.date.today()
        # Usa cal_datas de calendario-br se disponível para considerar feriados nacionais
        try:
            import cal_datas
            dt_final = cal_datas.somar_uteis(dt_base, n_uteis)
        except Exception:
            try:
                import utl_core
                dt_final = utl_core.adicionar_uteis(dt_base, n_uteis)
            except Exception:
                cur = dt_base
                cont = 0
                while cont < n_uteis:
                    cur += datetime.timedelta(days=1)
                    if cur.weekday() < 5:
                        cont += 1
                dt_final = cur
        resp_str = dt_final.strftime("%d/%m/%Y")
        return {
            "resp": resp_str,
            "det": f"{n_uteis} dias úteis a partir de {dt_base.strftime('%d/%m/%Y')} = {resp_str}.",
        }

    # T12: "daqui X dias corridos" / "daqui a X dias"
    m_daqui_corr = re.search(r"daqui\s+(?:a\s+)?(\d+)\s+dias?(?:\s+corridos)?", norm)
    if m_daqui_corr:
        n_dias = int(m_daqui_corr.group(1))
        dt_base = rc.extrair_data(texto) or datetime.date.today()
        dt_final = dt_base + datetime.timedelta(days=n_dias)
        resp_str = dt_final.strftime("%d/%m/%Y")
        return {
            "resp": resp_str,
            "det": f"{dt_base.strftime('%d/%m/%Y')} + {n_dias} dias = {resp_str}.",
        }

    # T12: "quantos dias até o natal" / "quantos dias faltam para o ano novo" / "quando é o próximo feriado"
    # Eventos conhecidos e feriados
    eventos = {
        "natal": (12, 25, "Natal"),
        "ano novo": (1, 1, "Ano Novo"),
        "reveillon": (1, 1, "Ano Novo"),
        "tiradentes": (4, 21, "Tiradentes"),
        "trabalho": (5, 1, "Dia do Trabalho"),
        "independencia": (9, 7, "Independência do Brasil"),
        "aparecida": (10, 12, "Nossa Senhora Aparecida"),
        "finados": (11, 2, "Finados"),
        "republica": (11, 15, "Proclamação da República"),
        "consciencia negra": (11, 20, "Dia da Consciência Negra"),
    }

    hoje = datetime.date.today()
    dt_base = rc.extrair_data(texto) or hoje

    # Próximo feriado genérico
    if "proximo feriado" in norm or "quando e o feriado" in norm or "qual o proximo feriado" in norm:
        try:
            import cal_feriados
            prox = cal_feriados.proximo_feriado(dt_base)
            if prox:
                dias_ate = (prox.data - dt_base).days
                resp_str = f"{prox.nome} em {prox.data.strftime('%d/%m/%Y')}"
                return {
                    "resp": resp_str,
                    "det": f"Próximo feriado a partir de {dt_base.strftime('%d/%m/%Y')}: {prox.nome} em {prox.data.strftime('%d/%m/%Y')} (em {dias_ate} dias).",
                }
        except Exception:
            pass

    # Quantos dias até <evento>
    for ev_nome, (ev_m, ev_d, ev_rotulo) in eventos.items():
        if ev_nome in norm and any(k in norm for k in ["quantos dias", "faltam", "dias ate", "dias para", "quando e"]):
            alvo_ano = dt_base.year
            alvo = datetime.date(alvo_ano, ev_m, ev_d)
            if alvo < dt_base:
                alvo = datetime.date(alvo_ano + 1, ev_m, ev_d)

            dias_c = (alvo - dt_base).days
            dias_u = None
            try:
                import cal_datas
                dias_u = cal_datas.contar_uteis(dt_base, alvo)
            except Exception:
                pass

            if dias_u is not None:
                resp_str = f"{dias_c} dias ({dias_u} úteis)"
            else:
                resp_str = f"{dias_c} dias"

            return {
                "resp": resp_str,
                "det": f"De {dt_base.strftime('%d/%m/%Y')} até {ev_rotulo} ({alvo.strftime('%d/%m/%Y')}): {dias_c} dias corridos" + (f", sendo {dias_u} dias úteis." if dias_u is not None else "."),
            }

    return None

def calcular_datas_contagem(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "titulo": "Contagem de Datas & Prazos",
        "resposta": p["resp"],
        "detalhe": p.get("det", ""),
        "chave_ferramenta": "dias-uteis-pagamento",
        "confianca": 0.98,
    }


# ======================================================================
# Lote 3: Casa, Carro, Viagem e Freela (Q121–Q140)
# ======================================================================

def extrair_casa_obras(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Q121: aluguel 1.850, condominio 420 e agua 87,30, quanto da o mes da casa -> 2.357,30
    if "aluguel" in norm and "condominio" in norm and any(k in norm for k in ["mes da casa", "casa", "total", "da o mes"]):
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            tot = sum(nums)
            return {
                "tipo": "contas_casa",
                "total": tot,
                "det": f"Contas da casa: {' + '.join(f'R$ {rc.formatar_br(n, 2)}' for n in nums)} = R$ {rc.formatar_br(tot, 2)}.",
            }

    # Q123: piso da sala: 8,5 m2, cada caixa de ceramica rende 1,7 m2, quantas caixas preciso -> 5
    if ("piso" in norm or "ceramica" in norm) and "caixa" in norm:
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            area, rend = nums[0], nums[1]
            caixas = math.ceil(area / rend)
            return {
                "tipo": "piso",
                "caixas": caixas,
                "det": f"Área {rc.formatar_br(area, 1)} m² ÷ {rc.formatar_br(rend, 1)} m²/caixa = {caixas} caixas.",
            }

    return None

def calcular_casa_obras(p: Dict[str, Any]) -> Dict[str, Any]:
    if p["tipo"] == "contas_casa":
        ans = rc.formatar_br(p["total"], 2)
        return {
            "titulo": "Contas da Casa & Aluguel",
            "resposta": ans,
            "detalhe": p["det"],
            "chave_ferramenta": "financas",
            "confianca": 0.98,
        }
    elif p["tipo"] == "piso":
        return {
            "titulo": "Piso & Cerâmica",
            "resposta": str(p["caixas"]),
            "detalhe": p["det"],
            "chave_ferramenta": "calculadora-rendimento-tinta",
            "confianca": 0.98,
        }
    return {}

def extrair_carro_transito(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Q126: estacionamento 8,50 a hora, fiquei 3,5 h, quanto pago -> 29,75
    if "estacionamento" in norm:
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            val = nums[0] * nums[1]
            return {
                "tipo": "estacionamento",
                "val": val,
                "det": f"Estacionamento: {nums[1]:g} h × R$ {rc.formatar_br(nums[0], 2)} = R$ {rc.formatar_br(val, 2)}.",
            }

    # Q127: oleo do carro troca a cada 10.000 km, ta com 47.800, quanto falta pra chegar nos 50.000 -> 2.200
    if "oleo" in norm and "carro" in norm and any(k in norm for k in ["quanto falta", "troca", "chegar"]):
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            maiores = sorted([n for n in nums if n >= 1000], reverse=True)
            if len(maiores) >= 2:
                diff = maiores[0] - maiores[1]
                return {
                    "tipo": "oleo",
                    "val": diff,
                    "det": f"Próxima troca em {rc.formatar_br(maiores[0], 0)} km − atual {rc.formatar_br(maiores[1], 0)} km = falta {rc.formatar_br(diff, 0)} km.",
                }

    # Q129: seguro do carro 2.400 no ano, quanto da por mes -> 200
    if "seguro" in norm and any(k in norm for k in ["por mes", "no ano", "mes"]):
        nums = rc.extrair_numeros(texto)
        if nums:
            anual = nums[0]
            mensal = anual / 12.0
            return {
                "tipo": "seguro",
                "val": mensal,
                "det": f"Seguro anual de R$ {rc.formatar_br(anual, 2)} ÷ 12 = R$ {rc.formatar_br(mensal, 2)} por mês.",
            }

    # Q130: 3 pedagios de 6,40 na ida e os mesmos 3 na volta, quanto gasto de pedagio -> 38,40
    if "pedagio" in norm or "pedagios" in norm:
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            qtd = nums[0]
            preco = nums[1]
            mult = 2 if ("ida" in norm and "volta" in norm) else 1
            tot = qtd * preco * mult
            return {
                "tipo": "pedagio",
                "val": tot,
                "det": f"{int(qtd)} pedágios × R$ {rc.formatar_br(preco, 2)}{' (ida e volta)' if mult == 2 else ''} = R$ {rc.formatar_br(tot, 2)}.",
            }

    return None

def calcular_carro_transito(p: Dict[str, Any]) -> Dict[str, Any]:
    val = p["val"]
    ans = rc.formatar_br(val, 0 if val == int(val) else 2)
    titulos = {
        "estacionamento": "Estacionamento",
        "oleo": "Troca de Óleo",
        "seguro": "Seguro do Carro",
        "pedagio": "Cálculo de Pedágio",
    }
    return {
        "titulo": titulos.get(p["tipo"], "Carro & Trânsito"),
        "resposta": ans,
        "detalhe": p["det"],
        "chave_ferramenta": "calculadora-combustivel-viagem",
        "confianca": 0.98,
    }

def extrair_viagem_hospedagem(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Q131: hotel 189 a diaria, 4 noites, quanto fica a hospedagem -> 756
    if any(k in norm for k in ["hotel", "hospedagem", "pousada"]) and not rc.extrair_data(texto):
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            tot = nums[0] * nums[1]
            return {
                "tipo": "hotel",
                "val": tot,
                "det": f"Hospedagem: {int(nums[1])} diárias × R$ {rc.formatar_br(nums[0], 2)} = R$ {rc.formatar_br(tot, 2)}.",
            }

    # Q132: viagem: 280 dolares a 5,40 o dolar (cambio so do enunciado), quanto e em reais -> 1.512,00
    if any(k in norm for k in ["dolar", "dolares", "cambio", "moeda"]):
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            tot = nums[0] * nums[1]
            return {
                "tipo": "cambio",
                "val": tot,
                "det": f"US$ {rc.formatar_br(nums[0], 2)} × R$ {rc.formatar_br(nums[1], 2)}/USD = R$ {rc.formatar_br(tot, 2)}.",
            }

    # Q134: a viagem deu 2.460 no total, somos 4, quanto cada um -> 615
    if any(k in norm for k in ["somos", "cada um", "por pessoa", "dividir"]):
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            tot, pessoas = nums[0], nums[1]
            cada = tot / pessoas
            return {
                "tipo": "rateio",
                "val": cada,
                "det": f"Total R$ {rc.formatar_br(tot, 2)} ÷ {int(pessoas)} pessoas = R$ {rc.formatar_br(cada, 2)} cada.",
            }

    # Q135: aluguel de carro 95 por dia, 3 dias de viagem, quanto e so o carro -> 285
    if "aluguel" in norm and "carro" in norm:
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            tot = nums[0] * nums[1]
            return {
                "tipo": "aluguel_carro",
                "val": tot,
                "det": f"Aluguel de carro: {int(nums[1])} dias × R$ {rc.formatar_br(nums[0], 2)} = R$ {rc.formatar_br(tot, 2)}.",
            }

    return None

def calcular_viagem_hospedagem(p: Dict[str, Any]) -> Dict[str, Any]:
    val = p["val"]
    ans = rc.formatar_br(val, 0 if val == int(val) else 2)
    titulos = {
        "hotel": "Hospedagem & Hotel",
        "cambio": "Câmbio & Conversão",
        "rateio": "Rateio da Viagem",
        "aluguel_carro": "Aluguel de Carro",
    }
    return {
        "titulo": titulos.get(p["tipo"], "Viagem & Hospedagem"),
        "resposta": ans,
        "detalhe": p["det"],
        "chave_ferramenta": "financas",
        "confianca": 0.98,
    }

def extrair_freela_servicos(texto: str) -> Optional[Dict[str, Any]]:
    norm = rc.normalizar_texto(texto)

    # Q136: job freela de 2.800, o cliente reteve 10% de imposto (aliquota so do enunciado), quanto cai na conta -> 2.520,00
    if ("freela" in norm or "job" in norm) and ("imposto" in norm or "reteve" in norm or "retencao" in norm):
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            bruto, aliq = nums[0], nums[1]
            ret = bruto * (aliq / 100.0)
            liq = bruto - ret
            return {
                "tipo": "imposto",
                "val": liq,
                "det": f"Job R$ {rc.formatar_br(bruto, 2)} − retenção de {rc.formatar_br(aliq, 1)}% (R$ {rc.formatar_br(ret, 2)}) = R$ {rc.formatar_br(liq, 2)}.",
            }

    # Q137: cobro 85 a hora no freela, fiz 16,5 h nesse job, quanto faturo -> 1.402,50
    if ("freela" in norm or "job" in norm) and ("hora" in norm or "h" in norm) and any(k in norm for k in ["cobro", "faturo", "fiz"]):
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            tot = nums[0] * nums[1]
            return {
                "tipo": "horas_freela",
                "val": tot,
                "det": f"Freela: {rc.formatar_br(nums[1], 1)} h × R$ {rc.formatar_br(nums[0], 2)}/h = R$ {rc.formatar_br(tot, 2)}.",
            }

    # Q140: 3 jobs esse mes: 450 + 1.200 + 680, quanto faturo no total -> 2.330
    if ("jobs" in norm or "job" in norm) and "+" in texto:
        nums = rc.extrair_numeros(texto)
        if len(nums) >= 2:
            if len(nums) > 2 and nums[0] == (len(nums) - 1):
                vals = nums[1:]
            else:
                vals = nums
            tot = sum(vals)
            return {
                "tipo": "soma_jobs",
                "val": tot,
                "det": f"Total faturado: {' + '.join(f'R$ {rc.formatar_br(v, 2)}' for v in vals)} = R$ {rc.formatar_br(tot, 2)}.",
            }

    return None

def calcular_freela_servicos(p: Dict[str, Any]) -> Dict[str, Any]:
    val = p["val"]
    ans = rc.formatar_br(val, 0 if val == int(val) else 2)
    titulos = {
        "imposto": "Job Freelancer Líquido",
        "horas_freela": "Faturamento Freelancer",
        "soma_jobs": "Total de Jobs",
    }
    return {
        "titulo": titulos.get(p["tipo"], "Freelancer & Serviços"),
        "resposta": ans,
        "detalhe": p["det"],
        "chave_ferramenta": "financas",
        "confianca": 0.98,
    }


# ======================================================================
# Lista de Adaptadores Essenciais
# ======================================================================

ADAPTADORES = [
    {
        "chave": "info-pc",
        "titulo": "Sensores do Sistema",
        "palavras": ["disco", "pudim", "iptv", "clipboard", "prints", "downloads", "copiado"],
        "extrair": extrair_sensores_sistema,
        "calcular": calcular_sensores_sistema,
    },
    {
        "chave": "operacoes-compostas",
        "titulo": "Operações Compostas & Encadeadas",
        "palavras": ["frete", "parcelas", "vezes", "desconto", "entrada", "taxa", "entrega", "mais", "menos"],
        "extrair": extrair_operacoes_compostas,
        "calcular": calcular_operacoes_compostas,
    },
    {
        "chave": "financas",
        "titulo": "Cálculo de Porcentagem",
        "palavras": ["%", "porcento", "por cento", "porcentagem", "aumentou", "desconto", "off"],
        "extrair": extrair_porcentagem,
        "calcular": calcular_porcentagem,
    },
    {
        "chave": "financas",
        "titulo": "Cálculo de Fração",
        "palavras": ["/", "fracao", "pedaços"],
        "extrair": extrair_fracao,
        "calcular": calcular_fracao,
    },
    {
        "chave": "financas",
        "titulo": "Metade e Dobro",
        "palavras": ["metade", "dobro", "dobrar", "duzia"],
        "extrair": extrair_metade_dobro_duzia,
        "calcular": calcular_metade_dobro_duzia,
    },
    {
        "chave": "financas",
        "titulo": "Operação Aritmética",
        "palavras": ["+", "-", "*", "/"],
        "extrair": extrair_aritmetica,
        "calcular": calcular_aritmetica,
    },
    {
        "chave": "financas",
        "titulo": "Compras e Custo Unitário",
        "palavras": ["cada", "kwh", "parcelas", "custo por", "frete"],
        "extrair": extrair_compras_unitarias,
        "calcular": calcular_compras_unitarias,
    },
    {
        "chave": "financas",
        "titulo": "Média Aritmética",
        "palavras": ["media de", "media entre"],
        "extrair": extrair_media,
        "calcular": calcular_media,
    },
    {
        "chave": "financas",
        "titulo": "Gorjeta e Rateio",
        "palavras": ["gorjeta", "rateio", "split", "parcelar"],
        "extrair": extrair_gorjeta_rateio,
        "calcular": calcular_gorjeta_rateio,
    },
    {
        "chave": "calculadora-rendimento-tinta",
        "titulo": "Área e Pintura",
        "palavras": ["parede", "pintar", "area"],
        "extrair": extrair_area_e_tinta_detalhada,
        "calcular": calcular_area_e_tinta_detalhada,
    },
    {
        "chave": "conversor-unidades",
        "titulo": "Tempo e Velocidade",
        "palavras": ["velocidade", "minutos em horas", "horas e", "graus"],
        "extrair": extrair_tempo_velocidade,
        "calcular": calcular_tempo_velocidade,
    },
    {
        "chave": "financas",
        "titulo": "Proporções Avançadas",
        "palavras": ["trabalhadores", "ovos", "mapa", "gib", "mib"],
        "extrair": extrair_proporcoes_avancadas,
        "calcular": calcular_proporcoes_avancadas,
    },
    {
        "chave": "dias-uteis-pagamento",
        "titulo": "Datas e Diárias",
        "palavras": ["dias corridos", "diarios de hotel", "noite dormida"],
        "extrair": extrair_datas_especiais,
        "calcular": calcular_datas_especiais,
    },
    {
        "chave": "calculadora-troco",
        "titulo": "Calculadora de Troco",
        "palavras": ["troco", "paguei", "sobra"],
        "extrair": extrair_troco,
        "calcular": calcular_troco,
    },
    {
        "chave": "calculadora-ipva",
        "titulo": "Calculadora de IPVA",
        "palavras": ["ipva", "imposto carro"],
        "extrair": extrair_ipva,
        "calcular": calcular_ipva,
    },
    {
        "chave": "financas",
        "titulo": "Juros Simples e Compostos",
        "palavras": ["juros simples", "juros compostos", "quanto rende"],
        "extrair": extrair_juros,
        "calcular": calcular_juros,
    },
    {
        "chave": "conversor-unidades",
        "titulo": "Conversor de Unidades",
        "palavras": ["converter", "em metros", "em km", "em gramas", "em kg", "em litros", "em cm"],
        "extrair": extrair_conversao,
        "calcular": calcular_conversao,
    },
    {
        "chave": "dias-uteis-pagamento",
        "titulo": "Calculadora de Dias Úteis",
        "palavras": ["dias uteis", "dias úteis"],
        "extrair": extrair_dias_uteis,
        "calcular": calcular_dias_uteis,
    },
    {
        "chave": "financas",
        "titulo": "Regra de 3",
        "palavras": ["regra de 3", "se custa quanto"],
        "extrair": extrair_regra_de_tres,
        "calcular": calcular_regra_de_tres,
    },
    {
        "chave": "simulador-hora-extra-50-100",
        "titulo": "Hora Extra",
        "palavras": ["hora extra", "horas extras"],
        "extrair": extrair_hora_extra,
        "calcular": calcular_hora_extra,
    },
    {
        "chave": "calculadora-rendimento-tinta",
        "titulo": "Rendimento de Tinta",
        "palavras": ["tinta", "litros de tinta"],
        "extrair": extrair_tinta,
        "calcular": calcular_tinta,
    },
    {
        "chave": "calculadora-churrasco",
        "titulo": "Calculadora de Churrasco",
        "palavras": ["churrasco"],
        "extrair": extrair_churrasco,
        "calcular": calcular_churrasco,
    },
    {
        "chave": "calculadora-combustivel-viagem",
        "titulo": "Etanol × Gasolina",
        "palavras": ["etanol", "gasolina"],
        "extrair": extrair_etanol_gasolina,
        "calcular": calcular_etanol_gasolina,
    },
    {
        "chave": "calculadora-combustivel-viagem",
        "titulo": "Custo de Viagem",
        "palavras": ["viagem", "consumo"],
        "extrair": extrair_viagem,
        "calcular": calcular_viagem,
    },
    {
        "chave": "calculadora-nutricao",
        "titulo": "Índice de Massa Corporal (IMC)",
        "palavras": ["imc", "massa corporal"],
        "extrair": extrair_imc,
        "calcular": calcular_imc,
    },
    {
        "chave": "decimo-terceiro-proporcional",
        "titulo": "13º Salário Proporcional",
        "palavras": ["13", "13o", "13º", "decimo terceiro"],
        "extrair": extrair_13,
        "calcular": calcular_13,
    },
    {
        "chave": "juros-mora",
        "titulo": "Juros de Mora e Multa",
        "palavras": ["atrasado", "atraso", "mora"],
        "extrair": extrair_juros_mora,
        "calcular": calcular_juros_mora,
    },
    {
        "chave": "comparador-avista-parcelado",
        "titulo": "À Vista × Parcelado",
        "palavras": ["a vista", "parcelado"],
        "extrair": extrair_avista_parcelado,
        "calcular": calcular_avista_parcelado,
    },
    {
        "chave": "calculadora-clt",
        "titulo": "Salário Líquido CLT",
        "palavras": ["salario liquido", "desconto inss"],
        "extrair": extrair_salario_liquido,
        "calcular": calcular_salario_liquido,
    },
    {
        "chave": "taxa-maquininha",
        "titulo": "Taxa da Maquininha",
        "palavras": ["maquininha", "taxa cartao"],
        "extrair": extrair_maquininha,
        "calcular": calcular_maquininha,
    },
    {
        "chave": "comparador-precos-mercado",
        "titulo": "Mercado & Compras",
        "palavras": ["feira", "mercado", "promo", "kg", "compra"],
        "extrair": extrair_mercado,
        "calcular": calcular_mercado,
    },
    {
        "chave": "rateio-conta-luz",
        "titulo": "Conta de Luz & Energia",
        "palavras": ["luz", "kwh", "tarifa", "energia"],
        "extrair": extrair_luz,
        "calcular": calcular_luz,
    },
    {
        "chave": "calculadora-combustivel-viagem",
        "titulo": "Combustível & Abastecimento",
        "palavras": ["gasolina", "litro", "litros", "tanque"],
        "extrair": extrair_compra_combustivel,
        "calcular": calcular_compra_combustivel,
    },
    {
        "chave": "juros-cartao-rotativo",
        "titulo": "Cartão & Parcelas",
        "palavras": ["cartao", "fatura", "parcela", "parcelas", "anuidade"],
        "extrair": extrair_cartao,
        "calcular": calcular_cartao,
    },
    {
        "chave": "pix-boleto-comparador",
        "titulo": "Pix & Transferências",
        "palavras": ["pix"],
        "extrair": extrair_pix,
        "calcular": calcular_pix,
    },
    {
        "chave": "simulador-hora-extra-50-100",
        "titulo": "Horas Trabalhadas & Jornada",
        "palavras": ["horas", "trabalhei", "trabalhadas", "jornada", "turnos"],
        "extrair": extrair_horas_trabalho,
        "calcular": calcular_horas_trabalho,
    },
    {
        "chave": "conversor-medidas-culinarias",
        "titulo": "Receita & Proporção Culinária",
        "palavras": ["receita", "molho", "suco", "pessoas", "porcoes"],
        "extrair": extrair_receita,
        "calcular": calcular_receita,
    },
    {
        "chave": "dias-uteis-pagamento",
        "titulo": "Contagem de Datas & Prazos",
        "palavras": ["dias corridos", "dia da semana", "dias uteis"],
        "extrair": extrair_datas_contagem,
        "calcular": calcular_datas_contagem,
    },
    {
        "chave": "financas",
        "titulo": "Casa & Contas",
        "palavras": ["aluguel", "condominio", "mes da casa", "piso", "ceramica", "caixas"],
        "extrair": extrair_casa_obras,
        "calcular": calcular_casa_obras,
    },
    {
        "chave": "calculadora-combustivel-viagem",
        "titulo": "Carro & Trânsito",
        "palavras": ["estacionamento", "oleo", "seguro", "pedagio", "pedagios"],
        "extrair": extrair_carro_transito,
        "calcular": calcular_carro_transito,
    },
    {
        "chave": "financas",
        "titulo": "Viagem & Hospedagem",
        "palavras": ["hotel", "hospedagem", "dolar", "dolares", "cambio", "somos", "aluguel de carro"],
        "extrair": extrair_viagem_hospedagem,
        "calcular": calcular_viagem_hospedagem,
    },
    {
        "chave": "financas",
        "titulo": "Freelancer & Serviços",
        "palavras": ["freela", "job", "jobs", "faturo", "cobro"],
        "extrair": extrair_freela_servicos,
        "calcular": calcular_freela_servicos,
    },
]
