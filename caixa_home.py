"""Tela Hoje — o que importa no PC do Caio agora.

Recebe sensores_core.ler_tudo() e desenha cartões vivos com botão de ação.
Atualiza a cada 60 s numa QThread (nunca trava a janela).
Cartão sem dado real não aparece.
"""
from __future__ import annotations

import os
import traceback
from datetime import datetime
from typing import Callable

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import caixa_tema as tema

INTERVALO_MS = 60_000
COLUNAS_PADRAO = 2

# 15 chaves curadas (CRITICA T18): os 8 primeiros = fallback pós-zeragem / uses vazio.
# Saiem do destaque: garantias, validade de remédios, assinaturas (continuam no catálogo).
DESTAQUES_CRITICA = (
    ("💰", "financas", "Finanças"),
    ("💾", "faxina-disco", "Faxina de Disco"),
    ("⚙️", "calculadora-engrenagens", "Engrenagens"),
    ("🖼️", "conversor-imagens", "Conversor de Imagens"),
    ("📥", "organizador-downloads", "Organizador de Downloads"),
    ("💵", "calculadora-troco", "Troco"),
    ("🔬", "inspetor-executavel", "Inspetor de Executáveis"),
    ("🖼️", "print-anotador", "Print Anotador"),
    ("📋", "area-transferencia", "Área de Transferência"),
    ("📄", "kit-pdf", "Kit de PDF"),
    ("🚗", "calculadora-ipva", "IPVA"),
    ("📅", "dias-uteis-pagamento", "Dias Úteis"),
    ("🎨", "calculadora-rendimento-tinta", "Rendimento de Tinta"),
    ("🔥", "calculadora-botijao-gas", "Botijão de Gás"),
    ("🖥️", "info-pc", "Info do PC"),
)

# Nomes pra chaves quentes do uses que não estão na lista curada (T09)
NOMES_ATALHO_EXTRA = {
    "calculadora-engrenagens": ("⚙️", "Engrenagens"),
    "conversor-imagens": ("🖼️", "Conversor de Imagens"),
    "inspetor-executavel": ("🔬", "Inspetor de Executáveis"),
    "auditoria-pc": ("🛡️", "Auditoria de Portas"),
    "conversor-unidades": ("📐", "Conversor de Unidades"),
    "ferramentas-br": ("🇧🇷", "Ferramentas BR"),
    "gerenciador-firewall": ("🧱", "Firewall"),
    "calculadora-financeira-black-scholes": ("📈", "Black-Scholes"),
}

_PUDIM_EXE = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\IPTV Player\IPTV Player.exe"
)
_CFG_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "CaixaFerramentas",
)
_CFG_PATH = os.path.join(_CFG_DIR, "config.json")
_ULTIMA_CHAVE_ARQ = os.path.join(_CFG_DIR, "ultima_chave.txt")
_HERE = os.path.dirname(os.path.abspath(__file__))
_VITRINE_PATH = os.path.join(_HERE, "vitrine.json")
_CATALOGO_PATH = os.path.join(_HERE, "catalogo.json")
MAX_DESTAQUES = 8

_CACHE_CATALOGO: dict[str, dict] | None = None


def _mapa_catalogo(catalogo_path: str | None = None) -> dict[str, dict]:
    """Mapeia chave -> {emoji, nome, desc, categoria} a partir do catalogo.json."""
    global _CACHE_CATALOGO
    if catalogo_path is None and _CACHE_CATALOGO is not None:
        return _CACHE_CATALOGO
    path = catalogo_path or _CATALOGO_PATH
    mapa: dict[str, dict] = {}
    try:
        import json
        with open(path, encoding="utf-8") as f:
            dados = json.load(f)
        for item in dados.get("ferramentas") or []:
            if isinstance(item, dict) and item.get("chave"):
                mapa[str(item["chave"])] = item
    except (OSError, ValueError, TypeError):
        pass
    if catalogo_path is None and mapa:
        _CACHE_CATALOGO = mapa
    return mapa


