"""sensores_core.py — Sensores de dados reais do sistema para a Tela Hoje.

Contrato (RUMO.md):
- sensores_core.ler_tudo() -> list[dict]
  dicts com:
  {"id", "emoji", "titulo", "valor", "detalhe", "acao": {"rotulo", "chave_ferramenta" ou "comando"}}
- Só sensor com dado real, em menos de 1 s.
- Cache com TTL de 5s para chamadas repetidas.
- F4: Disco, Downloads e Prints Recentes.
- F5: Vencimentos, Área de Transferência e Pudim IPTV.
- T06: Crescimento de pastas (7 dias) com cache em disco 6 h.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import datetime
import json
import os
import re
import shutil
import socket
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

CACHE_TTL_SEGUNDOS = 5.0
_CACHE_DADOS: Optional[List[Dict[str, Any]]] = None
_CACHE_TEMPO: float = 0.0


# ======================================================================
# Utilitários de Formatação
# ======================================================================

def _formatar_tamanho_bytes(num_bytes: int) -> str:
    """Formata bytes em B, KB, MB, GB com vírgula pt-BR."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 ** 2:
        val = num_bytes / 1024
        return f"{val:.1f}".replace(".", ",") + " KB"
    elif num_bytes < 1024 ** 3:
        val = num_bytes / (1024 ** 2)
        return f"{val:.1f}".replace(".", ",") + " MB"
    else:
        val = num_bytes / (1024 ** 3)
        return f"{val:.1f}".replace(".", ",") + " GB"


def _tempo_relativo(ts_epoch: float) -> str:
    """Devolve string amigavel como 'há 5 min', 'hoje às 14:30', 'ontem'."""
    agora = datetime.datetime.now()
    dt = datetime.datetime.fromtimestamp(ts_epoch)
    delta = agora - dt
    segundos = int(delta.total_seconds())

    if segundos < 60:
        return "agora mesmo"
    elif segundos < 3600:
        mins = segundos // 60
        return f"há {mins} min"
    elif segundos < 86400 and dt.date() == agora.date():
        horas = segundos // 3600
        return f"há {horas} h"
    elif dt.date() == (agora.date() - datetime.timedelta(days=1)):
        return f"ontem às {dt.strftime('%H:%M')}"
    else:
        return dt.strftime("%d/%m/%Y")


# ======================================================================
# F4: Sensores de Disco, Downloads e Prints Recentes
# ======================================================================

def _obter_tamanho_temp() -> int:
    """Calcula rapidamente o tamanho dos arquivos na pasta temporária do usuário."""
    temp_dir = os.environ.get("TEMP")
    total = 0
    if temp_dir and os.path.isdir(temp_dir):
        try:
            with os.scandir(temp_dir) as it:
                for entry in it:
                    try:
                        if entry.is_file():
                            total += entry.stat().st_size
                    except OSError:
                        pass
        except OSError:
            pass
    return total


def sensor_disco() -> Optional[Dict[str, Any]]:
    """Lê o espaço livre e total do disco do sistema (C:)."""
    try:
        drive = "C:\\" if os.name == "nt" else "/"
        du = shutil.disk_usage(drive)
        livre_gb = du.free / (1024 ** 3)
        total_gb = du.total / (1024 ** 3)
        usado_pct = (du.used / du.total) * 100.0

        temp_bytes = _obter_tamanho_temp()
        if temp_bytes > 50 * (1024 ** 2):
            detalhe = f"Total de {total_gb:.0f} GB — pasta Temp tem {_formatar_tamanho_bytes(temp_bytes)} para liberar"
        else:
            detalhe = f"Total de {total_gb:.0f} GB — liberar espaço em temporários e cache"

        livre_gb_str = f"{livre_gb:.1f}".replace(".", ",")
        return {
            "id": "disco",
            "emoji": "💾",
            "titulo": "Disco C:",
            "valor": f"{livre_gb_str} GB livres ({usado_pct:.0f}% usado)",
            "detalhe": detalhe,
            "acao": {
                "rotulo": "Liberar espaço",
                "chave_ferramenta": "faxina-disco",
            },
        }
    except Exception:
        return None


