# -*- coding: utf-8 -*-
"""Adaptadores da barra para Imagem & Design e o que caiu nessa categoria.

Cada calcular chama o modulo real. Nao refaz a conta.
"""
from __future__ import annotations

import os
import re
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)

import adp_financas as af

norm = af.norm
combina = af.combina
ler = af.ler
C = af.C
carregar = af.carregar
pacote = af.pacote
_num = af._num

ADAPTADORES = []

_RE_RELOGIO = re.compile(r"\d{1,2}:\d{2}(?::\d{2})?")
_RE_FRACAO = re.compile(r"(\d+)\s*/\s*(\d+)")
_RE_HEX = re.compile(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b")
_RE_DIGITOS = re.compile(r"\d{3,18}")

_HARMONIAS = (
    ("complementar dividida", "Complementar dividida"),
    ("complementar", "Complementar"),
    ("analoga", "Análoga"),
    ("triade", "Tríade"),
    ("tetrade", "Tétrade"),
    ("monocromatica", "Monocromática"),
)
_DALTONISMO = (
    ("protanopia", "Protanopia"),
    ("deuteranopia", "Deuteranopia"),
    ("tritanopia", "Tritanopia"),
    ("acromatopsia", "Acromatopsia"),
)
_RESOLUCOES = (
    ("1080p60", "1080p 60fps"),
    ("1080p30", "1080p 30fps"),
    ("4k60", "4K 60fps"),
    ("4k30", "4K 30fps"),
    ("720p30", "720p 30fps"),
    ("720p", "720p 30fps"),
)


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


def _chamar(fn):
    try:
        return fn()
    except ValueError as e:
        return pacote(str(e).splitlines()[0], "A ferramenta recusou esses dados.")


def _relogio(texto):
    m = _RE_RELOGIO.search(texto)
    return m.group(0) if m else None


def _fracao(texto):
    m = _RE_FRACAO.search(texto)
    if not m:
        return None
    den = int(m.group(2))
    if den == 0:
        return None
    return int(m.group(1)) / den


def _hexes(texto):
    return _RE_HEX.findall(texto)


def _harmonia(texto):
    t = norm(texto)
    for chave, tipo in _HARMONIAS:
        if chave in t:
            return tipo
    return None


def _daltonismo(texto):
    t = norm(texto)
    for chave, tipo in _DALTONISMO:
        if chave in t:
            return tipo
    return None


def _resolucao(texto):
    t = norm(texto)
    for chave, nome in _RESOLUCOES:
        if chave in t:
            return nome
    return None


def _formato_foto(texto):
    t = norm(texto)
    if "heic" in t or "heif" in t:
        return "HEIC"
    if "jpeg" in t or "jpg" in t:
        return "JPEG"
    return None


def _extrair_ritmo(texto):
    if not combina(texto, [("ritmo de corrida",)]):
        return None
    relogio = _relogio(texto)
    dados = ler(texto, [C("km", ["km"], "num", True)])
    if not relogio or not dados:
        return None
    dados["relogio"] = relogio
    return dados


def _calcular_ritmo(params):
    def fazer():
        mod = carregar("pace", "pac_core")
        segundos = mod.parse_time(params["relogio"])
        ritmo = mod.pace_from(segundos, params["km"])
        return pacote(mod.fmt_pace(ritmo), "Ritmo da prova, em minutos por km.")
    return _chamar(fazer)


def _extrair_vo2(texto):
    if not combina(texto, [("vo2max",)]):
        return None
    relogio = _relogio(texto)
    dados = ler(texto, [C("km", ["km"], "num", True)])
    if not relogio or not dados:
        return None
    dados["relogio"] = relogio
    return dados


def _calcular_vo2(params):
    def fazer():
        mod = carregar("pace", "pac_core")
        segundos = mod.parse_time(params["relogio"])
        vo2 = mod.vo2max(params["km"], segundos)
        return pacote(_num(vo2, 1), "VO2max estimado por Daniels e Gilbert.")
    return _chamar(fazer)


def _extrair_riegel(texto):
    if not combina(texto, [("riegel",)]):
        return None
    relogio = _relogio(texto)
    dados = ler(texto, [
        C("base", ["base"], "num", True),
        C("alvo", ["alvo"], "num", True),
    ])
    if not relogio or not dados:
        return None
    dados["relogio"] = relogio
    return dados


def _calcular_riegel(params):
    def fazer():
        mod = carregar("pace", "pac_core")
        segundos = mod.parse_time(params["relogio"])
        previsto = mod.riegel(segundos, params["base"], params["alvo"])
        return pacote(
            mod.fmt_time(previsto),
            "Previsão de Riegel. Expoente 1,06 da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_paleta(texto):
    if not combina(texto, [("paleta",)]):
        return None
    tipo = _harmonia(texto)
    cores = _hexes(texto)
    if not tipo or not cores:
        return None
    return {"tipo": tipo, "hex": cores[0]}


def _calcular_paleta(params):
    def fazer():
        mod = carregar("gerador-paleta-cores", "pal_core")
        cores = mod.harmonia(params["hex"], params["tipo"])
        return pacote(", ".join(cores), params["tipo"] + ".")
    return _chamar(fazer)


def _extrair_texto_ideal(texto):
    if not combina(texto, [("texto ideal",)]):
        return None
    cores = _hexes(texto)
    if not cores:
        return None
    return {"hex": cores[0]}


def _calcular_texto_ideal(params):
    def fazer():
        mod = carregar("gerador-paleta-cores", "pal_core")
        return pacote(mod.texto_ideal(params["hex"]), "Cor de texto com mais contraste.")
    return _chamar(fazer)


def _extrair_wcag(texto):
    if not combina(texto, [("contraste wcag",)]):
        return None
    cores = _hexes(texto)
    if len(cores) < 2:
        return None
    return {"a": cores[0], "b": cores[1]}


def _calcular_wcag(params):
    def fazer():
        mod = carregar("contraste-wcag", "wcg_core")
        razao = mod.contrast(mod.parse_color(params["a"]), mod.parse_color(params["b"]))
        aprovados = [nome for nome, ok in mod.grades(razao).items() if ok]
        detalhe = "Aprovado: " + ", ".join(aprovados) if aprovados else "Nenhum nível da tabela."
        return pacote(_num(razao, 2), detalhe)
    return _chamar(fazer)


def _extrair_daltonismo(texto):
    if not combina(texto, [("daltonismo",)]):
        return None
    tipo = _daltonismo(texto)
    cores = _hexes(texto)
    if not tipo or not cores:
        return None
    return {"tipo": tipo, "hex": cores[0]}


def _calcular_daltonismo(params):
    def fazer():
        mod = carregar("contraste-wcag", "wcg_core")
        rgb = mod.simulate(mod.parse_color(params["hex"]), params["tipo"])
        return pacote(mod.to_hex(rgb), "Simulação de " + params["tipo"] + ".")
    return _chamar(fazer)


def _extrair_escala(texto):
    if not combina(texto, [("escala tipografica",)]):
        return None
    return ler(texto, [
        C("base", ["base"], "num", True),
        C("razao", ["razao"], "num", False, 1.25),
    ])


def _calcular_escala(params):
    def fazer():
        mod = carregar("estudio-tipografia", "tip_core")
        escala = mod.calculate_modular_scale(params["base"], params["razao"])
        return pacote(
            str(escala["h1_px"]).replace(".", ",") + " px",
            "H1 da escala modular. Razão " + _num(params["razao"], 3) + ".",
        )
    return _chamar(fazer)


def _extrair_rle(texto):
    if not combina(texto, [("rle",)]):
        return None
    t = norm(texto)
    if "decodificar" in t:
        corpo = _depois(texto, "decodificar")
        modo = "decodificar"
    elif "codificar" in t:
        corpo = _depois(texto, "codificar")
        modo = "codificar"
    else:
        return None
    if not corpo:
        return None
    return {"modo": modo, "corpo": corpo}


def _calcular_rle(params):
    def fazer():
        mod = carregar("compressao-rle", "rle_core")
        if params["modo"] == "decodificar":
            saida = mod.rle_decode_text(params["corpo"])
        else:
            saida = mod.rle_encode_text(params["corpo"])
        return pacote(saida, "RLE de texto.")
    return _chamar(fazer)


def _extrair_markov(texto):
    if not combina(texto, [("markov",)]):
        return None
    corpo = _depois(texto, "texto")
    dados = ler(texto, [
        C("semente", ["semente"], "int", True),
        C("tamanho", ["tamanho"], "int", True),
    ])
    if not corpo or not dados:
        return None
    dados["corpo"] = corpo
    return dados


def _calcular_markov(params):
    def fazer():
        mod = carregar("gerador-markov", "mkv_core")
        modelo = mod.build_model(mod.tokenize(params["corpo"]), 2)
        frase = mod.generate(modelo, params["tamanho"], params["semente"])
        return pacote(frase, "Ordem 2, padrão da ferramenta. Semente da frase.")
    return _chamar(fazer)


def _extrair_lux(texto):
    if not combina(texto, [("iluminancia",)]):
        return None
    return ler(texto, [
        C("candela", ["candela"], "num", True),
        C("distancia", ["distancia"], "num", True),
    ])


def _calcular_lux(params):
    def fazer():
        mod = carregar("calculadora-fotometria-lux-lumen", "lux_core")
        lux = mod.inverse_square_law(params["candela"], params["distancia"])
        return pacote(_num(lux, 2) + " lux", "Ângulo 0 grau, padrão da ferramenta.")
    return _chamar(fazer)


def _extrair_lumens(texto):
    if not combina(texto, [("metodo dos lumens",)]):
        return None
    return ler(texto, [
        C("comprimento", ["comprimento"], "num", True),
        C("largura", ["largura"], "num", True),
        C("lux", ["lux"], "num", True),
        C("fluxo", ["fluxo"], "num", True),
    ])


def _calcular_lumens(params):
    def fazer():
        mod = carregar("calculadora-fotometria-lux-lumen", "lux_core")
        r = mod.calculate_lumen_method(
            params["comprimento"], params["largura"], params["lux"], params["fluxo"],
        )
        return pacote(
            str(r["num_fixtures"]) + " luminárias",
            "Lâmpada de 12 W, utilização 0,60 e manutenção 0,80, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_solar(texto):
    if not combina(texto, [("fotovoltaica",)]):
        return None
    return ler(texto, [
        C("consumo", ["consumo"], "num", True),
        C("hsp", ["hsp"], "num", True),
    ])


def _calcular_solar(params):
    def fazer():
        mod = carregar("calculadora-fotovoltaica", "pvs_core")
        r = mod.dimensionar(params["consumo"], params["hsp"])
        return pacote(
            str(r["modulos"]) + " módulos",
            "PR 0,78, módulo de 550 Wp e ligação monofásica, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_ev(texto):
    if not combina(texto, [("exposicao fotografica",)]):
        return None
    tempo = _fracao(texto)
    dados = ler(texto, [
        C("f", ["f"], "num", True),
        C("iso", ["iso"], "num", True),
    ])
    if tempo is None or not dados:
        return None
    dados["tempo"] = tempo
    return dados


def _calcular_ev(params):
    def fazer():
        mod = carregar("calculadora-fotografia", "fot_core")
        valor = mod.ev(params["f"], params["tempo"], params["iso"])
        return pacote("EV " + _num(valor, 2), "Exposição da frase.")
    return _chamar(fazer)


def _extrair_nd(texto):
    if not combina(texto, [("filtro nd",)]):
        return None
    tempo = _fracao(texto)
    dados = ler(texto, [C("stops", ["stops"], "num", True)])
    if tempo is None or not dados:
        return None
    dados["tempo"] = tempo
    return dados


def _calcular_nd(params):
    def fazer():
        mod = carregar("calculadora-fotografia", "fot_core")
        novo = mod.tempo_nd(params["tempo"], params["stops"])
        return pacote(mod.formatar_tempo(novo), "Tempo de obturador com o filtro ND.")
    return _chamar(fazer)


def _extrair_impressao(texto):
    if not combina(texto, [("tamanho impressao",)]):
        return None
    return ler(texto, [
        C("largura", ["largura"], "int", True),
        C("altura", ["altura"], "int", True),
        C("dpi", ["dpi"], "int", True),
    ])


def _calcular_impressao(params):
    def fazer():
        mod = carregar("calculadora-fotografia", "fot_core")
        largura, altura = mod.tamanho_impressao_cm(
            params["largura"], params["altura"], params["dpi"],
        )
        return pacote(
            _num(largura, 1) + " x " + _num(altura, 1) + " cm",
            "Tamanho de impressão.",
        )
    return _chamar(fazer)


def _extrair_regra500(texto):
    if not combina(texto, [("regra 500",)]):
        return None
    return ler(texto, [
        C("focal", ["focal"], "num", True),
        C("crop", ["crop"], "num", False, 1.0),
    ])


def _calcular_regra500(params):
    def fazer():
        mod = carregar("calculadora-fotografia", "fot_core")
        segundos = mod.regra_500(params["focal"], params["crop"])
        return pacote(
            _num(segundos, 2) + " s",
            "Regra dos 500. Crop " + _num(params["crop"], 2) + ".",
        )
    return _chamar(fazer)


def _extrair_hiperfocal(texto):
    if not combina(texto, [("hiperfocal",)]):
        return None
    return ler(texto, [
        C("focal", ["focal"], "num", True),
        C("abertura", ["abertura"], "num", True),
        C("largura", ["largura"], "num", True),
        C("altura", ["altura"], "num", True),
    ])


def _calcular_hiperfocal(params):
    def fazer():
        mod = carregar("calculadora-fotografia", "fot_core")
        coc = mod.coc(params["largura"], params["altura"])
        mm = mod.hiperfocal_mm(params["focal"], params["abertura"], coc)
        return pacote(
            _num(mm / 1000.0, 2) + " m",
            "CoC pela diagonal do sensor dividida por 1500, da própria ferramenta.",
        )
    return _chamar(fazer)


def _extrair_piscina(texto):
    if not combina(texto, [("volume piscina",)], ("cloro", "choque", "alcalinidade", "ph")):
        return None
    t = norm(texto)
    if "redonda" in t:
        dados = ler(texto, [
            C("diametro", ["diametro"], "num", True),
            C("profundidade", ["profundidade"], "num", True),
        ])
        if dados:
            dados["forma"] = "redonda"
        return dados
    if "retangular" not in t:
        return None
    dados = ler(texto, [
        C("comprimento", ["comprimento"], "num", True),
        C("largura", ["largura"], "num", True),
        C("profundidade", ["profundidade"], "num", True),
    ])
    if dados:
        dados["forma"] = "retangular"
    return dados


def _calcular_piscina(params):
    def fazer():
        mod = carregar("calculadora-piscina", "psc_core")
        if params["forma"] == "redonda":
            volume = mod.volume_redonda(params["diametro"], params["profundidade"])
        else:
            volume = mod.volume_retangular(
                params["comprimento"], params["largura"], params["profundidade"],
            )
        return pacote(_num(volume, 2) + " m3", "Só o volume. Sem dose de cloro, pH ou alcalinidade.")
    return _chamar(fazer)


def _extrair_cortina(texto):
    if not combina(texto, [("cortina",)]):
        return None
    return ler(texto, [
        C("trilho", ["trilho"], "num", True),
        C("altura", ["altura"], "num", True),
    ])


def _calcular_cortina(params):
    def fazer():
        mod = carregar("metragem-costura", "cst_core")
        r = mod.metros_cortina(params["trilho"], params["altura"])
        return pacote(
            _num(r["metros_compra"], 1) + " m",
            "Franzido 2, barra de 20 cm, tecido de 1,4 m e preço 0, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_mojibake(texto):
    if not combina(texto, [("mojibake",)]):
        return None
    corpo = _depois(texto, "mojibake")
    if not corpo:
        return None
    return {"corpo": corpo}


def _calcular_mojibake(params):
    def fazer():
        mod = carregar("conversor-encoding", "enc_core")
        return pacote(
            mod.fix_mojibake(params["corpo"]),
            "Reinterpretado de latin-1 para utf-8, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_piso(texto):
    if not combina(texto, [("piso vinilico",)]):
        return None
    return ler(texto, [
        C("area", ["area"], "num", True),
        C("largura", ["largura"], "num", True),
        C("comprimento", ["comprimento"], "num", True),
    ])


def _calcular_piso(params):
    def fazer():
        mod = carregar("piso-vinilico", "vin_core")
        r = mod.material(params["area"], params["largura"], params["comprimento"])
        return pacote(
            str(r["caixas"]) + " caixas",
            "Régua em cm. Paginação reta, perda de 10% e 8 réguas por caixa, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_ean(texto):
    if not combina(texto, [("ean", "codigo de barras")], ("pais gs1",)):
        return None
    m = _RE_DIGITOS.search(texto)
    if not m or len(m.group(0)) < 7:
        return None
    return {"digitos": m.group(0)}


def _calcular_ean(params):
    def fazer():
        mod = carregar("codigo-barras", "bar_core")
        return pacote(mod.calc_ean_check_digit(params["digitos"]), "Dígito verificador GS1.")
    return _chamar(fazer)


def _extrair_pais(texto):
    if not combina(texto, [("pais gs1",)]):
        return None
    m = _RE_DIGITOS.search(texto)
    if not m:
        return None
    return {"codigo": m.group(0)}


def _calcular_pais(params):
    def fazer():
        mod = carregar("codigo-barras", "bar_core")
        return pacote(mod.detect_gs1_country(params["codigo"]), "Prefixo GS1.")
    return _chamar(fazer)


def _extrair_grashof(texto):
    if not combina(texto, [("grashof",)]):
        return None
    return ler(texto, [
        C("base", ["base"], "num", True),
        C("manivela", ["manivela"], "num", True),
        C("biela", ["biela"], "num", True),
        C("balancim", ["balancim"], "num", True),
    ])


def _calcular_grashof(params):
    def fazer():
        mod = carregar("simulador-mecanismo-quatro-barras", "mqb_core")
        r = mod.classificar_grashof(
            params["base"], params["manivela"], params["biela"], params["balancim"],
        )
        return pacote(r["classe"], r["tipo"])
    return _chamar(fazer)


def _extrair_simulado(texto):
    if not combina(texto, [("simulado",)]):
        return None
    t = norm(texto)
    if "quadrix" in t:
        modelo = "quadrix_meio_ponto"
    elif "enem" in t or "multipla" in t:
        modelo = "multipla_escolha"
    elif "cespe" in t or "cebraspe" in t:
        modelo = "cespe_1_para_1"
    else:
        return None
    dados = ler(texto, [
        C("total", ["total"], "int", True),
        C("acertos", ["acertos"], "int", True),
        C("erros", ["erros"], "int", True),
        C("branco", ["branco"], "int", False, 0),
        C("tempo", ["tempo"], "int", True),
        C("corte", ["corte"], "num", False, 70.0),
    ])
    if not dados:
        return None
    dados["modelo"] = modelo
    return dados


def _calcular_simulado(params):
    def fazer():
        mod = carregar("analisador-desempenho-simulados", "qsm_core")
        r = mod.calcular_desempenho_simulado(
            params["total"], params["acertos"], params["erros"], params["branco"],
            params["tempo"], params["modelo"], params["corte"],
        )
        return pacote(
            _num(r["pontuacao_liquida"], 1),
            "Pontuação líquida. Corte " + _num(params["corte"], 1) + "%.",
        )
    return _chamar(fazer)


def _extrair_sisu(texto):
    if not combina(texto, [("sisu",)]):
        return None
    return ler(texto, [
        C("redacao", ["redacao"], "num", True),
        C("matematica", ["matematica"], "num", True),
        C("natureza", ["natureza"], "num", True),
        C("humanas", ["humanas"], "num", True),
        C("linguagens", ["linguagens"], "num", True),
    ])


def _calcular_sisu(params):
    def fazer():
        mod = carregar("analisador-nota-corte-sisu-enem", "nce_core")
        r = mod.calcular_sisu_enem(
            params["redacao"], 1,
            params["matematica"], 1,
            params["natureza"], 1,
            params["humanas"], 1,
            params["linguagens"], 1,
        )
        return pacote(
            _num(r["media_ponderada"], 2),
            "Pesos 1, corte 750 e sem bônus, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_fala(texto):
    if not combina(texto, [("ritmo de fala",)]):
        return None
    return ler(texto, [
        C("palavras", ["palavras"], "int", True),
        C("slot", ["slot"], "num", True),
    ])


def _calcular_fala(params):
    def fazer():
        mod = carregar("ritmo-fala-apresentacao", "spm_core")
        r = mod.analisar_apresentacao(params["palavras"], params["slot"])
        return pacote(
            _num(r["wpm_necessario"], 1) + " pal/min",
            "Alvo de 140 palavras por minuto e reserva de 15%, padrões da ferramenta.",
        )
    return _chamar(fazer)


def _extrair_fotos(texto):
    if not combina(texto, [("espaco fotos",)]):
        return None
    formato = _formato_foto(texto)
    resolucao = _resolucao(texto)
    dados = ler(texto, [
        C("livre", ["livre"], "num", True),
        C("megapixels", ["megapixels"], "num", True),
    ])
    if not formato or not resolucao or not dados:
        return None
    dados["formato"] = formato
    dados["resolucao"] = resolucao
    dados["h264"] = "h264" in norm(texto)
    return dados


def _calcular_fotos(params):
    def fazer():
        mod = carregar("espaco-fotos-videos-celular", "arm_core")
        r = mod.calcular(
            params["livre"], params["megapixels"], params["formato"],
            params["resolucao"], params["h264"],
        )
        codec = "H.264" if params["h264"] else "H.265"
        return pacote(
            str(r["so_fotos"]) + " fotos",
            codec + ", metade do espaço para vídeo e sem uso diário, padrões da ferramenta.",
        )
    return _chamar(fazer)


_registrar("pace", ["ritmo de corrida"], _extrair_ritmo, _calcular_ritmo)
_registrar("pace", ["vo2max"], _extrair_vo2, _calcular_vo2)
_registrar("pace", ["riegel"], _extrair_riegel, _calcular_riegel)
_registrar("gerador-paleta-cores", ["paleta"], _extrair_paleta, _calcular_paleta)
_registrar("gerador-paleta-cores", ["texto ideal"], _extrair_texto_ideal, _calcular_texto_ideal)
_registrar("contraste-wcag", ["contraste wcag"], _extrair_wcag, _calcular_wcag)
_registrar("contraste-wcag", ["daltonismo"], _extrair_daltonismo, _calcular_daltonismo)
_registrar("estudio-tipografia", ["escala tipografica"], _extrair_escala, _calcular_escala)
_registrar("compressao-rle", ["rle"], _extrair_rle, _calcular_rle)
_registrar("gerador-markov", ["markov"], _extrair_markov, _calcular_markov)
_registrar("calculadora-fotometria-lux-lumen", ["iluminancia"], _extrair_lux, _calcular_lux)
_registrar("calculadora-fotometria-lux-lumen", ["metodo dos lumens"], _extrair_lumens, _calcular_lumens)
_registrar("calculadora-fotovoltaica", ["fotovoltaica"], _extrair_solar, _calcular_solar)
_registrar("calculadora-fotografia", ["exposicao fotografica"], _extrair_ev, _calcular_ev)
_registrar("calculadora-fotografia", ["filtro nd"], _extrair_nd, _calcular_nd)
_registrar("calculadora-fotografia", ["tamanho impressao"], _extrair_impressao, _calcular_impressao)
_registrar("calculadora-fotografia", ["regra 500"], _extrair_regra500, _calcular_regra500)
_registrar("calculadora-fotografia", ["hiperfocal"], _extrair_hiperfocal, _calcular_hiperfocal)
_registrar("calculadora-piscina", ["volume piscina"], _extrair_piscina, _calcular_piscina)
_registrar("metragem-costura", ["cortina"], _extrair_cortina, _calcular_cortina)
_registrar("conversor-encoding", ["mojibake"], _extrair_mojibake, _calcular_mojibake)
_registrar("piso-vinilico", ["piso vinilico"], _extrair_piso, _calcular_piso)
_registrar("codigo-barras", ["ean"], _extrair_ean, _calcular_ean)
_registrar("codigo-barras", ["pais gs1"], _extrair_pais, _calcular_pais)
_registrar("simulador-mecanismo-quatro-barras", ["grashof"], _extrair_grashof, _calcular_grashof)
_registrar("analisador-desempenho-simulados", ["simulado"], _extrair_simulado, _calcular_simulado)
_registrar("analisador-nota-corte-sisu-enem", ["sisu"], _extrair_sisu, _calcular_sisu)
_registrar("ritmo-fala-apresentacao", ["ritmo de fala"], _extrair_fala, _calcular_fala)
_registrar("espaco-fotos-videos-celular", ["espaco fotos"], _extrair_fotos, _calcular_fotos)
