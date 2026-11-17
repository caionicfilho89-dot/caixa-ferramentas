"""Catálogo enxuto — ferramentas na categoria 📦 Arquivo (T23).

Não apaga nada: só saem da grade padrão ("Tudo") e não entram como atalho
da Hoje. Continuam acháveis pela barra e pela lateral 📦 Arquivo.

GrokBuild: em caixa.pyw use:
  from caixa_arquivo import (
      CAT_ARQUIVO, categoria_efetiva, filtrar_grade_padrao,
      tools_arquivo, esta_arquivada, proteger_atalhos,
  )
  - categoria_de → categoria_efetiva (ou: se esta_arquivada(t[3]): CAT_ARQUIVO)
  - em rebuild "__all__": rest = filtrar_grade_padrao(rest)
  - lateral: incluir CAT_ARQUIVO em CAT_ORDEM (no fim) + CAT_CORES
  - busca na grade (q): NÃO filtrar — achar rápido continua prioridade
  - barra (caixa_busca_ui): NÃO filtrar
"""
from __future__ import annotations

import json
import os
from typing import Iterable

HERE = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_JSON = os.path.join(HERE, "arquivo_chaves.json")

CAT_ARQUIVO = "📦 Arquivo"
COR_ARQUIVO = "#6b7280"

# Semente conservadora (0 usos no config do Caio + nicho acadêmico/engenheiro).
# Cocaino (T17/T24) amplia via arquivo_chaves.json — não editar BUILTIN.
_SEMENTE = (
    "simulador-gravitacional-n-corpos",
    "simulador-automato-celular",
    "calculadora-quaternions",
    "laboratorio-filtros-digitais",
    "calculadora-redes-neurais-mlp",
    "estudio-criptografia-feistel-des",
    "analisador-perfil-aerodinamico-naca",
    "calculadora-cinetica-quimica",
    "calculadora-dinamica-orbital-hohmann",
    "gerador-analisador-codigo-hdlc-crc16",
    "calculadora-tensao-cisalhamento-mohr",
    "simulador-modulacao-am-fm",
    "calculadora-flambagem-colunas-euler",
    "analisador-circuito-ressonante-lc",
    "calculadora-dilatacao-termica-tensao",
    "filtro-bloom",
    "calculadora-estatistica-bayesiana",
    "estudio-compressao-huffman",
    "simulador-monte-carlo",
    "laboratorio-crc",
    "teoria-filas",
    "analisador-benford",
    "calculadora-combinatoria",
    "simulador-logica",
    "arvore-decisao",
    "estudio-grafos",
    "calculadora-matrizes",
    "simulador-pendulo-duplo",
    "simulador-epidemias",
    "visualizador-ordenacao",
    "laboratorio-dna",
    "planetario",
)

# Nunca arquivar o que o Caio já usa / atalhos vivos da Hoje (CRITICA T18)
_PROTEGIDAS = frozenset({
    "financas",
    "faxina-disco",
    "calculadora-engrenagens",
    "conversor-imagens",
    "organizador-downloads",
    "calculadora-troco",
    "inspetor-executavel",
    "print-anotador",
    "area-transferencia",
    "auditoria-pc",
    "notas-de-voz",
    "tocando-agora",
    "controle-gastos",
    "canivete",
    "kit-pdf",
    "dias-uteis-pagamento",
    "info-pc",
    "conversor-unidades",
    "calculadora-ipva",
    "calculadora-botijao-gas",
    "calculadora-rendimento-tinta",
    "controle-garantias",
    "controle-validade-remedios",
    "controle-assinaturas",
    "calculadora-rescisao-trabalhista",
    "calculadora-seguro-desemprego",
    "calculadora-subrede",
})


def _carregar_extras() -> set[str]:
    if not os.path.isfile(ARQUIVO_JSON):
        return set()
    try:
        with open(ARQUIVO_JSON, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return set()
    if isinstance(data, dict):
        data = data.get("chaves") or data.get("arquivo") or []
    if not isinstance(data, list):
        return set()
    return {str(c).strip() for c in data if str(c).strip()}


def chaves_arquivo() -> frozenset[str]:
    """União semente + JSON, menos protegidas."""
    bruto = set(_SEMENTE) | _carregar_extras()
    return frozenset(c for c in bruto if c not in _PROTEGIDAS)


def esta_arquivada(chave: str | None) -> bool:
    if not chave:
        return False
    return str(chave) in chaves_arquivo()


def categoria_efetiva(chave: str, categoria_normal: str) -> str:
    """Se arquivada, vira 📦 Arquivo; senão mantém a categoria automática."""
    return CAT_ARQUIVO if esta_arquivada(chave) else categoria_normal


def filtrar_grade_padrao(tools: Iterable) -> list:
    """Remove arquivadas da visão Tudo / categorias normais.

    Aceita tuplas BUILTIN (emoji, nome, desc, pasta, script) ou dicts com chave.
    """
    out = []
    for t in tools:
        if isinstance(t, dict):
            chave = t.get("chave") or t.get("chave_ferramenta") or t.get("id")
        elif isinstance(t, (tuple, list)) and len(t) >= 4:
            chave = t[3]
        else:
            out.append(t)
            continue
        if not esta_arquivada(chave):
            out.append(t)
    return out


def tools_arquivo(tools: Iterable) -> list:
    """Só as arquivadas (pra lateral 📦 Arquivo)."""
    out = []
    for t in tools:
        if isinstance(t, dict):
            chave = t.get("chave") or t.get("chave_ferramenta") or t.get("id")
        elif isinstance(t, (tuple, list)) and len(t) >= 4:
            chave = t[3]
        else:
            continue
        if esta_arquivada(chave):
            out.append(t)
    return out


def proteger_atalhos(chaves: Iterable[str]) -> list[str]:
    """Atalhos da Hoje: tira arquivadas (não devem aparecer como 1–8)."""
    return [c for c in chaves if c and not esta_arquivada(c)]


def salvar_extras(chaves: Iterable[str]) -> str:
    """Persiste lista extra (Cocaino T17/T24). Une com o JSON atual; protegidas fora."""
    novas = {str(c).strip() for c in chaves if str(c).strip()}
    limpas = sorted((novas | _carregar_extras()) - _PROTEGIDAS)
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump({"chaves": limpas, "fonte": "CRITICA T17/T24"}, f, ensure_ascii=False, indent=2)
    return ARQUIVO_JSON
