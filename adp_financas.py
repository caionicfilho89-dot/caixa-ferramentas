# -*- coding: utf-8 -*-
"""Adaptadores da barra de busca para Finanças & Trabalho.

Cada item de ADAPTADORES chama a função real do _core.py / módulo da ferramenta.
Não recalcula por fora. Enquanto respostas_core não existe, numero_br daqui
serve os testes; se o motor publicar numero_br, a gente usa o dele.
"""
from __future__ import annotations

import importlib
import os
import re
import sys
from datetime import date, timedelta

_AQUI = os.path.dirname(os.path.abspath(__file__))
_PAI = os.path.dirname(_AQUI)


def _raiz_ferramentas():
    if os.path.isdir(os.path.join(_PAI, "financas")):
        return _PAI
    return _PAI


RAIZ = _raiz_ferramentas()

_ACENTOS = str.maketrans(
    "áàâãäéèêëíìîïóòôõöúùûüçñ",
    "aaaaaeeeeiiiiooooouuuucn",
)


def norm(texto):
    s = str(texto or "").replace("º", "o").replace("°", "o").replace("ª", "a")
    return s.translate(_ACENTOS).lower()


def numero_br(token):
    """Converte um número pt-BR ('1.234,50', '3 mil', '10%') para float.

    O '%' não divide: '10%' vira 10. 'mil' multiplica por 1000.
    """
    try:
        import respostas_core
        fn = getattr(respostas_core, "numero_br", None)
        if fn and fn is not numero_br:
            return fn(token)
    except ImportError:
        pass
    return _numero_local(token)


def _numero_local(token):
    t = norm(token).strip()
    if not t:
        raise ValueError("numero vazio")
    mult = 1.0
    if t.endswith("milhoes") or t.endswith("milhao"):
        t = t.replace("milhoes", "").replace("milhao", "").strip()
        mult = 1_000_000.0
    elif t.endswith("mil"):
        t = t[:-3].strip()
        mult = 1000.0
    elif t.endswith("k") and t[:-1].strip()[:1].isdigit():
        t = t[:-1].strip()
        mult = 1000.0
    t = t.replace("r$", "").replace("us$", "").replace("%", "").replace("reais", "")
    t = t.strip()
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    return float(t) * mult


_RE_TOK = re.compile(
    r"(?<![\w])(?:(r\$|us\$)\s*)?"
    r"(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)"
    r"(\s*milhoes|\s*milhao|\s*mil|\s*k)?"
    r"(\s*%|\s*por cento|\s*reais|\s*meses|\s*mes|\s*horas|\s*hora|\s*dias|\s*dia|\s*anos|\s*ano|\s*x|\s*h)?"
    r"(?!\w)",
    re.IGNORECASE,
)

_TIPO_UNIDADE = {
    "%": "pct",
    "por cento": "pct",
    "reais": "din",
    "meses": "mes",
    "mes": "mes",
    "horas": "hora",
    "hora": "hora",
    "h": "hora",
    "dias": "dia",
    "dia": "dia",
    "anos": "ano",
    "ano": "ano",
    "x": "vezes",
}
_MULT = {"mil": 1000.0, "milhao": 1_000_000.0, "milhoes": 1_000_000.0, "k": 1000.0}
_UNIDADES = {"pct", "mes", "hora", "dia", "ano", "vezes", "int"}


class _Tok:
    def __init__(self, valor, tipo, ini, fim):
        self.valor = valor
        self.tipo = tipo
        self.ini = ini
        self.fim = fim

    @property
    def span(self):
        return (self.ini, self.fim)


def tokens(texto):
    t = norm(texto)
    achados = []
    for m in _RE_TOK.finditer(t):
        prefixo, bruto, mult, unidade = m.group(1), m.group(2), m.group(3), m.group(4)
        try:
            val = _numero_local(bruto)
        except ValueError:
            continue
        if mult:
            chave = mult.strip()
            val *= _MULT.get(chave, 1.0)
        uni = (unidade or "").strip()
        if uni in _TIPO_UNIDADE:
            tipo = _TIPO_UNIDADE[uni]
        elif prefixo or mult:
            tipo = "din"
        else:
            tipo = "solto"
        achados.append(_Tok(val, tipo, m.start(), m.end()))
    return achados


def _tem(texto_norm, palavra):
    p = norm(palavra).strip()
    if not p:
        return False
    if " " in p or len(p) > 4:
        return p in texto_norm
    return re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", texto_norm) is not None


def combina(texto, grupos, evitar=()):
    t = norm(texto)
    if any(_tem(t, p) for p in evitar):
        return False
    for grupo in grupos:
        if not any(_tem(t, p) for p in grupo):
            return False
    return True


def _compativel(tok, tipo, com_rotulo):
    if tipo == "din":
        return tok.tipo in ("din", "solto")
    if tipo == "pct":
        return tok.tipo == "pct"
    if tipo == "mes":
        return tok.tipo in ("mes", "vezes") or (com_rotulo and tok.tipo == "solto") or tok.tipo == "solto"
    if tipo == "hora":
        return tok.tipo == "hora" or (com_rotulo and tok.tipo == "solto")
    if tipo == "dia":
        return tok.tipo == "dia" or (com_rotulo and tok.tipo == "solto")
    if tipo == "ano":
        return tok.tipo == "ano" or (com_rotulo and tok.tipo == "solto")
    if tipo == "vezes":
        return tok.tipo in ("vezes", "mes") or (com_rotulo and tok.tipo == "solto")
    if tipo == "int":
        return tok.tipo in ("solto", "vezes", "dia", "mes", "ano") or (com_rotulo and tok.tipo == "din")
    if tipo == "num":
        return tok.tipo in ("solto", "din", "mes", "hora", "dia", "ano", "vezes", "pct")
    return True


def _penalidade(tok, tipo):
    if tipo == "din" and tok.tipo == "din":
        return 0
    if tipo == "mes" and tok.tipo == "mes":
        return 0
    if tipo == "hora" and tok.tipo == "hora":
        return 0
    if tipo == "dia" and tok.tipo == "dia":
        return 0
    if tipo == "ano" and tok.tipo == "ano":
        return 0
    if tipo == "pct" and tok.tipo == "pct":
        return 0
    if tipo == "vezes" and tok.tipo == "vezes":
        return 0
    return 1


def _posicoes(texto, rotulos):
    """Intervalos do texto em que cada rótulo aparece com borda de palavra."""
    t = norm(texto)
    posicoes = []
    for rot in (norm(r) for r in rotulos if r):
        ini = 0
        while True:
            i = t.find(rot, ini)
            if i < 0:
                break
            # '%' e 'R$' colam no número ('1%', 'R$ 10'). Rótulo que
            # não é letra não exige borda alfanumérica nesse lado.
            antes_ok = i == 0 or not rot[0].isalnum() or not t[i - 1].isalnum()
            fim = i + len(rot)
            depois_ok = fim >= len(t) or not rot[-1].isalnum() or not t[fim].isalnum()
            if antes_ok and depois_ok:
                posicoes.append((i, fim))
            ini = i + max(len(rot), 1)
    return posicoes


def perto(texto, rotulos, tipo, usados, permitir_solto=False, janela=48, alheios=()):
    toks = tokens(texto)
    posicoes = _posicoes(texto, rotulos)
    candidatos = []
    for tok in toks:
        if tok.span in usados:
            continue
        if posicoes:
            if not _compativel(tok, tipo, True):
                continue
            dist = min(_dist(tok, a, b) for a, b in posicoes)
            if dist > janela:
                continue
            # Mesma distância: o número DEPOIS do rótulo ganha ("entre 4",
            # "pinhão 11"). Se ele está tão perto de outro rótulo quanto
            # deste, fica com o outro ("2000 watts 127 volts").
            lado = min(
                0 if tok.ini >= b else 1
                for a, b in posicoes
                if _dist(tok, a, b) == dist
            )
            if alheios:
                d_out = min(_dist(tok, a, b) for a, b in alheios)
                estranho = 0 if dist < d_out else 1
            else:
                estranho = 0
            candidatos.append((_penalidade(tok, tipo), dist, estranho, lado, tok.ini, tok))
        elif permitir_solto and _compativel(tok, tipo, False):
            if tipo == "pct" and tok.tipo != "pct":
                continue
            if tipo == "hora" and tok.tipo != "hora":
                continue
            if tipo == "dia" and tok.tipo != "dia":
                continue
            if tipo == "ano" and tok.tipo != "ano":
                continue
            if tipo == "mes" and tok.tipo != "mes":
                continue
            if tipo == "vezes" and tok.tipo != "vezes":
                continue
            if tipo == "din" and tok.tipo not in ("din", "solto"):
                continue
            if tipo == "int" and tok.tipo == "din":
                continue
            candidatos.append((_penalidade(tok, tipo), tok.ini, 0, tok.ini, tok))
    if not candidatos:
        return None
    candidatos.sort()
    return candidatos[0][-1]


def _dist(tok, ini_rot, fim_rot):
    if tok.ini >= fim_rot:
        return tok.ini - fim_rot
    if tok.fim <= ini_rot:
        return ini_rot - tok.fim
    return 0


class _Omit:
    pass


OMITIR = _Omit()