def sensor_downloads() -> Optional[Dict[str, Any]]:
    """Verifica arquivos soltos na pasta de Downloads do usuário."""
    try:
        caminho_dl = os.path.expanduser("~/Downloads")
        if not os.path.isdir(caminho_dl):
            return None

        qtd_arquivos = 0
        total_bytes = 0
        qtd_instaladores = 0
        qtd_duplicados = 0

        exts_instalador = {".exe", ".msi", ".zip", ".rar", ".7z", ".iso", ".tar", ".gz"}
        regex_dup = re.compile(r"\s*\(\d+\)\.[a-zA-Z0-9]+$")

        with os.scandir(caminho_dl) as it:
            for entry in it:
                if entry.is_file():
                    qtd_arquivos += 1
                    if regex_dup.search(entry.name):
                        qtd_duplicados += 1
                    try:
                        st = entry.stat()
                        total_bytes += st.st_size
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext in exts_instalador:
                            qtd_instaladores += 1
                    except OSError:
                        pass

        if qtd_arquivos == 0:
            return None

        tam_str = _formatar_tamanho_bytes(total_bytes)
        partes_detalhe = []
        if qtd_duplicados > 0:
            partes_detalhe.append(f"{qtd_duplicados} cópia(s) duplicada(s)")
        if qtd_instaladores > 0:
            partes_detalhe.append(f"{qtd_instaladores} instalador(es) velho(s)")

        if partes_detalhe:
            detalhe = " e ".join(partes_detalhe) + " para arrumar"
        else:
            detalhe = "Arquivos soltos prontos para catalogar"

        return {
            "id": "downloads",
            "emoji": "📥",
            "titulo": "Downloads",
            "valor": f"{qtd_arquivos} arquivos soltos ({tam_str})",
            "detalhe": detalhe,
            "acao": {
                "rotulo": "Organizar",
                "chave_ferramenta": "organizador-downloads",
            },
        }
    except Exception:
        return None


def sensor_prints_recentes() -> Optional[Dict[str, Any]]:
    """Procura capturas de tela recentes nas pastas padrão do Windows."""
    try:
        candidatos = [
            os.path.expanduser("~/Pictures/Screenshots"),
            os.path.expanduser("~/Imagens/Capturas de Tela"),
            os.path.expanduser("~/OneDrive/Imagens/Capturas de Tela"),
            os.path.expanduser("~/Pictures/Capturas de Tela"),
        ]

        prints_encontrados: List[Tuple[float, str, str]] = []

        exts_imagem = {".png", ".jpg", ".jpeg", ".bmp"}

        for pasta in candidatos:
            if not os.path.isdir(pasta):
                continue
            try:
                with os.scandir(pasta) as it:
                    for entry in it:
                        if entry.is_file():
                            ext = os.path.splitext(entry.name)[1].lower()
                            if ext in exts_imagem:
                                try:
                                    mtime = entry.stat().st_mtime
                                    prints_encontrados.append((mtime, entry.name, entry.path))
                                except OSError:
                                    pass
            except OSError:
                pass

        if not prints_encontrados:
            return None

        prints_encontrados.sort(key=lambda x: x[0], reverse=True)
        total = len(prints_encontrados)
        mtime_mais_recente, nome_mais_recente, path_recente = prints_encontrados[0]
        tempo_str = _tempo_relativo(mtime_mais_recente)

        return {
            "id": "prints",
            "emoji": "🖼️",
            "titulo": "Prints Recentes",
            "valor": f"{total} captura(s) salva(s)",
            "detalhe": f"Última: {nome_mais_recente} ({tempo_str})",
            "acao": {
                "rotulo": "Anotar / OCR",
                "chave_ferramenta": "print-anotador",
            },
        }
    except Exception:
        return None


