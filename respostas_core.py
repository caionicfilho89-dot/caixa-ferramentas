"""respostas_core.py — Motor de respostas da Barra de Busca da Caixa de Ferramentas.

Contrato (RUMO.md):
- respostas_core.responder(texto: str) -> list[dict]
  dicts com: {"titulo", "resposta", "detalhe", "chave_ferramenta", "confianca"}
  confianca de 0.0 a 1.0. Lista vazia = nao entendeu nada.
- Utilitarios pt-BR para adaptadores:
  numero_br(texto), formatar_br(val), extrair_numeros(texto), extrair_data(texto).
- Carrega adaptadores de adp_indice.MODULOS (com fallback para adp_essenciais).
- Se nenhum adaptador entender, busca_reserva consulta catalogo.json + AJUDA.json
  e devolve as ate 5 ferramentas mais parecidas.
"""
from __future__ import annotations

import datetime
import importlib
import json
import os
import re
import sys
import unicodedata
from typing import Any, Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
STAGED = os.path.join(HERE, "staged")
if os.path.isdir(STAGED) and STAGED not in sys.path:
    sys.path.insert(0, STAGED)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


# ======================================================================
# Utilitarios de texto e numeros pt-BR
# ======================================================================

def normalizar_texto(txt: str) -> str:
    """Minusculas e sem acentos para comparacoes flexiveis."""
    if not txt:
        return ""
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return txt.lower().strip()


# Regex para capturar numeros no padrao pt-BR com suporte a "mil" e "milhao/milhoes"
_REGEX_NUM_PTBR = re.compile(
    r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?|\d+(?:\.\d+)?)\s*(milh[oõ]es|milh[aã]o|mil)?\b",
    re.IGNORECASE,
)


def _limpar_str_numero(s_val: str) -> Optional[float]:
    s = s_val.strip()
    if not s:
        return None
    if "," in s and "." in s:
        # Ex: 1.250,50
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # Ex: 73,50
        s = s.replace(",", ".")
    elif "." in s:
        parts = s.split(".")
        # Se sao blocos de 3 digitos apos o ponto (1.000, 50.000), eh milhar
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            s = "".join(parts)
        else:
            # Ex: 1.80 (altura)
            pass
    try:
        return float(s)
    except ValueError:
        return None


def numero_br(texto: str) -> Optional[float]:
    """Extrai o primeiro numero de uma string no padrao pt-BR (ex: '60 mil', '1.250,50', '73,50')."""
    if not texto:
        return None
    m = _REGEX_NUM_PTBR.search(texto)
    if not m:
        return None
    val = _limpar_str_numero(m.group(1))
    if val is None:
        return None
    suffix = (m.group(2) or "").lower()
    if "milh" in suffix:
        val *= 1_000_000.0
    elif "mil" in suffix:
        val *= 1_000.0
    return val


def extrair_numeros(texto: str) -> List[float]:
    """Extrai todos os numeros de uma frase na ordem em que aparecem."""
    if not texto:
        return []
    res: List[float] = []
    for m in _REGEX_NUM_PTBR.finditer(texto):
        val = _limpar_str_numero(m.group(1))
        if val is None:
            continue
        suffix = (m.group(2) or "").lower()
        if "milh" in suffix:
            val *= 1_000_000.0
        elif "mil" in suffix:
            val *= 1_000.0
        res.append(val)
    return res


def formatar_br(val: float, casas: int = 2, prefixo: str = "") -> str:
    """Formata numero no padrao brasileiro (1.234,50)."""
    if val is None:
        return ""
    if casas == 0:
        fmt = f"{int(round(val)):,}".replace(",", ".")
    else:
        fmt = f"{val:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if prefixo:
        return f"{prefixo} {fmt}" if not prefixo.endswith(" ") else f"{prefixo}{fmt}"
    return fmt


