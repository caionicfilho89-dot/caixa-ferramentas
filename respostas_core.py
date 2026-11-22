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
import importlib.abc
import importlib.util
import json
import os
import re
import sys
import unicodedata
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
STAGED = os.path.join(HERE, "staged")
if os.path.isdir(STAGED) and STAGED not in sys.path:
    sys.path.insert(0, STAGED)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class IrmaosFinder(importlib.abc.MetaPathFinder):
    """Fallback para carregar <px>_core diretamente de C:\\Users\\caion\\<chave> se staged/ não existir."""
    _mapa: Optional[Dict[str, str]] = None

    @classmethod
    def _obter_mapa(cls) -> Dict[str, str]:
        if cls._mapa is not None:
            return cls._mapa
        cls._mapa = {}
        ferramentas = _carregar_catalogo()
        parent = os.path.dirname(HERE)
        for f in ferramentas:
            chave = f.get("chave")
            if not chave:
                continue
            pasta = os.path.join(parent, chave)
            if os.path.isdir(pasta):
                try:
                    for arq in os.listdir(pasta):
                        if arq.endswith(".py"):
                            mod_nome = arq[:-3]
                            if mod_nome not in cls._mapa:
                                cls._mapa[mod_nome] = os.path.join(pasta, arq)
                except Exception:
                    pass
        return cls._mapa

    def find_spec(self, fullname, path, target=None):
        if "." in fullname:
            return None
        mapa = self._obter_mapa()
        if fullname in mapa:
            caminho = mapa[fullname]
            if os.path.isfile(caminho):
                return importlib.util.spec_from_file_location(fullname, caminho)
        return None


if not any(isinstance(f, IrmaosFinder) for f in sys.meta_path):
    sys.meta_path.append(IrmaosFinder())


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


# ======================================================================
# Tolerância a Digitação e Abreviações Cotidianas (Proposta 1 / T29)
# ======================================================================

def distancia_edicao_ate_1(s1: str, s2: str) -> bool:
    """Retorna True se a distância de Damerau-Levenshtein entre s1 e s2 for <= 1."""
    n1, n2 = len(s1), len(s2)
    if abs(n1 - n2) > 1:
        return False
    if s1 == s2:
        return True
    # Transposição adjacente (troca de 2 letras vizinhas)
    if n1 == n2:
        for k in range(n1 - 1):
            if s1[k] != s2[k]:
                if s1[k] == s2[k + 1] and s1[k + 1] == s2[k] and s1[k + 2:] == s2[k + 2:]:
                    return True
                break

    # Inserção / Deleção / Substituição
    i = j = diff = 0
    while i < n1 and j < n2:
        if s1[i] != s2[j]:
            diff += 1
            if diff > 1:
                return False
            if n1 > n2:
                i += 1
            elif n2 > n1:
                j += 1
            else:
                i += 1
                j += 1
        else:
            i += 1
            j += 1
    if i < n1 or j < n2:
        diff += (n1 - i) + (n2 - j)
    return diff <= 1


TERMOS_CHAVE_TYPO: Set[str] = {
    # Combustíveis & Veículos
    "gasolina", "etanol", "combustivel", "alcool", "viagem", "pedagio", "distancia",
    "consumo", "quilometros", "quilometragem", "veiculo",
    # Finanças & Pagamentos
    "porcentagem", "desconto", "aumento", "acrescimo", "salario", "liquido",
    "rendimento", "investimento", "poupanca", "reserva", "parcela", "parcelas",
    "financiamento", "emprestimo", "entrada", "compras", "unidades", "imposto",
    "feriado", "feriados", "cotacao", "conversor", "moedas", "dolares", "sobra", "troco",
    # Trabalho
    "trabalho", "horas", "minutos", "segundos", "rescisao", "beneficio",
    # Casa & Medidas
    "metro", "metros", "quadrado", "quadrados", "largura", "comprimento",
    "diametro", "circunferencia", "superficie", "volume", "litros", "gramas",
    "quilogramas", "calorias", "proteinas", "carboidratos", "gorduras",
    # Cálculos & Geral
    "calculadora", "diferenca", "multiplicacao", "divisao", "dividir",
    "proporcao", "metade", "duzia", "quantidade", "quanto",
    "natal", "pascoa", "carnaval", "tiradentes", "independencia", "republica",
    "finados", "trabalhador", "aparecida"
}