def ler(texto, spec):
    """spec: (nome, rotulos, tipo, obrigatorio, default, permitir_solto)."""
    usados = set()
    ordem = sorted(
        range(len(spec)),
        key=lambda i: (0 if spec[i][2] in _UNIDADES else 1, i),
    )
    pos_por_campo = [_posicoes(texto, spec[i][1]) for i in range(len(spec))]
    saida = {}
    for i in ordem:
        nome, rotulos, tipo, obrig, default, solto = spec[i]
        alheios = [p for j, lista in enumerate(pos_por_campo) if j != i for p in lista]
        tok = perto(texto, rotulos, tipo, usados, permitir_solto=solto, alheios=alheios)
        if tok is None:
            if obrig:
                return None
            if default is not OMITIR:
                saida[nome] = default
            continue
        usados.add(tok.span)
        if tipo == "int":
            saida[nome] = int(round(tok.valor))
        else:
            saida[nome] = tok.valor
    return saida


def C(nome, rotulos, tipo, obrig=False, default=OMITIR, solto=False):
    return (nome, tuple(rotulos), tipo, obrig, default, solto)


def carregar(pasta, modulo):
    if modulo in sys.modules:
        return sys.modules[modulo]
    try:
        return importlib.import_module(modulo)
    except ImportError:
        caminho = os.path.join(RAIZ, pasta)
        if caminho not in sys.path:
            sys.path.insert(0, caminho)
        return importlib.import_module(modulo)


def _num(v, casas=2):
    s = f"{float(v):,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _brl(v):
    return "R$ " + _num(v)


def pacote(resposta, detalhe):
    return {"resposta": str(resposta).strip(), "detalhe": str(detalhe).strip()}


def detalhe_de(mod, resultado):
    if hasattr(resultado, "resumo") and callable(resultado.resumo):
        return resultado.resumo()
    for nome in ("formatar_relatorio", "formatar_resultado", "formatar"):
        fn = getattr(mod, nome, None)
        if not callable(fn):
            continue
        try:
            out = fn(resultado)
        except TypeError:
            continue
        if isinstance(out, str) and ("\n" in out or len(out) > 24):
            return out
    if isinstance(resultado, dict):
        linhas = []
        for k, v in resultado.items():
            if isinstance(v, (dict, list)):
                continue
            linhas.append(f"{k}: {v}")
        return "\n".join(linhas)
    return str(resultado)


def mostrar(mod, resultado, titulo, destaque=None, moeda=True):
    if isinstance(resultado, bool):
        return pacote(f"{titulo}: {'sim' if resultado else 'não'}", str(resultado))
    if isinstance(resultado, (int, float)):
        val = _brl(resultado) if moeda else _num(resultado)
        return pacote(f"{titulo}: {val}", f"{titulo}: {val}")
    texto = detalhe_de(mod, resultado)
    if hasattr(resultado, "liquido") and not isinstance(resultado, dict):
        brl = getattr(mod, "brl", _brl)
        rot = getattr(resultado, "rotulo_total", titulo)
        return pacote(f"{rot}: {brl(resultado.liquido)}", texto)
    if isinstance(resultado, dict) and destaque and destaque in resultado and not isinstance(resultado[destaque], (dict, list)):
        v = resultado[destaque]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            val = _brl(v) if moeda else _num(v)
        else:
            val = str(v)
        return pacote(f"{titulo}: {val}", texto)
    primeira = next((ln.strip() for ln in str(texto).splitlines() if ln.strip()), titulo)
    return pacote(primeira, texto)


def _chamar(fn, params):
    try:
        return fn(params)
    except ValueError as e:
        return pacote(str(e), str(e))


ADAPTADORES = []


def _registrar(chave, palavras, grupos, evitar, extrair, calcular):
    ADAPTADORES.append({
        "chave": chave,
        "palavras": list(palavras),
        "extrair": extrair,
        "calcular": calcular,
    })


def ligar(chave, palavras, grupos, evitar, pasta, modulo, funcao, spec, titulo, destaque=None, moeda=True, preparar=None):
    def extrair(texto):
        if not combina(texto, grupos, evitar):
            return None
        params = ler(texto, spec)
        if params is None:
            return None
        if preparar:
            params = preparar(texto, params)
            if params is None:
                return None
        return params

    def calcular(params):
        mod = carregar(pasta, modulo)
        fn = getattr(mod, funcao)
        try:
            r = fn(**params)
        except ValueError as e:
            return pacote(str(e), str(e))
        return mostrar(mod, r, titulo, destaque, moeda)

    _registrar(chave, palavras, grupos, evitar, extrair, calcular)


def _data_anos_atras(anos, meses=0):
    hoje = date.today()
    total = int(anos) * 12 + int(meses)
    y = hoje.year
    m = hoje.month - total
    while m <= 0:
        m += 12
        y -= 1
    dia = min(hoje.day, 28)
    return date(y, m, dia)


# ---------------------------------------------------------------------------
# CLT e trabalho
# ---------------------------------------------------------------------------

ligar(
    "decimo-terceiro-proporcional",
    ["13", "decimo", "13o salario"],
    [["13", "13o", "decimo", "decmo"]],
    ["rescis", "demiss", "ferias", "hora extra", "fgts", "insalubr", "pericul", "inss", "irrf", "liquido"],
    "decimo-terceiro-proporcional", "d13_core", "calcular",
    [
        C("meses_trabalhados", ["meses", "mes", "avos"], "mes", True, solto=True),
        C("adiantamento", ["adiantamento", "ja recebi", "recebido"], "din", False, 0.0),
        C("salario", ["salario", "bruto"], "din", True, solto=True),
    ],
    "A receber", "a_receber",
)

ligar(
    "calculadora-clt",
    ["salario liquido", "liquido", "inss", "irrf"],
    [["liquido", "liq", "cair na conta", "holerite"], ["salario", "bruto"]],
    ["13", "13o", "decimo", "ferias", "rescis", "demiss", "hora extra", "fgts", "noturn", "pericul", "insalubr", "plr", "pj", "freela", "freelancer"],
    "calculadora-clt", "clt_calc", "salario_liquido",
    [
        C("dependentes", ["dependente", "dependentes"], "int", False, 0),
        C("pensao", ["pensao"], "din", False, 0.0),
        C("outros_descontos", ["desconto", "outros descontos"], "din", False, 0.0),
        C("bruto", ["salario", "bruto"], "din", True, solto=True),
    ],
    "Líquido", None, True,
)

ligar(
    "calculadora-clt",
    ["ferias", "ferias clt"],
    [["ferias"]],
    ["abono", "vender", "venda de ferias", "pecuni"],
    "calculadora-clt", "clt_calc", "ferias",
    [
        C("dias_vendidos", ["vender", "vendidos", "abono"], "dia", False, 0),
        C("dependentes", ["dependente", "dependentes"], "int", False, 0),
        C("dias", ["dias"], "dia", False, 30),
        C("salario", ["salario", "bruto"], "din", True, solto=True),
    ],
    "Férias", None,
)

ligar(
    "calculadora-clt",
    ["13 salario", "decimo", "inss"],
    [["13", "13o", "decimo"], ["inss", "irrf", "liquido", "holerite"]],
    ["rescis", "demiss", "ferias"],
    "calculadora-clt", "clt_calc", "decimo_terceiro",
    [
        C("meses", ["meses", "mes", "avos"], "mes", False, 12, solto=True),
        C("dependentes", ["dependente", "dependentes"], "int", False, 0),
        C("salario", ["salario", "bruto"], "din", True, solto=True),
    ],
    "13º", None,
)

ligar(
    "calculadora-clt",
    ["fgts"],
    [["fgts", "fundo de garantia"]],
    ["rescis", "demiss", "multa de 40", "multa do fgts"],
    "calculadora-clt", "clt_calc", "fgts",
    [
        C("meses", ["meses", "mes"], "int", False, 12, solto=True),
        C("saldo_inicial", ["saldo"], "din", False, 0.0),
        C("salario", ["salario", "bruto"], "din", True, solto=True),
    ],
    "FGTS", None,
)


def _extrair_rescisao_clt(texto):
    if not combina(texto, [["rescis", "recisao", "demiss", "mandado embora", "mandaram embora"]], ["dias trabalhados", "avos", "no mes da saida"]):
        return None
    if _tem(norm(texto), "dias") and _tem(norm(texto), "meses"):
        return None
    params = ler(texto, [
        C("anos", ["anos", "ano"], "ano", True, solto=True),
        C("saldo_fgts", ["fgts", "saldo fgts"], "din", False, 0.0),
        C("dependentes", ["dependente", "dependentes"], "int", False, 0),
        C("salario", ["salario", "bruto"], "din", True, solto=True),
    ])
    if not params:
        return None
    t = norm(texto)
    if "justa causa" in t and "sem justa" not in t:
        params["motivo"] = "Justa causa"
    elif "acordo" in t:
        params["motivo"] = "Acordo (art. 484-A)"
    elif "pedido" in t:
        params["motivo"] = "Pedido de demissão"
    else:
        params["motivo"] = "Sem justa causa"
    return params


def _calcular_rescisao_clt(params):
    mod = carregar("calculadora-clt", "clt_calc")
    adm = _data_anos_atras(params["anos"])
    try:
        res = mod.rescisao(
            params["salario"], adm, date.today(),
            motivo=params["motivo"], saldo_fgts=params.get("saldo_fgts", 0.0),
            dependentes=params.get("dependentes", 0),
        )
    except ValueError as e:
        return pacote(str(e), str(e))
    return mostrar(mod, res, "Rescisão")