def ler_vitrine(
    vitrine_path: str | None = None,
    catalogo_path: str | None = None,
) -> list[dict]:
    """Lê vitrine.json e devolve os itens existentes (pula construir=true até existirem)."""
    vpath = vitrine_path or _VITRINE_PATH
    try:
        import json
        with open(vpath, encoding="utf-8") as f:
            bruto = json.load(f)
    except (OSError, ValueError, TypeError):
        return []
    lista = bruto.get("vitrine") if isinstance(bruto, dict) else []
    if not isinstance(lista, list):
        return []
    cat = _mapa_catalogo(catalogo_path)
    base_dir = os.path.dirname(_HERE)
    saida: list[dict] = []
    for item in lista:
        if not isinstance(item, dict):
            continue
        chave = str(item.get("chave") or "").strip()
        substitui = str(item.get("substitui") or "").strip()
        if not chave or not substitui:
            continue
        # Se construir=true, só entra quando a ferramenta já existir no catálogo ou pasta irmã
        if item.get("construir"):
            pasta_irma = os.path.join(base_dir, chave)
            if chave not in cat and not os.path.isdir(pasta_irma):
                continue
        info_cat = cat.get(chave) or {}
        emoji_fb, nome_fb = _rotulo_atalho(chave)
        emoji = str(info_cat.get("emoji") or emoji_fb)
        nome = str(info_cat.get("nome") or nome_fb)
        categoria = str(info_cat.get("categoria") or "hoje")
        saida.append({
            "chave": chave,
            "emoji": emoji,
            "nome": nome,
            "substitui": substitui,
            "evidencia": str(item.get("evidencia") or "").strip(),
            "essenciais": list(item.get("essenciais") or []),
            "categoria": categoria,
        })
    return saida


def ler_usos(cfg_path: str | None = None) -> dict[str, int]:
    """Lê cfg['uses'] do caixa.pyw (contagem real de aberturas)."""
    path = cfg_path or _CFG_PATH
    try:
        import json
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        uses = cfg.get("uses") or {}
        return {str(k): int(v) for k, v in uses.items() if isinstance(v, (int, float))}
    except (OSError, ValueError, TypeError):
        return {}


def _rotulo_atalho(chave: str) -> tuple[str, str]:
    """(emoji, nome) pra uma chave — curada, extra T09 ou título a partir da chave."""
    for emoji, k, nome in DESTAQUES_CRITICA:
        if k == chave:
            return emoji, nome
    if chave in NOMES_ATALHO_EXTRA:
        return NOMES_ATALHO_EXTRA[chave]
    nome = chave.replace("-", " ").replace("_", " ").strip().title() or chave
    return ("🔧", nome)


def ordenar_destaques(
    uses: dict[str, int] | None = None,
    base: tuple = DESTAQUES_CRITICA,
    max_n: int = MAX_DESTAQUES,
) -> list[tuple[str, str, str]]:
    """Top N pelo uses real (T09). Base do Grok só desempata / completa se uses vazio."""
    usos = uses if uses is not None else ler_usos()
    index_base = {chave: i for i, (_, chave, _) in enumerate(base)}
    candidatos: dict[str, tuple[str, str, str]] = {}
    for emoji, chave, nome in base:
        candidatos[chave] = (emoji, chave, nome)
    for chave, n in (usos or {}).items():
        if int(n) <= 0:
            continue
        if chave not in candidatos:
            emoji, nome = _rotulo_atalho(chave)
            candidatos[chave] = (emoji, chave, nome)

    def _chave_ord(item: tuple[str, str, str]):
        chave = item[1]
        return (-int(usos.get(chave, 0)), index_base.get(chave, 10_000), chave)

    ordenados = sorted(candidatos.values(), key=_chave_ord)
    # se ninguém tem uso, cai na ordem da base
    if not any(int(usos.get(c[1], 0)) > 0 for c in ordenados):
        ordenados = list(base)
    # T23: arquivadas somem dos atalhos 1–8 (continuam na barra)
    try:
        import caixa_arquivo as _arq
        ordenados = [c for c in ordenados if not _arq.esta_arquivada(c[1])]
    except ImportError:
        pass
    return ordenados[: max(1, int(max_n))]


def salvar_ultima_chave(chave: str, pasta: str | None = None) -> None:
    """T13: grava a última ferramenta aberta (Hoje ou Caixa via Grok CLI)."""
    chave = (chave or "").strip()
    if not chave:
        return
    arq = _ULTIMA_CHAVE_ARQ if pasta is None else os.path.join(pasta, "ultima_chave.txt")
    try:
        os.makedirs(os.path.dirname(arq), exist_ok=True)
        tmp = arq + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(chave)
        os.replace(tmp, arq)
    except OSError:
        pass


