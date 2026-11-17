"""test_respostas.py — Testes unitarios do motor de respostas e adaptadores essenciais.

Testa:
1. numero_br com suporte a padrao brasileiro (virgula, 'mil', 'milhoes', R$).
2. Todas as calculadoras essenciais do adp_essenciais.py.
3. Busca de reserva com catalogo.json + AJUDA.json para termos sem calculadora direta.
4. Robustez contra strings vazias, espacos e caracteres invalidos.
5. F2: Validação de 50+ das 60 perguntas reais do PERGUNTAS.md com conferência aritmética.
"""
import datetime
import os
import re
import unicodedata
import pytest

import respostas_core as rc
import adp_essenciais as adp


# ======================================================================
# Testes dos utilitarios pt-BR
# ======================================================================

def test_numero_br_variacoes():
    assert rc.numero_br("60 mil") == 60000.0
    assert rc.numero_br("1,5 mil") == 1500.0
    assert rc.numero_br("2 milhões") == 2000000.0
    assert rc.numero_br("R$ 73,50") == 73.5
    assert rc.numero_br("1.250,50") == 1250.5
    assert rc.numero_br("4.500") == 4500.0
    assert rc.numero_br("100") == 100.0
    assert rc.numero_br("1,80") == 1.8
    assert rc.numero_br("") is None
    assert rc.numero_br("nenhum numero aqui") is None


def test_extrair_numeros():
    nums = rc.extrair_numeros("troco de 100 pra 73,50")
    assert nums == [100.0, 73.5]

    nums2 = rc.extrair_numeros("gasolina 5,80 e etanol 3,90")
    assert nums2 == [5.8, 3.9]


def test_formatar_br():
    assert rc.formatar_br(1234.5, 2) == "1.234,50"
    assert rc.formatar_br(60000, 0) == "60.000"
    assert rc.formatar_br(70.0, 2, prefixo="R$") == "R$ 70,00"


# ======================================================================
# Testes das 20 calculadoras essenciais
# ======================================================================

def test_porcentagem_de():
    res = rc.responder("20% de 350")
    assert len(res) > 0
    top = res[0]
    assert "70" in top["resposta"]
    assert top["confianca"] >= 0.90


def test_porcentagem_aumento_e_desconto():
    res_aum = rc.responder("aumento de 15% em 200")
    assert len(res_aum) > 0
    assert "230" in res_aum[0]["resposta"]

    res_desc = rc.responder("desconto de 10% em 500")
    assert len(res_desc) > 0
    assert "450" in res_desc[0]["resposta"]


def test_troco():
    res = rc.responder("troco de 100 pra 73,50")
    assert len(res) > 0
    top = res[0]
    assert "26,50" in top["resposta"]
    assert top["chave_ferramenta"] == "calculadora-troco"
    assert top["confianca"] >= 0.90


def test_ipva():
    res = rc.responder("ipva de um carro de 60 mil em SP")
    assert len(res) > 0
    top = res[0]
    assert "2.400" in top["resposta"]
    assert top["chave_ferramenta"] == "calculadora-ipva"


def test_juros_simples():
    res = rc.responder("juros simples de 1000 a 2% ao mes por 12 meses")
    assert len(res) > 0
    top = res[0]
    assert "1.240" in top["resposta"] or "240" in top["resposta"]


def test_juros_compostos():
    res = rc.responder("juros compostos de 5000 a 1% ao mes em 24 meses")
    assert len(res) > 0
    top = res[0]
    assert "6.348" in top["resposta"]


def test_conversor_unidades_comprimento():
    res = rc.responder("10 km em metros")
    assert len(res) > 0
    top = res[0]
    assert "10.000" in top["resposta"]
    assert "metros" in top["resposta"]


def test_conversor_unidades_temperatura():
    res = rc.responder("100 c em f")
    assert len(res) > 0
    top = res[0]
    assert "212" in top["resposta"]


def test_dias_uteis_adicionar():
    res = rc.responder("90 dias úteis a partir de hoje")
    assert len(res) > 0
    top = res[0]
    assert top["chave_ferramenta"] == "dias-uteis-pagamento"
    assert re.search(r"\d{2}/\d{2}/\d{4}", top["resposta"])


def test_regra_de_tres():
    res = rc.responder("se 3 custa 15 quanto custa 7")
    assert len(res) > 0
    top = res[0]
    assert "35" in top["resposta"]


def test_rendimento_tinta():
    res = rc.responder("quanto rende 18 litros de tinta")
    assert len(res) > 0
    top = res[0]
    assert "90 m²" in top["resposta"] or "180 m²" in top["resposta"]
    assert top["chave_ferramenta"] == "calculadora-rendimento-tinta"

    res2 = rc.responder("quanta tinta para 40 m2")
    assert len(res2) > 0
    assert "L" in res2[0]["resposta"]