# ======================================================================
# F5: Sensores de Pudim IPTV, Área de Transferência e Vencimentos
# ======================================================================

def sensor_pudim() -> Optional[Dict[str, Any]]:
    """Lê configuração do Pudim IPTV para o 'Continuar Assistindo'."""
    try:
        caminho_cfg = os.path.expandvars(r"%LOCALAPPDATA%\Programs\IPTV Player\player_config.json")
        if not os.path.isfile(caminho_cfg):
            return None

        with open(caminho_cfg, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        recents = cfg.get("recents", [])
        if not recents or not isinstance(recents, list):
            return None

        ultimo = recents[0]
        if not isinstance(ultimo, dict):
            return None

        nome = ultimo.get("name") or "Canal / Filme"
        grupo = ultimo.get("group") or ""
        detalhe = f"Continuar assistindo ({grupo})" if grupo else "Continuar assistindo no PudimFlix"

        return {
            "id": "pudim",
            "emoji": "🍮",
            "titulo": "Pudim IPTV",
            "valor": nome,
            "detalhe": detalhe,
            "acao": {
                "rotulo": "Assistir",
                "chave_ferramenta": "iptv-player",
            },
        }
    except Exception:
        return None


def _ler_clipboard_windows() -> Optional[str]:
    """Le texto puro da area de transferencia do Windows usando ctypes com tipos explicitos."""
    if os.name != "nt":
        return None
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = wintypes.BOOL
        user32.GetClipboardData.argtypes = [wintypes.UINT]
        user32.GetClipboardData.restype = wintypes.HANDLE
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = ctypes.c_wchar_p
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL

        if not user32.OpenClipboard(None):
            return None
        try:
            CF_UNICODETEXT = 13
            h = user32.GetClipboardData(CF_UNICODETEXT)
            if not h:
                return None
            txt = kernel32.GlobalLock(h)
            kernel32.GlobalUnlock(h)
            return str(txt) if txt else None
        finally:
            user32.CloseClipboard()
    except Exception:
        return None


def sensor_clipboard() -> Optional[Dict[str, Any]]:
    """Mostra o que está copiado na Área de Transferência com identificação de tipo."""
    try:
        texto = _ler_clipboard_windows()
        if not texto or not texto.strip():
            return None

        texto_limpo = texto.strip()
        uma_linha = texto_limpo.replace("\r", " ").replace("\n", " ")

        if texto_limpo.startswith(("http://", "https://", "www.")):
            valor = f"Link: {texto_limpo[:36]}…" if len(texto_limpo) > 36 else f"Link: {texto_limpo}"
            detalhe = "Link copiado — abrir ou analisar"
        elif re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", texto_limpo):
            valor = f"E-mail: {texto_limpo[:36]}"
            detalhe = "Endereço de e-mail na área de transferência"
        elif "\n" in texto_limpo or "\r" in texto_limpo:
            linhas = [l for l in texto_limpo.splitlines() if l.strip()]
            preview = linhas[0][:36] + "…" if len(linhas[0]) > 36 else linhas[0]
            preview = preview.strip("\"'")
            valor = f'"{preview}"'
            detalhe = f"{len(linhas)} linhas ({len(texto)} caracteres) copiadas"
        else:
            if len(uma_linha) > 42:
                preview = uma_linha[:39] + "…"
            else:
                preview = uma_linha
            preview = preview.strip("\"'")
            valor = f'"{preview}"'
            detalhe = f"{len(texto)} caracteres prontos para colar"

        return {
            "id": "clipboard",
            "emoji": "📋",
            "titulo": "Área de Transferência",
            "valor": valor,
            "detalhe": detalhe,
            "acao": {
                "rotulo": "Histórico",
                "chave_ferramenta": "area-transferencia",
            },
        }
    except Exception:
        return None


def sensor_vencimentos() -> Optional[Dict[str, Any]]:
    """Verifica garantias, remédios, cosméticos ou assinaturas com vencimento próximo."""
    try:
        home = os.path.expanduser("~")
        hoje = datetime.date.today()
        proximos: List[Tuple[int, str, str]] = []  # (dias_restantes, nome, chave)

        # 1. Garantias (~/.caixa_garantias.json)
        arq_gar = os.path.join(home, ".caixa_garantias.json")
        if os.path.isfile(arq_gar):
            try:
                dados = json.loads(open(arq_gar, encoding="utf-8").read())
                itens = dados if isinstance(dados, list) else dados.get("itens", [])
                for item in itens:
                    # fim format YYYY-MM-DD
                    fim_str = item.get("fim")
                    if fim_str:
                        dt = datetime.datetime.strptime(fim_str[:10], "%Y-%m-%d").date()
                        dias = (dt - hoje).days
                        if 0 <= dias <= 30:
                            proximos.append((dias, f"Garantia: {item.get('produto', 'Item')}", "controle-garantias"))
            except Exception:
                pass

        # 2. Remédios (~/.caixa_remedios.json)
        arq_rmd = os.path.join(home, ".caixa_remedios.json")
        if os.path.isfile(arq_rmd):
            try:
                dados = json.loads(open(arq_rmd, encoding="utf-8").read())
                itens = dados if isinstance(dados, list) else dados.get("itens", [])
                for item in itens:
                    val_str = item.get("validade")
                    if val_str:
                        dt = datetime.datetime.strptime(val_str[:10], "%Y-%m-%d").date()
                        dias = (dt - hoje).days
                        if 0 <= dias <= 30:
                            proximos.append((dias, f"Remédio: {item.get('nome', 'Medicamento')}", "controle-validade-remedios"))
            except Exception:
                pass

        # 3. Cosméticos (~/.caixa_cosmeticos.json)
        arq_csm = os.path.join(home, ".caixa_cosmeticos.json")
        if os.path.isfile(arq_csm):
            try:
                dados = json.loads(open(arq_csm, encoding="utf-8").read())
                itens = dados if isinstance(dados, list) else dados.get("itens", [])
                for item in itens:
                    val_str = item.get("validade_impressa") or item.get("validade")
                    if val_str:
                        dt = datetime.datetime.strptime(val_str[:10], "%Y-%m-%d").date()
                        dias = (dt - hoje).days
                        if 0 <= dias <= 30:
                            proximos.append((dias, f"Cosmético: {item.get('nome', 'Cosmético')}", "controle-validade-cosmeticos"))
            except Exception:
                pass

        # 4. Contas Fixas (~/.caixa_contas_fixas.json)
        arq_cfx = os.path.join(home, ".caixa_contas_fixas.json")
        if os.path.isfile(arq_cfx):
            try:
                dados = json.loads(open(arq_cfx, encoding="utf-8").read())
                itens = dados if isinstance(dados, list) else dados.get("itens", [])
                for item in itens:
                    dia = item.get("dia_vencimento") or item.get("dia")
                    if dia:
                        dia = int(dia)
                        import calendar
                        dmax = calendar.monthrange(hoje.year, hoje.month)[1]
                        venc = datetime.date(hoje.year, hoje.month, min(dia, dmax))
                        if venc < hoje:
                            m = hoje.month + 1
                            y = hoje.year + (1 if m == 13 else 0)
                            m = 1 if m == 13 else m
                            dmax = calendar.monthrange(y, m)[1]
                            venc = datetime.date(y, m, min(dia, dmax))
                        dias = (venc - hoje).days
                        if 0 <= dias <= 30:
                            proximos.append((dias, f"Conta: {item.get('nome', 'Conta')}", "controle-contas-fixas"))
            except Exception:
                pass

        # 5. Assinaturas (~/.caixa_assinaturas.json)
        arq_ass = os.path.join(home, ".caixa_assinaturas.json")
        if os.path.isfile(arq_ass):
            try:
                dados = json.loads(open(arq_ass, encoding="utf-8").read())
                itens = dados if isinstance(dados, list) else dados.get("itens", [])
                for item in itens:
                    dia = item.get("dia_renovacao") or item.get("dia") or item.get("dia_vencimento")
                    if dia:
                        dia = int(dia)
                        import calendar
                        dmax = calendar.monthrange(hoje.year, hoje.month)[1]
                        venc = datetime.date(hoje.year, hoje.month, min(dia, dmax))
                        if venc < hoje:
                            m = hoje.month + 1
                            y = hoje.year + (1 if m == 13 else 0)
                            m = 1 if m == 13 else m
                            dmax = calendar.monthrange(y, m)[1]
                            venc = datetime.date(y, m, min(dia, dmax))
                        dias = (venc - hoje).days
                        if 0 <= dias <= 30:
                            proximos.append((dias, f"Assinatura: {item.get('nome', 'Assinatura')}", "controle-assinaturas"))
            except Exception:
                pass

        if not proximos:
            return None

        proximos.sort(key=lambda x: x[0])
        mais_proximo = proximos[0]
        dias_rest, desc, chave = mais_proximo

        if dias_rest == 0:
            tempo_aviso = "Vence hoje!"
        elif dias_rest == 1:
            tempo_aviso = "Vence amanhã!"
        else:
            tempo_aviso = f"Vence em {dias_rest} dias"

        return {
            "id": "vencimentos",
            "emoji": "⏰",
            "titulo": "Vencendo em Breve",
            "valor": f"{desc} ({tempo_aviso})",
            "detalhe": f"{len(proximos)} item(ns) com validade nos próximos 30 dias",
            "acao": {
                "rotulo": "Ver detalhes",
                "chave_ferramenta": chave,
            },
        }
    except Exception:
        return None


# ======================================================================
# T06: O que mais cresceu no disco (últimos 7 dias) — cache leve
# ======================================================================

_CRESC_TTL = 6 * 3600  # não reamostra a cada 60 s da Hoje
_CRESC_JANELA = 7 * 86400
_CRESC_ORCAMENTO_S = 0.75  # orçamento total da amostragem
_CRESC_ARQ = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "CaixaFerramentas",
    "disco_crescimento.json",
)