def ler_ultima_chave(pasta: str | None = None) -> str | None:
    arq = _ULTIMA_CHAVE_ARQ if pasta is None else os.path.join(pasta, "ultima_chave.txt")
    try:
        with open(arq, encoding="utf-8") as f:
            chave = f.read().strip()
        return chave or None
    except OSError:
        return None


def _pasta_downloads() -> str:
    return os.path.normpath(os.path.expanduser("~/Downloads"))


def _ultimo_print() -> str | None:
    """Caminho do print mais recente nas pastas padrão do Windows."""
    candidatos = [
        os.path.expanduser("~/Pictures/Screenshots"),
        os.path.expanduser("~/Imagens/Capturas de Tela"),
        os.path.expanduser("~/OneDrive/Imagens/Capturas de Tela"),
        os.path.expanduser("~/Pictures/Capturas de Tela"),
    ]
    exts = {".png", ".jpg", ".jpeg", ".bmp"}
    melhor: tuple[float, str] | None = None
    for pasta in candidatos:
        if not os.path.isdir(pasta):
            continue
        try:
            with os.scandir(pasta) as it:
                for entry in it:
                    if not entry.is_file():
                        continue
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext not in exts:
                        continue
                    try:
                        mtime = entry.stat().st_mtime
                    except OSError:
                        continue
                    if melhor is None or mtime > melhor[0]:
                        melhor = (mtime, entry.path)
        except OSError:
            continue
    return melhor[1] if melhor else None


def enriquecer_acao(sensor: dict) -> dict:
    """F9: botão da Hoje resolve de verdade — anexa pasta/arquivo/comando.

    Disco → Faxina no C:; Downloads → Organizador na pasta Downloads;
    Prints → Print Anotador com último print; Pudim → abre o player.
    """
    dados = dict(sensor or {})
    acao = dict(dados.get("acao") or {})
    sid = str(dados.get("id") or "")

    if sid == "disco":
        acao.setdefault("rotulo", "Liberar espaço")
        acao["chave_ferramenta"] = acao.get("chave_ferramenta") or "faxina-disco"
        acao["pasta"] = "C:\\" if os.name == "nt" else "/"
        acao["args"] = ["--pasta", acao["pasta"]]
    elif sid == "crescimento":
        # T06: Faxina já na pasta que mais cresceu
        pasta = acao.get("pasta") or ""
        acao.setdefault("rotulo", "Abrir na Faxina")
        acao["chave_ferramenta"] = acao.get("chave_ferramenta") or "faxina-disco"
        if pasta:
            acao["pasta"] = pasta
            acao["args"] = ["--pasta", pasta]
    elif sid == "downloads":
        pasta = _pasta_downloads()
        acao.setdefault("rotulo", "Organizar")
        acao["chave_ferramenta"] = (
            acao.get("chave_ferramenta") or "organizador-downloads"
        )
        acao["pasta"] = pasta
        acao["args"] = ["--pasta", pasta]
    elif sid == "prints":
        arq = _ultimo_print()
        acao.setdefault("rotulo", "Anotar / OCR")
        # não sobrescreve ação que já é só comando (ex.: abrir pasta Capturas)
        if not (acao.get("comando") and not acao.get("chave_ferramenta")):
            acao["chave_ferramenta"] = (
                acao.get("chave_ferramenta") or "print-anotador"
            )
            if arq:
                acao["arquivo"] = arq
                acao["args"] = ["--arquivo", arq]
    elif sid == "pudim":
        acao.setdefault("rotulo", "Assistir")
        # iptv-player NÃO está no BUILTIN — abre o exe direto
        if os.path.isfile(_PUDIM_EXE):
            acao["comando"] = _PUDIM_EXE
        acao.pop("chave_ferramenta", None)  # evita "não achei iptv-player"

    if acao:
        dados["acao"] = acao
    return dados


def _ler_sensores_padrao() -> list[dict]:
    """Chama sensores_core.ler_tudo(); se ainda não existir, devolve []."""
    try:
        import sensores_core  # type: ignore
    except ImportError:
        return []
    try:
        dados = sensores_core.ler_tudo()
    except Exception:
        traceback.print_exc()
        return []
    if not isinstance(dados, list):
        return []
    return [d for d in dados if isinstance(d, dict) and d.get("valor")]