def extrair_data(texto: str) -> Optional[datetime.date]:
    """Extrai uma data de termos como 'hoje', 'amanha', 'amanhã' ou 'DD/MM/AAAA'."""
    norm = normalizar_texto(texto)
    hoje = datetime.date.today()
    if "hoje" in norm:
        return hoje
    if "amanha" in norm:
        return hoje + datetime.timedelta(days=1)
    if "ontem" in norm:
        return hoje - datetime.timedelta(days=1)

    # DD/MM/AAAA ou DD/MM/AA ou DD-MM-AAAA
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", texto)
    if m:
        dia = int(m.group(1))
        mes = int(m.group(2))
        ano_str = m.group(3)
        if ano_str:
            ano = int(ano_str)
            if ano < 100:
                ano += 2000
        else:
            ano = hoje.year
        try:
            return datetime.date(ano, mes, dia)
        except ValueError:
            return None
    return None


# ======================================================================
# Catalogo e Busca de Reserva (F3)
# ======================================================================

_CATALOGO_CACHE: Optional[List[Dict[str, Any]]] = None
_AJUDA_CACHE: Optional[Dict[str, Any]] = None


def _carregar_catalogo() -> List[Dict[str, Any]]:
    global _CATALOGO_CACHE
    if _CATALOGO_CACHE is not None:
        return _CATALOGO_CACHE
    caminhos = [
        os.path.join(HERE, "catalogo.json"),
        os.path.join(getattr(sys, "_MEIPASS", HERE), "catalogo.json"),
    ]
    for c in caminhos:
        if os.path.isfile(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    _CATALOGO_CACHE = dados.get("ferramentas", [])
                    return _CATALOGO_CACHE
            except Exception:
                pass
    _CATALOGO_CACHE = []
    return _CATALOGO_CACHE


def _carregar_ajuda() -> Dict[str, Any]:
    global _AJUDA_CACHE
    if _AJUDA_CACHE is not None:
        return _AJUDA_CACHE
    caminhos = [
        os.path.join(HERE, "AJUDA.json"),
        os.path.join(getattr(sys, "_MEIPASS", HERE), "AJUDA.json"),
    ]
    for c in caminhos:
        if os.path.isfile(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    _AJUDA_CACHE = json.load(f)
                    return _AJUDA_CACHE
            except Exception:
                pass
    _AJUDA_CACHE = {}
    return _AJUDA_CACHE


STOPWORDS = {
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
    "um", "uma", "uns", "umas", "o", "a", "os", "as", "e", "ou",
    "se", "so", "por", "pra", "para", "com", "sem", "como", "que",
    "varios", "varias", "mais", "menos"
}

def busca_reserva(texto: str, limite: int = 5) -> List[Dict[str, Any]]:
    """Devolve as ate 5 ferramentas mais parecidas usando catalogo.json + AJUDA.json."""
    if not texto or not texto.strip():
        return []
    termo = normalizar_texto(texto)
    palavras_termo = [w for w in re.split(r"\W+", termo) if len(w) >= 2 and w not in STOPWORDS]
    if not palavras_termo:
        return []

    ferramentas = _carregar_catalogo()
    ajuda = _carregar_ajuda()

    pontuados: List[Tuple[float, Dict[str, Any]]] = []

    for f in ferramentas:
        chave = f.get("chave", "")
        nome = f.get("nome", "")
        desc = f.get("desc", "")
        cat_nome = f.get("categoria", "")

        aj = ajuda.get(chave, {})
        sinopse = aj.get("sinopse", "")
        para_que = aj.get("para_que", "")

        nome_norm = normalizar_texto(nome)
        desc_norm = normalizar_texto(desc)
        sinopse_norm = normalizar_texto(sinopse)
        chave_partes = chave.lower().split("-")

        score = 0.0
        # Match exato do termo inteiro no nome
        if termo in nome_norm:
            score += 35.0
        elif termo in desc_norm:
            score += 20.0
        elif termo in sinopse_norm:
            score += 15.0

        for p in palavras_termo:
            if p in chave_partes:
                score += 20.0
            elif p in chave:
                score += 10.0

            if re.search(rf"\b{re.escape(p)}\b", nome_norm):
                score += 25.0
            elif re.search(rf"\b{re.escape(p)}\b", desc_norm):
                score += 10.0
            elif re.search(rf"\b{re.escape(p)}\b", sinopse_norm):
                score += 8.0

        if score > 0:
            emoji = f.get("emoji", "🔧")
            detalhe = sinopse or desc or f"Categoria: {cat_nome}"
            conf = min(0.65, 0.25 + (score / 50.0) * 0.4)
            card = {
                "titulo": f"{emoji} {nome}",
                "resposta": f"Abrir ferramenta ({nome})",
                "detalhe": detalhe,
                "chave_ferramenta": chave,
                "confianca": round(conf, 2),
            }
            pontuados.append((score, card))

    pontuados.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in pontuados[:limite]]


# ======================================================================
# Carregador de Adaptadores
# ======================================================================

def carregar_adaptadores() -> List[Dict[str, Any]]:
    """Importa modulos de adp_indice.MODULOS e sempre inclui adp_essenciais.
    
    Recarrega adp_indice dinamicamente caso novos modulos sejam registrados
    pelo GrokBuild em tempo de execucao sem precisar reiniciar o processo.
    """
    mod_nomes = ["adp_essenciais"]
    try:
        if "adp_indice" in sys.modules:
            try:
                adp_ind = importlib.reload(sys.modules["adp_indice"])
            except Exception:
                adp_ind = sys.modules["adp_indice"]
        else:
            adp_ind = importlib.import_module("adp_indice")
        if hasattr(adp_ind, "MODULOS"):
            for m in adp_ind.MODULOS:
                if m not in mod_nomes:
                    mod_nomes.append(m)
    except Exception:
        # Se adp_indice nao existir ou tiver erro de sintaxe temporario, segue com adp_essenciais
        pass

    adaptadores: List[Dict[str, Any]] = []
    for mod_nome in mod_nomes:
        try:
            if mod_nome in sys.modules:
                mod = sys.modules[mod_nome]
            else:
                mod = importlib.import_module(mod_nome)
            adps = getattr(mod, "ADAPTADORES", None)
            if isinstance(adps, list):
                adaptadores.extend(adps)
        except Exception:
            # Modulo ainda nao criado ou com erro: nao quebra os outros
            continue

    return adaptadores


# ======================================================================
# Motor Principal de Resposta
# ======================================================================

def responder(texto: str) -> List[Dict[str, Any]]:
    """Processa o texto do usuario e retorna a lista de respostas.

    Formato do retorno:
    list[dict] com:
      - 'titulo': str (ex: 'Calculadora de Troco' ou 'IPVA SP')
      - 'resposta': str (ex: 'R$ 26,50' ou 'R$ 2.400,00')
      - 'detalhe': str (ex: 'Troco de R$ 100,00 para compra de R$ 73,50')
      - 'chave_ferramenta': str (ex: 'calculadora-troco')
      - 'confianca': float (0.0 a 1.0)

    Se nenhum adaptador direto entender a frase, busca_reserva devolve as
    ate 5 ferramentas mais parecidas.
    """
    if not texto or not texto.strip():
        return []

    adaptadores = carregar_adaptadores()
    candidatos: List[Dict[str, Any]] = []

    for adp in adaptadores:
        extrair_fn = adp.get("extrair")
        calcular_fn = adp.get("calcular")
        if not callable(extrair_fn) or not callable(calcular_fn):
            continue

        try:
            params = extrair_fn(texto)
            if params is None or params is False:
                continue

            calc_res = calcular_fn(params)
            if not isinstance(calc_res, dict):
                continue

            confianca = float(calc_res.get("confianca", params.get("_confianca", 0.90)))
            titulo = calc_res.get("titulo") or adp.get("titulo") or adp.get("chave", "")
            resposta = calc_res.get("resposta", "")
            detalhe = calc_res.get("detalhe", "")
            chave = calc_res.get("chave_ferramenta") or adp.get("chave", "")

            if resposta:
                candidatos.append({
                    "titulo": titulo,
                    "resposta": str(resposta),
                    "detalhe": str(detalhe),
                    "chave_ferramenta": chave,
                    "confianca": round(confianca, 2),
                })
        except Exception:
            # Qualquer erro interno em um calculo especifico nao quebra os outros
            continue

    if candidatos:
        candidatos.sort(key=lambda x: x["confianca"], reverse=True)
        return candidatos

    # Se nenhum adaptador direto resolveu, aciona a busca de reserva
    return busca_reserva(texto, limite=5)