_registrar(
    "calculadora-clt",
    ["rescisao", "demissao", "aviso previo"],
    [["rescisao"]], [],
    _extrair_rescisao_clt, _calcular_rescisao_clt,
)


def _modalidade_rst(texto):
    t = norm(texto)
    if "justa causa" in t and "sem justa" not in t:
        return "com_justa_causa"
    if "acordo" in t:
        return "acordo_mutuo"
    if "pedido" in t:
        return "pedido_demissao"
    return "sem_justa_causa"


def _extrair_rst(texto):
    if not combina(texto, [["rescis", "recisao", "demiss"], ["dias"]]):
        return None
    params = ler(texto, [
        C("anos_trabalhados", ["anos", "ano"], "ano", False, 0, solto=True),
        C("meses_trabalhados_ano_atual", ["meses no ano", "meses", "mes"], "mes", True, solto=True),
        C("dias_trabalhados_mes_rescisao", ["dias"], "dia", True, solto=True),
        C("saldo_fgts_acumulado", ["fgts"], "din", False, 0.0),
        C("num_dependentes", ["dependente", "dependentes"], "int", False, 0),
        C("salario_bruto", ["salario", "bruto"], "din", True, solto=True),
    ])
    if not params:
        return None
    params["modalidade"] = _modalidade_rst(texto)
    params["aviso_previo_indenizado"] = "trabalhado" not in norm(texto)
    params["tem_ferias_vencidas"] = "ferias vencidas" in norm(texto)
    return params


def _calcular_rst(params):
    mod = carregar("calculadora-rescisao-trabalhista", "rst_core")
    try:
        r = mod.calcular_rescisao_clt(**params)
    except ValueError as e:
        return pacote(str(e), str(e))
    return mostrar(mod, r, "Líquido da rescisão", "total_liquido_disponivel")


_registrar(
    "calculadora-rescisao-trabalhista",
    ["rescisao", "trct", "aviso previo"],
    [["rescisao"]], [],
    _extrair_rst, _calcular_rst,
)

ligar(
    "simulador-abono-pecuniario-ferias",
    ["abono pecuniario", "vender ferias"],
    [["abono", "pecuni", "vender ferias", "venda de ferias"]],
    [],
    "simulador-abono-pecuniario-ferias", "abn_core", "simular_venda_ferias",
    [
        C("media_adicionais_mensal", ["adicional", "media"], "din", False, 0.0),
        C("num_dependentes", ["dependente", "dependentes"], "int", False, 0),
        C("salario_bruto", ["salario", "bruto"], "din", True, solto=True),
    ],
    "Venda de férias", "salario_base",
)


def _extrair_hex(texto):
    if not combina(texto, [["hora extra", "horas extras", "hora-extra", "hrs extra", "hora estra", "he50"]], ["noturn", "banco de hora", "sobreaviso", "prontidao"]):
        return None
    base = ler(texto, [
        C("salario_mensal", ["salario", "bruto"], "din", True, solto=True),
        C("horas_base_mes", ["divisor", "jornada", "base de"], "hora", False, 220.0),
    ])
    if not base:
        return None
    t = norm(texto)
    he50 = he100 = 0.0
    horas = [tok for tok in tokens(texto) if tok.tipo == "hora"]
    pcts = [tok for tok in tokens(texto) if tok.tipo == "pct"]
    if horas and pcts:
        # O percentual descreve a hora que veio antes ('10 horas 50%').
        # Se o percentual vem na frente ('50% 10 horas'), pega a hora seguinte.
        livres = list(horas)
        for p in pcts:
            antes = [h for h in livres if h.ini <= p.ini]
            if antes:
                h = min(antes, key=lambda h: p.ini - h.ini)
            else:
                depois = [h for h in livres if h.ini > p.ini]
                if not depois:
                    continue
                h = min(depois, key=lambda h: h.ini - p.ini)
            livres.remove(h)
            if abs(p.valor - 100) < 1:
                he100 += h.valor
            else:
                he50 += h.valor
        if livres:
            if "100" in t and "50" not in t:
                he100 += sum(h.valor for h in livres)
            else:
                he50 += sum(h.valor for h in livres)
    elif horas:
        if "100" in t and "50" not in t:
            he100 = sum(h.valor for h in horas)
        else:
            he50 = sum(h.valor for h in horas)
    else:
        return None
    base["horas_he50"] = he50
    base["horas_he100"] = he100
    return base


def _calcular_hex(params):
    mod = carregar("simulador-hora-extra-50-100", "hex_core")
    try:
        r = mod.simular(**params)
    except ValueError as e:
        return pacote(str(e), str(e))
    return mostrar(mod, r, "Horas extras", "total_extras")


_registrar(
    "simulador-hora-extra-50-100",
    ["hora extra", "he50", "he100"],
    [["hora extra"]], [],
    _extrair_hex, _calcular_hex,
)

ligar(
    "calculadora-adicional-noturno",
    ["adicional noturno", "hora noturna"],
    [["noturn", "notuno"]],
    ["sobreaviso", "prontidao"],
    "calculadora-adicional-noturno", "adt_core", "calcular",
    [
        C("horas_noturnas_mes", ["noturn", "horas"], "hora", True, solto=True),
        C("percentual_adicional", ["adicional", "percentual"], "pct", False, 20.0),
        C("horas_mes", ["divisor", "jornada"], "hora", False, 220.0),
        C("salario_mensal", ["salario", "bruto"], "din", True, solto=True),
    ],
    "Adicional noturno no mês", "valor_adicional_mes",
    preparar=lambda texto, p: {**p, "jornada_reduzida": "reduzid" in norm(texto) or "52" in norm(texto)},
)

ligar(
    "calculadora-adicional-periculosidade",
    ["periculosidade"],
    [["pericul"]],
    ["sobreaviso", "prontidao"],
    "calculadora-adicional-periculosidade", "per_core", "calcular",
    [
        C("percentual", ["percentual"], "pct", False, 30.0),
        C("proporcionalidade", ["proporcional"], "pct", False, 100.0),
        C("salario_base", ["salario", "base"], "din", True, solto=True),
    ],
    "Periculosidade no mês", "adicional_mensal",
)


def _grau_ins(texto):
    t = norm(texto)
    if any(p in t for p in ("maximo", "grau max", "40%")):
        return "maximo"
    if any(p in t for p in ("minimo", "grau min", "10%")):
        return "minimo"
    return "medio"


def _extrair_ins(texto):
    if not combina(texto, [["insalubr"]]):
        return None
    params = ler(texto, [
        C("salario_minimo", ["salario minimo", "minimo de", "piso"], "din", False, OMITIR, solto=True),
    ])
    if params is None:
        return None
    if "salario_minimo" not in params:
        mod = carregar("calculadora-adicional-insalubridade", "ins_core")
        params["salario_minimo"] = float(getattr(mod, "SALARIO_MINIMO_PADRAO", 1518.0))
        params["_piso_padrao"] = True
    params["grau"] = _grau_ins(texto)
    return params


def _calcular_ins(params):
    mod = carregar("calculadora-adicional-insalubridade", "ins_core")
    piso_padrao = params.pop("_piso_padrao", False)
    try:
        r = mod.calcular(params["grau"], params["salario_minimo"])
    except ValueError as e:
        return pacote(str(e), str(e))
    out = mostrar(mod, r, "Insalubridade no mês", "adicional_mensal")
    if piso_padrao:
        out["detalhe"] += "\nPiso usado: salário mínimo de referência da ferramenta (" + _brl(params["salario_minimo"]) + ")."
    return out


_registrar(
    "calculadora-adicional-insalubridade",
    ["insalubridade"],
    [["insalubridade"]], [],
    _extrair_ins, _calcular_ins,
)


def _extrair_sbp(texto):
    if not combina(texto, [["sobreaviso", "prontidao"]]):
        return None
    params = ler(texto, [
        C("horas_escala_no_mes", ["escala", "horas"], "hora", False, 60.0, solto=True),
        C("horas_acionamento_efetivo", ["acionamento", "acionado"], "hora", False, 0.0),
        C("salario_base_mensal", ["salario", "bruto"], "din", True, solto=True),
    ])
    if not params:
        return None
    params["regime"] = "prontidao" if "prontid" in norm(texto) else "sobreaviso"
    if params["horas_acionamento_efetivo"] > params["horas_escala_no_mes"]:
        params["horas_acionamento_efetivo"] = 0.0
    return params


def _calcular_sbp(params):
    mod = carregar("calculadora-adicional-sobreaviso-prontidao", "sbp_core")
    try:
        r = mod.calcular_sobreaviso_prontidao(**params)
    except ValueError as e:
        return pacote(str(e), str(e))
    return mostrar(mod, r, "Sobreaviso/prontidão no mês", "total_bruto_mes")


_registrar(
    "calculadora-adicional-sobreaviso-prontidao",
    ["sobreaviso", "prontidao"],
    [["sobreaviso"]], [],
    _extrair_sbp, _calcular_sbp,
)

ligar(
    "calculadora-equiparacao-salarial-clt",
    ["equiparacao", "desvio de funcao", "paradigma"],
    [["equiparacao", "desvio de funcao", "paradigma"]],
    [],
    "calculadora-equiparacao-salarial-clt", "eqs_core", "calcular_liquidacao_equiparacao",
    [
        C("meses_trabalhados", ["meses", "mes"], "mes", True, solto=True),
        C("salario_paradigma", ["paradigma", "colega", "referencia"], "din", True),
        C("salario_requerente", ["eu ganho", "meu salario", "requerente", "salario"], "din", True, solto=True),
    ],
    "Diferença total", "total_geral",
)