def _pastas_candidatas_crescimento() -> List[str]:
    """Pastas relevantes do usuário — nunca o C:\\ inteiro."""
    home = os.path.expanduser("~")
    nomes = [
        "Downloads",
        "Documents",
        "Documentos",
        "Desktop",
        "Área de Trabalho",
        "Videos",
        "Vídeos",
        "Pictures",
        "Imagens",
        "Music",
        "Músicas",
        "OneDrive",
    ]
    out: List[str] = []
    vistos = set()
    for n in nomes:
        p = os.path.normpath(os.path.join(home, n))
        key = os.path.normcase(p)
        if key in vistos or not os.path.isdir(p):
            continue
        vistos.add(key)
        out.append(p)
    temp = os.environ.get("TEMP") or os.environ.get("TMP")
    if temp and os.path.isdir(temp):
        key = os.path.normcase(os.path.normpath(temp))
        if key not in vistos:
            out.append(os.path.normpath(temp))
            vistos.add(key)
    return out


def _tamanho_limitado(pasta: str, deadline: float, max_arquivos: int = 6000) -> int:
    """Soma tamanho com teto de tempo/arquivos (amostra, não inventário forense)."""
    total = 0
    n = 0
    pilha = [pasta]
    while pilha and n < max_arquivos and time.perf_counter() < deadline:
        atual = pilha.pop()
        try:
            with os.scandir(atual) as it:
                for entry in it:
                    if n >= max_arquivos or time.perf_counter() >= deadline:
                        break
                    n += 1
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            pilha.append(entry.path)
                    except OSError:
                        continue
        except OSError:
            continue
    return total