PALAVRAS_VALIDAS_TYPO: Set[str] = {
    "quando", "quanto", "quantos", "quanta", "quantas", "custo", "custos",
    "gasto", "gastos", "preco", "precos", "valor", "valores", "total", "totais",
    "saldo", "saldos", "tempo", "meses", "sobre", "entre", "depois", "antes",
    "contra", "minimo", "maximo", "media", "padrao", "compra", "compras",
    "venda", "vendas", "renda", "rendas", "folha", "ferias", "tabela", "diaria"
}

ABREVIACOES_BUSCA: List[Tuple[Any, str]] = [
    (re.compile(r"\bp/(?=\s|\d|$)", re.IGNORECASE), "para "),
    (re.compile(r"\bpra(?=\s|\d|$)", re.IGNORECASE), "para"),
    (re.compile(r"\btd(?=\s|\d|$)", re.IGNORECASE), "tudo"),
    (re.compile(r"\bvc(?=\s|\d|$)", re.IGNORECASE), "voce"),
    (re.compile(r"\bqto(?=\s|\d|$)", re.IGNORECASE), "quanto"),
    (re.compile(r"\bqtde?(?=\s|\d|$)", re.IGNORECASE), "quantidade"),
    (re.compile(r"\bhr\s+extra\b", re.IGNORECASE), "hora extra"),
    (re.compile(r"\bhrs?\s+extras?\b", re.IGNORECASE), "horas extras"),
    (re.compile(r"\bhrs?\b", re.IGNORECASE), "horas"),
    (re.compile(r"\bmin\b", re.IGNORECASE), "minutos"),
    (re.compile(r"\bseg\b", re.IGNORECASE), "segundos"),
    (re.compile(r"\bdesc\b", re.IGNORECASE), "desconto"),
    (re.compile(r"\bdescto\b", re.IGNORECASE), "desconto"),
    (re.compile(r"\bparc\b", re.IGNORECASE), "parcela"),
    (re.compile(r"\bparcs\b", re.IGNORECASE), "parcelas"),
    (re.compile(r"\bgasol\b", re.IGNORECASE), "gasolina"),
    (re.compile(r"\betan\b", re.IGNORECASE), "etanol"),
    (re.compile(r"\bcomb\b", re.IGNORECASE), "combustivel"),
    (re.compile(r"\bsal\b", re.IGNORECASE), "salario"),
    (re.compile(r"\bliq\b", re.IGNORECASE), "liquido"),
    (re.compile(r"\bbrut\b", re.IGNORECASE), "bruto"),
    (re.compile(r"\bcalc\b", re.IGNORECASE), "calculadora"),
    (re.compile(r"\bdif\b", re.IGNORECASE), "diferenca"),
    (re.compile(r"\bmult\b", re.IGNORECASE), "multiplicacao"),
    (re.compile(r"\bdiv\b", re.IGNORECASE), "divisao"),
    (re.compile(r"\bvel\b", re.IGNORECASE), "velocidade"),
    (re.compile(r"\bdist\b", re.IGNORECASE), "distancia"),
    (re.compile(r"\bpct\b", re.IGNORECASE), "por cento"),
]


def normalizar_consulta_typos(texto: str) -> str:
    """Normaliza abreviações comuns e erros de digitação leves (distância <= 1)."""
    if not texto:
        return ""
    res = texto
    for padrao, subst in ABREVIACOES_BUSCA:
        res = padrao.sub(subst, res)

    def repl(m: Any) -> str:
        w = m.group(0)
        wn = normalizar_texto(w)
        if len(wn) >= 5 and wn not in TERMOS_CHAVE_TYPO and wn not in PALAVRAS_VALIDAS_TYPO:
            for t in TERMOS_CHAVE_TYPO:
                if distancia_edicao_ate_1(wn, t):
                    return t
        return w

    return re.sub(r"[a-zA-ZÀ-ÿ]+", repl, res)


