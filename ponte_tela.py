"""Ponte entre a tela nova (Tauri, CaixaTela.exe) e o Python da Caixa.

A tela roda `Caixa.exe --ponte` uma vez e conversa por stdin/stdout, uma linha
JSON por pedido e uma linha JSON por resposta:

    → {"id": 1, "op": "dados"}
    ← {"id": 1, "ok": true, "res": {...}}

Operações:
    dados                 catálogo, categorias, vitrine, usos, favoritos, versão
    hoje                  cartões vivos do "Agora no seu PC" (sensores_core)
    responder  texto      respostas da barra (respostas_core)
    abrir      chave      abre a ferramenta (Caixa.exe --tool <chave>) e conta o uso
    acao_hoje  cartao     executa o botão de um cartão do Hoje
    favorito   chave      liga/desliga favorito
    classica              abre a Caixa clássica (PyQt)

Fora do exe dá pra testar com:  python ponte_tela.py  (e digitar as linhas JSON).
"""
from __future__ import annotations

import importlib.machinery
import json
import os
import subprocess
import sys
import threading
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = getattr(sys, "frozen", False)


def _carregar_caixa():
    """O módulo da Caixa clássica: caixa_ui no exe, caixa.pyw fora dele."""
    if FROZEN:
        import caixa_ui  # type: ignore
        return caixa_ui
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    loader = importlib.machinery.SourceFileLoader("caixa_ui", os.path.join(HERE, "caixa.pyw"))
    mod = loader.load_module()
    sys.modules["caixa_ui"] = mod
    return mod


cx = _carregar_caixa()
try:
    import caixa_home as _home  # type: ignore
except Exception:  # noqa: BLE001
    _home = None
try:
    import respostas_core as _respostas  # type: ignore
except Exception:  # noqa: BLE001
    _respostas = None

_trava_cfg = threading.Lock()
_acoes_hoje: dict[str, dict] = {}
_ultima_aberta = ("", 0.0)


def _ferramentas():
    return list(cx.BUILTIN) + [tuple(t) for t in cx.load_cfg().get("extra_tools", [])]


def _sem_emoji(nome: str) -> tuple[str, str]:
    partes = nome.split(" ", 1)
    return (partes[0], partes[1]) if len(partes) == 2 else ("", nome)


def op_dados(_pedido):
    cfg = cx.load_cfg()
    lista = []
    contagem: dict[str, int] = {}
    for t in _ferramentas():
        cat = cx.categoria_de(t)
        contagem[cat] = contagem.get(cat, 0) + 1
        lista.append({"emoji": t[0], "nome": t[1], "desc": t[2], "chave": t[3], "categoria": cat})
    ordem = [c for c in cx.CAT_ORDEM if c in contagem] + [c for c in contagem if c not in cx.CAT_ORDEM]
    categorias = []
    for c in ordem:
        emoji, nome = _sem_emoji(c)
        categorias.append({"id": c, "emoji": emoji, "nome": nome, "total": contagem[c],
                           "cor": cx.CAT_CORES.get(c, "#8a93a8")})
    chaves = {f["chave"] for f in lista}
    vitrine = []
    if _home is not None:
        try:
            vitrine = [{k: v[k] for k in ("chave", "emoji", "nome", "substitui")}
                       for v in _home.ler_vitrine() if v["chave"] in chaves]
        except Exception:  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
    return {
        "versao": cx.APP_VERSION,
        "total": len(lista),
        "ferramentas": lista,
        "categorias": categorias,
        "tendencia": cx.CAT_TENDENCIAS,
        "vitrine": vitrine,
        "usos": {k: v for k, v in (cfg.get("uses") or {}).items() if k in chaves},
        "favoritos": [k for k in cfg.get("favorites", []) if k in chaves],
    }


def op_hoje(_pedido):
    if _home is None:
        return []
    cartoes = []
    _acoes_hoje.clear()
    for s in _home._ler_sensores_padrao():
        s = _home.enriquecer_acao(s)
        sid = str(s.get("id") or len(cartoes))
        acao = s.get("acao") or {}
        _acoes_hoje[sid] = acao
        cartoes.append({
            "id": sid,
            "emoji": s.get("emoji") or "•",
            "titulo": s.get("titulo") or "",
            "valor": s.get("valor") or "",
            "detalhe": s.get("detalhe") or "",
            "rotulo": acao.get("rotulo") or ("Abrir" if acao else ""),
            "urgencia": s.get("urgencia") or s.get("nivel") or "",
        })
    return cartoes


def op_responder(pedido):
    texto = str(pedido.get("texto") or "")
    if _respostas is None or not texto.strip():
        return []
    return _respostas.responder(texto)