def _ler_cache_crescimento() -> Dict[str, Any]:
    try:
        with open(_CRESC_ARQ, encoding="utf-8") as f:
            dados = json.load(f)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _salvar_cache_crescimento(dados: Dict[str, Any]) -> None:
    try:
        pasta = os.path.dirname(_CRESC_ARQ)
        os.makedirs(pasta, exist_ok=True)
        tmp = _CRESC_ARQ + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=0)
        os.replace(tmp, _CRESC_ARQ)
    except OSError:
        pass


def _amostrar_pastas_agora() -> Dict[str, int]:
    candidatos = _pastas_candidatas_crescimento()
    if not candidatos:
        return {}
    por = max(0.05, _CRESC_ORCAMENTO_S / max(1, len(candidatos)))
    tamanhos: Dict[str, int] = {}
    t0 = time.perf_counter()
    for pasta in candidatos:
        if time.perf_counter() - t0 > _CRESC_ORCAMENTO_S:
            break
        deadline = time.perf_counter() + por
        tamanhos[pasta] = _tamanho_limitado(pasta, deadline)
    return tamanhos


def _calcular_top_crescimento(
    amostras: List[Dict[str, Any]], atual: Dict[str, int], agora: float
) -> List[Tuple[str, int, int]]:
    """Devolve [(pasta, delta, tamanho_atual)] top 3 com delta > 0 na janela de 7 dias."""
    alvo = agora - _CRESC_JANELA
    base: Optional[Dict[str, int]] = None
    # amostra mais antiga ainda dentro/perto da janela (ou a mais antiga disponível)
    candidatas = [a for a in amostras if isinstance(a, dict) and isinstance(a.get("pastas"), dict)]
    if not candidatas:
        return []
    # preferir amostra ~7 dias atrás; senão a mais antiga
    com_ts = [(float(a.get("ts") or 0), a["pastas"]) for a in candidatas]
    com_ts.sort(key=lambda x: x[0])
    base = com_ts[0][1]
    for ts, pastas in com_ts:
        if ts <= alvo:
            base = pastas
        else:
            break
    deltas: List[Tuple[str, int, int]] = []
    for pasta, tam in atual.items():
        ant = int(base.get(pasta, 0)) if isinstance(base, dict) else 0
        delta = int(tam) - ant
        if delta > 0:
            deltas.append((pasta, delta, int(tam)))
    deltas.sort(key=lambda x: -x[1])
    return deltas[:3]


