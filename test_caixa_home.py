"""Testes da tela Hoje (caixa_home.py). Usa stub de sensores_core."""
from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PyQt6.QtCore import QEventLoop, QTimer  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

import caixa_home as home  # noqa: E402

_APP = QApplication.instance() or QApplication(sys.argv)


def _stub_sensores():
    return [
        {
            "id": "disco",
            "emoji": "💾",
            "titulo": "Disco C:",
            "valor": "42 GB livres",
            "detalhe": "de 512 GB · 8% livre",
            "acao": {"rotulo": "Liberar espaço", "chave_ferramenta": "disk-analyzer"},
        },
        {
            "id": "downloads",
            "emoji": "📥",
            "titulo": "Downloads",
            "valor": "17 arquivos soltos",
            "detalhe": "3 instaladores velhos",
            "acao": {"rotulo": "Arrumar", "chave_ferramenta": "organizador-downloads"},
        },
        {
            "id": "vazio-falso",
            "emoji": "👻",
            "titulo": "Não deve aparecer",
            "valor": "",
            "detalhe": "sem dado real",
            "acao": {"rotulo": "X", "chave_ferramenta": "x"},
        },
    ]


def _esperar(ms: int = 200) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


class TestTelaHoje(unittest.TestCase):
    def tearDown(self):
        # garante que threads de sensores morreram antes do próximo teste
        _APP.processEvents()

    def _tela(self, leitor):
        tela = home.TelaHoje(leitor=leitor, intervalo_ms=600_000)
        # espera a 1ª leitura do __init__ terminar pra não competir com renderizar()
        for _ in range(40):
            _APP.processEvents()
            if not tela._carregando:
                break
            _esperar(25)
        return tela

    def test_renderiza_so_com_valor(self):
        tela = self._tela(_stub_sensores)
        tela.renderizar(_stub_sensores())
        ids = [c["id"] for c in tela.cartoes_visiveis()]
        self.assertEqual(ids, ["disco", "downloads"])
        self.assertNotIn("vazio-falso", ids)
        tela._parar()
        tela.deleteLater()

    def test_lista_vazia_mostra_estado_vazio(self):
        tela = self._tela(lambda: [])
        tela.renderizar([])
        self.assertEqual(tela.cartoes_visiveis(), [])
        self.assertFalse(tela.estado_vazio.isHidden())
        tela._parar()
        tela.deleteLater()

    def test_sinal_abrir_ferramenta(self):
        tela = self._tela(_stub_sensores)
        tela.renderizar(_stub_sensores())
        recebido = []
        tela.abrir_ferramenta.connect(lambda k: recebido.append(k))
        tela._cartoes[0].btn.click()
        self.assertEqual(recebido, ["disk-analyzer"])
        tela._parar()
        tela.deleteLater()

    def test_sinal_comando(self):
        tela = self._tela(lambda: [])
        tela.renderizar([{
            "id": "prints",
            "emoji": "🖼️",
            "titulo": "Prints",
            "valor": "2 recentes",
            "detalhe": "",
            "acao": {"rotulo": "Abrir pasta", "comando": "explorer:Capturas"},
        }])
        cmds = []
        tela.executar_comando.connect(lambda c: cmds.append(c))
        tela._cartoes[0].btn.click()
        self.assertEqual(cmds, ["explorer:Capturas"])
        tela._parar()
        tela.deleteLater()

    def test_thread_atualiza_sem_travar(self):
        chamadas = {"n": 0}

        def leitor():
            chamadas["n"] += 1
            return _stub_sensores()

        tela = self._tela(leitor)
        self.assertGreaterEqual(chamadas["n"], 1)
        self.assertEqual(len(tela.cartoes_visiveis()), 2)
        self.assertTrue(tela.estado_carregando.isHidden())
        tela._parar()
        tela.deleteLater()

    def test_pediu_todas(self):
        tela = self._tela(lambda: [])
        hits = []
        tela.pediu_todas.connect(lambda: hits.append(1))
        tela.btn_todas.click()
        self.assertEqual(hits, [1])
        tela._parar()
        tela.deleteLater()

    def test_leitor_padrao_sem_sensores_core(self):
        dados = home._ler_sensores_padrao()
        self.assertIsInstance(dados, list)

    def test_atalhos_da_critica(self):
        tela = self._tela(lambda: [])
        self.assertEqual(len(home.DESTAQUES_CRITICA), 15)
        # F10: no máx. 8 destaques
        self.assertEqual(len(tela._atalhos), home.MAX_DESTAQUES)
        chaves = [c.dados()["acao"]["chave_ferramenta"] for c in tela._atalhos]
        self.assertIn("faxina-disco", chaves)
        abertos = []
        tela.abrir_ferramenta.connect(lambda k: abertos.append(k))
        tela._atalhos[0].acao_clicada.emit(tela._atalhos[0].dados()["acao"])
        self.assertEqual(abertos, [chaves[0]])
        tela._parar()
        tela.deleteLater()

    def test_f10_ordenar_por_uso(self):
        uses = {"calculadora-troco": 40, "financas": 25, "faxina-disco": 3}
        out = home.ordenar_destaques(uses, max_n=8)
        self.assertEqual(len(out), 8)
        self.assertEqual(out[0][1], "calculadora-troco")
        self.assertEqual(out[1][1], "financas")
        self.assertEqual(out[2][1], "faxina-disco")
        tela = home.TelaHoje(leitor=lambda: [], intervalo_ms=600_000, usos=uses)
        for _ in range(40):
            _APP.processEvents()
            if not tela._carregando:
                break
            _esperar(25)
        chaves = [c.dados()["acao"]["chave_ferramenta"] for c in tela._atalhos]
        self.assertEqual(chaves[0], "calculadora-troco")
        self.assertEqual(tela._atalhos[0].dados()["valor"], "[1] 40×")
        self.assertEqual(len(chaves), 8)
        tela._parar()
        tela.deleteLater()

    def test_t09_atalhos_incluem_uses_fora_da_lista_curada(self):
        """Engrenagens/Conversor/Inspetor entram; Garantias (1) perde pra quem tem mais uso."""
        uses = {
            "financas": 6,
            "faxina-disco": 5,
            "calculadora-engrenagens": 4,
            "conversor-imagens": 4,
            "organizador-downloads": 4,
            "calculadora-troco": 3,
            "inspetor-executavel": 3,
            "print-anotador": 3,
            "controle-garantias": 1,
            "info-pc": 2,
        }
        out = home.ordenar_destaques(uses, max_n=8)
        chaves = [c[1] for c in out]
        self.assertEqual(chaves[0], "financas")
        self.assertIn("calculadora-engrenagens", chaves)
        self.assertIn("conversor-imagens", chaves)
        self.assertIn("inspetor-executavel", chaves)
        self.assertNotIn("controle-garantias", chaves)

    def test_t65_fallback_sem_uses_promove_reais(self):
        """CRITICA T18: zeragem não esconde Finanças/Troco; nicho fora dos 8."""
        out = home.ordenar_destaques({}, max_n=8)
        chaves = [c[1] for c in out]
        self.assertEqual(
            chaves,
            [
                "financas",
                "faxina-disco",
                "calculadora-engrenagens",
                "conversor-imagens",
                "organizador-downloads",
                "calculadora-troco",
                "inspetor-executavel",
                "print-anotador",
            ],
        )
        for nicho in (
            "controle-garantias",
            "controle-validade-remedios",
            "controle-assinaturas",
        ):
            self.assertNotIn(nicho, chaves)
            self.assertNotIn(nicho, [c[1] for c in home.DESTAQUES_CRITICA])

    def test_t19_chip_ultima_e_flash_atalho(self):
        """Chip '0 · …' visível; ativar_atalho(2) liga flash no 3º cartão."""
        uses = {
            "financas": 6,
            "faxina-disco": 5,
            "organizador-downloads": 4,
            "print-anotador": 3,
            "calculadora-troco": 2,
            "info-pc": 2,
            "kit-pdf": 1,
            "calculadora-ipva": 1,
        }
        tela = home.TelaHoje(leitor=lambda: [], intervalo_ms=600_000, usos=uses)
        for _ in range(40):
            _APP.processEvents()
            if not tela._carregando:
                break
            _esperar(25)
        tela.show()
        _APP.processEvents()
        self.assertTrue(hasattr(tela, "chip_ultima"))
        self.assertIn("0 ·", tela.chip_ultima.text())
        self.assertEqual(tela.chip_ultima.objectName(), "chipUltima")
        self.assertTrue(tela.ativar_atalho(2, exigir_foco_livre=False))
        card = tela._atalhos[2]
        self.assertTrue(card.property("flash"))
        _esperar(600)
        self.assertFalse(card.property("flash"))
        # chip reflete a última aberta
        self.assertIn("0 ·", tela.chip_ultima.text())
        tela._parar()
        tela.deleteLater()

    def test_t13_atalho_teclado_1_a_8_e_ultima(self):
        import tempfile
        uses = {
            "financas": 6,
            "faxina-disco": 5,
            "organizador-downloads": 4,
            "print-anotador": 3,
            "calculadora-troco": 2,
            "info-pc": 2,
            "kit-pdf": 1,
            "calculadora-ipva": 1,
        }
        tela = home.TelaHoje(leitor=lambda: [], intervalo_ms=600_000, usos=uses)
        for _ in range(40):
            _APP.processEvents()
            if not tela._carregando:
                break
            _esperar(25)
        tela.show()
        _APP.processEvents()
        abertos = []
        tela.abrir_ferramenta.connect(lambda k: abertos.append(k))

        self.assertTrue(tela.ativar_atalho(0, exigir_foco_livre=False))
        self.assertEqual(abertos[-1], "financas")
        self.assertTrue(tela.ativar_atalho(1, exigir_foco_livre=False))
        self.assertEqual(abertos[-1], "faxina-disco")

        with tempfile.TemporaryDirectory() as tmp:
            home.salvar_ultima_chave("print-anotador", pasta=tmp)
            self.assertEqual(home.ler_ultima_chave(pasta=tmp), "print-anotador")
        # ultima global gravada pelo ativar_atalho(0) acima = financas
        self.assertEqual(home.ler_ultima_chave(), "faxina-disco")
        abertos.clear()
        self.assertTrue(tela.ativar_ultima(exigir_foco_livre=False))
        self.assertEqual(abertos, ["faxina-disco"])
        # badge [1] no valor
        self.assertIn("[1]", tela._atalhos[0].dados()["valor"])
        self.assertIn("1–8", tela.lbl_atalhos.text())
        tela._parar()
        tela.deleteLater()

    def test_f10_layout_1366_e_4k(self):
        """Offscreen 1366×768 e 3840×2160 (DPI 300% simulado pela largura)."""
        uses = {"info-pc": 9, "kit-pdf": 5}
        tela = home.TelaHoje(leitor=lambda: [], intervalo_ms=600_000, usos=uses)
        for _ in range(40):
            _APP.processEvents()
            if not tela._carregando:
                break
            _esperar(25)
        tela.renderizar(self._quatro_sensores())
        for w, h in ((1366, 768), (3840, 2160)):
            tela.resize(w, h)
            _APP.processEvents()
            self.assertEqual(len(tela._atalhos), 8)
            self.assertTrue(tela.cabe_sensores_sem_rolar(w, h - 140))
            # cartões de atalho com altura real
            for card in tela._atalhos:
                self.assertGreaterEqual(card.minimumHeight(), 80)
        tela._parar()
        tela.deleteLater()

    def test_unicode_limpo(self):
        path = os.path.join(HERE, "caixa_home.py")
        with open(path, encoding="utf-8") as f:
            txt = f.read()
        ruins = [c for c in txt if 0x0300 <= ord(c) <= 0x1CFF]
        self.assertEqual(ruins, [])

    def _quatro_sensores(self):
        return [
            {
                "id": "disco",
                "emoji": "💾",
                "titulo": "Disco C:",
                "valor": "42 GB livres",
                "detalhe": "de 512 GB · 8% livre",
                "acao": {"rotulo": "Liberar espaço", "chave_ferramenta": "disk-analyzer"},
            },
            {
                "id": "downloads",
                "emoji": "📥",
                "titulo": "Downloads",
                "valor": "17 arquivos soltos",
                "detalhe": "3 instaladores velhos",
                "acao": {"rotulo": "Arrumar", "chave_ferramenta": "organizador-downloads"},
            },
            {
                "id": "prints",
                "emoji": "🖼️",
                "titulo": "Prints",
                "valor": "3 recentes",
                "detalhe": "pasta Capturas de Tela",
                "acao": {"rotulo": "Anotar", "chave_ferramenta": "print-anotador"},
            },
            {
                "id": "clipboard",
                "emoji": "📋",
                "titulo": "Área de transferência",
                "valor": "texto copiado",
                "detalhe": "últimos 40 caracteres…",
                "acao": {"rotulo": "Abrir", "chave_ferramenta": "area-transferencia"},
            },
        ]

    def test_sensores_altura_de_verdade(self):
        """Cartões ≥ 160 px — nada de faixa de 60 px (CRITICA F3 / F7)."""
        tela = self._tela(lambda: [])
        tela.renderizar(self._quatro_sensores())
        self.assertEqual(len(tela._cartoes), 4)
        for card in tela._cartoes:
            self.assertGreaterEqual(card.minimumHeight(), 160)
            self.assertGreaterEqual(card.sizeHint().height(), 160)
        self.assertGreaterEqual(tela.altura_sensores(), 160)
        tela._parar()
        tela.deleteLater()

    def test_quatro_sensores_cabem_1366_e_1080(self):
        """1366×768 e 1920×1080 mostram GB livres + 4 sensores sem rolar a grade."""
        tela = self._tela(lambda: [])
        tela.renderizar(self._quatro_sensores())
        # viewport da Hoje (descontando chrome/barra ~120 px)
        self.assertTrue(tela.cabe_sensores_sem_rolar(1366, 768 - 120))
        self.assertTrue(tela.cabe_sensores_sem_rolar(1920, 1080 - 140))
        vals = [c.dados()["valor"] for c in tela._cartoes]
        self.assertTrue(any("GB" in v for v in vals))
        tela._parar()
        tela.deleteLater()

    def test_botao_todas_com_contraste(self):
        tela = self._tela(lambda: [])
        self.assertEqual(tela.btn_todas.objectName(), "todasFerramentas")
        tela._parar()
        tela.deleteLater()

    def test_labels_cartao_transparentes(self):
        """Print 1.5.3: cada QLabel tinha faixa escura própria — fundo transparente."""
        tela = self._tela(lambda: [])
        tela.renderizar(self._quatro_sensores())
        card = tela._cartoes[0]
        for lbl in (card.titulo, card.valor, card.detalhe, card.emoji):
            ss = (lbl.styleSheet() or "").lower()
            self.assertIn("transparent", ss)
            self.assertFalse(lbl.autoFillBackground())
        tela._parar()
        tela.deleteLater()

    def test_botao_acao_tamanho_real(self):
        """Botão do cartão não pode ser minúsculo sob o valor gigante (print 1.5.3)."""
        tela = self._tela(lambda: [])
        tela.renderizar(self._quatro_sensores())
        btn = tela._cartoes[0].btn
        self.assertGreaterEqual(btn.minimumHeight(), 36)
        self.assertGreaterEqual(btn.minimumWidth(), 120)
        self.assertGreaterEqual(btn.sizeHint().height(), 36)
        tela._parar()
        tela.deleteLater()

    def test_t26_botao_nao_cortado_no_cartao(self):
        """CRITICA T09/T16: Anotar/Assistir cabe inteiro dentro do cartão (1366)."""
        from PyQt6.QtWidgets import QApplication

        tela = self._tela(lambda: [])
        tela.resize(1366, 648)
        tela.show()
        pudim = {
            "id": "pudim",
            "emoji": "🍮",
            "titulo": "Pudim IPTV",
            "valor": "Uma Familia da Pesada — episódio bem longo pra forçar wrap",
            "detalhe": "Continuar assistindo · temporada 3 · última vez ontem à noite",
            "acao": {"rotulo": "Assistir", "comando": "x"},
        }
        tela.renderizar(self._quatro_sensores()[:3] + [pudim])
        QApplication.processEvents()
        for card in tela._cartoes:
            card.show()
            QApplication.processEvents()
            btn = card.btn
            self.assertFalse(btn.isHidden())
            # botão dentro do retângulo do cartão (não clipado embaixo)
            br = btn.geometry()
            self.assertGreaterEqual(br.top(), 0)
            self.assertLessEqual(br.bottom(), max(card.height(), card.sizeHint().height()))
            self.assertGreaterEqual(br.height(), 36)
            self.assertGreaterEqual(card.minimumHeight(), 200)
        # linha da grade ≥ sizeHint (não só minimumHeight)
        self.assertGreaterEqual(tela._altura_cartao_grade(), tela._cartoes[0].sizeHint().height())
        tela._parar()
        tela.deleteLater()

    def test_f9_enriquecer_disco_e_downloads(self):
        disco = home.enriquecer_acao({
            "id": "disco", "valor": "10 GB", "acao": {"rotulo": "Liberar espaço",
                                                      "chave_ferramenta": "faxina-disco"},
        })
        self.assertEqual(disco["acao"]["pasta"], "C:\\" if os.name == "nt" else "/")
        self.assertIn("--pasta", disco["acao"]["args"])
        self.assertEqual(disco["acao"]["chave_ferramenta"], "faxina-disco")

        dl = home.enriquecer_acao({
            "id": "downloads", "valor": "3", "acao": {"rotulo": "Organizar",
                                                      "chave_ferramenta": "organizador-downloads"},
        })
        self.assertTrue(dl["acao"]["pasta"].lower().endswith("downloads"))
        self.assertIn("--pasta", dl["acao"]["args"])

    def test_f9_pudim_abre_exe_nao_chave(self):
        pudim = home.enriquecer_acao({
            "id": "pudim", "valor": "Serie", "acao": {
                "rotulo": "Assistir", "chave_ferramenta": "iptv-player",
            },
        })
        acao = pudim["acao"]
        self.assertNotIn("chave_ferramenta", acao)
        if os.path.isfile(home._PUDIM_EXE):
            self.assertEqual(acao.get("comando"), home._PUDIM_EXE)

    def test_f9_clique_emite_acao_resolvida(self):
        tela = self._tela(lambda: [])
        tela.renderizar([{
            "id": "disco", "emoji": "💾", "titulo": "Disco", "valor": "1 GB",
            "detalhe": "", "acao": {"rotulo": "Liberar", "chave_ferramenta": "faxina-disco"},
        }])
        resolvidas, chaves = [], []
        tela.acao_resolvida.connect(lambda a: resolvidas.append(a))
        tela.abrir_ferramenta.connect(lambda k: chaves.append(k))
        tela._cartoes[0].btn.click()
        self.assertEqual(len(resolvidas), 1)
        self.assertIn("pasta", resolvidas[0])
        self.assertEqual(chaves, ["faxina-disco"])
        tela._parar()
        tela.deleteLater()

    def test_t211_secao_vitrine_substitui_e_clique(self):
        import tempfile

        itens = home.ler_vitrine()
        self.assertGreaterEqual(len(itens), 23)
        chaves_vitrine = [it["chave"] for it in itens]
        # As que já existem entram:
        for ch in ("ferramentas-br", "kit-pdf", "conversor-av", "print-anotador", "busca-arquivos"):
            self.assertIn(ch, chaves_vitrine)
        # As construir=true que ainda não existem ficam fora:
        for ch_futura in ("desinstalador", "copiador-rapido", "player-video", "editor-texto"):
            if not os.path.isdir(os.path.join(os.path.dirname(HERE), ch_futura)):
                self.assertNotIn(ch_futura, chaves_vitrine)

        tela = self._tela(_stub_sensores)
        tela.resize(1366, 900)
        tela.show()
        _APP.processEvents()

        self.assertFalse(tela.lbl_vitrine.isHidden())
        self.assertIn("VITRINE", tela.lbl_vitrine.text())
        cards = tela.vitrine_visivel()
        self.assertEqual(len(cards), len(itens))
        for dados in cards:
            self.assertTrue(dados["emoji"])
            self.assertTrue(dados["titulo"])
            self.assertTrue(str(dados["valor"]).startswith("substitui "))

        # Clique num cartão da vitrine abre a ferramenta correspondente
        abertas = []
        tela.abrir_ferramenta.connect(lambda k: abertas.append(k))
        primeiro_card = tela._vitrine_cards[0]
        primeiro_card.acao_clicada.emit(primeiro_card.dados()["acao"])
        self.assertEqual(abertas, [cards[0]["acao"]["chave_ferramenta"]])

        # Captura foto offscreen da tela inicial com a seção VITRINE e confere pixels
        with tempfile.TemporaryDirectory() as tmpdir:
            snap_path = os.path.join(tmpdir, "tela_hoje_vitrine.png")
            pm = tela.grab()
            self.assertTrue(pm.save(snap_path, "PNG"))
            self.assertTrue(os.path.isfile(snap_path))
            self.assertGreater(os.path.getsize(snap_path), 2000)

        tela._parar()
        tela.deleteLater()

    def test_t314_sensores_responsivos_1366x768_gb_livres(self):
        """T314 / CRITICA F3: Garante que '206,2 GB livres' não é cortado e cabe em 1366x768."""
        tela = self._tela(lambda: [])
        disco_sensor = {
            "id": "disco",
            "emoji": "💾",
            "titulo": "Disco C:",
            "valor": "206,2 GB livres (54% de 446 GB)",
            "detalhe": "Espaço suficiente · aviso temp limpo",
            "acao": {"rotulo": "Liberar espaço", "chave_ferramenta": "faxina-disco"},
        }
        tela.renderizar([disco_sensor] + self._quatro_sensores()[:3])
        tela.resize(1366, 648)
        tela.show()
        _APP.processEvents()

        # Cabe no viewport 1366x768 sem rolar a grade de sensores
        self.assertTrue(tela.cabe_sensores_sem_rolar(1366, 648))

        card = tela._cartoes[0]
        self.assertEqual(card.valor.text(), "206,2 GB livres (54% de 446 GB)")
        self.assertGreaterEqual(card.valor.height(), 24)
        self.assertGreaterEqual(card.minimumHeight(), 200)

        # Botão completamente visível dentro do cartão
        br = card.btn.geometry()
        self.assertGreaterEqual(br.top(), 0)
        self.assertLessEqual(br.bottom(), max(card.height(), card.sizeHint().height()))
        self.assertFalse(card.btn.isHidden())

        tela._parar()
        tela.deleteLater()


if __name__ == "__main__":
    unittest.main()