ligar(
    "simulador-banco-horas-compensacao",
    ["banco de horas"],
    [["banco de hora"]],
    [],
    "simulador-banco-horas-compensacao", "bhc_core", "calcular_banco_horas",
    [
        C("he_100_dec", ["100%", "domingo", "feriado"], "hora", False, 0.0),
        C("horas_folgadas_dec", ["folga", "folgadas", "compens"], "hora", False, 0.0),
        C("he_50_dec", ["50%", "extras", "horas"], "hora", True, solto=True),
        C("divisor_jornada", ["divisor", "jornada"], "int", False, 220),
        C("salario_base", ["salario", "bruto"], "din", True, solto=True),
    ],
    "Saldo do banco", "saldo_formatado_str", False,
    preparar=lambda texto, p: {**p, "saldo_anterior_dec": 0.0, "meses_decorridos": 0},
)


def _regime_cdf(texto):
    t = norm(texto)
    if "mei" in t.split() or _tem(t, "mei"):
        return "mei"
    if "anexo iv" in t or "anexo 4" in t:
        return "simples_anexo_4"
    if "lucro presumido" in t or "lucro real" in t or "presumido" in t:
        return "lucro_presumido_real"
    return "simples_anexo_1_2_3"


def _extrair_cdf(texto):
    if not combina(
        texto,
        [["custo", "contratar", "contratacao", "folha"], ["funcionario", "empregado"]],
        ["domestic", "domestico", "empregada", "diarista"],
    ):
        return None
    params = ler(texto, [
        C("vale_transporte_mensal", ["vale transporte", "vt"], "din", False, 0.0),
        C("vale_alimentacao_mensal", ["vale alimentacao", "vale refeicao", "vr", "va"], "din", False, 0.0),
        C("plano_saude_mensal", ["plano", "saude"], "din", False, 0.0),
        C("salario_bruto", ["salario", "bruto"], "din", True, solto=True),
    ])
    if not params:
        return None
    params["regime_tributario"] = _regime_cdf(texto)
    params["outros_beneficios_mensais"] = 0.0
    params["exame_ocupacional_mensal"] = 0.0
    return params


def _calcular_cdf(params):
    mod = carregar("calculadora-custo-contratacao-funcionario", "cdf_core")
    try:
        r = mod.calcular_custo_funcionario(**params)
    except ValueError as e:
        return pacote(str(e), str(e))
    out = mostrar(mod, r, "Custo mensal do funcionário", "custo_total_mensal")
    out["detalhe"] += "\nBenefícios não citados entraram como zero (VT/VA/plano/exame)."
    return out


_registrar(
    "calculadora-custo-contratacao-funcionario",
    ["custo funcionario", "contratar clt", "folha"],
    [["custo"]], [],
    _extrair_cdf, _calcular_cdf,
)

ligar(
    "custo-empregado-domestico",
    ["empregada", "domestico", "diarista"],
    [["domestic", "empregada", "diarista"]],
    [],
    "custo-empregado-domestico", "emd_core", "calcular",
    [
        C("vale_transporte", ["vale transporte", "vt", "transporte"], "din", False, 0.0),
        C("outros_beneficios", ["beneficio", "beneficios"], "din", False, 0.0),
        C("salario", ["salario", "bruto"], "din", True, solto=True),
    ],
    "Custo mensal", "total_mes",
)


def _extrair_cpj(texto):
    if not combina(texto, [["pj"], ["clt", "equival", "virar pj", "quanto faturar"]]):
        return None
    params = ler(texto, [C("salario", ["salario", "bruto", "clt"], "din", True, solto=True)])
    if not params:
        return None
    t = norm(texto)
    params["zerar"] = "sem beneficio" in t or "sem vr" in t
    return params


def _calcular_cpj(params):
    mod = carregar("comparador-clt-pj", "cpj_core")
    extra = {}
    if params.get("zerar"):
        extra = {"va_vr_clt": 0.0, "plano_saude_clt": 0.0, "custo_contabilidade": 0.0}
    try:
        eq = mod.encontrar_equivalencia_pj_para_clt(params["salario"], **extra)
        pac = mod.calcular_pacote_clt(params["salario"], **({"va_vr_mensal": 0.0, "plano_saude_empresa": 0.0} if params.get("zerar") else {}))
    except ValueError as e:
        return pacote(str(e), str(e))
    resp = f"PJ para empatar: {_brl(eq)} de faturamento por mês"
    det = (
        f"Faturamento PJ mínimo para igualar o pacote CLT de {_brl(params['salario'])}: {_brl(eq)}.\n"
        f"Pacote CLT percebido/mês (função da ferramenta): {_brl(pac.get('total_liquido_percebido_mes', 0))}."
    )
    if not params.get("zerar"):
        det += "\nPadrão da ferramenta: VR/VA R$ 800, plano R$ 450, contabilidade R$ 250."
    return pacote(resp, det)


_registrar(
    "comparador-clt-pj",
    ["clt ou pj", "virar pj", "equivalencia pj"],
    [["pj", "clt"]], [],
    _extrair_cpj, _calcular_cpj,
)

ligar(
    "calculadora-beneficio-vr-va",
    ["vale refeicao", "vale alimentacao"],
    [["vale refeicao", "vale alimentacao", "vale-refeicao", "vr", "va"]],
    [],
    "calculadora-beneficio-vr-va", "vva_core", "calcular",
    [
        C("desconto_pct", ["desconto", "coparticipacao"], "pct", False, 0.0),
        C("feriados_faltas", ["falta", "faltas", "feriado"], "dia", False, 0),
        C("valor_dia_va", ["alimentacao", "va"], "din", False, 0.0),
        C("valor_dia_vr", ["refeicao", "vr", "por dia", "dia"], "din", True, solto=True),
        C("dias_uteis", ["dias", "uteis"], "dia", True, solto=True),
    ],
    "Líquido do vale", "liquido_total",
)

ligar(
    "simulador-plr",
    ["plr", "participacao nos lucros"],
    [["plr", "participacao nos lucros"]],
    [],
    "simulador-plr", "plr_core", "simular",
    [
        C("meta_pct", ["meta"], "pct", False, 100.0),
        C("multiplo", ["salarios", "multiplo", "vezes"], "num", True, solto=True),
        C("salario_base", ["salario", "bruto"], "din", True, solto=True),
    ],
    "PLR líquida", "liquido",
)


def _extrair_phr(texto):
    if not combina(texto, [["freelancer", "freela", "hora tecnica", "preco da hora"]]):
        return None
    params = ler(texto, [
        C("aliquota_imposto_pct", ["imposto"], "pct", False, 0.0),
        C("margem_lucro_reserva_pct", ["margem"], "pct", False, 0.0),
        C("custos_fixos_mensais", ["custo fixo", "custos"], "din", False, 0.0),
        C("renda_liquida_mensal", ["ganhar", "renda", "salario", "liquido"], "din", True, solto=True),
    ])
    if not params:
        return None
    params.update({
        "horas_trabalho_dia": 6.0,
        "dias_semana": 5,
        "semanas_ferias_ano": 4,
        "dias_feriados_ano": 12,
        "pct_horas_faturaveis": 65.0,
        "investimento_equipamento_total": 0.0,
        "anos_vida_util_equipamento": 3.0,
    })
    return params


def _calcular_phr(params):
    mod = carregar("calculadora-preco-freelancer", "phr_core")
    try:
        r = mod.calcular_hora_freelancer(**params)
    except ValueError as e:
        return pacote(str(e), str(e))
    out = mostrar(mod, r, "Hora freelancer", "valor_hora_recomendado")
    out["detalhe"] += (
        "\nJornada padrão da ferramenta (6 h/dia, 5 dias, 4 semanas de férias, "
        "65% faturável). Custos, equipamento, imposto e margem ficam zerados "
        "quando você não informa."
    )
    return out


_registrar(
    "calculadora-preco-freelancer",
    ["freelancer", "hora tecnica"],
    [["freelancer"]], [],
    _extrair_phr, _calcular_phr,
)


def _lado_proposta(texto, nome):
    sal = ler(texto, [C("salario_bruto", ["salario", "bruto"], "din", True, solto=True)])
    if not sal:
        return None
    extra = ler(texto, [
        C("vale_refeicao", ["vr", "refeicao"], "din", False, 0.0),
        C("vale_transporte", ["vt", "transporte"], "din", False, 0.0),
        C("plano_saude", ["plano", "saude"], "din", False, 0.0),
        C("outros_beneficios", ["outros"], "din", False, 0.0),
    ]) or {}
    extra["nome"] = nome
    extra["salario_bruto"] = sal["salario_bruto"]
    return extra


def _extrair_csb(texto):
    if not combina(texto, [["proposta", "beneficio"], ["contra", "versus", " vs "]]):
        return None
    t = norm(texto)
    pedacos = re.split(r"\bcontra\b|\bversus\b|\bvs\b", t, maxsplit=1)
    if len(pedacos) != 2:
        return None
    a = _lado_proposta(pedacos[0], "A")
    b = _lado_proposta(pedacos[1], "B")
    if not a or not b:
        return None
    return {"a": a, "b": b}


