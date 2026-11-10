# -*- coding: utf-8 -*-
"""Adaptadores da barra para Rede & Seguranca.

Cada calcular chama o modulo real. Nao refaz a conta.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

import adp_financas as af

norm = af.norm
tokens = af.tokens
combina = af.combina
ler = af.ler
C = af.C
carregar = af.carregar
pacote = af.pacote
_num = af._num

ADAPTADORES = []

# Dias de certificado nao podem depender do relogio do teste.
HOJE_CERT = datetime.datetime(2026, 11, 9)

_RE_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_RE_JWT = re.compile(r"\b[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}\b")
_RE_HEX = re.compile(r"\b[0-9a-fA-F]{32,128}\b")
_RE_DATA = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_PORTAS = ("xnor", "nand", "xor", "nor", "and", "not", "or")


def _registrar(chave, palavras, extrair, calcular):
    ADAPTADORES.append({
        "chave": chave,
        "palavras": list(palavras),
        "extrair": extrair,
        "calcular": calcular,
    })


def _depois(texto, marca):
    t = norm(texto)
    i = t.find(norm(marca))
    if i < 0:
        return None
    return texto[i + len(norm(marca)):].strip()


def _entre(texto, ini, fim):
    t = norm(texto)
    a = t.find(norm(ini))
    if a < 0:
        return None
    a += len(norm(ini))
    b = t.find(norm(fim), a)
    if b < 0:
        return None
    return texto[a:b].strip()


def _chamar(fn):
    try:
        return fn()
    except ValueError as e:
        return pacote(str(e).splitlines()[0], "A ferramenta recusou esses dados.")


def _soltos(texto):
    return [tok.valor for tok in tokens(texto) if tok.tipo == "solto"]


# ---------------------------------------------------------------- morse / nato / antena
def _extrair_morse(texto):
    if not combina(texto, [("morse",)]):
        return None
    corpo = _depois(texto, "morse")
    if not corpo:
        return None
    return {"texto": corpo, "codigo": bool(re.fullmatch(r"[.\- /]+", corpo))}


def _calcular_morse(params):
    def fazer():
        mod = carregar("radio-morse", "mrs_core")
        if params["codigo"]:
            return pacote(mod.morse_to_text(params["texto"]), "Morse para texto.")
        return pacote(mod.text_to_morse(params["texto"]), "Texto para Morse.")
    return _chamar(fazer)


def _extrair_nato(texto):
    if not combina(texto, [("fonetico", "otan")]):
        return None
    marca = "fonetico" if "fonetico" in norm(texto) else "otan"
    corpo = _depois(texto, marca)
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_nato(params):
    def fazer():
        mod = carregar("radio-morse", "mrs_core")
        return pacote(mod.text_to_nato(params["texto"]), "Alfabeto fonético OTAN.")
    return _chamar(fazer)


def _extrair_antena(texto):
    if not combina(texto, [("antena", "dipolo")]):
        return None
    nums = _soltos(texto)
    if len(nums) != 1:
        return None
    return {"mhz": nums[0]}


def _calcular_antena(params):
    def fazer():
        mod = carregar("radio-morse", "mrs_core")
        r = mod.calculate_antenna_and_swr(params["mhz"])
        return pacote(
            _num(r["dipole_total_m"], 3) + " m",
            "Dipolo de meia onda. Direta 50 W e refletida 2 W (padrões da ferramenta).",
        )
    return _chamar(fazer)


# ---------------------------------------------------------------- crc / hdlc / cifras / feistel
def _extrair_crc(texto):
    if "crc32" not in norm(texto):
        return None
    corpo = _depois(texto, "de ")
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_crc(params):
    def fazer():
        mod = carregar("laboratorio-crc", "crc_core")
        r = mod.crc_named(params["texto"].encode("utf-8"), "CRC-32")
        return pacote(r["hex"], "Preset CRC-32 da ferramenta.")
    return _chamar(fazer)


def _extrair_hdlc(texto):
    if not combina(texto, [("hdlc",)]):
        return None
    corpo = _depois(texto, "hdlc")
    corpo = _depois(corpo or "", "crc") or corpo
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_hdlc(params):
    def fazer():
        mod = carregar("gerador-analisador-codigo-hdlc-crc16", "hdl_core")
        valor = mod.crc16_ccitt_hdlc(params["texto"].encode("utf-8"))
        return pacote(str(valor), "CRC-16-CCITT do HDLC, em inteiro.")
    return _chamar(fazer)


def _extrair_cesar(texto):
    if not combina(texto, [("cesar",)]):
        return None
    campos = ler(texto, [C("deslocamento", ["deslocamento", "desloca"], "int", True)])
    corpo = _depois(texto, "texto")
    if not campos or not corpo:
        return None
    return {"shift": campos["deslocamento"], "texto": corpo}


def _calcular_cesar(params):
    def fazer():
        mod = carregar("estudio-cifras", "cfr_core")
        return pacote(
            mod.caesar_cipher(params["texto"], params["shift"]),
            "Cifra de César, sem decifrar.",
        )
    return _chamar(fazer)


def _extrair_atbash(texto):
    if not combina(texto, [("atbash",)]):
        return None
    corpo = _depois(texto, "atbash")
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_atbash(params):
    def fazer():
        mod = carregar("estudio-cifras", "cfr_core")
        return pacote(mod.atbash_cipher(params["texto"]), "Atbash.")
    return _chamar(fazer)


def _extrair_vigenere(texto):
    if not combina(texto, [("vigenere",)]):
        return None
    chave = _entre(texto, "chave", "texto")
    corpo = _depois(texto, "texto")
    if not chave or not corpo:
        return None
    return {"chave": chave, "texto": corpo}


def _calcular_vigenere(params):
    def fazer():
        mod = carregar("estudio-cifras", "cfr_core")
        return pacote(
            mod.vigenere_cipher(params["texto"], params["chave"]),
            "Vigenère, sem decifrar.",
        )
    return _chamar(fazer)


def _extrair_feistel(texto):
    if not combina(texto, [("feistel",)]):
        return None
    campos = ler(texto, [
        C("bloco", ["bloco"], "int", True),
        C("chave", ["chave"], "int", True),
    ])
    return campos


def _calcular_feistel(params):
    def fazer():
        mod = carregar("estudio-criptografia-feistel-des", "fei_core")
        cifra, _hist = mod.feistel_encrypt_block(params["bloco"], params["chave"])
        return pacote(str(cifra), "8 rodadas (padrão da ferramenta).")
    return _chamar(fazer)


# ---------------------------------------------------------------- logica / ip / jwt / kit
def _extrair_porta(texto):
    if not combina(texto, [("porta",)]):
        return None
    nome = None
    for candidato in _PORTAS:
        if combina(texto, [(candidato,)]):
            nome = candidato.upper()
            break
    nums = [int(round(v)) for v in _soltos(texto)]
    if nome is None or not nums:
        return None
    return {"porta": nome, "a": nums[0], "b": nums[1] if len(nums) > 1 else 0}


def _calcular_porta(params):
    def fazer():
        mod = carregar("simulador-logica", "lgc_core")
        r = mod.evaluate_gate(params["porta"], params["a"], params["b"])
        return pacote(str(r), "Porta " + params["porta"] + ".")
    return _chamar(fazer)


def _extrair_ip(texto):
    if not combina(texto, [("ip",), ("tipo",)]):
        return None
    if combina(texto, [("subrede", "cidr", "vlsm")]):
        return None
    m = _RE_IP.search(texto)
    if not m or "/" in texto:
        return None
    return {"ip": m.group(0)}


def _calcular_ip(params):
    def fazer():
        mod = carregar("analisador-geo-ip", "gip_core")
        r = mod.analyze_ip_type(params["ip"])
        return pacote(r["type_desc"], r["version"] + " " + params["ip"])
    return _chamar(fazer)


def _extrair_jwt(texto):
    if not combina(texto, [("jwt",)]):
        return None
    m = _RE_JWT.search(texto)
    if not m:
        return None
    return {"token": m.group(0)}


def _calcular_jwt(params):
    def fazer():
        mod = carregar("decodificador-jwt", "jwt_core")
        info = mod.decode(params["token"])
        return pacote(
            json.dumps(info["payload"], ensure_ascii=False),
            "Algoritmo " + str(info["header"].get("alg", "?")) + ". Sem verificar assinatura.",
        )
    return _chamar(fazer)


def _extrair_rot13(texto):
    if "rot13" not in norm(texto):
        return None
    corpo = _depois(texto, "rot13")
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_rot13(params):
    def fazer():
        mod = carregar("kit-hacker", "kh_core")
        return pacote(mod.rot13(params["texto"]), "ROT13.")
    return _chamar(fazer)


def _extrair_idhash(texto):
    if "identificar hash" not in norm(texto):
        return None
    m = _RE_HEX.search(texto)
    if not m:
        return None
    return {"hex": m.group(0)}


def _calcular_idhash(params):
    def fazer():
        mod = carregar("kit-hacker", "kh_core")
        nomes = mod.identify_hash(params["hex"])
        return pacote(", ".join(nomes), "Identificação pelo tamanho. Não confere arquivo.")
    return _chamar(fazer)


# ---------------------------------------------------------------- contas que cairam em Rede
def _extrair_album(texto):
    if not combina(texto, [("album", "figurinhas")]):
        return None
    campos = ler(texto, [C("total", ["total"], "int", True)])
    m = re.search(r"(\d+)\s*-\s*(\d+)", texto)
    if not campos or not m:
        return None
    return {"total": campos["total"], "faixa": m.group(0).replace(" ", "")}


def _calcular_album(params):
    def fazer():
        mod = carregar("album-figurinhas", "alb_core")
        coladas = mod.parse_numeros(params["faixa"])
        r = mod.status(params["total"], coladas)
        return pacote(str(r["n_faltantes"]) + " faltam", str(r["pct"]) + "% colado.")
    return _chamar(fazer)


def _extrair_papel(texto):
    if "papel de parede" not in norm(texto):
        return None
    campos = ler(texto, [C("area", ["area"], "num", True)])
    return campos


def _calcular_papel(params):
    def fazer():
        mod = carregar("papel-parede", "ppd_core")
        r = mod.rolos_papel(params["area"])
        return pacote(
            str(r["rolos"]) + " rolos",
            "Rolo 0,53 m por 10,05 m e parede de 2,70 m (padrões da ferramenta).",
        )
    return _chamar(fazer)


def _extrair_dry(texto):
    if not combina(texto, [("drywall", "gesso")]):
        return None
    return ler(texto, [C("area", ["area"], "num", True)])


def _calcular_dry(params):
    def fazer():
        mod = carregar("gesso-drywall", "dry_core")
        r = mod.material(params["area"])
        return pacote(
            str(r["placas"]) + " placas",
            "Parede, 1 face, perda 10% e placa de 2,88 m2 (padrões da ferramenta).",
        )
    return _chamar(fazer)


def _extrair_tinta(texto):
    if not combina(texto, [("pintura",)]):
        return None
    return ler(texto, [
        C("demaos", ["demaos", "demao"], "int", True),
        C("perda", ["perda"], "pct", True),
        C("area", ["area"], "num", True),
        C("rendimento", ["rendimento"], "num", True),
        C("preco", ["preco"], "num", True),
        C("litros", ["litros", "litro"], "num", True),
        C("mao", ["mao"], "num", True),
    ])


def _calcular_tinta(params):
    def fazer():
        mod = carregar("custo-pintura-parede", "pnt_core")
        r = mod.calcular(
            params["area"], params["demaos"], params["rendimento"], params["perda"],
            params["preco"], params["litros"], params["mao"],
        )
        return pacote("R$ " + _num(r["total"]), "Sem primer. A mão de obra é a da frase.")
    return _chamar(fazer)


def _extrair_neg(texto):
    if not combina(texto, [("negociacao",)]):
        return None
    return ler(texto, [C("bruto", ["bruto"], "num", True)])


def _calcular_neg(params):
    def fazer():
        mod = carregar("simulador-negociacao-salarial", "neg_core")
        r = mod.liquido_salario(params["bruto"], 0)
        return pacote(
            mod.formatar_brl(r["liquido"]),
            "0 dependentes (padrão desta pergunta). INSS e IR saem da própria ferramenta.",
        )
    return _chamar(fazer)


def _extrair_cert(texto):
    if not combina(texto, [("certificado",)]):
        return None
    m = _RE_DATA.search(texto)
    if not m:
        return None
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return {"quando": datetime.datetime(ano, mes, dia)}


def _calcular_cert(params):
    def fazer():
        mod = carregar("certificado-ssl", "ssl_core")
        dias = mod.days_left(params["quando"], HOJE_CERT)
        return pacote(str(dias) + " dias", "Contagem a partir de 09/11/2026.")
    return _chamar(fazer)


_registrar("radio-morse", ["morse"], _extrair_morse, _calcular_morse)
_registrar("radio-morse", ["fonetico", "otan"], _extrair_nato, _calcular_nato)
_registrar("radio-morse", ["antena", "dipolo"], _extrair_antena, _calcular_antena)
_registrar("laboratorio-crc", ["crc32"], _extrair_crc, _calcular_crc)
_registrar("gerador-analisador-codigo-hdlc-crc16", ["hdlc"], _extrair_hdlc, _calcular_hdlc)
_registrar("estudio-cifras", ["cesar"], _extrair_cesar, _calcular_cesar)
_registrar("estudio-cifras", ["atbash"], _extrair_atbash, _calcular_atbash)
_registrar("estudio-cifras", ["vigenere"], _extrair_vigenere, _calcular_vigenere)
_registrar("estudio-criptografia-feistel-des", ["feistel"], _extrair_feistel, _calcular_feistel)
_registrar("simulador-logica", ["porta logica"], _extrair_porta, _calcular_porta)
_registrar("analisador-geo-ip", ["tipo do ip"], _extrair_ip, _calcular_ip)
_registrar("decodificador-jwt", ["jwt"], _extrair_jwt, _calcular_jwt)
_registrar("kit-hacker", ["rot13"], _extrair_rot13, _calcular_rot13)
_registrar("kit-hacker", ["identificar hash"], _extrair_idhash, _calcular_idhash)
_registrar("album-figurinhas", ["album"], _extrair_album, _calcular_album)
_registrar("papel-parede", ["papel de parede"], _extrair_papel, _calcular_papel)
_registrar("gesso-drywall", ["drywall"], _extrair_dry, _calcular_dry)
_registrar("custo-pintura-parede", ["pintura"], _extrair_tinta, _calcular_tinta)
_registrar("simulador-negociacao-salarial", ["negociacao"], _extrair_neg, _calcular_neg)
_registrar("certificado-ssl", ["certificado"], _extrair_cert, _calcular_cert)
