"""test_sensores.py — Testes unitarios dos sensores da Tela Hoje (sensores_core.py).

Testa:
1. Contrato dos dicionarios devolvidos por ler_tudo():
   {"id", "emoji", "titulo", "valor", "detalhe", "acao": {"rotulo", "chave_ferramenta" ou "comando"}}
2. Performance: ler_tudo() roda em menos de 1 segundo (requisito do RUMO.md).
3. Cache em memória e atualização forçada.
4. Validação de dados reais (Disco C:, Downloads, Prints, Pudim, Clipboard).
5. Regra de ouro: cartão sem dado real não aparece.
"""
import os
import time
import pytest

import sensores_core as sc


def test_ler_tudo_tempo_menor_que_1_segundo():
    t0 = time.time()
    dados = sc.ler_tudo(forcar=True)
    dt = time.time() - t0

    assert dt < 1.0, f"ler_tudo demorou {dt:.3f}s (limite é 1.0s)"
    assert isinstance(dados, list)
    assert len(dados) > 0, "Deve haver ao menos o sensor de disco com dados reais"


def test_contrato_dos_sensores():
    dados = sc.ler_tudo(forcar=True)
    for card in dados:
        assert isinstance(card, dict)
        assert "id" in card and isinstance(card["id"], str)
        assert "emoji" in card and isinstance(card["emoji"], str)
        assert "titulo" in card and isinstance(card["titulo"], str)
        assert "valor" in card and isinstance(card["valor"], str) and len(card["valor"]) > 0
        assert "detalhe" in card and isinstance(card["detalhe"], str)

        assert "acao" in card and isinstance(card["acao"], dict)
        acao = card["acao"]
        assert "rotulo" in acao and isinstance(acao["rotulo"], str)
        assert ("chave_ferramenta" in acao) or ("comando" in acao), "Ação deve ter chave_ferramenta ou comando"


def test_sensor_disco_real():
    d = sc.sensor_disco()
    assert d is not None
    assert d["id"] == "disco"
    assert "GB livres" in d["valor"]
    assert d["acao"]["chave_ferramenta"] == "faxina-disco"


def test_sensor_downloads_real():
    d = sc.sensor_downloads()
    # Se a pasta Downloads existe e tem arquivos, deve retornar o card
    if d is not None:
        assert d["id"] == "downloads"
        assert "arquivos soltos" in d["valor"]
        assert "chave_ferramenta" in d["acao"]


def test_sensor_prints_real():
    d = sc.sensor_prints_recentes()
    if d is not None:
        assert d["id"] == "prints"
        assert "captura" in d["valor"]
        assert d["acao"]["chave_ferramenta"] == "print-anotador"


def test_sensor_pudim_real():
    d = sc.sensor_pudim()
    if d is not None:
        assert d["id"] == "pudim"
        assert len(d["valor"]) > 0
        assert "assistindo" in d["detalhe"].lower()


def test_cache_de_sensores():
    # Primeira chamada forçada
    d1 = sc.ler_tudo(forcar=True)
    t_cache = sc._CACHE_TEMPO

    # Segunda chamada imediata: deve usar o mesmo cache
    d2 = sc.ler_tudo(forcar=False)
    assert sc._CACHE_TEMPO == t_cache
    assert len(d1) == len(d2)

    # Chamada forçada: atualiza timestamp
    time.sleep(0.01)
    d3 = sc.ler_tudo(forcar=True)
    assert sc._CACHE_TEMPO > t_cache


def test_sensor_vencimentos_stub_e_isolamento():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        orig_expand = sc.os.path.expanduser
        sc.os.path.expanduser = lambda p: tmp_dir if p == "~" else orig_expand(p)
        try:
            # Sem arquivos: retorna None
            assert sc.sensor_vencimentos() is None

            # Cria arquivo de garantia vencendo em 5 dias
            import json, datetime
            dt_venc = datetime.date.today() + datetime.timedelta(days=5)
            dados = [{"produto": "Notebook Dell", "fim": dt_venc.strftime("%Y-%m-%d")}]
            with open(os.path.join(tmp_dir, ".caixa_garantias.json"), "w", encoding="utf-8") as f:
                json.dump(dados, f)

            card = sc.sensor_vencimentos()
            assert card is not None
            assert card["id"] == "vencimentos"
            assert "Notebook Dell" in card["valor"]
            assert "5 dias" in card["valor"]

            # Adiciona remédio vencendo amanhã (1 dia) — deve se tornar o mais urgente!
            dt_rmd = datetime.date.today() + datetime.timedelta(days=1)
            dados_rmd = [{"nome": "Dipirona", "validade": dt_rmd.strftime("%Y-%m-%d")}]
            with open(os.path.join(tmp_dir, ".caixa_remedios.json"), "w", encoding="utf-8") as f:
                json.dump(dados_rmd, f)

            card2 = sc.sensor_vencimentos()
            assert card2 is not None
            assert "Dipirona" in card2["valor"]
            assert "Vence amanhã!" in card2["valor"]
            assert card2["acao"]["chave_ferramenta"] == "controle-validade-remedios"
            assert "2 item(ns)" in card2["detalhe"]

            # Adiciona conta fixa vencendo hoje (0 dias) — deve liderar a urgência!
            hoje_dia = datetime.date.today().day
            dados_cfx = [{"nome": "Energia CPFL", "dia_vencimento": hoje_dia}]
            with open(os.path.join(tmp_dir, ".caixa_contas_fixas.json"), "w", encoding="utf-8") as f:
                json.dump(dados_cfx, f)

            card3 = sc.sensor_vencimentos()
            assert card3 is not None
            assert "Energia CPFL" in card3["valor"]
            assert "Vence hoje!" in card3["valor"]
            assert card3["acao"]["chave_ferramenta"] == "controle-contas-fixas"
            assert "3 item(ns)" in card3["detalhe"]

            # Adiciona cosmético
            dt_csm = datetime.date.today() + datetime.timedelta(days=10)
            dados_csm = [{"nome": "Protetor Solar", "validade_impressa": dt_csm.strftime("%Y-%m-%d")}]
            with open(os.path.join(tmp_dir, ".caixa_cosmeticos.json"), "w", encoding="utf-8") as f:
                json.dump(dados_csm, f)

            card4 = sc.sensor_vencimentos()
            assert "4 item(ns)" in card4["detalhe"]
        finally:
            sc.os.path.expanduser = orig_expand


if __name__ == "__main__":
    import os
    funcs = [obj for name, obj in list(globals().items()) if name.startswith("test_") and callable(obj)]
    print(f"Executando {len(funcs)} testes de sensores...")
    passou = 0
    for f in funcs:
        try:
            f()
            print(f"  OK: {f.__name__}")
            passou += 1
        except Exception as e:
            print(f"  FALHA: {f.__name__} -> {e}")
    print(f"\nResultado: {passou}/{len(funcs)} testes de sensores passaram com sucesso.")
    if passou != len(funcs):
        exit(1)