def _calcular_csb(params):
    mod = carregar("comparador-salario-beneficios", "csb_core")
    a = mod.Proposta(**params["a"])
    b = mod.Proposta(**params["b"])
    try:
        r = mod.comparar(a, b)
    except ValueError as e:
        return pacote(str(e), str(e))
    texto = mod.formatar_relatorio(r) if hasattr(mod, "formatar_relatorio") else detalhe_de(mod, r)
    return pacote(f"Melhor pacote: {r.get('melhor')}", texto)


_registrar(
    "comparador-salario-beneficios",
    ["proposta", "beneficios", "vale"],
    [["proposta"]], [],
    _extrair_csb, _calcular_csb,
)


def _extrair_scd(texto):
    if not combina(texto, [["indice"], ["salario"], ["contra", "versus", " vs ", "cidade"]]):
        return None
    t = norm(texto)
    pedacos = re.split(r"\bcontra\b|\bversus\b|\bvs\b", t, maxsplit=1)
    if len(pedacos) != 2:
        return None
    a = ler(pedacos[0], [
        C("indice_a", ["indice", "custo"], "num", True, solto=True),
        C("salario_a", ["salario"], "din", True, solto=True),
    ])
    b = ler(pedacos[1], [
        C("indice_b", ["indice", "custo"], "num", True, solto=True),
        C("salario_b", ["salario"], "din", True, solto=True),
    ])
    if not a or not b:
        return None
    a.update(b)
    return a


def _calcular_scd(params):
    mod = carregar("comparador-salario-cidade", "scd_core")
    try:
        r = mod.comparar(params["salario_a"], params["indice_a"], params["salario_b"], params["indice_b"])
    except ValueError as e:
        return pacote(str(e), str(e))
    return mostrar(mod, r, "Para igualar A, B precisa pagar", "salario_necessario_b")


_registrar(
    "comparador-salario-cidade",
    ["salario cidade", "custo de vida", "indice"],
    [["indice"]], [],
    _extrair_scd, _calcular_scd,
)

# ---------------------------------------------------------------------------
# Juros, financiamento, dia a dia do dinheiro
# ---------------------------------------------------------------------------

def _extrair_mora(texto):
    if not combina(texto, [["mora", "atraso"], ["juros", "multa", "divida", "boleto", "conta"]]):
        return None
    if combina(texto, [["banco de horas"]]):
        return None
    params = ler(texto, [
        C("dias", ["dias", "atraso"], "dia", True, solto=True),
        C("multa_pct", ["multa"], "pct", False, 2.0),
        C("juros_mensal_pct", ["juros", "mora"], "pct", False, 1.0),
        C("principal", ["divida", "conta", "boleto", "valor", "de"], "din", True, solto=True),
    ])
    if not params:
        return None
    params["composto"] = "composto" in norm(texto)
    return params


def _calcular_mora(params):
    mod = carregar("juros-mora", "jmr_core")
    pag = date.today()
    venc = pag - timedelta(days=int(params["dias"]))
    try:
        r = mod.calcular(
            params["principal"], venc, pag,
            multa_pct=params["multa_pct"], juros_mensal_pct=params["juros_mensal_pct"],
            composto=params["composto"],
        )
    except ValueError as e:
        return pacote(str(e), str(e))
    return mostrar(mod, r, "Total atualizado", "total")


_registrar(
    "juros-mora",
    ["juros de mora", "multa", "atraso"],
    [["mora"]], [],
    _extrair_mora, _calcular_mora,
)


def _taxa_frac(texto, params, chave_pct="taxa"):
    t = norm(texto)
    pct = params[chave_pct]
    mod = carregar("financas", "fin_calc")
    if any(p in t for p in ("ao ano", "a.a", "anual", "por ano")):
        return mod.aa_to_am(pct / 100.0)
    return pct / 100.0


def _extrair_composto(texto):
    if not combina(texto, [["composto", "rende", "render", "aplicad", "rendimento"]], ["mora", "atraso", "price", "financi", "prestacao", "rotativ", "maquininha", "pix", "consign", "entrada", "aposent"]):
        return None
    params = ler(texto, [
        C("meses", ["meses", "mes"], "mes", True, solto=True),
        C("taxa", ["juros", "taxa", "%", "ao mes", "ao ano"], "pct", True, solto=True),
        C("aporte", ["aporte", "por mes", "todo mes"], "din", False, 0.0),
        C("capital", ["capital", "aplicar", "aplicado", "tenho", "valor"], "din", True, solto=True),
    ])
    return params


def _calcular_composto_com(params, i_am, mod):
    linhas = mod.compound(params["capital"], params.get("aporte", 0.0), i_am, int(params["meses"]))
    saldo = linhas[-1][3]
    juros = linhas[-1][2]
    resp = f"Saldo: {_brl(saldo)}"
    det = f"Depois de {int(params['meses'])} meses: {_brl(saldo)} (juros {_brl(juros)}).\nTaxa mensal usada: {_num(i_am * 100, 4)}% a.m."
    return pacote(resp, det)


def _extrair_composto2(texto):
    params = _extrair_composto(texto)
    if not params:
        return None
    params["_texto"] = texto
    return params


def _calcular_composto2(params):
    texto = params.pop("_texto")
    mod = carregar("financas", "fin_calc")
    i = _taxa_frac(texto, params)
    try:
        return _calcular_composto_com(params, i, mod)
    except ValueError as e:
        return pacote(str(e), str(e))


_registrar(
    "financas",
    ["juros compostos", "rende", "aplicacao"],
    [["juros"]], [],
    _extrair_composto2, _calcular_composto2,
)


def _extrair_price(texto):
    if not combina(
        texto,
        [["price", "prestacao", "financi", "sac"]],
        ["entrada", "consorcio", "amort", "fies", "estudant", "rotativ", "consign"],
    ):
        return None
    params = ler(texto, [
        C("meses", ["meses", "mes", "parcelas", "vezes"], "mes", True, solto=True),
        C("taxa", ["juros", "taxa", "ao ano", "ao mes"], "pct", True),
        C("valor", ["valor", "financiar", "financiado", "emprestimo", "de"], "din", True, solto=True),
    ])
    if not params:
        return None
    params["sistema"] = "SAC" if _tem(norm(texto), "sac") else "PRICE"
    params["_texto"] = texto
    return params


def _calcular_price(params):
    texto = params.pop("_texto")
    mod = carregar("financas", "fin_calc")
    i = _taxa_frac(texto, params)
    n = int(params["meses"])
    pv = params["valor"]
    if params["sistema"] == "SAC":
        rows = mod.schedule_sac(pv, i, n)
        juros = sum(r[2] for r in rows)
        primeira = rows[0][1]
        ultima = rows[-1][1]
        resp = f"Primeira prestação SAC: {_brl(primeira)}"
        det = f"SAC {n} meses. Primeira {_brl(primeira)}, última {_brl(ultima)}. Juros totais {_brl(juros)}."
    else:
        pmt = mod.price_pmt(pv, i, n)
        juros = pmt * n - pv
        resp = f"Prestação Price: {_brl(pmt)}"
        det = f"PRICE {n}x de {_brl(pmt)}. Total {_brl(pmt * n)}. Juros {_brl(juros)}."
    det += f"\nTaxa mensal usada: {_num(i * 100, 4)}% a.m."
    return pacote(resp, det)


_registrar(
    "financas",
    ["price", "sac", "prestacao", "financiamento"],
    [["financiamento"]], [],
    _extrair_price, _calcular_price,
)


def _extrair_dividir(texto):
    if not combina(texto, [["dividir", "rachar"]], ["buffet"]):
        return None
    params = ler(texto, [
        C("pessoas", ["pessoas", "pessoa", "gente", "entre"], "int", True),
        C("gorjeta_pct", ["garcom", "gorjeta", "servico"], "pct", False, 0.0),
        C("valor", ["conta", "valor", "total"], "din", True, solto=True),
    ])
    return params


def _calcular_dividir(params):
    mod = carregar("financas", "fin_calc")
    r = mod.dividir_conta(params["valor"], int(params["pessoas"]), params.get("gorjeta_pct", 0.0) / 100.0)
    return mostrar(mod, r, "Cada um paga", "nao_bebe")


_registrar(
    "financas",
    ["dividir conta", "rachar"],
    [["dividir"]], [],
    _extrair_dividir, _calcular_dividir,
)

ligar(
    "entrada-financiamento",
    ["entrada", "financiamento imovel"],
    [["entrada"], ["imovel", "financi", "apartamento", "casa"]],
    ["consorcio"],
    "entrada-financiamento", "ent_core", "calcular",
    [
        C("meses", ["meses", "mes", "prazo"], "mes", True, solto=True),
        C("taxa_anual_pct", ["ao ano", "anual", "juros", "taxa"], "pct", True),
        C("entrada_pct", ["entrada"], "pct", True),
        C("valor_imovel", ["imovel", "apartamento", "casa", "valor"], "din", True, solto=True),
    ],
    "Prestação", "prestacao",
)

ligar(
    "consignado-vs-credito-pessoal",
    ["consignado"],
    [["consignado"]],
    [],
    "consignado-vs-credito-pessoal", "ccn_core", "comparar",
    [
        C("taxa_pessoal", ["pessoal", "comum"], "pct", True),
        C("taxa_consignado", ["consignado"], "pct", True),
        C("n", ["vezes", "parcelas", "meses"], "vezes", True, solto=True),
        C("valor", ["valor", "emprestimo", "de"], "din", True, solto=True),
    ],
    "Mais barato", "vencedor", False,
)