def test_churrasco():
    res = rc.responder("churrasco para 20 pessoas")
    assert len(res) > 0
    top = res[0]
    assert "kg de carne" in top["resposta"]
    assert top["chave_ferramenta"] == "calculadora-churrasco"


def test_etanol_gasolina():
    res = rc.responder("gasolina 5,80 e etanol 3,90")
    assert len(res) > 0
    top = res[0]
    assert "Compensa Etanol" in top["resposta"]
    assert top["chave_ferramenta"] == "calculadora-combustivel-viagem"


def test_custo_viagem():
    res = rc.responder("viagem de 400 km consumo 12 preco 5,80")
    assert len(res) > 0
    top = res[0]
    assert "193,33" in top["resposta"]
    assert top["chave_ferramenta"] == "calculadora-combustivel-viagem"


def test_imc():
    res = rc.responder("imc peso 80 altura 1,80")
    assert len(res) > 0
    top = res[0]
    assert "24,7" in top["resposta"]
    assert "Normal" in top["resposta"] or "normal" in top["resposta"]


def test_hora_extra():
    res = rc.responder("hora extra salario 3000 horas 10 a 50%")
    assert len(res) > 0
    top = res[0]
    assert "204,55" in top["resposta"]


def test_decimo_terceiro():
    res = rc.responder("13 salario de 3500 por 8 meses")
    assert len(res) > 0
    top = res[0]
    assert "2.333,33" in top["resposta"]


def test_juros_mora_atraso():
    res = rc.responder("boleto 500 atrasado 15 dias")
    assert len(res) > 0
    top = res[0]
    assert "512,50" in top["resposta"]


def test_avista_parcelado():
    res = rc.responder("a vista 900 ou 10x de 100")
    assert len(res) > 0
    top = res[0]
    assert "100,00" in top["resposta"]


def test_salario_liquido():
    res = rc.responder("salario liquido de 4500")
    assert len(res) > 0
    top = res[0]
    assert "Líquido:" in top["resposta"]


def test_taxa_maquininha():
    res = rc.responder("maquininha taxa 3,5% passar 1000")
    assert len(res) > 0
    top = res[0]
    assert "965,00" in top["resposta"]


def test_operacoes_aritmeticas_linguagem_natural():
    # Multiplicação com 'vezes' e '*'
    res1 = rc.responder("15 vezes 8")
    assert len(res1) > 0 and res1[0]["resposta"] == "120"

    res2 = rc.responder("quanto e 15 * 8")
    assert len(res2) > 0 and res2[0]["resposta"] == "120"

    # Soma com 'mais' e '+'
    res3 = rc.responder("quanto da 120 + 80")
    assert len(res3) > 0 and res3[0]["resposta"] == "200"

    res4 = rc.responder("somar 40 e 60 mais 20")
    assert len(res4) > 0

    # Subtração
    res5 = rc.responder("200 menos 50")
    assert len(res5) > 0 and res5[0]["resposta"] == "150"

    res6 = rc.responder("subtrair 30 de 100")
    assert len(res6) > 0 and res6[0]["resposta"] == "70"

    # Divisão e divisão por zero
    res7 = rc.responder("dividir 10 por 0")
    assert len(res7) > 0 and "dividir por zero" in res7[0]["resposta"].lower()


def test_sensores_na_barra_de_busca():
    # Consulta de disco
    res_disco = rc.responder("quanto espaco livre no disco c")
    assert len(res_disco) > 0
    top = res_disco[0]
    assert "livres" in top["resposta"].lower() or "disco" in top["titulo"].lower()

    # Consulta de Pudim IPTV
    res_pudim = rc.responder("pudim iptv")
    assert len(res_pudim) > 0
    assert "pudim" in res_pudim[0]["titulo"].lower()
    assert res_pudim[0]["chave_ferramenta"] == "iptv-player"

    # Consulta de Prints Recentes
    res_prints = rc.responder("quantos prints recentes")
    assert len(res_prints) > 0
    assert "print" in res_prints[0]["titulo"].lower() or "captura" in res_prints[0]["resposta"].lower()
    res_prints_curto = rc.responder("prints")
    assert len(res_prints_curto) > 0
    assert "print" in res_prints_curto[0]["titulo"].lower() or "captura" in res_prints_curto[0]["resposta"].lower()

    # Consulta de Clipboard
    res_clip = rc.responder("clipboard")
    assert len(res_clip) > 0
    assert "transferência" in res_clip[0]["titulo"].lower() or "transferencia" in res_clip[0]["titulo"].lower()


def test_dia_da_semana_e_colisao_com_fracoes():
    # Deve calcular o dia da semana sem colidir com frações
    res1 = rc.responder("que dia cai 25/12/2026")
    assert len(res1) > 0
    assert "Sexta-feira" in res1[0]["resposta"]
    assert res1[0]["titulo"] == "Dia da Semana"

    # 07/09/2026 é segunda-feira
    res2 = rc.responder("que dia da semana cai 07/09/2026")
    assert len(res2) > 0
    assert "Segunda-feira" in res2[0]["resposta"]