# Regex para capturar numeros no padrao pt-BR com suporte a "mil" e "milhao/milhoes"
_REGEX_NUM_PTBR = re.compile(
    r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)|\d+)\s*(milh[oõ]es|milh[aã]o|mil)?(?:\b|(?=[a-zA-Z]))",
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

    try:
        from caixa_arquivo import esta_arquivada
    except Exception:
        def esta_arquivada(k: str | None) -> bool:
            return False

    ferramentas = _carregar_catalogo()
    ajuda = _carregar_ajuda()

    pontuados: List[Tuple[float, Dict[str, Any]]] = []

    for f in ferramentas:
        chave = f.get("chave", "")
        nome = f.get("nome", "")
        nome_norm = normalizar_texto(nome)

        # T67: ferramentas arquivadas (inuteis/nicho) ficam fora das sugestoes padrao da barra,
        # a menos que o usuario busque exatamente pelo nome ou chave da ferramenta
        if esta_arquivada(chave) and termo != chave and termo != nome_norm:
            continue

        desc = f.get("desc", "")
        cat_nome = f.get("categoria", "")

        aj = ajuda.get(chave, {})
        sinopse = aj.get("sinopse", "")
        para_que = aj.get("para_que", "")

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
# Limpeza e Pós-processamento pt-BR (F6 & F7)
# ======================================================================

def _eh_tautologica(resposta: str) -> bool:
    """Detecta respostas tautológicas inuteis onde lado esquerdo == lado direito (ex: '1 mês = 1 mês')."""
    if not resposta:
        return True
    if "=" in resposta:
        partes = resposta.split("=")
        if len(partes) == 2:
            e, d = partes[0].strip(), partes[1].strip()
            # Remove textos explicativos entre parenteses (ex: '(30,44 dias)')
            e_limpo = re.sub(r"\(.*?\)", "", e).strip()
            d_limpo = re.sub(r"\(.*?\)", "", d).strip()
            # Se normalizados forem identicos, eh tautologia
            if normalizar_texto(e_limpo) == normalizar_texto(d_limpo):
                return True
            # Se tokens normalizados forem identicos
            e_toks = normalizar_texto(e_limpo).split()
            d_toks = normalizar_texto(d_limpo).split()
            if e_toks and d_toks and e_toks == d_toks:
                return True
    return False


_RE_NUM_PONTO = re.compile(r"(?<![0-9/A-Za-z_.])(\d+(?:\.\d+)+)(?![0-9/A-Za-z_.])")


def formatar_texto_ptbr(texto: str) -> str:
    """Pós-processamento central para formatar números e floats em pt-BR.

    Converte floats crus (ex: 37.199999999999996 -> 37,20; 285.2 -> 285,20; 26.50 -> 26,50)
    sem quebrar números já no padrão pt-BR (1.030,30; 60.000), versões (1.5.1) ou IPs (192.168.1.1).
    """
    if not texto:
        return ""

    def replacer(match: re.Match) -> str:
        num_str = match.group(1)

        # Ignora se tem múltiplos pontos (versão 1.5.0, IP 192.168.1.1, etc.)
        if num_str.count(".") != 1:
            return num_str

        inteiro, decimal = num_str.split(".")

        # Se for milhar pt-BR puro: 1 a 3 dígitos antes do ponto, e exatamente 3 depois
        # Ex: 1.320, 2.400, 60.000, 4.096, 5.000
        # Exceção: 0.xxx é sempre decimal (0,123)
        if len(decimal) == 3 and inteiro != "0" and len(inteiro) <= 3:
            return num_str

        # Se logo após o número vier vírgula decimal (ex: parte inteira de 1.030,30)
        pos_fim = match.end()
        if pos_fim < len(texto) and texto[pos_fim] == ",":
            return num_str

        try:
            val = float(num_str)
        except ValueError:
            return num_str

        idx = match.start()
        trecho_prox = texto[max(0, idx - 40):min(len(texto), idx + 40)].lower()
        eh_dinheiro = any(
            k in trecho_prox
            for k in [
                "r$", "valor", "conta", "total", "gorjeta", "troco", "saldo",
                "preco", "preço", "pago", "frete", "salario", "salário",
                "juros", "parcela", "custo", "desconto", "aumento", "compra",
                "taxa", "tarifa", "boleto", "subtotal", "reais", "multa",
                "mensalidade", "dividendo", "rendimento", "aluguel", "venda",
                "orçamento", "orcamento", "divida", "dívida", "crédito", "credito"
            ]
        )

        val_round2 = round(val, 2)

        if len(decimal) >= 3:
            # Imprecisão de float cru (ex: 37.199999999999996 -> 37,20)
            fmt = f"{val_round2:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        elif eh_dinheiro or len(decimal) == 2:
            # Valores monetários ou decimais com 2 casas (ex: 285.2 -> 285,20; 26.50 -> 26,50; 220.00 -> 220,00)
            fmt = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            # 1 casa decimal geral (ex: 1.5 -> 1,5; 14.4 -> 14,4)
            s = f"{val:.4f}".rstrip("0").rstrip(".")
            p_int, p_dec = s.split(".") if "." in s else (s, "")
            p_int_fmt = f"{int(p_int):,}".replace(",", ".")
            fmt = f"{p_int_fmt},{p_dec}" if p_dec else p_int_fmt

        return fmt

    return _RE_NUM_PONTO.sub(replacer, texto)