def _extrair_rotativo(texto):
    if not combina(texto, [["rotativo"]]):
        return None
    return ler(texto, [
        C("taxa_mes", ["juros", "taxa"], "pct", False, 14.0),
        C("pagamento", ["pagar", "pagamento", "pago"], "din", True),
        C("fatura", ["fatura", "valor"], "din", True, solto=True),
    ])


def _calcular_rotativo(params):
    mod = carregar("cartao-rotativo", "rot_core")
    try:
        r = mod.simular_rotativo(params["fatura"], params["pagamento"], params["taxa_mes"], 12)
    except ValueError as e:
        return pacote(str(e), str(e))
    return mostrar(mod, r, "Custo extra do rotativo", "custo_extra")


_registrar("cartao-rotativo", ["rotativo", "fatura"], [["rotativo"]], [], _extrair_rotativo, _calcular_rotativo)


def _extrair_parc_fatura(texto):
    if not combina(texto, [["parcelar fatura", "parcelamento da fatura", "parcelar a fatura"]]):
        return None
    return ler(texto, [
        C("taxa_mes", ["juros", "taxa"], "pct", True),
        C("n_parcelas", ["vezes", "parcelas"], "vezes", True, solto=True),
        C("fatura", ["fatura", "valor"], "din", True, solto=True),
    ])


def _calcular_parc_fatura(params):
    mod = carregar("cartao-rotativo", "rot_core")
    try:
        r = mod.simular_parcelamento(params["fatura"], int(params["n_parcelas"]), params["taxa_mes"])
    except ValueError as e:
        return pacote(str(e), str(e))
    chave = "prestacao" if "prestacao" in r else "parcela"
    if chave not in r:
        return mostrar(mod, r, "Parcelamento")
    return mostrar(mod, r, "Parcela", chave)


_registrar(
    "cartao-rotativo",
    ["parcelar fatura"],
    [["parcelar"]], [],
    _extrair_parc_fatura, _calcular_parc_fatura,
)


def _extrair_apo_acum(texto):
    if not combina(texto, [["aposent", "independencia financeira"], ["guardo", "aporte", "por mes", "tenho"]], ["quanto preciso", "regra dos 4", "gastar"]):
        return None
    return ler(texto, [
        C("years", ["anos", "ano"], "ano", True, solto=True),
        C("annual_pct", ["ao ano", "anual", "juros", "taxa"], "pct", True),
        C("monthly", ["guardo", "aporte", "por mes"], "din", True),
        C("initial", ["tenho", "ja tenho", "saldo", "reserva"], "din", False, 0.0, solto=True),
    ])


def _calcular_apo_acum(params):
    mod = carregar("simulador-aposentadoria", "apo_core")
    serie = mod.accumulate(params["initial"], params["monthly"], params["annual_pct"], params["years"])
    saldo = serie[-1][1]
    return pacote(
        f"Patrimônio: {_brl(saldo)}",
        f"Em {params['years']} anos, a {params['annual_pct']}% a.a., o saldo chega a {_brl(saldo)}.",
    )


_registrar(
    "simulador-aposentadoria",
    ["aposentadoria", "independencia"],
    [["aposentadoria"]], [],
    _extrair_apo_acum, _calcular_apo_acum,
)


def _extrair_apo_meta(texto):
    if not combina(texto, [["aposent", "independencia financeira"], ["gastar", "retirar", "quanto preciso", "regra dos 4"]], ["guardo", "aporte mensal"]):
        return None
    params = ler(texto, [
        C("withdrawal_rate_pct", ["retirada", "taxa segura"], "pct", False, 4.0),
        C("monthly_expense", ["gastar", "retirar", "por mes", "despesa"], "din", True, solto=True),
    ])
    return params


def _calcular_apo_meta(params):
    mod = carregar("simulador-aposentadoria", "apo_core")
    try:
        alvo = mod.target_wealth(params["monthly_expense"], params["withdrawal_rate_pct"])
    except ValueError as e:
        return pacote(str(e), str(e))
    return pacote(
        f"Patrimônio necessário: {_brl(alvo)}",
        f"Para gastar {_brl(params['monthly_expense'])}/mês com retirada de {params['withdrawal_rate_pct']}%, o alvo é {_brl(alvo)}.",
    )


_registrar(
    "simulador-aposentadoria",
    ["regra dos 4", "quanto preciso aposentar"],
    [["aposentadoria"]], [],
    _extrair_apo_meta, _calcular_apo_meta,
)


def _extrair_pmt_proj(texto):
    if not combina(texto, [["poupanca"], ["meses"]], ["reserva de emerg", "aposent", "quantos meses", "meta"]):
        return None
    return ler(texto, [
        C("meses", ["meses", "mes"], "mes", True, solto=True),
        C("taxa_mes_pct", ["juros", "taxa", "%"], "pct", False, 0.5),
        C("aporte_mes", ["aporte", "por mes", "guardo"], "din", False, 0.0),
        C("saldo_atual", ["saldo", "tenho", "poupanca"], "din", True, solto=True),
    ])


def _calcular_pmt_proj(params):
    mod = carregar("poupanca-meta", "pmt_core")
    try:
        r = mod.projetar(params["saldo_atual"], params["aporte_mes"], params["taxa_mes_pct"], int(params["meses"]))
    except ValueError as e:
        return pacote(str(e), str(e))
    return pacote(f"Saldo final: {_brl(r['saldo_final'])}", mod.formatar_proj(r))


_registrar("poupanca-meta", ["poupanca", "render poupanca"], [["poupanca"]], [], _extrair_pmt_proj, _calcular_pmt_proj)


def _extrair_pmt_meta(texto):
    if not combina(texto, [["poupanca", "juntar"], ["meta", "quantos meses"]], ["reserva de emerg", "aposent"]):
        return None
    return ler(texto, [
        C("meta", ["meta", "juntar", "chegar"], "din", True),
        C("taxa_mes_pct", ["juros", "taxa"], "pct", False, 0.5),
        C("aporte_mes", ["aporte", "por mes", "guardo"], "din", True, solto=True),
        C("saldo_atual", ["saldo", "tenho"], "din", False, 0.0),
    ])


def _calcular_pmt_meta(params):
    mod = carregar("poupanca-meta", "pmt_core")
    try:
        r = mod.meses_para_meta(params["saldo_atual"], params["aporte_mes"], params["taxa_mes_pct"], params["meta"])
    except ValueError as e:
        return pacote(str(e), str(e))
    return pacote(f"Meses até a meta: {r['meses']}", mod.formatar_meta(r))


_registrar("poupanca-meta", ["meta", "juntar", "poupanca"], [["meta"]], [], _extrair_pmt_meta, _calcular_pmt_meta)

ligar(
    "reserva-emergencia",
    ["reserva de emergencia", "colchao"],
    [["reserva de emerg", "reserva emergencia", "colchao"]],
    [],
    "reserva-emergencia", "rsv_core", "projetar",
    [
        C("meses_para_juntar", ["juntar em", "em meses", "prazo"], "mes", False, 12),
        C("reserva_atual", ["tenho", "ja tenho", "atual"], "din", False, 0.0),
        C("meses_alvo", ["meses", "mes"], "mes", True, solto=True),
        C("gasto_mensal", ["gasto", "custo", "despesa"], "din", True, solto=True),
    ],
    "Aporte da reserva", "aporte_mensal",
)

ligar(
    "taxa-maquininha",
    ["maquininha", "taxa da maquininha"],
    [["maquininha"]],
    ["pix"],
    "taxa-maquininha", "maq_core", "calcular",
    [
        C("taxa_parcelado_pct", ["parcelado"], "pct", False, 0.0),
        C("parcelas", ["vezes", "parcelas"], "vezes", False, 1, solto=True),
        C("taxa_fixa", ["fixa"], "din", False, 0.0),
        C("taxa_pct", ["taxa", "debito", "credito"], "pct", True),
        C("valor_venda", ["venda", "valor"], "din", True, solto=True),
    ],
    "Você recebe", "liquido",
)

ligar(
    "taxa-pix-recebimento",
    ["taxa pix", "pix recebimento"],
    [["pix"], ["taxa", "receber", "recebimento"]],
    ["boleto"],
    "taxa-pix-recebimento", "txp_core", "calcular",
    [
        C("taxa_fixa", ["fixa"], "din", False, 0.0),
        C("taxa_pct", ["taxa"], "pct", True),
        C("valor_bruto", ["valor", "receber", "venda"], "din", True, solto=True),
    ],
    "Líquido no Pix", "liquido",
)

ligar(
    "imposto-compra-internacional",
    ["importacao", "remessa conforme", "compra internacional"],
    [["importacao", "remessa conforme", "compra internacional", "imposto de importacao"]],
    ["viagem"],
    "imposto-compra-internacional", "imx_core", "calcular",
    [
        C("cambio", ["cambio", "cotacao"], "num", False, OMITIR),
        C("aliquota_icms", ["icms"], "pct", False, OMITIR),
        C("frete_usd", ["frete"], "din", False, 0.0),
        C("produto_usd", ["produto", "compra", "dolar", "usd"], "din", True, solto=True),
    ],
    "Total em reais", "total_brl",
    preparar=lambda texto, p: {**p, "remessa_conforme": "fora" not in norm(texto) and "sem remessa" not in norm(texto)},
)


