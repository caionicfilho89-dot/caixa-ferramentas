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


def test_sensor_crescimento_com_historico_sintetico():
    """T06: com 2 amostras, devolve top pastas e ação Faxina na #1."""
    import json
    import tempfile
    import time

    with tempfile.TemporaryDirectory() as tmp:
        arq = os.path.join(tmp, "disco_crescimento.json")
        p_dl = os.path.join(tmp, "Downloads")
        p_doc = os.path.join(tmp, "Documents")
        os.makedirs(p_dl)
        os.makedirs(p_doc)
        with open(os.path.join(p_dl, "a.bin"), "wb") as f:
            f.write(b"x" * 5000)
        with open(os.path.join(p_doc, "b.bin"), "wb") as f:
            f.write(b"y" * 1000)

        orig_arq = sc._CRESC_ARQ
        orig_ttl = sc._CRESC_TTL
        orig_cand = sc._pastas_candidatas_crescimento
        try:
            sc._CRESC_ARQ = arq
            sc._CRESC_TTL = 0
            sc._pastas_candidatas_crescimento = lambda: [p_dl, p_doc]

            agora = time.time()
            baseline = {
                "atualizado": agora - 6 * 86400,
                "amostras": [{
                    "ts": agora - 6 * 86400,
                    "pastas": {p_dl: 100, p_doc: 900},
                }],
                "top": [],
            }
            with open(arq, "w", encoding="utf-8") as f:
                json.dump(baseline, f)

            card = sc.sensor_crescimento_disco()
            assert card is not None
            assert card["id"] == "crescimento"
            assert card["acao"]["chave_ferramenta"] == "faxina-disco"
            assert card["acao"]["pasta"] == p_dl
            assert "--pasta" in card["acao"]["args"]
            assert "Downloads" in card["valor"] or "downloads" in card["valor"].lower()
        finally:
            sc._CRESC_ARQ = orig_arq
            sc._CRESC_TTL = orig_ttl
            sc._pastas_candidatas_crescimento = orig_cand


def test_sensor_crescimento_cache_quente_nao_revarre():
    """Cache < 6 h: não chama amostragem pesada."""
    import json
    import tempfile
    import time

    with tempfile.TemporaryDirectory() as tmp:
        arq = os.path.join(tmp, "disco_crescimento.json")
        pasta = os.path.join(tmp, "Downloads")
        orig_arq = sc._CRESC_ARQ
        orig_amostrar = sc._amostrar_pastas_agora
        chamado = {"n": 0}

        def _boom():
            chamado["n"] += 1
            raise AssertionError("não deveria amostrar com cache quente")

        try:
            sc._CRESC_ARQ = arq
            sc._amostrar_pastas_agora = _boom
            agora = time.time()
            with open(arq, "w", encoding="utf-8") as f:
                json.dump({
                    "atualizado": agora,
                    "amostras": [
                        {"ts": agora - 86400, "pastas": {pasta: 10}},
                        {"ts": agora, "pastas": {pasta: 100}},
                    ],
                    "top": [{"pasta": pasta, "delta": 90, "agora": 100}],
                }, f)

            card = sc.sensor_crescimento_disco()
            assert card is not None
            assert chamado["n"] == 0
            assert card["acao"]["pasta"] == pasta
        finally:
            sc._CRESC_ARQ = orig_arq
            sc._amostrar_pastas_agora = orig_amostrar


def test_sensor_bateria():
    """T05: sensor_bateria devolve dict com contrato ou None se for desktop."""
    card = sc.sensor_bateria()
    if card is not None:
        assert card["id"] == "bateria"
        assert "Bateria" in card["titulo"]
        assert "%" in card["valor"]
        assert "acao" in card and "rotulo" in card["acao"]
    else:
        # Em desktops/VMs sem bateria, deve ser None
        assert card is None

    # Simula notebook com 75% carregando
    import ctypes
    orig_fn = sc.ctypes.windll.kernel32.GetSystemPowerStatus

    def _mock_power(byref_s):
        s = byref_s._obj
        s.ACLineStatus = 1
        s.BatteryFlag = 0
        s.BatteryLifePercent = 75
        s.BatteryLifeTime = 0xFFFFFFFF
        return 1

    try:
        sc.ctypes.windll.kernel32.GetSystemPowerStatus = _mock_power
        mock_card = sc.sensor_bateria()
        assert mock_card is not None
        assert mock_card["id"] == "bateria"
        assert "75%" in mock_card["valor"]
        assert "Carregando" in mock_card["valor"]
        assert mock_card["emoji"] == "⚡"
    finally:
        sc.ctypes.windll.kernel32.GetSystemPowerStatus = orig_fn


def test_sensor_windows_update():
    """T05: sensor_windows_update devolve cartão de reinício pendente ou None se em dia."""
    card = sc.sensor_windows_update()
    if card is not None:
        assert card["id"] == "windows_update"
        assert card["emoji"] == "🔄"
        assert "Windows Update" in card["titulo"]
        assert "Reinício" in card["valor"] or "Pendente" in card["valor"]
        assert "ms-settings:windowsupdate" in card["acao"]["comando"]
    else:
        assert card is None


def test_sensor_rede():
    """T31: sensor_rede detecta conexão ativa, tipo e IP local em < 50 ms."""
    t0 = time.perf_counter()
    card = sc.sensor_rede()
    dt_ms = (time.perf_counter() - t0) * 1000.0

    assert dt_ms < 50.0, f"sensor_rede demorou {dt_ms:.2f} ms (limite é 50 ms)"
    assert card is not None
    assert card["id"] == "rede"
    assert card["emoji"] in ["🌐", "📶"]
    assert "Rede" in card["titulo"]
    assert "Conectado" in card["valor"] or "Desconectado" in card["valor"]
    assert "IP local:" in card["detalhe"] or "Nenhuma conexão" in card["detalhe"]
    assert "acao" in card
    assert card["acao"].get("chave_ferramenta") == "rede" or "network" in card["acao"].get("comando", "")


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