class _SensorWorker(QThread):
    """Lê sensores off-thread e emite a lista pronta."""

    pronto = pyqtSignal(list)
    falhou = pyqtSignal(str)

    def __init__(self, leitor: Callable[[], list[dict]], parent=None):
        super().__init__(parent)
        self._leitor = leitor

    def run(self) -> None:
        try:
            dados = self._leitor() or []
            if not isinstance(dados, list):
                dados = []
            limpos = [d for d in dados if isinstance(d, dict) and d.get("valor")]
            self.pronto.emit(limpos)
        except Exception as exc:
            self.falhou.emit(str(exc))


class TelaHoje(QWidget):
    """Primeira tela da Caixa: cartões vivos do PC.

    Sinais:
      abrir_ferramenta(str chave) — ação com chave_ferramenta
      executar_comando(str comando) — ação com comando (ex.: explorer)
      pediu_todas() — botão "Todas as ferramentas"
    """

    abrir_ferramenta = pyqtSignal(str)
    executar_comando = pyqtSignal(str)
    pediu_todas = pyqtSignal()
    # F9: ação completa {rotulo, chave_ferramenta?, pasta?, arquivo?, args?, comando?}
    # Claude: conecte e passe args no open_tool (subprocess + --pasta/--arquivo).
    acao_resolvida = pyqtSignal(dict)

    def __init__(
        self,
        leitor: Callable[[], list[dict]] | None = None,
        intervalo_ms: int = INTERVALO_MS,
        usos: dict[str, int] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._leitor = leitor or _ler_sensores_padrao
        self._intervalo_ms = max(1_000, int(intervalo_ms))
        self._worker: _SensorWorker | None = None
        self._cartoes: list[tema.CartaoGrande] = []
        self._carregando = False
        self._usos = dict(usos) if usos is not None else None

        self.setObjectName("telaHoje")
        # altura natural do conteúdo — a rolagem fica no QScrollArea do caixa.pyw
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._timer = None
        tema.aplicar_tema(self)
        self._montar()
        self._timer = self.startTimer(self._intervalo_ms)
        # primeira leitura já na criação (assíncrona)
        self.atualizar(forcar=True)

    def _montar(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(*tema.margens_para_largura(1366))
        root.setSpacing(12)
        self._root = root

        topo = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(2)
        self.lbl_saudacao = QLabel(self._saudacao())
        self.lbl_saudacao.setObjectName("saudacao")
        self.lbl_hora = QLabel(self._texto_hora())
        self.lbl_hora.setObjectName("horaHoje")
        col.addWidget(self.lbl_saudacao)
        col.addWidget(self.lbl_hora)
        topo.addLayout(col, 1)

        self.btn_todas = QPushButton("Todas as ferramentas")
        # contraste alto (CRITICA F3) — não mais "fantasma" apagado
        self.btn_todas.setObjectName("todasFerramentas")
        self.btn_todas.clicked.connect(self.pediu_todas.emit)
        topo.addWidget(self.btn_todas, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(topo)

        self.lbl_secao = QLabel("AGORA NO SEU PC")
        self.lbl_secao.setObjectName("secao")
        root.addWidget(self.lbl_secao)

        self.estado_carregando = tema.EstadoCarregando("Lendo sensores…")
        self.estado_carregando.hide()
        root.addWidget(self.estado_carregando)

        # Sem scroll interno: cartões com altura real; rolagem é do caixa.pyw.
        # Scroll aninhado esmagava os sensores numa faixa de ~60 px (CRITICA F3).
        self.area = QWidget()
        self.area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.grade = QGridLayout(self.area)
        self.grade.setContentsMargins(0, 0, 4, 0)
        self.grade.setHorizontalSpacing(14)
        self.grade.setVerticalSpacing(14)
        self.grade.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.addWidget(self.area, 0)

        # alias p/ testes antigos que olhavam self.scroll
        self.scroll = self.area

        self.estado_vazio = tema.EstadoVazio(
            "Nada urgente agora. Quando o disco encher, Downloads bagunçar "
            "ou algo vencer, aparece aqui.",
            emoji="✨",
            titulo="Tudo em ordem",
        )
        self.estado_vazio.hide()
        root.addWidget(self.estado_vazio)

        # T19: seção + chip clicável "0 · última"
        row_atalhos = QHBoxLayout()
        row_atalhos.setSpacing(10)
        self.lbl_atalhos = QLabel("ATALHOS  ·  teclas 1–8")
        self.lbl_atalhos.setObjectName("secao")
        row_atalhos.addWidget(self.lbl_atalhos, 0, Qt.AlignmentFlag.AlignVCenter)
        self.chip_ultima = QPushButton("0 · última")
        self.chip_ultima.setObjectName("chipUltima")
        self.chip_ultima.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chip_ultima.setToolTip("Tecla 0 (ou Alt+0): reabre a última ferramenta usada")
        self.chip_ultima.clicked.connect(lambda: self.ativar_ultima(exigir_foco_livre=False))
        row_atalhos.addWidget(self.chip_ultima, 0, Qt.AlignmentFlag.AlignVCenter)
        row_atalhos.addStretch(1)
        root.addLayout(row_atalhos)
        self._atualizar_chip_ultima()

        self.grade_atalhos = QGridLayout()
        self.grade_atalhos.setHorizontalSpacing(10)
        self.grade_atalhos.setVerticalSpacing(10)
        root.addLayout(self.grade_atalhos)
        self._atalhos: list[tema.CartaoPequeno] = []
        self._atalhos_chaves: list[str] = []
        self._atalhos_teclado: list = []
        self._montar_atalhos()
        self._instalar_atalhos_teclado()

        # T211: seção VITRINE (substitui os programas famosos)
        self.lbl_vitrine = QLabel("⭐ VITRINE  ·  SUBSTITUI OS PROGRAMAS QUE VOCÊ BAIXARIA")
        self.lbl_vitrine.setObjectName("secao")
        root.addWidget(self.lbl_vitrine)

        self.grade_vitrine = QGridLayout()
        self.grade_vitrine.setHorizontalSpacing(10)
        self.grade_vitrine.setVerticalSpacing(10)
        root.addLayout(self.grade_vitrine)
        self._vitrine_cards: list[tema.CartaoPequeno] = []
        self._vitrine_chaves: list[str] = []
        self._montar_vitrine()

    def _instalar_atalhos_teclado(self) -> None:
        """T13: 1–8 abrem atalhos; 0 abre a última. Alt+dígito funciona mesmo com a barra em foco."""
        for sc in getattr(self, "_atalhos_teclado", []) or []:
            try:
                sc.setParent(None)
                sc.deleteLater()
            except RuntimeError:
                pass
        self._atalhos_teclado = []

        def _liga(seq: str, slot):
            sc = QShortcut(QKeySequence(seq), self)
            # ApplicationShortcut: TelaHoje não é top-level; filtramos no slot
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
            sc.activated.connect(slot)
            self._atalhos_teclado.append(sc)

        for n in range(1, 9):
            idx = n - 1
            _liga(str(n), lambda i=idx: self.ativar_atalho(i, exigir_foco_livre=True))
            _liga(f"Alt+{n}", lambda i=idx: self.ativar_atalho(i, exigir_foco_livre=False))
        _liga("0", lambda: self.ativar_ultima(exigir_foco_livre=True))
        _liga("Alt+0", lambda: self.ativar_ultima(exigir_foco_livre=False))

    def _teclado_livre(self) -> bool:
        """Hoje visível e foco fora de campos de texto (dígito solto não digita na barra)."""
        if not self.isVisible():
            return False
        fw = QApplication.focusWidget()
        if fw is None:
            return True
        return not isinstance(
            fw, (QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox)
        )

    def _hoje_ativa(self) -> bool:
        return bool(self.isVisible())

    def _atualizar_chip_ultima(self) -> None:
        """Atualiza texto/tooltip do chip 0 com a última chave conhecida."""
        chave = ler_ultima_chave()
        if not hasattr(self, "chip_ultima") or self.chip_ultima is None:
            return
        if chave:
            emoji, nome = _rotulo_atalho(chave)
            self.chip_ultima.setText(f"0 · {nome}")
            self.chip_ultima.setToolTip(
                f"Tecla 0 / Alt+0 — última: {nome} ({chave})"
            )
            self.chip_ultima.setEnabled(True)
        else:
            self.chip_ultima.setText("0 · última")
            self.chip_ultima.setToolTip(
                "Tecla 0 / Alt+0 — ainda não abriu nenhuma ferramenta nesta sessão"
            )
            self.chip_ultima.setEnabled(True)

    def _flash_chip_ultima(self, ms: int = 450) -> None:
        if not hasattr(self, "chip_ultima") or self.chip_ultima is None:
            return
        self.chip_ultima.setProperty("flash", True)
        self.chip_ultima.style().unpolish(self.chip_ultima)
        self.chip_ultima.style().polish(self.chip_ultima)
        self.chip_ultima.update()

        def _off():
            try:
                self.chip_ultima.setProperty("flash", False)
                self.chip_ultima.style().unpolish(self.chip_ultima)
                self.chip_ultima.style().polish(self.chip_ultima)
                self.chip_ultima.update()
            except RuntimeError:
                pass

        from PyQt6.QtCore import QTimer
        QTimer.singleShot(max(80, int(ms)), _off)

    def ativar_atalho(self, indice: int, exigir_foco_livre: bool = True) -> bool:
        """Abre o atalho N (0-based). Retorna True se disparou."""
        if not self._hoje_ativa():
            return False
        if exigir_foco_livre and not self._teclado_livre():
            return False
        if indice < 0 or indice >= len(self._atalhos):
            return False
        card = self._atalhos[indice]
        acao = (card.dados() or {}).get("acao") or {}
        if not acao:
            return False
        if hasattr(card, "destacar"):
            card.destacar(450)
        self._on_acao(dict(acao))
        self._atualizar_chip_ultima()
        return True

    def ativar_ultima(self, exigir_foco_livre: bool = True) -> bool:
        """Abre a última ferramenta usada (arquivo ultima_chave.txt)."""
        if not self._hoje_ativa():
            return False
        if exigir_foco_livre and not self._teclado_livre():
            return False
        chave = ler_ultima_chave()
        if not chave:
            self._atualizar_chip_ultima()
            return False
        self._flash_chip_ultima(450)
        # se a última ainda está nos atalhos 1–8, pisca o cartão também
        if chave in self._atalhos_chaves:
            i = self._atalhos_chaves.index(chave)
            if 0 <= i < len(self._atalhos) and hasattr(self._atalhos[i], "destacar"):
                self._atalhos[i].destacar(450)
        self._on_acao({"rotulo": "Última", "chave_ferramenta": chave})
        self._atualizar_chip_ultima()
        return True

    def _montar_atalhos(self) -> None:
        while self.grade_atalhos.count():
            item = self.grade_atalhos.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._atalhos.clear()
        self._atalhos_chaves = []
        cols = min(4, max(2, self._colunas()))
        destaque = ordenar_destaques(self._usos)
        for i, (emoji, chave, nome) in enumerate(destaque):
            usos_n = 0
            if self._usos is not None:
                usos_n = int(self._usos.get(chave, 0))
            else:
                usos_n = int(ler_usos().get(chave, 0))
            tecla = str(i + 1)
            valor = f"[{tecla}] {usos_n}×" if usos_n > 0 else f"[{tecla}] Abrir"
            card = tema.CartaoPequeno(self)
            card.preencher({
                "id": "hoje",
                "emoji": emoji,
                "titulo": nome,
                "valor": valor,
                "detalhe": chave,
                "acao": {"rotulo": "Abrir", "chave_ferramenta": chave},
                "tecla": tecla,
            }, cor=tema.ACCENT)
            card.acao_clicada.connect(self._on_acao)
            r, c = divmod(i, cols)
            self.grade_atalhos.addWidget(card, r, c)
            self._atalhos.append(card)
            self._atalhos_chaves.append(chave)

    def set_usos(self, uses: dict[str, int]) -> None:
        """Atualiza ranking dos atalhos (Claude pode chamar após save_cfg)."""
        self._usos = dict(uses or {})
        self._montar_atalhos()
        self._atualizar_chip_ultima()

    def _montar_vitrine(self) -> None:
        """T211: monta os cartões da VITRINE (vitrine.json, pulando construir=true até existirem)."""
        while self.grade_vitrine.count():
            item = self.grade_vitrine.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._vitrine_cards.clear()
        self._vitrine_chaves = []
        itens = ler_vitrine()
        if not itens:
            self.lbl_vitrine.hide()
            return
        self.lbl_vitrine.show()
        cols = min(4, max(2, self._colunas()))
        for i, it in enumerate(itens):
            chave = it["chave"]
            substitui = it["substitui"]
            linha_sub = f"substitui {substitui}"
            card = tema.CartaoPequeno(self)
            card.setMinimumHeight(96)
            card.setMaximumHeight(118)
            card.preencher({
                "id": it.get("categoria") or "hoje",
                "emoji": it["emoji"],
                "titulo": it["nome"],
                "valor": linha_sub,
                "detalhe": it.get("evidencia") or chave,
                "acao": {"rotulo": "Abrir", "chave_ferramenta": chave},
                "substitui": substitui,
                "chave": chave,
            }, cor=tema.cor_categoria(it.get("categoria") or "hoje"))
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setToolTip(f"{it['nome']} — substitui {substitui}")
            card.acao_clicada.connect(self._on_acao)
            r, c = divmod(i, cols)
            self.grade_vitrine.addWidget(card, r, c)
            self._vitrine_cards.append(card)
            self._vitrine_chaves.append(chave)

    def vitrine_visivel(self) -> list[dict]:
        """Devolve os dados dos cartões da vitrine atualmente exibidos."""
        return [c.dados() for c in self._vitrine_cards]

    def _saudacao(self) -> str:
        h = datetime.now().hour
        if h < 6:
            return "Boa madrugada"
        if h < 12:
            return "Bom dia"
        if h < 18:
            return "Boa tarde"
        return "Boa noite"

    def _texto_hora(self) -> str:
        agora = datetime.now()
        dias = (
            "segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo",
        )
        return f"{dias[agora.weekday()]}, {agora.strftime('%d/%m · %H:%M')}"

    def timerEvent(self, event) -> None:  # noqa: N802
        if event.timerId() == self._timer:
            self.lbl_saudacao.setText(self._saudacao())
            self.lbl_hora.setText(self._texto_hora())
            self.atualizar()
        super().timerEvent(event)

    def atualizar(self, forcar: bool = False) -> None:
        """Dispara leitura em thread. Ignora se já houver uma em andamento."""
        if self._carregando and not forcar:
            return
        if self._worker is not None and self._worker.isRunning():
            return
        self._carregando = True
        self.estado_carregando.show()
        self.estado_carregando.set_mensagem("Atualizando…")
        worker = _SensorWorker(self._leitor, self)
        worker.pronto.connect(self._on_sensores)
        worker.falhou.connect(self._on_falha)
        worker.finished.connect(self._on_worker_fim)
        self._worker = worker
        worker.start()

    def _on_worker_fim(self) -> None:
        self._carregando = False
        self.estado_carregando.hide()

    def _on_falha(self, msg: str) -> None:
        self.estado_carregando.set_mensagem(f"Falha ao ler sensores: {msg}")
        # mantém cartões antigos; se não houver nenhum, mostra vazio
        if not self._cartoes:
            self._mostrar_vazio(True)

    def _on_sensores(self, itens: list) -> None:
        self.renderizar(list(itens or []))

    def renderizar(self, itens: list[dict]) -> None:
        """Desenha só cartões com valor real. Lista vazia → estado vazio."""
        while self.grade.count():
            item = self.grade.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._cartoes.clear()

        validos = [d for d in (itens or []) if isinstance(d, dict) and d.get("valor")]
        if not validos:
            self._mostrar_vazio(True)
            return

        self._mostrar_vazio(False)
        cols = self._colunas()
        for i, bruto in enumerate(validos):
            dados = enriquecer_acao(bruto)
            card = tema.CartaoGrande(self.area)
            card.preencher(dados, cor=tema.cor_categoria(str(dados.get("id") or "")))
            card.acao_clicada.connect(self._on_acao)
            r, c = divmod(i, cols)
            self.grade.addWidget(card, r, c)
            self._cartoes.append(card)
            tema.animar_entrada(card, duracao_ms=200, atraso_ms=min(i * 40, 240))
        # estica colunas e trava altura por linha = sizeHint real (T26: minHeight sozinho
        # clipava Anotar/Assistir quando o valor/detalhe pedia mais que o mínimo)
        rows = (len(self._cartoes) + cols - 1) // cols
        card_h = self._altura_cartao_grade()
        for c in range(cols):
            self.grade.setColumnStretch(c, 1)
        for r in range(rows):
            self.grade.setRowMinimumHeight(r, card_h)

    def _mostrar_vazio(self, vazio: bool) -> None:
        self.estado_vazio.setVisible(vazio)
        self.area.setVisible(not vazio)

    def _altura_cartao_grade(self) -> int:
        """Altura de linha: máximo entre minimumHeight e sizeHint (botão visível)."""
        if not self._cartoes:
            return 200
        return max(
            (
                max(int(c.minimumHeight()), int(c.sizeHint().height()))
                for c in self._cartoes
            ),
            default=200,
        )

    def altura_sensores(self, largura: int | None = None) -> int:
        """Altura da grade pela geometria (cols×rows), não pelo sizeHint 1-col."""
        n = len(self._cartoes)
        if n == 0 or self.area.isHidden():
            return 0
        w = int(largura) if largura else max(self.width(), 400)
        cols = max(1, tema.colunas_para_largura(w))
        rows = (n + cols - 1) // cols
        card_h = self._altura_cartao_grade()
        spacing = max(0, int(self.grade.verticalSpacing()))
        return rows * card_h + max(0, rows - 1) * spacing

    def cabe_sensores_sem_rolar(self, largura: int, altura_viewport: int) -> bool:
        """True se topo + seção + 4 sensores cabem no viewport (sem rolar a grade)."""
        self.resize(max(400, int(largura)), max(200, int(altura_viewport)))
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        # se o resize reflowou a grade, garante que ainda há cartões medidos
        if not self._cartoes:
            return False
        topo_h = (
            self.lbl_saudacao.sizeHint().height()
            + self.lbl_hora.sizeHint().height()
            + 8
        )
        secao_h = self.lbl_secao.sizeHint().height() + 12
        sens_h = self.altura_sensores(largura)
        return (topo_h + secao_h + sens_h) <= int(altura_viewport)

    def _colunas(self) -> int:
        dpr = tema.dpr_de_widget(self)
        return tema.colunas_para_largura(max(self.width(), 400), dpr=dpr)

    def _aplicar_layout_largura(self) -> None:
        from PyQt6.QtGui import QFont

        # T20: respeita DPI do monitor atual (100% vs 300%)
        lay = tema.layout_grade(max(self.width(), 400), tema.dpr_de_widget(self))
        self._root.setContentsMargins(*lay["margens"])
        escala = float(lay["escala"])
        self.lbl_saudacao.setFont(
            tema.fonte(max(14, int(18 * escala)), QFont.Weight.Bold)
        )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._aplicar_layout_largura()
        # reflow dos atalhos (sempre presentes)
        if self._atalhos:
            cols_at = min(5, max(2, self._colunas() + 1))
            cols_old = sum(
                1 for c in range(5) if self.grade_atalhos.itemAtPosition(0, c) is not None
            ) or 1
            if cols_at != cols_old:
                self._montar_atalhos()
        if getattr(self, "_vitrine_cards", None):
            cols_vt = min(4, max(2, self._colunas()))
            cols_vt_old = sum(
                1 for c in range(5) if self.grade_vitrine.itemAtPosition(0, c) is not None
            ) or 1
            if cols_vt != cols_vt_old:
                self._montar_vitrine()
        if not self._cartoes:
            return
        cols = self._colunas()
        cols_antigas = sum(
            1 for c in range(4) if self.grade.itemAtPosition(0, c) is not None
        ) or 1
        if cols != cols_antigas:
            self.renderizar([c.dados() for c in self._cartoes])

    def _on_acao(self, acao: dict) -> None:
        if not isinstance(acao, dict):
            return
        self.acao_resolvida.emit(dict(acao))
        # Pudim / atalho direto: comando resolve na hora (sem chave no BUILTIN)
        comando = acao.get("comando")
        chave = acao.get("chave_ferramenta")
        if comando and not chave:
            self.executar_comando.emit(str(comando))
            return
        if chave:
            salvar_ultima_chave(str(chave))
            self._atualizar_chip_ultima()
            # Claude/Grok CLI: ler acao_resolvida e repassar --pasta/--arquivo
            self.abrir_ferramenta.emit(str(chave))
            return
        if comando:
            self.executar_comando.emit(str(comando))

    def cartoes_visiveis(self) -> list[dict]:
        return [c.dados() for c in self._cartoes]

    def set_leitor(self, leitor: Callable[[], list[dict]]) -> None:
        self._leitor = leitor

    def closeEvent(self, event) -> None:  # noqa: N802
        self._parar()
        super().closeEvent(event)

    def _parar(self) -> None:
        if self._timer is not None:
            self.killTimer(self._timer)
            self._timer = None
        w = self._worker
        if w is not None and w.isRunning():
            w.wait(1500)
        self._worker = None