def _extrair_cxv(texto):
    if not combina(texto, [["viagem", "iof", "spread"], ["cartao", "dolar", "euro"]]):
        return None
    if combina(texto, [["importacao", "remessa"]]):
        return None
    return ler(texto, [
        C("iof_pct", ["iof"], "pct", False, OMITIR),
        C("spread_pct", ["spread"], "pct", False, 0.0),
        C("cotacao", ["cotacao", "cambio"], "num", True, solto=True),
        C("gasto", ["gastar", "gasto", "dolar", "euro"], "din", True, solto=True),
    ])


def _calcular_cxv(params):
    mod = carregar("cartao-ou-especie-viagem", "cxv_core")
    iof = params["iof_pct"] if "iof_pct" in params else float(getattr(mod, "IOF_PADRAO", 3.5))
    try:
        custo = mod.custo_cartao(params["gasto"], params["cotacao"], params["spread_pct"], iof)
    except ValueError as e:
        return pacote(str(e), str(e))
    return pacote(
        f"No cartão sai {_brl(custo)}",
        f"Gasto de {params['gasto']} x cotação {params['cotacao']} com spread {params['spread_pct']}% e IOF {iof}%: {_brl(custo)}.",
    )


_registrar(
    "cartao-ou-especie-viagem",
    ["cartao viagem", "iof", "spread"],
    [["viagem"]], [],
    _extrair_cxv, _calcular_cxv,
)


def _extrair_troco(texto):
    if not combina(texto, [["troco"]]):
        return None
    params = ler(texto, [
        C("pago", ["paguei", "pago", "dei", "com"], "din", False, OMITIR),
        C("total", ["conta", "total", "foi", "compra"], "din", False, OMITIR),
    ])
    if params is None:
        return None
    if "pago" in params and "total" in params:
        return params
    dins = [tok for tok in tokens(texto) if tok.tipo in ("din", "solto")]
    if len(dins) < 2:
        return None
    # "troco de 100 pra 73,50" = pagou o primeiro, conta é o segundo
    return {"pago": dins[0].valor, "total": dins[1].valor}


def _calcular_troco(params):
    mod = carregar("calculadora-troco", "tro_core")
    try:
        r = mod.calcular_troco(params["total"], params["pago"])
    except ValueError as e:
        return pacote(str(e), str(e))
    texto = mod.formatar(r)
    if r.get("ok"):
        return pacote(f"Troco: {_brl(r['troco'])}", texto)
    return pacote(f"Faltam {_brl(r['faltam'])}", texto)


_registrar("calculadora-troco", ["troco"], [["troco"]], [], _extrair_troco, _calcular_troco)

ligar(
    "calculadora-gorjeta",
    ["gorjeta"],
    [["gorjeta"]],
    ["buffet", "delivery", "entrega", "ifood", "dividir", "rachar"],
    "calculadora-gorjeta", "tg_core", "calcular",
    [
        C("num_pessoas", ["pessoas", "pessoa"], "int", False, 1),
        C("porcentagem_gorjeta", ["gorjeta", "%"], "pct", True),
        C("valor_conta", ["conta", "valor"], "din", True, solto=True),
    ],
    "Total com gorjeta", "total",
)

ligar(
    "gorjeta-buffet",
    ["buffet", "couvert"],
    [["buffet"]],
    [],
    "gorjeta-buffet", "buf_core", "calcular",
    [
        C("gorjeta_pct", ["gorjeta"], "pct", False, 10.0),
        C("couvert", ["couvert"], "din", False, 0.0),
        C("bebidas", ["bebida", "bebidas"], "din", False, 0.0),
        C("pessoas", ["pessoas", "pessoa"], "int", True, solto=True),
        C("preco_buffet", ["buffet", "pessoa", "preco"], "din", True, solto=True),
    ],
    "Total do buffet", "total",
)

ligar(
    "calculadora-taxa-delivery",
    ["delivery", "ifood"],
    [["delivery", "ifood"]],
    ["sedex", "frete"],
    "calculadora-taxa-delivery", "dlv_core", "total_pedido",
    [
        C("gorjeta_pct", ["gorjeta"], "pct", False, 0.0),
        C("cupom_desconto", ["cupom", "desconto"], "din", False, 0.0),
        C("taxa_entrega", ["taxa", "entrega"], "din", False, 0.0),
        C("subtotal", ["pedido", "subtotal", "valor"], "din", True, solto=True),
    ],
    "Total do delivery", "total",
)

ligar(
    "comparador-avista-parcelado",
    ["a vista", "parcelado"],
    [["a vista", "avista"]],
    [],
    "comparador-avista-parcelado", "dav_core", "comparar",
    [
        C("juros_mes_pct", ["juros"], "pct", False, 0.0),
        C("n_parcelas", ["vezes", "parcelas", "x"], "vezes", True, solto=True),
        C("desconto_avista_pct", ["desconto", "a vista", "avista"], "pct", True),
        C("preco_tabela", ["produto", "preco", "valor", "de"], "din", True, solto=True),
    ],
    "Melhor", "melhor", False,
)


_MOEDAS = (
    ("BTC", ("bitcoin", "btc")),
    ("ETH", ("ethereum", "eth")),
    ("USD", ("dolar", "dolares", "usd", "us$")),
    ("EUR", ("euro", "euros", "eur")),
    ("BRL", ("real", "reais", "brl", "r$")),
)


def _moedas_no_texto(texto):
    t = norm(texto)
    achadas = []
    for cod, nomes in _MOEDAS:
        for nome in nomes:
            m = re.search(r"(?<!\w)" + re.escape(nome) + r"(?!\w)", t)
            if m:
                achadas.append((m.start(), cod))
                break
    achadas.sort()
    return achadas


def _extrair_moeda(texto):
    if not combina(texto, [["dolar", "euro", "bitcoin", "ethereum", "btc", "eth", "usd", "eur"]], ["importac", "remessa", "viagem", "iof", "frete", "sedex", "pac", "internacional", "cambio", "compra"]):
        return None
    nums = [tok for tok in tokens(texto) if tok.tipo in ("din", "solto")]
    moedas = _moedas_no_texto(texto)
    if not nums or len(moedas) < 1:
        return None
    valor = nums[0].valor
    if len(moedas) >= 2:
        de, para = moedas[0][1], moedas[1][1]
    else:
        de, para = moedas[0][1], "BRL"
        if de == "BRL":
            return None
    if de == para:
        return None
    return {"valor": valor, "de": de, "para": para}


def _calcular_moeda(params):
    mod = carregar("conversor-moedas", "cm_core")
    try:
        r = mod.converter(params["valor"], params["de"], params["para"])
    except ValueError as e:
        return pacote(str(e), str(e))
    texto = f"{params['valor']} {params['de']} = {mod.formatar(r, params['para'])}"
    return pacote(texto, texto + "\nCotações offline gravadas na ferramenta.")


_registrar(
    "conversor-moedas",
    ["dolar", "euro", "bitcoin", "moeda"],
    [["dolar"]], [],
    _extrair_moeda, _calcular_moeda,
)


def _dois_itens(texto):
    t = norm(texto)
    pedacos = re.split(r"\bcontra\b|\bversus\b|\bvs\b|\bou\b", t, maxsplit=1)
    if len(pedacos) != 2:
        return None
    return pedacos


def _extrair_ppu(texto):
    if not combina(texto, [["preco unitario", "por unidade", "por quilo", "por litro", "mais barato por"]]):
        return None
    pedacos = _dois_itens(texto)
    if not pedacos:
        return None
    itens = []
    for i, ped in enumerate(pedacos, start=1):
        p = ler(ped, [
            C("qtd", ["un", "unidade", "kg", "g", "l", "ml", "com"], "num", True, solto=True),
            C("preco", ["reais", "por", "custa"], "din", True, solto=True),
        ])
        if not p:
            return None
        itens.append((f"opção {i}", p["preco"], p["qtd"]))
    return {"itens": itens}


def _calcular_ppu(params):
    mod = carregar("comparador-preco-unitario", "ppu_core")
    try:
        r = mod.comparar(params["itens"])
    except ValueError as e:
        return pacote(str(e), str(e))
    return pacote(f"Mais barato por unidade: {r['melhor']}", mod.formatar(r))


_registrar(
    "comparador-preco-unitario",
    ["preco unitario", "por quilo", "por litro"],
    [["preco unitario"]], [],
    _extrair_ppu, _calcular_ppu,
)

ligar(
    "comparador-atacado-varejo",
    ["atacado", "varejo"],
    [["atacado"], ["varejo"]],
    [],
    "comparador-atacado-varejo", "atv_core", "comparar",
    [
        C("desperdicio_pct", ["desperdicio", "perda"], "pct", False, 0.0),
        C("qtd_atacado", ["unidades do atacado", "atacado"], "num", True),
        C("preco_atacado", ["atacado"], "din", True),
        C("qtd_varejo", ["unidades do varejo", "varejo"], "num", True),
        C("preco_varejo", ["varejo"], "din", True),
    ],
    "Melhor", "melhor", False,
)

ligar(
    "comparador-generico-marca",
    ["generico", "marca"],
    [["generico"], ["marca"]],
    [],
    "comparador-generico-marca", "gen_core", "comparar",
    [
        C("caixa_comprimidos", ["comprimido", "caixa"], "int", False, 1),
        C("preco_generico", ["generico"], "din", True),
        C("preco_marca", ["marca"], "din", True),
    ],
    "Economia do genérico", "economia",
)