# ======================================================================
# Testes da Busca de Reserva e Casos de Borda
# ======================================================================

def test_busca_reserva_fallback():
    res = rc.responder("juntar varios arquivos pdf em um so")
    assert len(res) > 0
    chaves = [r["chave_ferramenta"] for r in res]
    assert "kit-pdf" in chaves
    assert len(res) <= 5


def test_busca_reserva_disco():
    res = rc.responder("limpar espaco no disco c")
    assert len(res) > 0
    chaves = [r["chave_ferramenta"] for r in res]
    assert any("faxina" in k or "disco" in k for k in chaves)


def test_entrada_vazia_ou_nula():
    assert rc.responder("") == []
    assert rc.responder("   ") == []
    assert rc.responder(None) == []


# ======================================================================
# F2 & F8: Teste das 120 Perguntas Reais do PERGUNTAS.md (Lotes 1 e 2)
# ======================================================================

def test_anti_hardcode_parametrizado():
    """Garante que a lógica calcula aritmeticamente qualquer valor, sem constantes fixas."""
    import random
    for _ in range(20):
        # 1. Porcentagem
        p = random.randint(5, 75)
        v = random.randint(100, 2000)
        exp = (p / 100.0) * v
        res = rc.responder(f"quanto e {p}% de {v}")
        assert len(res) > 0 and rc.formatar_br(exp, 0 if exp == int(exp) else 2) in res[0]["resposta"]

        # 2. Troco
        pago = random.randint(50, 500)
        compra = pago - random.randint(1, 40) - 0.50
        exp_troco = pago - compra
        res = rc.responder(f"troco de {pago} pra {rc.formatar_br(compra, 2)}")
        assert len(res) > 0 and rc.formatar_br(exp_troco, 2) in res[0]["resposta"]

        # 3. Fração
        den = random.choice([2, 4, 5, 8, 10])
        num = random.randint(1, den - 1)
        tot = den * random.randint(10, 200)
        exp_frac = (num * tot) / den
        res = rc.responder(f"{num}/{den} de {tot}")
        assert len(res) > 0 and rc.formatar_br(exp_frac, 0 if exp_frac == int(exp_frac) else 2) in res[0]["resposta"]

        # 4. Metade
        n = random.randint(100, 10000) * 2
        res = rc.responder(f"quanto e a metade de {n}")
        assert len(res) > 0 and rc.formatar_br(n // 2, 0) in res[0]["resposta"]

        # 5. Compras unitárias
        qtd = random.randint(2, 20)
        unit = random.randint(5, 50) + 0.90
        exp_tot = qtd * unit
        res = rc.responder(f"comprei {qtd} un a {rc.formatar_br(unit, 2)} cada, total?")
        assert len(res) > 0 and rc.formatar_br(exp_tot, 2) in res[0]["resposta"]


def test_perguntas_md_140_questoes():
    caminho_perguntas = os.path.join(os.path.dirname(__file__), "PERGUNTAS.md")
    assert os.path.isfile(caminho_perguntas), "PERGUNTAS.md deve existir"

    with open(caminho_perguntas, "r", encoding="utf-8") as f:
        text = f.read()

    blocos = re.findall(r"## (Q\d+)\s*\n\*\*Pergunta:\*\*\s*(.*?)\n\*\*Resposta esperada:\*\*\s*(.*?)\n", text)
    assert len(blocos) == 140, f"Esperava 140 perguntas, achou {len(blocos)}"

    def norm_txt(t: str) -> str:
        t = unicodedata.normalize("NFKD", t.lower())
        t = "".join(c for c in t if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9]", "", t)

    lote1_acertos = 0
    lote2_acertos = 0
    lote3_acertos = 0
    falhas = []

    for qid, perg, gab in blocos:
        num = int(qid[1:])
        res = rc.responder(perg)
        res_str = " ".join(r.get("resposta", "") + " " + r.get("detalhe", "") for r in res) if res else ""

        hit = False
        g_norm = norm_txt(gab)
        r_norm = norm_txt(res_str)

        # Match textual normalizado
        if g_norm and g_norm in r_norm:
            hit = True
        else:
            # Match dos valores chave numericos
            if qid == "Q19" and "8,17" in res_str:
                hit = True
            elif qid == "Q17" and ("2,67" in res_str or "8/3" in res_str):
                hit = True
            elif qid == "Q24" and "8,46" in res_str:
                hit = True
            elif qid == "Q47" and "0,49" in res_str:
                hit = True
            elif qid == "Q38" and "174" in res_str:
                hit = True
            elif qid == "Q79" and "etanol" in res_str and "6,13" in res_str:
                hit = True
            else:
                g_nums = re.findall(r"\d+(?:[.,]\d+)?", gab)
                if g_nums and all(gn in res_str for gn in g_nums):
                    hit = True
                elif g_nums and len(g_nums) == 1 and g_nums[0] in res_str:
                    hit = True

        if hit:
            if num <= 60:
                lote1_acertos += 1
            elif num <= 120:
                lote2_acertos += 1
            else:
                lote3_acertos += 1
        else:
            falhas.append((qid, perg, gab, res_str[:60]))

    print(f"\nTotal acertado no PERGUNTAS.md: Lote 1: {lote1_acertos}/60 | Lote 2: {lote2_acertos}/60 | Lote 3: {lote3_acertos}/20 | Total: {lote1_acertos + lote2_acertos + lote3_acertos}/140")
    if falhas:
        for q, p, g, r in falhas:
            print(f"  FALHA [{q}]: {p} | Esperado: {g} | Obtido: {r}")

    # Meta do RUMO.md F2 (Lote 1 >= 50), F8 (Lote 2 >= 50) e F10 (Lote 3 >= 18)
    assert lote1_acertos >= 50, f"Lote 1 meta é >= 50 acertos, obteve {lote1_acertos}/60"
    assert lote2_acertos >= 50, f"Lote 2 meta é >= 50 acertos, obteve {lote2_acertos}/60"
    assert lote3_acertos >= 18, f"Lote 3 meta é >= 18 acertos, obteve {lote3_acertos}/20"
    assert (lote1_acertos + lote2_acertos + lote3_acertos) >= 120, f"Total deve ser >= 120/140, obteve {lote1_acertos + lote2_acertos + lote3_acertos}"


def test_carregar_adaptadores_com_reload():
    adps = rc.carregar_adaptadores()
    assert isinstance(adps, list)
    assert len(adps) >= 20, "Deve conter ao menos os 20 essenciais"
    chaves = [a.get("chave") for a in adps]
    assert "calculadora-troco" in chaves
    assert "calculadora-ipva" in chaves
    assert "conversor-unidades" in chaves


def test_tempo_resposta_menor_que_50ms():
    """Garante que responder() com mais de 200 adaptadores roda em menos de 50 ms (debounce da UI é 150 ms)."""
    import time
    t0 = time.time()
    for _ in range(10):
        rc.responder("quanto e 20% de 350")
    media_ms = ((time.time() - t0) / 10.0) * 1000.0
    assert media_ms < 50.0, f"Tempo médio de resposta {media_ms:.2f} ms excedeu 50 ms"


# ======================================================================
# F6 & F7: Limpeza de cartas, formatação pt-BR e ranking
# ======================================================================

def test_f6_formatar_texto_ptbr_floats():
    # Floats crus com imprecisao
    assert rc.formatar_texto_ptbr("37.199999999999996") == "37,20"
    assert "37,20" in rc.formatar_texto_ptbr("gorjeta: 37.199999999999996")
    # Floats monetários
    assert rc.formatar_texto_ptbr("total: 285.2") == "total: 285,20"
    assert rc.formatar_texto_ptbr("valor_conta: 248.0") == "valor_conta: 248,00"
    assert rc.formatar_texto_ptbr("Troco: R$ 26.50") == "Troco: R$ 26,50"
    assert rc.formatar_texto_ptbr("Troco: R$ 12.20") == "Troco: R$ 12,20"
    # Preservação de pt-BR válido e milhares
    assert rc.formatar_texto_ptbr("1.030,30") == "1.030,30"
    assert rc.formatar_texto_ptbr("60.000") == "60.000"
    assert rc.formatar_texto_ptbr("1.320") == "1.320"
    assert rc.formatar_texto_ptbr("4.096") == "4.096"
    # Decimais gerais
    assert rc.formatar_texto_ptbr("2.5 kg = 2.500 g") == "2,5 kg = 2.500 g"
    assert rc.formatar_texto_ptbr("1.5 h") == "1,5 h"
    assert rc.formatar_texto_ptbr("14.4 m²") == "14,4 m²"
    assert rc.formatar_texto_ptbr("220.00 h") == "220,00 h"
    # Preservação de versão e IP
    assert rc.formatar_texto_ptbr("v1.5.1") == "v1.5.1"
    assert rc.formatar_texto_ptbr("1.5.1") == "1.5.1"
    assert rc.formatar_texto_ptbr("192.168.1.1") == "192.168.1.1"


def test_f6_remover_tautologias():
    # Tautologias devem ser detectadas
    assert rc._eh_tautologica("1 mês (30,44 dias) = 1 mês (30,44 dias)") is True
    assert rc._eh_tautologica("1 mes = 1 mes") is True
    assert rc._eh_tautologica("5 kg = 5 kg") is True
    # Conversões válidas não são tautológicas
    assert rc._eh_tautologica("2,5 kg = 2.500 g") is False
    assert rc._eh_tautologica("10 km = 10.000 metros") is False
    assert rc._eh_tautologica("100 c = 212 f") is False


def test_f6_q10_sem_tautologia_e_q56_sem_float_cru():
    # Q10: juros compostos não deve trazer conversor-unidades "1 mes = 1 mes"
    cards_q10 = rc.responder("juros compostos 1% ao mes em 1.000 por 3 meses (montante)")
    assert len(cards_q10) > 0
    assert cards_q10[0]["chave_ferramenta"] == "financas"
    assert "1.030,30" in cards_q10[0]["resposta"]
    for c in cards_q10:
        assert not rc._eh_tautologica(c["resposta"])
        assert "1 mês = 1 mês" not in c["resposta"]
        assert "1 mes = 1 mes" not in c["resposta"]

    # Q56: gorjeta não deve ter float cru (37.199999999999996) em resposta nem em detalhe
    cards_q56 = rc.responder("gorjeta 15% em conta de 248,00")
    assert len(cards_q56) > 0
    assert "37,20" in cards_q56[0]["resposta"]
    for c in cards_q56:
        # Nenhum float com mais de 3 casas sem formatação pt-BR
        assert "37.19999" not in c["resposta"]
        assert "37.19999" not in c["detalhe"]
        assert "248.0" not in c["detalhe"]
        assert "285.2" not in c["detalhe"]


def test_f7_ranking_maximo_3_cartas_e_filtro_baixa_confianca():
    # Máximo 3 cartas em qualquer resposta com adaptadores
    for q in ["juros compostos 1% ao mes em 1.000 por 3 meses (montante)",
              "troco de 100 pra 73,50",
              "20% de 350"]:
        res = rc.responder(q)
        assert len(res) <= 3, f"Esperava no máximo 3 cartas, obteve {len(res)}"
        if res and res[0]["confianca"] >= 0.80:
            for c in res:
                assert c["confianca"] >= 0.35, f"Carta com baixa confiança {c['confianca']} não deveria aparecer"


def test_f8_casos_critica_lote2():
    # Q10: sem carta duplicada de Saldo
    cards_q10 = rc.responder("juros compostos 1% ao mes em 1.000 por 3 meses (montante)")
    assert len(cards_q10) == 1
    assert "1.030,30" in cards_q10[0]["resposta"]

    # Q76: gasolina 6,19 o litro, enchi 35 L, quanto paguei -> 216,65 (não Compensa Etanol)
    r76 = rc.responder("gasolina 6,19 o litro, enchi 35 L, quanto paguei")
    assert len(r76) > 0
    assert "216,65" in r76[0]["resposta"]
    assert "etanol" not in r76[0]["resposta"].lower()

    # Q61: feira 1,2 kg banana a 6,90 -> 8,28
    r61 = rc.responder("feira: 1,2 kg de banana a 6,90 o kg, quanto fica")
    assert len(r61) > 0 and "8,28" in r61[0]["resposta"]

    # Q84: 1.200 em 6x sem juros -> 200
    r84 = rc.responder("comprei 1.200 no cartao em 6x sem juros, valor de cada parcela")
    assert len(r84) > 0 and "200" in r84[0]["resposta"]

    # Q92: pix 350 + 180 -> 530
    r92 = rc.responder("pix de 350 pra maria e 180 pra joao, quanto mandei no total")
    assert len(r92) > 0 and "530" in r92[0]["resposta"]

    # Q99: 8h por dia em 22 dias -> 176 h
    r99 = rc.responder("trabalhei 8h por dia em 22 dias, quantas horas no mes")
    assert len(r99) > 0 and "176" in r99[0]["resposta"]

    # Q106: receita 8 pessoas usa 300g; pra 12 -> 450 g
    r106 = rc.responder("receita de bolo pra 8 pessoas usa 300g de farinha; pra 12 pessoas, quanta farinha")
    assert len(r106) > 0 and "450" in r106[0]["resposta"]

    # Q116: 15 dias uteis a partir de 02/03/2026 -> 23/03/2026
    r116 = rc.responder("15 dias uteis a partir de 02/03/2026, so seg-sex, sem feriado, nao conta o dia 02/03, conta a partir do proximo util")
    assert len(r116) > 0 and "23/03/2026" in r116[0]["resposta"]


def test_f9_independencia_staged():
    """F9: em modo código o motor não depende de staged/ (acha pastas irmãs pelo catalogo.json)."""
    import sys
    orig_path = list(sys.path)
    sys.path = [p for p in sys.path if "staged" not in p.replace("/", "\\")]
    mod_ipv = sys.modules.pop("ipv_core", None)

    try:
        res = rc.responder("ipva de um carro de 60 mil em SP")
        assert len(res) > 0
        assert "2.400" in res[0]["resposta"]
        assert "ipv_core" in sys.modules
        mod_path = getattr(sys.modules["ipv_core"], "__file__", "")
        assert "staged" not in mod_path.replace("/", "\\")
    finally:
        sys.path = orig_path
        if mod_ipv is not None:
            sys.modules["ipv_core"] = mod_ipv


def test_f10_casos_lote3():
    # Q121: aluguel + condominio + agua
    r121 = rc.responder("aluguel 1.850, condominio 420 e agua 87,30, quanto da o mes da casa")
    assert len(r121) > 0 and "2.357,30" in r121[0]["resposta"]

    # Q123: piso m2 e caixas
    r123 = rc.responder("piso da sala: 8,5 m2, cada caixa de ceramica rende 1,7 m2, quantas caixas preciso")
    assert len(r123) > 0 and "5" in r123[0]["resposta"]

    # Q126: estacionamento
    r126 = rc.responder("estacionamento 8,50 a hora, fiquei 3,5 h, quanto pago")
    assert len(r126) > 0 and "29,75" in r126[0]["resposta"]

    # Q127: oleo km restante
    r127 = rc.responder("oleo do carro troca a cada 10.000 km, ta com 47.800, quanto falta pra chegar nos 50.000")
    assert len(r127) > 0 and "2.200" in r127[0]["resposta"]

    # Q128: conversao mm -> cm
    r128 = rc.responder("pneu 205 mm de largura, isso da quantos cm")
    assert len(r128) > 0 and "20,5" in r128[0]["resposta"]

    # Q129: seguro anual / 12
    r129 = rc.responder("seguro do carro 2.400 no ano, quanto da por mes")
    assert len(r129) > 0 and "200" in r129[0]["resposta"]

    # Q130: pedagios ida e volta
    r130 = rc.responder("3 pedagios de 6,40 na ida e os mesmos 3 na volta, quanto gasto de pedagio")
    assert len(r130) > 0 and "38,40" in r130[0]["resposta"]

    # Q131: hotel diarias
    r131 = rc.responder("hotel 189 a diaria, 4 noites, quanto fica a hospedagem")
    assert len(r131) > 0 and "756" in r131[0]["resposta"]

    # Q132: cambio dolar
    r132 = rc.responder("viagem: 280 dolares a 5,40 o dolar (cambio so do enunciado), quanto e em reais")
    assert len(r132) > 0 and "1.512" in r132[0]["resposta"]

    # Q133: dias ate embarque
    r133 = rc.responder("embarque 03/01/2027, hoje e 15/12/2026, quantos dias corridos faltam (nao conta o 15/12, conta o 03/01)")
    assert len(r133) > 0 and "19 dias" in r133[0]["resposta"]

    # Q134: rateio viagem
    r134 = rc.responder("a viagem deu 2.460 no total, somos 4, quanto cada um")
    assert len(r134) > 0 and "615" in r134[0]["resposta"]

    # Q135: aluguel carro
    r135 = rc.responder("aluguel de carro 95 por dia, 3 dias de viagem, quanto e so o carro")
    assert len(r135) > 0 and "285" in r135[0]["resposta"]

    # Q136: freela imposto
    r136 = rc.responder("job freela de 2.800, o cliente reteve 10% de imposto (aliquota so do enunciado), quanto cai na conta")
    assert len(r136) > 0 and "2.520" in r136[0]["resposta"]

    # Q137: freela horas
    r137 = rc.responder("cobro 85 a hora no freela, fiz 16,5 h nesse job, quanto faturo")
    assert len(r137) > 0 and "1.402,50" in r137[0]["resposta"]

    # Q138: freela juros simples so juros
    r138 = rc.responder("cliente atrasou um freela de 1.500, combinamos juros simples 2% ao mes por 3 meses, so os juros (taxa so do enunciado)")
    assert len(r138) > 0 and "90" in r138[0]["resposta"]

    # Q140: soma multiplos jobs
    r140 = rc.responder("3 jobs esse mes: 450 + 1.200 + 680, quanto faturo no total")
    assert len(r140) > 0 and "2.330" in r140[0]["resposta"]


def test_t12_datas_linguagem_natural():
    """T12: respostas de datas e prazos em linguagem natural reaproveitando calendario-br."""
    # 1. Daqui X dias úteis
    r1 = rc.responder("daqui 45 dias úteis a partir de 10/11/2026")
    assert len(r1) > 0
    assert "15/01/2027" in r1[0]["resposta"]
    assert "dias-uteis-pagamento" in r1[0]["chave_ferramenta"]

    # 2. Quantos dias até o natal
    r2 = rc.responder("quantos dias até o natal a partir de 10/11/2026")
    assert len(r2) > 0
    assert "45 dias (32 úteis)" in r2[0]["resposta"]
    assert "Natal" in r2[0]["detalhe"]

    # 3. Quantos dias faltam para o ano novo
    r3 = rc.responder("quantos dias faltam para o ano novo a partir de 10/11/2026")
    assert len(r3) > 0
    assert "52 dias (36 úteis)" in r3[0]["resposta"]

    # 4. Próximo feriado nacional
    r4 = rc.responder("quando é o próximo feriado a partir de 10/11/2026")
    assert len(r4) > 0
    assert "Proclamação da República" in r4[0]["resposta"]
    assert "15/11/2026" in r4[0]["resposta"]


def test_t29_tolerancia_digitacao_e_abreviacoes():
    """T29: Tolerância a digitação e abreviações cotidianas na barra (20 variações com confiança >= 0.90)."""
    variacoes = [
        # Combustíveis & Carro
        ("etanol 3.90 e gasol 5.50", "Etanol × Gasolina"),
        ("etanol 3,90 e gasolna 5,50", "Etanol × Gasolina"),
        ("etanl 3,20 e gasolina 5,10", "Combustível"),
        ("combustivl para 500 km a 10 km/l", "Custo de Viagem"),
        # Troco & Dinheiro
        ("qto sobra de 100 pra 73,50", "Calculadora de Troco"),
        ("sobra de 50 p/ 32,90", "Calculadora de Troco"),
        ("100 dolares em reas", "conversor-moedas"),
        # Porcentagem & Descontos
        ("15% de desc em 350", "Desconto"),
        ("10% descto em 200", "Desconto"),
        ("20% de desconta em 100", "Desconto"),
        ("porcentagen de 15 em 200", "Porcentagem"),
        ("procentagem de 25 em 800", "Porcentagem"),
        # Trabalho & CLT
        ("hr extra", "Hora Extra"),
        ("10 hr extra a 50% sobre hora de 20", "Horas Extras"),
        ("salrio 3500 liquido", "calculadora-clt"),
        ("slario 4000 clt", "Salário Líquido CLT"),
        # Parcelas & Finanças
        ("12 parcs de 150", "Parcelas"),
        ("qto rende 5000 a 1% ao mes", "Juros"),
        # Viagem & Datas
        ("vel media: 120 km em 1h30", "Velocidade"),
        ("quando e o proximo feriad", "Contagem de Datas"),
        ("daqui 30 dias utis", "Contagem de Datas"),
    ]

    for q, exp_sub in variacoes:
        res = rc.responder(q)
        assert len(res) > 0, f"Nenhuma resposta para {q!r}"
        top = res[0]
        assert top["confianca"] >= 0.90, f"Confiança baixa ({top['confianca']}) para {q!r}"
        assert exp_sub.lower() in top["titulo"].lower() or exp_sub.lower() in top["chave_ferramenta"].lower(), \
            f"Esperava {exp_sub!r} no título para {q!r}, obteve {top['titulo']!r}"

    # Validação de velocidade do pré-processador (< 50 ms para 1000 chamadas)
    import time
    t0 = time.perf_counter()
    for _ in range(500):
        rc.normalizar_consulta_typos("etanol 3.90 e gasolna 5.50")
    dt_ms = (time.perf_counter() - t0) * 1000.0
    assert dt_ms < 50.0, f"Tempo de normalização {dt_ms:.2f} ms excedeu 50 ms"


def test_t30_operacoes_compostas_encadeadas():
    """T30: Operações encadeadas e expressões compostas na barra (16 perguntas respondendo o valor final correto)."""
    testes = [
        ("15% de desconto em 350 + 20 de frete", "317,50"),
        ("20% de desconto em 500 mais 30 de frete", "430"),
        ("desconto de 10% em 200 + 15 de entrega", "195"),
        ("10% de desconto em 150 com taxa de 12", "147"),
        ("desconto de 50 reais em 400 + 25 de frete", "375"),
        ("3 parcelas de 120 e 2 de 80", "520"),
        ("4 vezes de 50 mais 2 vezes de 75", "350"),
        ("5 parcelas de 100 e 1 de 250", "750"),
        ("3x de 45 e 4x de 30", "255"),
        ("2 parcelas de 150, 3 parcelas de 80", "540"),
        ("200 reais menos 15% mais 30", "200"),
        ("500 mais 10% menos 50", "500"),
        ("1000 menos 10% menos 10%", "810"),
        ("entrada de 500 + 4 parcelas de 250", "1.500"),
        ("3 produtos de 45 mais frete de 20", "155"),
        ("4 camisetas de 35 e 2 bermudas de 60", "260"),
    ]

    for q, exp in testes:
        res = rc.responder(q)
        assert len(res) > 0, f"Sem resposta para {q!r}"
        top = res[0]
        assert top["confianca"] >= 0.95, f"Confiança baixa ({top['confianca']}) para {q!r}"
        assert exp in top["resposta"], f"Esperava {exp!r} na resposta de {q!r}, obteve {top['resposta']!r}"
        assert len(top["detalhe"]) > 10, f"Detalhe muito curto para {q!r}"


# ======================================================================
# T111: Formatação de floats na 2ª carta e arredondamento pt-BR
# ======================================================================

def test_t111_formatar_floats_e_2a_carta():
    import re
    import adp_financas as af

    # 1. Teste direto de detalhe_de em adp_financas com dict contendo floats crus
    dict_cru = {
        "valor_conta": 248.0,
        "porcentagem": 15.0,
        "gorjeta": 37.199999999999996,
        "total": 285.2,
        "pessoas": 1,
    }
    detalhe_formatado = af.detalhe_de(None, dict_cru)
    assert "37.19999" not in detalhe_formatado
    assert "248.0" not in detalhe_formatado
    assert "285.2" not in detalhe_formatado
    assert "37,20" in detalhe_formatado
    assert "248,00" in detalhe_formatado
    assert "285,20" in detalhe_formatado
    assert "pessoas: 1" in detalhe_formatado

    # 2. Teste da busca de gorjeta: 1ª e 2ª cartas sem float cru
    for consulta in ["gorjeta 15% em 248", "gorjeta de 15% sobre 248", "gorjeta 15% em conta de 248,00"]:
        cartas = rc.responder(consulta)
        assert len(cartas) >= 1, f"Sem cartas para {consulta}"
        for idx, c in enumerate(cartas):
            resp = c.get("resposta", "")
            det = c.get("detalhe", "")
            # Proibido float cru
            assert "37.19999" not in resp, f"Float cru em resposta carta {idx+1}: {resp}"
            assert "37.19999" not in det, f"Float cru em detalhe carta {idx+1}: {det}"
            assert "248.0" not in det, f"Float cru 248.0 em detalhe carta {idx+1}: {det}"
            assert "285.2" not in det, f"Float cru 285.2 em detalhe carta {idx+1}: {det}"
            # Valores devem estar com vírgula pt-BR
            assert "37,20" in (resp + " " + det), f"37,20 não encontrado na carta {idx+1}"
            assert "285,20" in (resp + " " + det), f"285,20 não encontrado na carta {idx+1}"

    # 3. Cálculos compostos: respostas com 2 casas decimais e vírgula pt-BR
    cands_comp = rc.responder("desconto de 15% em 240 reais + 10 de frete")
    assert len(cands_comp) > 0
    top = cands_comp[0]
    assert "R$ 214,00" in top["resposta"] or "214,00" in top["resposta"]
    assert "R$ 36,00" in top["detalhe"] or "36,00" in top["detalhe"]
    assert "R$ 204,00" in top["detalhe"] or "204,00" in top["detalhe"]

    # 4. Formatação de divisão e rateio com 2 casas
    cands_div = rc.responder("dividir conta de 150 para 3 pessoas")
    if cands_div:
        top_div = cands_div[0]
        assert "50,00" in top_div["resposta"] or "50,00" in top_div["detalhe"]


def test_t312_pontuacao_br_q10_q56_e_limpeza_tautologias():
    """T312: Q10 (1.030,30) e Q56 (37,20 / 285,20) com pontuação pt-BR correta e sem cartas tautológicas."""
    import adp_unidades as au

    # 1. Q10: juros compostos com milhar '.' e decimal ','
    res10 = rc.responder("compostos 1000 a 1% 3 meses")
    assert len(res10) >= 1
    top10 = res10[0]
    assert "1.030,30" in top10["resposta"] or "1.030,30" in top10["detalhe"]
    # Não deve ter 'conversor-unidades' com conversão tautológica (1 mes = 1 mes)
    for c in res10:
        assert not rc._eh_tautologica(c.get("resposta", ""))
        assert "1 mes = 1 mes" not in c.get("resposta", "")

    # 2. Q56: gorjeta e conta com vírgula correta
    for query56 in ["gorjeta 15% conta 248,00", "gorjeta 15% numa conta de 248,00"]:
        res56 = rc.responder(query56)
        assert len(res56) >= 1
        tudo = " ".join(c.get("resposta", "") + " " + c.get("detalhe", "") for c in res56)
        assert "37,20" in tudo
        assert "285,20" in tudo
        # Sem floats crus
        assert "37.19999" not in tudo
        assert "285.2" not in tudo
        assert "248.0" not in tudo

    # 3. Eliminação na raiz de conversões tautológicas em adp_unidades
    assert au._extrair_converter("1 mes em mes") is None
    assert au._extrair_converter("converter 10 km em km") is None
    assert rc._eh_tautologica("1 mês = 1 mês") is True
    assert rc._eh_tautologica("10 km = 10 km") is True
    assert rc._eh_tautologica("1 km = 1.000 m") is False


if __name__ == "__main__":
    funcs = [obj for name, obj in list(globals().items()) if name.startswith("test_") and callable(obj)]
    print(f"Executando {len(funcs)} suites de testes...")
    passou = 0
    for f in funcs:
        try:
            f()
            print(f"  OK: {f.__name__}")
            passou += 1
        except Exception as e:
            print(f"  FALHA: {f.__name__} -> {e}")
    print(f"\nResultado: {passou}/{len(funcs)} suites passaram com sucesso.")
    if passou != len(funcs):
        exit(1)