def sensor_crescimento_disco() -> Optional[Dict[str, Any]]:
    """Top 3 pastas que mais cresceram (cache 6 h; sem varrer o C: inteiro)."""
    try:
        agora = time.time()
        cache = _ler_cache_crescimento()
        amostras = list(cache.get("amostras") or [])
        top_cache = cache.get("top") or []
        atualizado = float(cache.get("atualizado") or 0)

        precisa_amostrar = (agora - atualizado) >= _CRESC_TTL or not amostras
        if precisa_amostrar:
            atual = _amostrar_pastas_agora()
            if atual:
                amostras.append({"ts": agora, "pastas": atual})
                # mantém ~14 dias; sempre preserva as 2 mais recentes (baseline)
                corte = agora - (_CRESC_JANELA + 7 * 86400)
                recentes = [
                    a for a in amostras
                    if isinstance(a, dict) and float(a.get("ts") or 0) >= corte
                ]
                if len(recentes) < 2:
                    validas = [a for a in amostras if isinstance(a, dict)]
                    validas.sort(key=lambda a: float(a.get("ts") or 0))
                    recentes = validas[-2:]
                amostras = recentes
                top = _calcular_top_crescimento(amostras[:-1], atual, agora) if len(amostras) >= 2 else []
                cache = {
                    "atualizado": agora,
                    "amostras": amostras,
                    "top": [
                        {"pasta": p, "delta": d, "agora": t} for p, d, t in top
                    ],
                }
                _salvar_cache_crescimento(cache)
                top_cache = cache["top"]
        else:
            # cache quente: zero I/O pesado
            top_cache = cache.get("top") or []

        if not top_cache:
            return None  # ainda coletando baseline ou nada cresceu

        def _rotulo(caminho: str) -> str:
            nome = os.path.basename(caminho.rstrip("\\/")) or caminho
            if nome.lower() in ("temp", "tmp"):
                return "Temp"
            return nome

        linhas = []
        for item in top_cache[:3]:
            pasta = str(item.get("pasta") or "")
            delta = int(item.get("delta") or 0)
            if not pasta or delta <= 0:
                continue
            linhas.append(f"{_rotulo(pasta)} +{_formatar_tamanho_bytes(delta)}")
        if not linhas:
            return None

        pasta_acao = str(top_cache[0].get("pasta") or "")
        return {
            "id": "crescimento",
            "emoji": "📈",
            "titulo": "O que mais cresceu (7 dias)",
            "valor": linhas[0],
            "detalhe": " · ".join(linhas),
            "acao": {
                "rotulo": "Abrir na Faxina",
                "chave_ferramenta": "faxina-disco",
                "pasta": pasta_acao,
                "args": ["--pasta", pasta_acao],
            },
        }
    except Exception:
        return None