# ======================================================================
# Motor Principal de Resposta
# ======================================================================

def _executar_adaptadores(txt: str, adaptadores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidatos: List[Dict[str, Any]] = []
    for adp in adaptadores:
        extrair_fn = adp.get("extrair")
        calcular_fn = adp.get("calcular")
        if not callable(extrair_fn) or not callable(calcular_fn):
            continue

        try:
            params = extrair_fn(txt)
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
    return candidatos


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
    candidatos = _executar_adaptadores(texto, adaptadores)

    # Tolerância a digitação (Proposta 1 / T29): se nenhum adaptador direto respondeu com alta confiança
    texto_norm = normalizar_consulta_typos(texto)
    if not any(c.get("confianca", 0) >= 0.85 for c in candidatos) and texto_norm != texto:
        cands_norm = _executar_adaptadores(texto_norm, adaptadores)
        if cands_norm:
            for cn in cands_norm:
                cn["confianca"] = max(0.90, round(cn["confianca"], 2))
            candidatos.extend(cands_norm)

    candidatos_validos: List[Dict[str, Any]] = []
    for c in candidatos:
        # F6: Limpeza de cartas tautológicas (ex: 1 mes = 1 mes)
        if _eh_tautologica(c.get("resposta", "")):
            continue

        # F6: Formatação central de resposta e detalhe em pt-BR (elimina float cru)
        c["resposta"] = formatar_texto_ptbr(c.get("resposta", ""))
        c["detalhe"] = formatar_texto_ptbr(c.get("detalhe", ""))

        candidatos_validos.append(c)

    if candidatos_validos:
        candidatos_validos.sort(key=lambda x: x["confianca"], reverse=True)

        # F7: Se a 1ª tiver confiança >= 0.8, carta com confiança < 0.35 não aparece
        top_conf = candidatos_validos[0]["confianca"]
        if top_conf >= 0.80:
            candidatos_validos = [c for c in candidatos_validos if c["confianca"] >= 0.35]

        # Deduplicação de cartas da mesma ferramenta (mantém a de maior confiança)
        vistos_chave: set = set()
        dedup: List[Dict[str, Any]] = []
        for c in candidatos_validos:
            ch = c.get("chave_ferramenta", "")
            if ch:
                if ch in vistos_chave:
                    continue
                vistos_chave.add(ch)
            dedup.append(c)

        # F7: No máximo 3 cartas
        return dedup[:3]

    # Se nenhum adaptador direto resolveu, aciona a busca de reserva
    res_busca = busca_reserva(texto, limite=5)
    if not res_busca and texto_norm != texto:
        res_busca = busca_reserva(texto_norm, limite=5)
    return res_busca
