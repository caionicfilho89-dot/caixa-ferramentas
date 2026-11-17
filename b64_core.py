# -*- coding: utf-8 -*-
"""Motor do Conversor Base64 de Arquivos (sem UI).

Codifica/decodifica arquivos <-> Base64 (padrao/URL-safe), gera data URI e
estima expansao de tamanho.
"""
from __future__ import annotations

import base64
import mimetypes
import os
from dataclasses import dataclass


@dataclass
class EncodeResult:
    path: str
    mime: str
    tamanho_orig: int
    tamanho_b64: int
    texto: str
    data_uri: str


def guess_mime(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def encode_file(
    path: str,
    *,
    url_safe: bool = False,
    wrap: int = 76,
    max_out: int = 8_000_000,
) -> EncodeResult:
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "rb") as f:
        data = f.read()
    if url_safe:
        raw = base64.urlsafe_b64encode(data).decode("ascii")
    else:
        raw = base64.b64encode(data).decode("ascii")
    if wrap and wrap > 0:
        texto = "\n".join(raw[i : i + wrap] for i in range(0, len(raw), wrap))
    else:
        texto = raw
    if len(texto) > max_out:
        raise ValueError(
            f"saida Base64 muito grande ({len(texto)} chars). "
            f"Use arquivo menor ou aumente o limite."
        )
    mime = guess_mime(path)
    uri = f"data:{mime};base64,{raw}"
    return EncodeResult(path, mime, len(data), len(raw), texto, uri)


def decode_to_bytes(text: str, url_safe: bool = False) -> bytes:
    limpo = "".join(text.split())
    # data URI
    if limpo.lower().startswith("data:") and ";base64," in limpo:
        limpo = limpo.split(";base64,", 1)[1]
    pad = (-len(limpo)) % 4
    if pad:
        limpo += "=" * pad
    try:
        if url_safe:
            return base64.urlsafe_b64decode(limpo)
        return base64.b64decode(limpo, validate=False)
    except Exception as e:
        raise ValueError(f"Base64 invalido: {e}") from e


def decode_to_file(text: str, dest: str, url_safe: bool = False) -> dict:
    data = decode_to_bytes(text, url_safe=url_safe)
    dest = os.path.abspath(dest)
    parent = os.path.dirname(dest)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)
    return {"path": dest, "tamanho": len(data)}


def expansao(n_bytes: int) -> dict:
    """Base64 cresce ~4/3."""
    b64 = 4 * ((n_bytes + 2) // 3)
    return {
        "original": n_bytes,
        "base64": b64,
        "razao": (b64 / n_bytes) if n_bytes else 0.0,
        "overhead_pct": ((b64 / n_bytes) - 1.0) * 100 if n_bytes else 0.0,
    }


def is_probably_base64(text: str) -> bool:
    limpo = "".join(text.split())
    if limpo.lower().startswith("data:") and ";base64," in limpo.lower():
        return True
    if len(limpo) < 8:
        return False
    alphabet = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/_=-")
    return all(c in alphabet for c in limpo[:2000])