ligar(
    "cartucho-vs-toner",
    ["toner", "cartucho"],
    [["toner"], ["cartucho"]],
    [],
    "cartucho-vs-toner", "tdc_core", "comparar",
    [
        C("paginas_mes", ["por mes", "mes"], "int", True, solto=True),
        C("paginas_toner", ["paginas do toner", "toner"], "int", True),
        C("preco_toner", ["toner"], "din", True),
        C("paginas_cartucho", ["paginas do cartucho", "cartucho"], "int", True),
        C("preco_cartucho", ["cartucho"], "din", True),
    ],
    "Mais barato", "melhor", False,
)

ligar(
    "frete-sedex-vs-pac",
    ["sedex", "pac"],
    [["sedex"], ["pac"]],
    [],
    "frete-sedex-vs-pac", "sdx_core", "comparar",
    [
        C("dias_pac", ["dias pac", "pac"], "dia", True),
        C("preco_pac", ["pac"], "din", True),
        C("dias_sedex", ["dias sedex", "sedex"], "dia", True),
        C("preco_sedex", ["sedex"], "din", True),
    ],
    "Recomendação", "recomendacao", False,
)

ligar(
    "orcamento-festa",
    ["festa", "aniversario"],
    [["festa", "aniversario"]],
    ["casamento"],
    "orcamento-festa", "fan_core", "orcar",
    [
        C("taxa_servico_pct", ["taxa", "servico"], "pct", False, 0.0),
        C("bebida_adulto", ["bebida"], "din", False, 0.0),
        C("comida_crianca", ["comida crianca", "crianca"], "din", False, 0.0),
        C("criancas", ["criancas", "crianca"], "int", False, 0),
        C("comida_adulto", ["comida", "por adulto", "por pessoa"], "din", True),
        C("adultos", ["adultos", "adulto", "pessoas", "convidados"], "int", True, solto=True),
    ],
    "Total da festa", "total",
)

ligar(
    "lance-consorcio",
    ["lance", "consorcio"],
    [["lance"], ["consorcio"]],
    [],
    "lance-consorcio", "csc_core", "calcular",
    [
        C("lance_pct", ["lance"], "pct", True),
        C("meses_restantes", ["meses", "restam", "faltam"], "mes", True, solto=True),
        C("parcela", ["parcela", "prestacao"], "din", True),
        C("credito", ["credito", "carta"], "din", True, solto=True),
    ],
    "Recomendação", "recomendacao", False,
    preparar=lambda texto, p: {**p, "embutido": "embutid" in norm(texto)},
)


def _extrair_amort(texto):
    if not combina(texto, [["amortiz"]]):
        return None
    params = ler(texto, [
        C("monthly_extra", ["amortizacao", "extra", "a mais"], "din", True),
        C("annual_rate_pct", ["juros", "taxa", "ao ano"], "pct", True),
        C("months", ["meses", "mes"], "mes", True, solto=True),
        C("principal", ["financiamento", "saldo", "valor"], "din", True, solto=True),
    ])
    if not params:
        return None
    params["system"] = "PRICE" if "price" in norm(texto) else "SAC"
    return params


def _calcular_amort(params):
    mod = carregar("comparador-credito", "crd_core")
    try:
        r = mod.simulate_loan_with_extra_amort(
            params["principal"], params["annual_rate_pct"], int(params["months"]),
            params["system"], params["monthly_extra"],
        )
    except ValueError as e:
        return pacote(str(e), str(e))
    return mostrar(mod, r, "Juros economizados", "interest_saved")


_registrar(
    "comparador-credito",
    ["amortizacao extra", "amortizar"],
    [["amortizacao"]], [],
    _extrair_amort, _calcular_amort,
)


def _extrair_cons_fin(texto):
    if not combina(texto, [["consorcio"], ["financi"]], ["lance", "amort"]):
        return None
    return ler(texto, [
        C("cons_admin_fee_pct", ["admin", "administracao", "taxa do consorcio"], "pct", True),
        C("fin_annual_rate_pct", ["juros", "taxa do financiamento", "financiamento"], "pct", True),
        C("months", ["meses", "mes"], "mes", True, solto=True),
        C("asset_value", ["bem", "carro", "imovel", "valor", "carta"], "din", True, solto=True),
    ])


def _calcular_cons_fin(params):
    mod = carregar("comparador-credito", "crd_core")
    try:
        r = mod.compare_consorcio_vs_financiamento(
            params["asset_value"], int(params["months"]),
            params["fin_annual_rate_pct"], params["cons_admin_fee_pct"],
        )
    except ValueError as e:
        return pacote(str(e), str(e))
    melhor = "financiamento" if r["financiamento_total"] <= r["consorcio_total"] else "consórcio"
    det = detalhe_de(mod, r)
    return pacote(f"Mais barato: {melhor}", det)


_registrar(
    "comparador-credito",
    ["consorcio ou financiamento"],
    [["consorcio"]], [],
    _extrair_cons_fin, _calcular_cons_fin,
)


def _extrair_alg(texto):
    if not combina(texto, [["alavancagem", "ponto de equilibrio"]]):
        return None
    return ler(texto, [
        C("interest", ["juros"], "din", False, 0.0),
        C("f", ["fixo", "fixos"], "din", True),
        C("v", ["variavel"], "din", True),
        C("p", ["preco"], "din", True),
        C("q", ["quantidade", "qtde", "unidades"], "num", False, OMITIR, solto=True),
    ])


def _calcular_alg(params):
    mod = carregar("calculadora-alavancagem", "alg_core")
    try:
        if "q" not in params:
            r = mod.break_even(params["p"], params["v"], params["f"])
            return mostrar(mod, r, "Quantidade de equilíbrio", "q_star", False)
        r = mod.leverage_report(params["q"], params["p"], params["v"], params["f"], params.get("interest", 0.0))
    except ValueError as e:
        return pacote(str(e), str(e))
    dol = r.get("dol", r.get("operating", {}))
    if isinstance(r.get("operating"), dict):
        dol = r["operating"].get("dol")
    elif "dol" in r:
        dol = r["dol"]
    else:
        dol = None
    texto = detalhe_de(mod, r)
    if isinstance(dol, (int, float)):
        return pacote(f"Alavancagem operacional: {_num(dol, 2)}", texto)
    return mostrar(mod, r, "Alavancagem", moeda=False)


_registrar(
    "calculadora-alavancagem",
    ["alavancagem", "ponto de equilibrio"],
    [["alavancagem"]], [],
    _extrair_alg, _calcular_alg,
)


def _extrair_bsc(texto):
    if not combina(texto, [["black scholes", "black-scholes", "opcao de compra"]]):
        return None
    params = ler(texto, [
        C("sigma_pct", ["vol", "volatilidade"], "pct", True),
        C("r_pct", ["juros", "taxa", "selic"], "pct", True),
        C("t_anos", ["anos", "ano"], "ano", False, OMITIR),
        C("t_dias", ["dias"], "dia", False, OMITIR),
        C("k", ["strike", "exercicio"], "din", True),
        C("s", ["acao", "spot", "ativo", "preco"], "din", True, solto=True),
    ])
    if not params:
        return None
    if "t_anos" not in params and "t_dias" not in params:
        return None
    return params


def _calcular_bsc(params):
    if "t_anos" in params:
        t = params["t_anos"]
    else:
        t = params["t_dias"] / 365.0
    mod = carregar("calculadora-financeira-black-scholes", "bsc_core")
    try:
        r = mod.calculate_black_scholes(params["s"], params["k"], t, params["r_pct"] / 100.0, params["sigma_pct"] / 100.0)
    except ValueError as e:
        return pacote(str(e), str(e))
    return mostrar(mod, r, "Call", "call_price")


_registrar(
    "calculadora-financeira-black-scholes",
    ["black scholes", "opcao", "call"],
    [["black scholes"]], [],
    _extrair_bsc, _calcular_bsc,
)

ligar(
    "simulador-financiamento-estudantil-fies",
    ["fies", "financiamento estudantil"],
    [["fies", "financiamento estudantil"]],
    [],
    "simulador-financiamento-estudantil-fies", "fie_core", "calcular_fies",
    [
        C("percentual_retencao_folha_pct", ["retencao"], "pct", False, OMITIR),
        C("salario_bruto_esperado", ["salario"], "din", False, OMITIR),
        C("taxa_juros_anual_pct", ["juros", "taxa"], "pct", False, 0.0),
        C("duracao_meses", ["meses", "mes"], "mes", True, solto=True),
        C("percentual_financiado_pct", ["financiado", "percentual"], "pct", True),
        C("mensalidade_curso", ["mensalidade", "faculdade"], "din", True, solto=True),
    ],
    "Saldo na formatura", "saldo_devedor_formatura",
    preparar=lambda texto, p: {**p, "duracao_meses": int(round(p["duracao_meses"]))},
)

ligar(
    "simulador-transicao-carreira-reserva",
    ["runway", "transicao de carreira"],
    [["runway", "transicao de carreira", "folego financeiro"]],
    [],
    "simulador-transicao-carreira-reserva", "tcr_core", "simular_transicao_carreira",
    [
        C("renda_transicao_mensal", ["renda", "freelance", "bico"], "din", False, 0.0),
        C("despesa_superflua_mensal", ["superfluo", "lazer"], "din", False, 0.0),
        C("despesa_essencial_mensal", ["essencial", "gasto", "despesa"], "din", True),
        C("reserva_total", ["reserva", "tenho", "guardado"], "din", True, solto=True),
    ],
    "Meses de fôlego", "meses_runway_operacional", False,
)