# ======================================================================
# T05: Sensores de Bateria/Energia e Windows Update
# ======================================================================

def sensor_bateria() -> Optional[Dict[str, Any]]:
    """Informa o status e percentual da bateria em notebooks.

    Some se for desktop ou se não houver bateria física instalada.
    """
    if os.name != "nt":
        return None

    try:
        class SYSTEM_POWER_STATUS(ctypes.Structure):
            _fields_ = [
                ("ACLineStatus", ctypes.c_byte),
                ("BatteryFlag", ctypes.c_byte),
                ("BatteryLifePercent", ctypes.c_byte),
                ("SystemStatusFlag", ctypes.c_byte),
                ("BatteryLifeTime", ctypes.c_ulong),
                ("BatteryFullLifeTime", ctypes.c_ulong),
            ]

        s = SYSTEM_POWER_STATUS()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s)):
            return None

        flag = s.BatteryFlag & 0xFF
        pct = s.BatteryLifePercent & 0xFF

        # Flag 128 (0x80) = No system battery, 255 = Unknown
        if (flag & 128) != 0 or pct > 100 or pct == 255:
            return None

        ac = s.ACLineStatus & 0xFF
        # ac: 0 = Bateria, 1 = Na tomada, 255 = Desconhecido

        if ac == 1:
            if pct >= 99:
                emoji = "🔋"
                valor = f"{pct}% · Bateria cheia"
                detalhe = "Conectado à tomada (100% carregada)"
            else:
                emoji = "⚡"
                valor = f"{pct}% · Carregando"
                detalhe = "Conectado à tomada"
        else:
            emoji = "🪫" if pct <= 20 else "🔋"
            valor = f"{pct}% · Na bateria"
            if s.BatteryLifeTime != 0xFFFFFFFF and s.BatteryLifeTime > 0:
                horas = int(s.BatteryLifeTime // 3600)
                mins = int((s.BatteryLifeTime % 3600) // 60)
                detalhe = f"Restam aprox. {horas}h {mins}min de autonomia"
            else:
                detalhe = f"{pct}% de carga restante"

        return {
            "id": "bateria",
            "emoji": emoji,
            "titulo": "Bateria & Energia",
            "valor": valor,
            "detalhe": detalhe,
            "acao": {
                "rotulo": "Opções de Energia",
                "comando": "control powercfg.cpl",
            },
        }
    except Exception:
        return None


# ======================================================================
# Sensor de Conectividade de Rede e IP Local (Proposta 3 / T31)
# ======================================================================

def sensor_rede() -> Optional[Dict[str, Any]]:
    """Informa o status da conexão ativa de rede e IP local.

    Executa em menos de 15 ms via tabela de roteamento de socket e psutil.
    """
    my_ip: Optional[str] = None
    online = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        my_ip = s.getsockname()[0]
        s.close()
        online = True
    except Exception:
        pass

    if not online or not my_ip:
        return {
            "id": "rede",
            "emoji": "🌐",
            "titulo": "Conexão de Rede",
            "valor": "Desconectado",
            "detalhe": "Nenhuma conexão de rede ativa detectada",
            "acao": {
                "rotulo": "Configurações de Rede",
                "chave_ferramenta": "rede",
                "comando": "ms-settings:network",
            },
        }

    tipo = "Rede Local"
    emoji = "🌐"
    detalhe_vel = ""
    try:
        import psutil
        for name, addrs in psutil.net_if_addrs().items():
            if any(getattr(a, "address", "") == my_ip for a in addrs):
                nl = name.lower()
                if "wi-fi" in nl or "wifi" in nl or "wlan" in nl or "sem fio" in nl:
                    tipo = "Wi-Fi"
                    emoji = "📶"
                elif "ethernet" in nl or "eth" in nl or "local" in nl:
                    tipo = "Ethernet"
                    emoji = "🌐"
                else:
                    tipo = name
                stats = psutil.net_if_stats().get(name)
                if stats and getattr(stats, "speed", 0) > 0:
                    detalhe_vel = f" ({stats.speed} Mbps)"
                break
    except Exception:
        pass

    return {
        "id": "rede",
        "emoji": emoji,
        "titulo": "Conexão de Rede",
        "valor": f"{tipo} Conectado",
        "detalhe": f"IP local: {my_ip}{detalhe_vel}",
        "acao": {
            "rotulo": "Ver Conexão",
            "chave_ferramenta": "rede",
            "comando": "ms-settings:network",
        },
    }


def sensor_windows_update() -> Optional[Dict[str, Any]]:
    """Detecta se há atualizações pendentes do Windows ou reinicialização necessária.

    Lê diretamente do Registro do Windows (< 5 ms). Some se estiver tudo em dia.
    """
    if os.name != "nt":
        return None

    try:
        import winreg
        chaves_reboot = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\WindowsUpdate\Auto Update\RebootRequired"),
        ]

        reboot_pendente = False
        for hkey, subkey in chaves_reboot:
            try:
                with winreg.OpenKey(hkey, subkey):
                    reboot_pendente = True
                    break
            except (FileNotFoundError, OSError):
                pass

        if reboot_pendente:
            return {
                "id": "windows_update",
                "emoji": "🔄",
                "titulo": "Windows Update",
                "valor": "Reinício pendente",
                "detalhe": "Atualizações instaladas aguardando reinicialização do sistema",
                "acao": {
                    "rotulo": "Windows Update",
                    "comando": "ms-settings:windowsupdate",
                },
            }

        return None
    except Exception:
        return None


# ======================================================================
# Leitor Completo com Cache
# ======================================================================

def ler_tudo(forcar: bool = False) -> List[Dict[str, Any]]:
    """Lê todos os sensores e devolve apenas os cartões que têm dados reais.

    Executa em menos de 1 segundo (tipicamente < 50 ms).
    Cache automático com TTL de 5 segundos.
    """
    global _CACHE_DADOS, _CACHE_TEMPO
    agora = time.time()

    if not forcar and _CACHE_DADOS is not None and (agora - _CACHE_TEMPO) < CACHE_TTL_SEGUNDOS:
        return list(_CACHE_DADOS)

    sensores = [
        sensor_disco,
        sensor_crescimento_disco,
        sensor_rede,
        sensor_bateria,
        sensor_windows_update,
        sensor_downloads,
        sensor_prints_recentes,
        sensor_pudim,
        sensor_clipboard,
        sensor_vencimentos,
    ]

    resultado: List[Dict[str, Any]] = []

    for fn in sensores:
        try:
            d = fn()
            # Cartão sem dado real ou sem campo 'valor' não aparece
            if isinstance(d, dict) and d.get("valor") and d.get("id"):
                resultado.append(d)
        except Exception:
            continue

    _CACHE_DADOS = resultado
    _CACHE_TEMPO = agora
    return list(resultado)