def _abrir(chave: str, extra: list[str] | None = None):
    global _ultima_aberta
    chave = (chave or "").strip()
    tool = next((t for t in _ferramentas() if t[3] == chave), None)
    if tool is None:
        raise ValueError(f"Não achei a ferramenta “{chave}”.")
    agora = time.monotonic()
    if _ultima_aberta[0] == chave and agora - _ultima_aberta[1] < 2.5:
        return {"nome": tool[1], "repetido": True}
    _ultima_aberta = (chave, agora)
    extra = list(extra or [])
    if cx.MODO_TESTE:
        extra.append("--teste")
    os.makedirs(cx.CFG_DIR, exist_ok=True)
    log = os.path.join(cx.CFG_DIR, "ultima_ferramenta.log")
    with open(log, "w", encoding="utf-8") as fh:
        if FROZEN:
            p = subprocess.Popen([sys.executable, "--tool", chave] + extra, stdout=fh, stderr=fh,
                                 stdin=subprocess.DEVNULL)
        else:
            caminho = os.path.join(cx.BASE, tool[3], tool[4])
            p = subprocess.Popen([cx.pythonw(), caminho] + extra, cwd=os.path.dirname(caminho),
                                 stdout=fh, stderr=fh, stdin=subprocess.DEVNULL)
    if os.environ.get("CAIXA_TESTE") != "1":
        with _trava_cfg:
            cfg = cx.load_cfg()
            cfg.setdefault("uses", {})
            cfg["uses"][chave] = cfg["uses"].get(chave, 0) + 1
            cx.save_cfg(cfg)
    if _home is not None:
        try:
            _home.salvar_ultima_chave(chave)
        except Exception:  # noqa: BLE001
            pass
    threading.Thread(target=_vigiar, args=(p, tool[1], log), daemon=True).start()
    return {"nome": tool[1]}


def _vigiar(p, nome, log):
    """Se a ferramenta fechar com erro logo ao abrir, guarda o motivo no erros.log."""
    time.sleep(6)
    rc = p.poll()
    if rc in (None, 0):
        return
    try:
        with open(log, encoding="utf-8", errors="replace") as f:
            txt = f.read()[-1500:]
        with open(os.path.join(cx.CFG_DIR, "erros.log"), "a", encoding="utf-8") as f:
            f.write(f"\n=== {nome} (código {rc}) ===\n{txt}\n")
    except OSError:
        pass


def op_abrir(pedido):
    return _abrir(str(pedido.get("chave") or ""))


def op_acao_hoje(pedido):
    # "cartao" (não "id": o id é o número do pedido, que a tela preenche sozinha)
    cid = str(pedido.get("cartao") or "")
    if cid not in _acoes_hoje:
        op_hoje(None)  # a ponte reiniciou ou o cartão é novo: lê os sensores de novo
    acao = _acoes_hoje.get(cid)
    if not acao:
        raise ValueError("Esse cartão mudou, atualize o Hoje.")
    if acao.get("chave_ferramenta"):
        return _abrir(acao["chave_ferramenta"], acao.get("args") or [])
    cmd = str(acao.get("comando") or "").strip()
    if cmd and (os.path.isfile(cmd) or os.path.isdir(cmd)):
        os.startfile(cmd)  # noqa: S606 — caminho vindo do sensor, não da tela
        return {"nome": os.path.basename(cmd)}
    raise ValueError("Esse cartão não tem ação.")


def op_favorito(pedido):
    chave = str(pedido.get("chave") or "")
    with _trava_cfg:
        cfg = cx.load_cfg()
        favs = cfg.setdefault("favorites", [])
        if chave in favs:
            favs.remove(chave)
        else:
            favs.append(chave)
        cx.save_cfg(cfg)
        return list(favs)


def op_classica(_pedido):
    if FROZEN:
        subprocess.Popen([sys.executable, "--classico"], stdin=subprocess.DEVNULL)
    else:
        subprocess.Popen([cx.pythonw(), os.path.join(HERE, "caixa.pyw")], stdin=subprocess.DEVNULL)
    return True


OPS = {
    "dados": op_dados,
    "hoje": op_hoje,
    "responder": op_responder,
    "abrir": op_abrir,
    "acao_hoje": op_acao_hoje,
    "favorito": op_favorito,
    "classica": op_classica,
}


def main():
    entrada = sys.stdin
    saida = sys.stdout
    if entrada is None or saida is None:
        return  # sem canal com a tela (aberto à mão, sem pipe)
    try:
        entrada.reconfigure(encoding="utf-8")
        saida.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    for linha in entrada:
        linha = linha.strip().lstrip("﻿")
        if not linha:
            continue
        pid = None
        try:
            pedido = json.loads(linha)
            pid = pedido.get("id")
            fn = OPS.get(pedido.get("op"))
            if fn is None:
                raise ValueError(f"operação desconhecida: {pedido.get('op')}")
            resposta = {"id": pid, "ok": True, "res": fn(pedido)}
        except Exception as e:  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
            resposta = {"id": pid, "ok": False, "erro": str(e)}
        saida.write(json.dumps(resposta, ensure_ascii=False) + "\n")
        saida.flush()


if __name__ == "__main__":
    main()
