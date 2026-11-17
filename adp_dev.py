# -*- coding: utf-8 -*-
"""Adaptadores da barra para Dev & Dados.

Cada calcular chama o modulo real da ferramenta. Nao refaz a conta.
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
numero_br = af.numero_br

ADAPTADORES = []

# Proximas execucoes de cron nao podem depender do relogio do teste.
INICIO_CRON = datetime.datetime(2026, 11, 9, 0, 0)

_RE_CIDR = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b")
_RE_UUID = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_RE_ULID = re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b", re.IGNORECASE)
_RE_CRON = re.compile(r"(?<!\S)([0-9*,/\-?]+(?:\s+[0-9*,/\-?]+){4})(?!\S)")
_RE_HORA = re.compile(r"\b(\d{1,2}:\d{2})\b")
_REDES_SNOW = {
    "twitter": "Twitter/X",
    "discord": "Discord",
    "instagram": "Instagram",
    "unix": "Unix",
}


def _registrar(chave, palavras, extrair, calcular):
    ADAPTADORES.append({
        "chave": chave,
        "palavras": list(palavras),
        "extrair": extrair,
        "calcular": calcular,
    })


def _depois(texto, marca):
    t = norm(texto)
    m = norm(marca)
    i = t.find(m)
    if i < 0:
        return None
    return texto[i + len(m):].strip()


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


def _soltos(texto):
    return [tok.valor for tok in tokens(texto) if tok.tipo == "solto"]


def _chamar(fn):
    try:
        return fn()
    except ValueError as e:
        return pacote(str(e).splitlines()[0], "A ferramenta recusou esses dados.")
    except Exception as e:
        if type(e).__name__ == "FdError":
            return pacote(str(e).splitlines()[0], "A ferramenta recusou esses dados.")
        raise


def _pares(texto):
    achados = []
    for nome, bruto in re.findall(r"([A-Za-z][A-Za-z0-9_-]*)\s+(\d+(?:[.,]\d+)?)", texto):
        achados.append((nome, numero_br(bruto)))
    return achados


# ---------------------------------------------------------------- hash
def _extrair_hash(texto):
    if not combina(texto, [("hash",)], ("arquivo", "pasta")):
        return None
    if " de " not in norm(texto):
        return None
    corpo = _depois(texto, " de ")
    if not corpo:
        return None
    algo = "sha256"
    for nome in ("sha512", "sha256", "sha1", "md5"):
        if combina(texto, [(nome,)]):
            algo = nome
            break
    return {"texto": corpo, "algo": algo}


def _calcular_hash(params):
    def fazer():
        mod = carregar("verificador-hash", "hsh_core")
        digest = mod.hash_data(params["texto"].encode("utf-8"), params["algo"])
        return pacote(digest, "Algoritmo " + params["algo"] + ". Hash do texto, nao de arquivo.")
    return _chamar(fazer)


# ---------------------------------------------------------------- base64
def _extrair_b64_enc(texto):
    t = norm(texto)
    if "base64 de " not in t:
        return None
    if "decodificar" in t or "expansao" in t:
        return None
    corpo = _depois(texto, "base64 de ")
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_b64_enc(params):
    def fazer():
        mod = carregar("ferramentas-dev", "fd_core")
        return pacote(mod.encode_text(params["texto"], "Base64"), "Base64 padrão (com padding).")
    return _chamar(fazer)


def _extrair_b64_dec(texto):
    t = norm(texto)
    if "decodificar base64" not in t:
        return None
    corpo = _depois(texto, "decodificar base64")
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_b64_dec(params):
    def fazer():
        mod = carregar("ferramentas-dev", "fd_core")
        return pacote(mod.decode_text(params["texto"], "Base64"), "Base64 para texto UTF-8.")
    return _chamar(fazer)


def _extrair_expansao(texto):
    if not combina(texto, [("expansao",), ("base64",)]):
        return None
    campos = ler(texto, [C("bytes", ["bytes", "byte"], "int", True)])
    if not campos:
        return None
    return campos


def _calcular_expansao(params):
    def fazer():
        mod = carregar("conversor-base64-arquivo", "b64_core")
        r = mod.expansao(params["bytes"])
        return pacote(
            str(r["base64"]) + " caracteres",
            "Original " + str(r["original"]) + " bytes. Base64 cresce cerca de 4/3.",
        )
    return _chamar(fazer)


# ---------------------------------------------------------------- bases / ieee / bitwise
def _extrair_base(texto):
    if not combina(texto, [("hexadecimal", "binario", "octal")]):
        return None
    if combina(texto, [("ieee", "bitwise", "base64")]):
        return None
    nums = _soltos(texto)
    if len(nums) != 1:
        return None
    t = norm(texto)
    if "hexadecimal" in t:
        dest = "HEX"
    elif "binario" in t:
        dest = "BIN"
    else:
        dest = "OCT"
    return {"n": int(round(nums[0])), "dest": dest}


def _calcular_base(params):
    def fazer():
        mod = carregar("conversor-bases", "bse_core")
        r = mod.all_bases(params["n"])
        return pacote(r[params["dest"]], "Entrada decimal " + str(params["n"]) + ".")
    return _chamar(fazer)


def _extrair_ieee(texto):
    if not combina(texto, [("ieee",)]):
        return None
    campos = ler(texto, [C("valor", ["valor"], "num", True)])
    if not campos:
        return None
    return {"valor": campos["valor"], "duplo": "duplo" in norm(texto)}


def _calcular_ieee(params):
    def fazer():
        mod = carregar("conversor-bases", "bse_core")
        r = mod.ieee754(params["valor"], double=params["duplo"])
        bits = "64" if params["duplo"] else "32"
        return pacote(r["hex"], "IEEE-754 " + bits + " bits, tipo " + r["kind"] + ".")
    return _chamar(fazer)


def _extrair_bit(texto):
    if not combina(texto, [("bitwise",)]):
        return None
    op = None
    for nome, codigo in (
        ("nand", "NAND"), ("nor", "NOR"), ("xor", "XOR"),
        ("shl", "SHL"), ("shr", "SHR"), ("and", "AND"), ("or", "OR"),
    ):
        if combina(texto, [(nome,)]):
            op = codigo
            break
    nums = _soltos(texto)
    if op is None or len(nums) < 2:
        return None
    return {"a": int(round(nums[0])), "b": int(round(nums[1])), "op": op}


def _calcular_bit(params):
    def fazer():
        mod = carregar("conversor-bases", "bse_core")
        r = mod.bitwise(params["a"], params["b"], params["op"])
        return pacote(str(r), "32 bits. Operacao " + params["op"] + ".")
    return _chamar(fazer)


# ---------------------------------------------------------------- identificadores
def _extrair_uuid5(texto):
    if "uuid5" not in norm(texto):
        return None
    ns = None
    for nome in ("x500", "dns", "url", "oid"):
        if combina(texto, [(nome,)]):
            ns = nome
            break
    if ns is None:
        return None
    nome_txt = _depois(texto, ns)
    if not nome_txt:
        return None
    codigo = {"dns": "DNS", "url": "URL", "oid": "OID", "x500": "X500"}[ns]
    return {"ns": codigo, "nome": nome_txt}


def _calcular_uuid5(params):
    def fazer():
        mod = carregar("gerador-identificadores", "uid_core")
        return pacote(
            mod.uuid5(params["ns"], params["nome"]),
            "UUIDv5 namespace " + params["ns"] + ".",
        )
    return _chamar(fazer)


def _extrair_uuid_dec(texto):
    t = norm(texto)
    if "decodificar" not in t or not combina(texto, [("uuid",)]):
        return None
    if "uuid5" in t or "ulid" in t or "uuid4" in t:
        return None
    m = _RE_UUID.search(texto)
    if not m:
        return None
    return {"uuid": m.group(0)}


def _calcular_uuid_dec(params):
    def fazer():
        mod = carregar("gerador-identificadores", "uid_core")
        info = mod.decode_uuid(params["uuid"])
        return pacote("versao " + str(info["version"]), info["canonical"])
    return _chamar(fazer)


def _extrair_uuid4(texto):
    t = norm(texto)
    if "uuid4" not in t and "uuid 4" not in t:
        return None
    if "decodificar" in t or "uuid5" in t:
        return None
    return {"gerar": True}


def _calcular_uuid4(params):
    def fazer():
        mod = carregar("gerador-identificadores", "uid_core")
        return pacote(mod.uuid4(), "UUIDv4 aleatorio, muda a cada pergunta.")
    return _chamar(fazer)


def _extrair_ulid(texto):
    if not combina(texto, [("ulid",)]):
        return None
    m = _RE_ULID.search(texto.upper())
    if not m:
        return None
    return {"ulid": m.group(0)}


def _calcular_ulid(params):
    def fazer():
        mod = carregar("gerador-identificadores", "uid_core")
        info = mod.decode_ulid(params["ulid"])
        return pacote(str(info["timestamp_ms"]), info["timestamp"])
    return _chamar(fazer)


def _extrair_snow(texto):
    if "snowflake" not in norm(texto):
        return None
    rede = None
    for nome in _REDES_SNOW:
        if combina(texto, [(nome,)]):
            rede = nome
            break
    nums = _soltos(texto)
    if rede is None or not nums:
        return None
    return {"sid": int(round(nums[0])), "rede": rede}


def _calcular_snow(params):
    def fazer():
        mod = carregar("gerador-identificadores", "uid_core")
        chave = _REDES_SNOW[params["rede"]]
        info = mod.decode_snowflake(params["sid"], mod.EPOCHS[chave])
        return pacote(str(info["timestamp_ms"]), "Epoch " + chave + " da propria ferramenta.")
    return _chamar(fazer)


def _extrair_colisao(texto):
    if not combina(texto, [("colisao",), ("nanoid",)]):
        return None
    return ler(texto, [
        C("tamanho", ["tamanho"], "int", True),
        C("alfabeto", ["alfabeto"], "int", True),
        C("taxa", ["taxa"], "int", True),
    ])


def _calcular_colisao(params):
    def fazer():
        mod = carregar("gerador-identificadores", "uid_core")
        anos = mod.collision_years(params["tamanho"], params["alfabeto"], params["taxa"])
        return pacote(
            _num(anos, 2) + " anos",
            "Anos ate cerca de 1% de chance de colisao. Taxa em ids por hora.",
        )
    return _chamar(fazer)


# ---------------------------------------------------------------- cron / sql / json
def _extrair_cron(texto):
    if not combina(texto, [("cron",)]):
        return None
    m = _RE_CRON.search(texto)
    if not m:
        return None
    return {"expr": m.group(1), "proximas": "proximas" in norm(texto)}


def _calcular_cron(params):
    def fazer():
        mod = carregar("explicador-cron", "crx_core")
        desc = mod.describe(params["expr"])
        if not params["proximas"]:
            return pacote(desc, params["expr"])
        runs = mod.next_runs(params["expr"], INICIO_CRON, 3)
        quando = ", ".join(d.strftime("%d/%m/%Y %H:%M") for d in runs) or "nenhuma"
        return pacote(quando, desc + " Contagem a partir de 09/11/2026 00:00.")
    return _chamar(fazer)


def _extrair_sql(texto):
    if "formatar sql" not in norm(texto):
        return None
    corpo = _depois(texto, "formatar sql")
    if not corpo:
        return None
    return {"sql": corpo}


def _calcular_sql(params):
    def fazer():
        mod = carregar("formatador-sql-ast", "sqf_core")
        return pacote(mod.format_sql(params["sql"]), "Palavras-chave em maiusculas.")
    return _chamar(fazer)


def _extrair_json_acao(texto, verbo):
    marca = verbo + " json"
    if marca not in norm(texto):
        return None
    corpo = _depois(texto, marca)
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_json_fmt(params):
    def fazer():
        mod = carregar("ferramentas-dev", "fd_core")
        return pacote(mod.json_format(params["texto"]), "Indentacao 2.")
    return _chamar(fazer)


def _calcular_json_mini(params):
    def fazer():
        mod = carregar("ferramentas-dev", "fd_core")
        return pacote(mod.json_minify(params["texto"]), "JSON em uma linha.")
    return _chamar(fazer)


def _calcular_json_val(params):
    def fazer():
        mod = carregar("ferramentas-dev", "fd_core")
        return pacote(mod.json_validate(params["texto"]), "So valida, nao formata.")
    return _chamar(fazer)


def _extrair_schema(texto):
    if "inferir schema" not in norm(texto):
        return None
    corpo = _depois(texto, "inferir schema")
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_schema(params):
    def fazer():
        mod = carregar("validador-json-schema", "jsc_core")
        esquema = mod.infer_schema(json.loads(params["texto"]))
        return pacote(str(esquema.get("type", "?")), json.dumps(esquema, ensure_ascii=False))
    return _chamar(fazer)


# ---------------------------------------------------------------- regex / rede / texto
def _extrair_regex(texto):
    if not combina(texto, [("regex",)]):
        return None
    if " no texto " not in norm(texto):
        return None
    padrao = _entre(texto, "regex", "no texto")
    alvo = _depois(texto, "no texto")
    if not padrao or not alvo:
        return None
    return {"padrao": padrao, "alvo": alvo}


def _calcular_regex(params):
    def fazer():
        mod = carregar("inspetor-regex", "rgx_core")
        r = mod.test_regex(params["padrao"], params["alvo"])
        achou = r["matches"][0]["full_match"] if r["matches"] else (r.get("error") or "nenhum")
        return pacote(str(r["match_count"]), "Flags im (padrao da ferramenta). Achou: " + str(achou))
    return _chamar(fazer)


def _extrair_cidr(texto):
    if not combina(texto, [("subrede", "sub-rede", "cidr")]):
        return None
    if "vlsm" in norm(texto):
        return None
    m = _RE_CIDR.search(texto)
    if not m:
        return None
    return {"cidr": m.group(0)}


def _calcular_cidr(params):
    def fazer():
        mod = carregar("calculadora-subrede", "ipm_core")
        r = mod.analyze_cidr(params["cidr"])
        return pacote(
            str(r["usable_hosts"]) + " hosts",
            r["cidr"] + " mascara " + r["netmask"] + " primeiro " + r["first_host"],
        )
    return _chamar(fazer)


def _extrair_vlsm(texto):
    if "vlsm" not in norm(texto):
        return None
    m = _RE_CIDR.search(texto)
    if not m:
        return None
    pares = _pares(texto[m.end():])
    if not pares:
        return None
    return {"base": m.group(0), "reqs": [(n, int(v)) for n, v in pares]}


def _calcular_vlsm(params):
    def fazer():
        mod = carregar("calculadora-subrede", "ipm_core")
        blocos = mod.allocate_vlsm(params["base"], params["reqs"])
        linhas = [b["department"] + " " + b["subnet_cidr"] for b in blocos]
        return pacote(" | ".join(linhas), "VLSM sem sobreposicao, maior bloco primeiro.")
    return _chamar(fazer)


def _extrair_slug(texto):
    if not combina(texto, [("slug",)]):
        return None
    corpo = _depois(texto, "slug")
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_slug(params):
    def fazer():
        mod = carregar("gerador-slug", "slg_core")
        return pacote(mod.slugify(params["texto"]), "Minusculo, hifen, sem acento.")
    return _chamar(fazer)


def _extrair_path(texto):
    if not combina(texto, [("path",), ("converter", "wsl", "windows", "posix")]):
        return None
    corpo = _depois(texto, "path")
    if not corpo:
        return None
    return {"caminho": corpo}


def _calcular_path(params):
    def fazer():
        mod = carregar("conversor-path", "wup_core")
        r = mod.convert_all(params["caminho"])
        return pacote(r["wsl"], "Windows " + r["windows"] + " | git " + r["git_bash"])
    return _chamar(fazer)


def _extrair_yml(texto):
    t = norm(texto)
    if "toml" not in t and "yaml" not in t:
        return None
    origem = "toml" if "toml" in t else "yaml"
    destino = None
    marca = None
    for nome in ("json", "yaml", "toml"):
        for lig in ("para " + nome, "pra " + nome):
            if lig in t and nome != origem:
                destino = nome
                marca = lig
                break
        if destino:
            break
    if not destino:
        return None
    corpo = _depois(texto, marca)
    if not corpo:
        return None
    return {"texto": corpo, "origem": origem, "destino": destino}


def _calcular_yml(params):
    def fazer():
        mod = carregar("formatador-yaml-toml", "yml_core")
        saida = mod.converter(params["texto"], params["origem"], params["destino"])
        return pacote(saida.strip(), params["origem"] + " para " + params["destino"] + ".")
    return _chamar(fazer)


# ---------------------------------------------------------------- estruturas / codigo
def _extrair_bloom(texto):
    if not combina(texto, [("bloom",)]):
        return None
    return ler(texto, [
        C("itens", ["itens", "item"], "int", True),
        C("taxa", ["taxa"], "num", True),
    ])


def _calcular_bloom(params):
    def fazer():
        mod = carregar("filtro-bloom", "blm_core")
        r = mod.size_report(params["itens"], params["taxa"])
        return pacote(
            str(r["m_bits"]) + " bits",
            str(r["k_hashes"]) + " hashes. Taxa pedida em fracao (0,01 = 1%).",
        )
    return _chamar(fazer)


def _extrair_pareto(texto):
    if not combina(texto, [("pareto",)]):
        return None
    corpo = _depois(texto, "pareto")
    pares = _pares(corpo or "")
    if len(pares) < 2:
        return None
    return {"nomes": [n for n, _ in pares], "valores": [v for _, v in pares]}


def _calcular_pareto(params):
    def fazer():
        mod = carregar("analisador-pareto", "prt_core")
        r = mod.pareto_analyze(params["nomes"], params["valores"])
        return pacote(
            str(r["k_for_80"]) + " itens para 80%",
            "Total " + _num(r["total"]) + ". Corte A em 80% (padrao da ferramenta).",
        )
    return _chamar(fazer)


def _extrair_spline(texto):
    if not combina(texto, [("spline",)]):
        return None
    if " em " not in norm(texto):
        return None
    corpo = _entre(texto, "spline", " em ")
    if not corpo:
        return None
    xs, ys = [], []
    for bloco in corpo.split(";"):
        nums = [numero_br(p) for p in re.findall(r"\d+(?:[.,]\d+)?", bloco)]
        if len(nums) != 2:
            return None
        xs.append(nums[0])
        ys.append(nums[1])
    if len(xs) < 2:
        return None
    alvo = _depois(texto, " em ")
    if not alvo:
        return None
    m = re.search(r"\d+(?:[.,]\d+)?", alvo)
    if not m:
        return None
    return {"xs": xs, "ys": ys, "x": numero_br(m.group(0))}


def _calcular_spline(params):
    def fazer():
        mod = carregar("estudio-splines", "spl_core")
        curva = mod.natural_cubic_spline(params["xs"], params["ys"])
        y = mod.evaluate_spline(curva, params["x"])
        return pacote(_num(y, 4), "Spline cubica natural.")
    return _chamar(fazer)


def _extrair_cyc(texto):
    if "ciclomatica" not in norm(texto):
        return None
    corpo = _depois(texto, "ciclomatica")
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_cyc(params):
    def fazer():
        mod = carregar("complexidade-ciclomatica", "cyc_core")
        n = mod.complexity_text(params["texto"])
        return pacote(str(n), mod.rank_label(n))
    return _chamar(fazer)


def _extrair_coment(texto):
    if "remover comentarios" not in norm(texto):
        return None
    if " python " not in (" " + norm(texto) + " "):
        return None
    corpo = _depois(texto, "python")
    if corpo is None:
        return None
    return {"texto": corpo}


def _calcular_coment(params):
    def fazer():
        mod = carregar("removedor-comentarios", "scm_core")
        limpo = mod.strip_python(params["texto"])
        return pacote(limpo, mod.stats(params["texto"], limpo))
    return _chamar(fazer)


# ---------------------------------------------------------------- contas que cairam nesta categoria
def _extrair_carnot(texto):
    if not combina(texto, [("carnot",)]):
        return None
    return ler(texto, [
        C("frio", ["frio"], "num", True),
        C("quente", ["quente"], "num", True),
    ])


def _calcular_carnot(params):
    def fazer():
        mod = carregar("simulador-ciclos-termodinamicos", "ctm_core")
        r = mod.calcular_ciclo_carnot(params["frio"], params["quente"])
        return pacote(
            _num(r["rendimento_pct"]) + "%",
            "Temperaturas em kelvin. Calor de entrada 800 kJ/kg (padrao da ferramenta).",
        )
    return _chamar(fazer)


def _extrair_otto(texto):
    if not combina(texto, [("otto",)]):
        return None
    campos = ler(texto, [C("taxa", ["taxa"], "num", True)])
    if not campos:
        return None
    return campos


def _calcular_otto(params):
    def fazer():
        mod = carregar("simulador-ciclos-termodinamicos", "ctm_core")
        r = mod.calcular_ciclo_otto(params["taxa"])
        return pacote(
            _num(r["rendimento_pct"]) + "%",
            "T1 300 K, P1 100 kPa e calor 1200 kJ/kg (padroes da ferramenta).",
        )
    return _chamar(fazer)


def _extrair_filtro(texto):
    if not combina(texto, [("filtro",), ("digital",)]):
        return None
    campos = ler(texto, [
        C("corte", ["corte"], "num", True),
        C("amostragem", ["amostragem"], "num", True),
    ])
    if not campos:
        return None
    t = norm(texto)
    if "altas" in t:
        tipo = "passa_altas"
    elif "faixa" in t:
        tipo = "passa_faixa"
    elif "notch" in t:
        tipo = "notch"
    else:
        tipo = "passa_baixas"
    campos["tipo"] = tipo
    return campos


def _calcular_filtro(params):
    def fazer():
        mod = carregar("laboratorio-filtros-digitais", "fdt_core")
        b, a = mod.projetar_biquad_iir(params["tipo"], params["corte"], params["amostragem"])
        return pacote(
            "b0 " + _num(b[0], 4),
            params["tipo"] + ". Q 0,7071 (padrao da ferramenta). a0 normalizado.",
        )
    return _chamar(fazer)


def _extrair_ir(texto):
    if "ir simplificado" not in norm(texto):
        return None
    return ler(texto, [
        C("dependentes", ["dependentes", "dependente"], "int", False, 0),
        C("rendimento", ["rendimento"], "num", True),
        C("inss", ["inss"], "num", False, 0),
    ])


def _calcular_ir(params):
    def fazer():
        mod = carregar("calculadora-ir-simplificado", "irs_core")
        r = mod.calcular_mensal(params["rendimento"], params["dependentes"], params["inss"])
        return pacote(mod.brl(r.ir_devido), mod.formatar_relatorio(r))
    return _chamar(fazer)


def _extrair_dissidio(texto):
    if not combina(texto, [("dissidio",)]):
        return None
    return ler(texto, [
        C("reajuste", ["reajuste"], "pct", True),
        C("mes", ["mes", "data base"], "int", True),
        C("salario", ["salario"], "num", True),
    ])


def _calcular_dissidio(params):
    def fazer():
        mod = carregar("simulador-dissidio", "dsi_core")
        r = mod.simular(params["salario"], params["reajuste"], params["mes"])
        return pacote(
            mod.brl(r["salario_novo"]),
            "Retroativo 0 meses e sem beneficios (padroes da ferramenta).",
        )
    return _chamar(fazer)


def _extrair_rem(texto):
    if "ciclos rem" not in norm(texto):
        return None
    m = _RE_HORA.search(texto)
    if not m:
        return None
    return {"hora": m.group(1)}


def _calcular_rem(params):
    def fazer():
        mod = carregar("calculadora-ciclos-sono-rem", "csr_core")
        r = mod.calcular_horarios_dormir_para_acordar(params["hora"])
        hora = r["sugestoes"][0]["horario_deitar"]
        return pacote(
            hora,
            "6 ciclos. Latencia 14 min e ciclo de 90 min (padroes da ferramenta).",
        )
    return _chamar(fazer)


def _extrair_cronotipo(texto):
    if not combina(texto, [("cronotipo",)]):
        return None
    return ler(texto, [
        C("acordar", ["acordar"], "int", True),
        C("disposicao", ["disposicao"], "int", True),
        C("dormir", ["dormir"], "int", True),
        C("pico", ["pico"], "int", True),
        C("eu", ["eu"], "int", True),
    ])


def _calcular_cronotipo(params):
    def fazer():
        mod = carregar("analisador-cronotipo-sono-rotina", "cts_core")
        pontos = mod.calcular_pontuacao_meq(
            params["acordar"], params["disposicao"], params["dormir"],
            params["pico"], params["eu"],
        )
        classe = mod.classificar_cronotipo(pontos)
        return pacote(str(pontos) + " " + classe["rotulo"], classe["descricao"])
    return _chamar(fazer)


def _extrair_olhos(texto):
    if "pausa olhos" not in norm(texto):
        return None
    m = _RE_HORA.search(texto)
    campos = ler(texto, [C("horas", ["horas", "hora"], "hora", True)])
    if not m or not campos:
        return None
    return {"horas": campos["horas"], "inicio": m.group(1)}


def _calcular_olhos(params):
    def fazer():
        mod = carregar("planejador-pausa-olhos-20-20-20", "p20_core")
        plano = mod.planejar(params["horas"], params["inicio"])
        return pacote(str(plano.num_pausas) + " pausas", plano.linhas_relatorio()[0])
    return _chamar(fazer)


def _extrair_postura(texto):
    if not combina(texto, [("postura",)]):
        return None
    return ler(texto, [
        C("sentado", ["sentado"], "int", True),
        C("pausa", ["pausa"], "int", True),
        C("sessoes", ["sessoes", "sessao"], "int", True),
    ])


def _calcular_postura(params):
    def fazer():
        mod = carregar("controle-postura-timer", "ptr_core")
        r = mod.gerar_plano(params["sentado"], params["pausa"], params["sessoes"])
        return pacote(r["hora_fim_estimada"], "Comeca as 09:00 (padrao da ferramenta).")
    return _chamar(fazer)


def _extrair_edital(texto):
    if not combina(texto, [("edital",)]):
        return None
    return ler(texto, [
        C("dias", ["dias", "dia"], "int", True),
        C("uteis", ["uteis"], "int", True),
        C("fim", ["fim"], "int", True),
        C("topicos", ["topicos", "topico"], "int", True),
    ])


def _calcular_edital(params):
    def fazer():
        mod = carregar("planejador-cronograma-estudo-edital", "pce_core")
        materias = [{"nome": "Materia", "topicos_restantes": params["topicos"]}]
        r = mod.calcular_cronograma_edital(
            params["dias"], params["uteis"], params["fim"], materias,
        )
        return pacote(
            r["status_viabilidade"],
            "Uma materia, 60 min por topico, peso 1 e 7 dias de reserva (padroes da ferramenta).",
        )
    return _chamar(fazer)


def _extrair_docker(texto):
    if "dockerfile" not in norm(texto):
        return None
    if "auditar" not in norm(texto) and "auditoria" not in norm(texto):
        return None
    corpo = _depois(texto, "dockerfile")
    if not corpo:
        return None
    return {"texto": corpo}


def _calcular_docker(params):
    def fazer():
        mod = carregar("painel-docker", "dck_core")
        r = mod.audit_dockerfile(params["texto"])
        return pacote(str(r["score"]) + " pontos", " | ".join(r["issues"]) or "sem ressalvas")
    return _chamar(fazer)


# ----------------------------------------------------------------------
# Lote 1 Novos Adaptadores Dev & Dados (15 chaves)
# ----------------------------------------------------------------------

# 1. calculadora-cientifica
def _extrair_calc_cientifica(texto):
    if not combina(texto, [["calcular expressao", "calc cientifica", "calculadora cientifica"]]):
        return None
    expr = _depois(texto, "calcular expressao") or _depois(texto, "calc cientifica") or _depois(texto, "calculadora cientifica")
    if not expr:
        return None
    return {"expr": expr.strip()}

def _calcular_calc_cientifica(params):
    def fazer():
        mod = carregar("calculadora-cientifica", "cc_eval")
        res = mod.evaluate(params["expr"])
        return pacote(str(res), f"Expressão: {params['expr']}")
    return _chamar(fazer)


# 2. gerador-gitignore
def _extrair_gitignore(texto):
    if not combina(texto, [["gerar gitignore", "gitignore template"]]):
        return None
    lang = _depois(texto, "gerar gitignore") or _depois(texto, "gitignore template") or "Python"
    return {"lang": lang.strip()}

def _calcular_gitignore(params):
    def fazer():
        mod = carregar("gerador-gitignore", "gig_core")
        t = mod.get_template(params["lang"]) or mod.get_template("Python")
        linhas = len(t.splitlines())
        return pacote(f"{linhas} regras (.gitignore)", f"Template {params['lang']} com {linhas} linhas.")
    return _chamar(fazer)


# 3. gerador-gitattributes
def _extrair_gitattributes(texto):
    if not combina(texto, [["gerar gitattributes", "gitattributes preset"]]):
        return None
    preset = _depois(texto, "gerar gitattributes") or _depois(texto, "gitattributes preset") or "EOL LF (texto)"
    return {"preset": preset.strip()}

def _calcular_gitattributes(params):
    def fazer():
        mod = carregar("gerador-gitattributes", "gat_core")
        attr = mod.build([params["preset"]])
        linhas = len(attr.lines)
        return pacote(f"{linhas} regras (.gitattributes)", f"Preset {params['preset']} gerado com sucesso.")
    return _chamar(fazer)


# 4. gerador-makefile
def _extrair_makefile(texto):
    if not combina(texto, [["gerar makefile", "makefile template"]]):
        return None
    stack = _depois(texto, "gerar makefile") or _depois(texto, "makefile template") or "Python"
    return {"stack": stack.strip()}

def _calcular_makefile(params):
    def fazer():
        mod = carregar("gerador-makefile", "mkf_core")
        m = mod.get_template(params["stack"]) or mod.get_template("Python")
        linhas = len(m.splitlines())
        return pacote(f"{linhas} linhas (Makefile)", f"Makefile para {params['stack']} gerado.")
    return _chamar(fazer)


# 5. gerador-dockerignore
def _extrair_dockerignore(texto):
    if not combina(texto, [["gerar dockerignore", "dockerignore template"]]):
        return None
    stack = _depois(texto, "gerar dockerignore") or _depois(texto, "dockerignore template") or "Python"
    return {"stack": stack.strip()}

def _calcular_dockerignore(params):
    def fazer():
        mod = carregar("gerador-dockerignore", "dik_core")
        out = mod.merge([params["stack"]])
        linhas = len(out.splitlines())
        return pacote(f"{linhas} regras (.dockerignore)", f".dockerignore para {params['stack']} gerado.")
    return _chamar(fazer)


# 6. gerador-pre-commit
def _extrair_precommit(texto):
    if not combina(texto, [["gerar pre-commit", "gerar pre commit", "pre-commit preset"]]):
        return None
    stack = _depois(texto, "gerar pre-commit") or _depois(texto, "gerar pre commit") or _depois(texto, "pre-commit preset") or "Python"
    return {"stack": stack.strip()}

def _calcular_precommit(params):
    def fazer():
        mod = carregar("gerador-pre-commit", "pcc_core")
        out = mod.merge([params["stack"]])
        linhas = len(out.splitlines())
        return pacote(f"{linhas} linhas (.pre-commit-config.yaml)", f"Hooks para {params['stack']} gerados.")
    return _chamar(fazer)


# 7. gerador-badges
def _extrair_badges(texto):
    if not combina(texto, [["gerar badge", "badge shield"]]):
        return None
    rotulo = _depois(texto, "gerar badge") or _depois(texto, "badge shield") or "status"
    return {"rotulo": rotulo.strip()}

def _calcular_badges(params):
    def fazer():
        mod = carregar("gerador-badges", "bdg_core")
        s = mod.shield(params["rotulo"], "ok", color="green")
        return pacote(s, f"Badge Markdown gerado para '{params['rotulo']}'.")
    return _chamar(fazer)


# 8. gerador-codeowners
def _extrair_codeowners(texto):
    if not combina(texto, [["gerar codeowners", "codeowners template"]]):
        return None
    owner = _depois(texto, "gerar codeowners") or _depois(texto, "codeowners template") or "@team"
    return {"owner": owner.strip()}

def _calcular_codeowners(params):
    def fazer():
        mod = carregar("gerador-codeowners", "own_core")
        out = mod.render("Basico", owner=params["owner"])
        linhas = len(out.splitlines())
        return pacote(f"{linhas} linhas (CODEOWNERS)", f"CODEOWNERS para {params['owner']} gerado.")
    return _chamar(fazer)


# 9. gerador-coveragerc
def _extrair_coveragerc(texto):
    if not combina(texto, [["gerar coveragerc", "coveragerc preset"]]):
        return None
    preset = _depois(texto, "gerar coveragerc") or _depois(texto, "coveragerc preset") or "Basico"
    return {"preset": preset.strip()}

def _calcular_coveragerc(params):
    def fazer():
        mod = carregar("gerador-coveragerc", "cov_core")
        out = mod.render(params["preset"])
        linhas = len(out.splitlines())
        return pacote(f"{linhas} linhas (.coveragerc)", f"Configuração de cobertura preset '{params['preset']}'.")
    return _chamar(fazer)


# 10. gerador-eslintignore
def _extrair_eslintignore(texto):
    if not combina(texto, [["gerar eslintignore", "eslintignore template"]]):
        return None
    tmpl = _depois(texto, "gerar eslintignore") or _depois(texto, "eslintignore template") or "Base"
    return {"tmpl": tmpl.strip()}

def _calcular_eslintignore(params):
    def fazer():
        mod = carregar("gerador-eslintignore", "esi_core")
        out = mod.merge([params["tmpl"]])
        linhas = len(out.splitlines())
        return pacote(f"{linhas} regras (.eslintignore)", f".eslintignore para {params['tmpl']} gerado.")
    return _chamar(fazer)


# 11. gerador-github-actions
def _extrair_gha(texto):
    if not combina(texto, [["gerar github actions", "workflow github actions"]]):
        return None
    tmpl = _depois(texto, "gerar github actions") or _depois(texto, "workflow github actions") or "Python CI"
    return {"tmpl": tmpl.strip()}

def _calcular_gha(params):
    def fazer():
        mod = carregar("gerador-github-actions", "gha_core")
        out = mod.render(params["tmpl"])
        linhas = len(out.splitlines())
        return pacote(f"{linhas} linhas (.github/workflows)", f"Workflow '{params['tmpl']}' gerado.")
    return _chamar(fazer)


# 12. gerador-prettierrc
def _extrair_prettierrc(texto):
    if not combina(texto, [["gerar prettierrc", "prettierrc preset"]]):
        return None
    preset = _depois(texto, "gerar prettierrc") or _depois(texto, "prettierrc preset") or "Padrao"
    return {"preset": preset.strip()}

def _calcular_prettierrc(params):
    def fazer():
        mod = carregar("gerador-prettierrc", "ptt_core")
        out = mod.render(params["preset"])
        linhas = len(out.splitlines())
        return pacote(f"{linhas} linhas (.prettierrc)", f"Configuração Prettier '{params['preset']}' gerada.")
    return _chamar(fazer)


# 13. gerador-justfile
def _extrair_justfile(texto):
    if not combina(texto, [["gerar justfile", "justfile preset"]]):
        return None
    preset = _depois(texto, "gerar justfile") or _depois(texto, "justfile preset") or "Python"
    return {"preset": preset.strip()}

def _calcular_justfile(params):
    def fazer():
        mod = carregar("gerador-justfile", "jst_core")
        out = mod.render(params["preset"])
        linhas = len(out.splitlines())
        return pacote(f"{linhas} receitas (justfile)", f"Justfile para {params['preset']} gerado.")
    return _chamar(fazer)


# 14. gerador-taskfile
def _extrair_taskfile(texto):
    if not combina(texto, [["gerar taskfile", "taskfile preset"]]):
        return None
    preset = _depois(texto, "gerar taskfile") or _depois(texto, "taskfile preset") or "Python"
    return {"preset": preset.strip()}

def _calcular_taskfile(params):
    def fazer():
        mod = carregar("gerador-taskfile", "tsk_core")
        out = mod.render(params["preset"])
        linhas = len(out.splitlines())
        return pacote(f"{linhas} linhas (Taskfile.yml)", f"Taskfile para {params['preset']} gerado.")
    return _chamar(fazer)


# 15. gerador-python-version
def _extrair_pyversion(texto):
    if not combina(texto, [["gerar python-version", "gerar python version"]]):
        return None
    ver = _depois(texto, "gerar python-version") or _depois(texto, "gerar python version") or "3.13.0"
    return {"ver": ver.strip()}

def _calcular_pyversion(params):
    def fazer():
        mod = carregar("gerador-python-version", "pyv_core")
        out = mod.render(params["ver"])
        return pacote(out.strip(), f"Arquivo .python-version com versão {params['ver']}.")
    return _chamar(fazer)


_registrar("verificador-hash", ["hash"], _extrair_hash, _calcular_hash)
_registrar("ferramentas-dev", ["base64"], _extrair_b64_enc, _calcular_b64_enc)
_registrar("ferramentas-dev", ["decodificar base64"], _extrair_b64_dec, _calcular_b64_dec)
_registrar("conversor-base64-arquivo", ["expansao base64"], _extrair_expansao, _calcular_expansao)
_registrar("conversor-bases", ["hexadecimal"], _extrair_base, _calcular_base)
_registrar("conversor-bases", ["ieee"], _extrair_ieee, _calcular_ieee)
_registrar("conversor-bases", ["bitwise"], _extrair_bit, _calcular_bit)
_registrar("gerador-identificadores", ["uuid5"], _extrair_uuid5, _calcular_uuid5)
_registrar("gerador-identificadores", ["decodificar uuid"], _extrair_uuid_dec, _calcular_uuid_dec)
_registrar("gerador-identificadores", ["uuid4"], _extrair_uuid4, _calcular_uuid4)
_registrar("gerador-identificadores", ["ulid"], _extrair_ulid, _calcular_ulid)
_registrar("gerador-identificadores", ["snowflake"], _extrair_snow, _calcular_snow)
_registrar("gerador-identificadores", ["colisao nanoid"], _extrair_colisao, _calcular_colisao)
_registrar("explicador-cron", ["cron"], _extrair_cron, _calcular_cron)
_registrar("formatador-sql-ast", ["formatar sql"], _extrair_sql, _calcular_sql)
_registrar("ferramentas-dev", ["formatar json"], lambda t: _extrair_json_acao(t, "formatar"), _calcular_json_fmt)
_registrar("ferramentas-dev", ["minificar json"], lambda t: _extrair_json_acao(t, "minificar"), _calcular_json_mini)
_registrar("ferramentas-dev", ["validar json"], lambda t: _extrair_json_acao(t, "validar"), _calcular_json_val)
_registrar("validador-json-schema", ["inferir schema"], _extrair_schema, _calcular_schema)
_registrar("inspetor-regex", ["regex"], _extrair_regex, _calcular_regex)
_registrar("calculadora-subrede", ["subrede", "cidr"], _extrair_cidr, _calcular_cidr)
_registrar("calculadora-subrede", ["vlsm"], _extrair_vlsm, _calcular_vlsm)
_registrar("gerador-slug", ["slug"], _extrair_slug, _calcular_slug)
_registrar("conversor-path", ["path"], _extrair_path, _calcular_path)
_registrar("formatador-yaml-toml", ["toml", "yaml"], _extrair_yml, _calcular_yml)
_registrar("filtro-bloom", ["bloom"], _extrair_bloom, _calcular_bloom)
_registrar("analisador-pareto", ["pareto"], _extrair_pareto, _calcular_pareto)
_registrar("estudio-splines", ["spline"], _extrair_spline, _calcular_spline)
_registrar("complexidade-ciclomatica", ["ciclomatica"], _extrair_cyc, _calcular_cyc)
_registrar("removedor-comentarios", ["comentarios"], _extrair_coment, _calcular_coment)
_registrar("simulador-ciclos-termodinamicos", ["carnot"], _extrair_carnot, _calcular_carnot)
_registrar("simulador-ciclos-termodinamicos", ["otto"], _extrair_otto, _calcular_otto)
_registrar("laboratorio-filtros-digitais", ["filtro digital"], _extrair_filtro, _calcular_filtro)
_registrar("calculadora-ir-simplificado", ["ir simplificado"], _extrair_ir, _calcular_ir)
_registrar("simulador-dissidio", ["dissidio"], _extrair_dissidio, _calcular_dissidio)
_registrar("calculadora-ciclos-sono-rem", ["ciclos rem"], _extrair_rem, _calcular_rem)
_registrar("analisador-cronotipo-sono-rotina", ["cronotipo"], _extrair_cronotipo, _calcular_cronotipo)
_registrar("planejador-pausa-olhos-20-20-20", ["pausa olhos"], _extrair_olhos, _calcular_olhos)
_registrar("controle-postura-timer", ["postura"], _extrair_postura, _calcular_postura)
_registrar("planejador-cronograma-estudo-edital", ["edital"], _extrair_edital, _calcular_edital)
_registrar("painel-docker", ["dockerfile"], _extrair_docker, _calcular_docker)

# 15 novos adaptadores T03
_registrar("calculadora-cientifica", ["calcular expressao", "calc cientifica"], _extrair_calc_cientifica, _calcular_calc_cientifica)
_registrar("gerador-gitignore", ["gerar gitignore"], _extrair_gitignore, _calcular_gitignore)
_registrar("gerador-gitattributes", ["gerar gitattributes"], _extrair_gitattributes, _calcular_gitattributes)
_registrar("gerador-makefile", ["gerar makefile"], _extrair_makefile, _calcular_makefile)
_registrar("gerador-dockerignore", ["gerar dockerignore"], _extrair_dockerignore, _calcular_dockerignore)
_registrar("gerador-pre-commit", ["gerar pre-commit", "gerar pre commit"], _extrair_precommit, _calcular_precommit)
_registrar("gerador-badges", ["gerar badge"], _extrair_badges, _calcular_badges)
_registrar("gerador-codeowners", ["gerar codeowners"], _extrair_codeowners, _calcular_codeowners)
_registrar("gerador-coveragerc", ["gerar coveragerc"], _extrair_coveragerc, _calcular_coveragerc)
_registrar("gerador-eslintignore", ["gerar eslintignore"], _extrair_eslintignore, _calcular_eslintignore)
_registrar("gerador-github-actions", ["gerar github actions"], _extrair_gha, _calcular_gha)
_registrar("gerador-prettierrc", ["gerar prettierrc"], _extrair_prettierrc, _calcular_prettierrc)
_registrar("gerador-justfile", ["gerar justfile"], _extrair_justfile, _calcular_justfile)
_registrar("gerador-taskfile", ["gerar taskfile"], _extrair_taskfile, _calcular_taskfile)
_registrar("gerador-python-version", ["gerar python-version", "gerar python version"], _extrair_pyversion, _calcular_pyversion)
