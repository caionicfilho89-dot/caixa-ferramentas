"""Caixa de Ferramentas do Caio — um app só que reúne todas as ferramentas.

Grade de cartões; clicar abre a ferramenta (cada uma roda no seu processo, então nada
interfere em nada). Busca no topo, favoritos, abrir no boot, e dá pra adicionar
ferramentas novas pela própria Caixa (sem mexer no código). Tudo offline.

Config do usuário (favoritos + ferramentas adicionadas) em %LOCALAPPDATA%\\CaixaFerramentas.
"""
import json
import os
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (QApplication, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
                             QInputDialog, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton,
                             QScrollArea, QVBoxLayout, QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)   # C:\Users\caion — onde ficam as pastas das ferramentas
FROZEN = getattr(sys, "frozen", False)  # True quando empacotado num .exe (instalador)
ACCENT = "#7c5cff"

CFG_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "CaixaFerramentas")
CFG = os.path.join(CFG_DIR, "config.json")
STARTUP = os.path.join(os.environ.get("APPDATA", ""),
                       r"Microsoft\Windows\Start Menu\Programs\Startup")
BOOT_LNK = os.path.join(STARTUP, "Caixa de Ferramentas.lnk")

# ferramentas de fábrica: (emoji, nome, descrição, pasta, script)
BUILTIN = [
    ("📄", "Kit de PDF", "Juntar, separar, girar, comprimir, imagens↔PDF", "kit-pdf", "kit_pdf.pyw"),
    ("🧹", "Faxina de Disco", "Vê o que ocupa o HD e manda pra Lixeira", "faxina-disco", "faxina.pyw"),
    ("♻️", "Recupera Arquivos", "Recupera arquivos apagados (carving / NTFS)", "recupera-arquivos", "recupera.pyw"),
    ("🧽", "Limpar Metadados", "Remove GPS/autor de fotos, PDF e Office", "limpa-metadados", "limpar_metadados.pyw"),
    ("🔳", "QR Code", "Gera e lê QR (link, wifi, contato…)", "qrcode-tool", "qrcode_tool.pyw"),
    ("✏️", "Print Anotador", "Captura a tela e anota (seta, tarja, texto)", "print-anotador", "print_anotador.pyw"),
    ("🖼️", "Conversor de Imagens", "Converte fotos em lote (inclusive HEIC)", "conversor-imagens", "conversor_imagens.pyw"),
    ("🔐", "Cofre de Senhas", "Gera senhas fortes + cofre criptografado", "cofre-senhas", "cofre_senhas.pyw"),
    ("🎥", "Gravador de Tela", "Grava a tela em MP4 ou GIF com som", "gravador-tela", "gravador_tela.pyw"),
    ("🎵", "Conversor Áudio/Vídeo", "Troca formato, extrai áudio, corta trecho", "conversor-av", "conversor_av.pyw"),
    ("🎨", "Capturador de Cores", "Conta-gotas da tela (HEX/RGB) + paleta", "capturador-cores", "capturador_cores.pyw"),
    ("📝", "Extrator de Texto", "OCR: copia o texto de uma área da tela", "extrator-texto", "extrator_texto.pyw"),
    ("🔍", "Busca de Arquivos", "Acha arquivo pelo nome na hora (Everything)", "busca-arquivos", "busca_arquivos.pyw"),
    ("✎", "Renomeador em Lote", "Renomeia vários arquivos com prévia", "renomeador", "renomeador.pyw"),
    ("📋", "Área de Transferência", "Histórico do que você copiou (Ctrl+Shift+V)", "area-transferencia", "area_transferencia.pyw"),
    ("⏱️", "Rastreador de Tempo", "Quanto tempo você passa em cada app", "rastreador-tempo", "rastreador_tempo.pyw"),
    ("🛰️", "GPS Falso", "Simula um GPS (NMEA) por TCP/UDP pra apps de navegação", "gps-falso", "gps_falso.pyw"),
]

QSS = """
QWidget { background:#0e1016; color:#e7e9f0; font:10pt 'Segoe UI'; }
#title { font:800 22pt 'Segoe UI'; }
#sub { color:#8a93a8; }
QLineEdit { background:#161a23; border:1px solid #2d3550; border-radius:12px; padding:10px 14px; font:12pt 'Segoe UI'; }
QLineEdit:focus { border:1px solid #7c5cff; }
QScrollArea { border:0; }
#card { background:#161a23; border:1px solid #232a3b; border-radius:16px; }
#card:hover { border:1px solid #7c5cff; background:#1a1f2b; }
#emoji { font:22pt 'Segoe UI Emoji'; }
#name { font:700 11pt 'Segoe UI'; }
#desc { color:#8a93a8; font:9pt 'Segoe UI'; }
#missing { color:#ff6b6b; font:9pt 'Segoe UI'; }
#star { color:#ffd166; font:12pt 'Segoe UI'; }
#section { color:#8a93a8; font:700 10pt 'Segoe UI'; }
QPushButton { background:#222a38; border:0; border-radius:9px; padding:8px 12px; }
QPushButton:hover { background:#2d3550; }
QPushButton:checked { background:#2a2740; color:#c9b8ff; }
#add { background:#1d2b22; }
#add:hover { background:#28402f; }
"""


def app_icon():
    pm = QPixmap(64, 64)
    pm.fill(QColor("transparent"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(ACCENT))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(6, 14, 52, 42, 10, 10)
    p.setBrush(QColor("#0e1016"))
    p.drawRoundedRect(24, 8, 16, 12, 4, 4)
    p.setBrush(QColor("#fff"))
    p.drawRect(30, 26, 4, 18)
    p.drawRect(25, 33, 14, 4)
    p.end()
    return QIcon(pm)


def pythonw():
    exe = sys.executable
    d = os.path.dirname(exe)
    cand = os.path.join(d, "pythonw.exe")
    return cand if os.path.exists(cand) else exe


def load_cfg():
    try:
        with open(CFG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"favorites": [], "extra_tools": []}


def save_cfg(cfg):
    os.makedirs(CFG_DIR, exist_ok=True)
    try:
        with open(CFG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


class Card(QFrame):
    def __init__(self, tool, caixa, fav):
        super().__init__(objectName="card")
        emoji, name, desc, folder, script = tool
        self.tool = tool
        self.key = folder
        self.caixa = caixa
        self.path = os.path.join(BASE, folder, script)
        self.exists = True if FROZEN else os.path.exists(self.path)
        self.setFixedSize(230, 120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 12, 10)
        lay.setSpacing(4)
        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(QLabel(emoji, objectName="emoji"))
        nm = QLabel(name, objectName="name")
        nm.setWordWrap(True)
        top.addWidget(nm, 1)
        if fav:
            top.addWidget(QLabel("★", objectName="star"), 0, Qt.AlignmentFlag.AlignTop)
        lay.addLayout(top)
        d = QLabel(desc, objectName="desc")
        d.setWordWrap(True)
        lay.addWidget(d, 1)
        if not self.exists:
            lay.addWidget(QLabel("não encontrada", objectName="missing"))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.caixa.open_tool(self)

    def _menu(self, pos):
        m = QMenu(self)
        is_fav = self.key in self.caixa.cfg["favorites"]
        a_fav = m.addAction("☆ Tirar dos favoritos" if is_fav else "⭐ Favoritar")
        a_folder = m.addAction("Abrir pasta")
        a_rm = None
        if any(self.key == t[3] for t in self.caixa.extra_tools):
            a_rm = m.addAction("Remover da Caixa")
        act = m.exec(self.mapToGlobal(pos))
        if act is a_fav:
            self.caixa.toggle_fav(self.key)
        elif act is a_folder:
            folder = os.path.dirname(self.path)
            if os.path.isdir(folder):
                os.startfile(folder)  # noqa: S606
        elif a_rm is not None and act is a_rm:
            self.caixa.remove_tool(self.key)


class Caixa(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Caixa de Ferramentas do Caio")
        self.setWindowIcon(app_icon())
        self.resize(800, 660)
        self.cfg = load_cfg()
        self.cfg.setdefault("favorites", [])
        self.cfg.setdefault("extra_tools", [])
        self.extra_tools = [tuple(t) for t in self.cfg["extra_tools"]]

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(10)

        head = QHBoxLayout()
        tt = QVBoxLayout()
        tt.setSpacing(2)
        tt.addWidget(QLabel("🧰 Caixa de Ferramentas", objectName="title"))
        self.sub = QLabel("", objectName="sub")
        tt.addWidget(self.sub)
        head.addLayout(tt)
        head.addStretch(1)
        self.boot_btn = QPushButton("🔌  Abrir no boot")
        self.boot_btn.setCheckable(True)
        self.boot_btn.setChecked(os.path.exists(BOOT_LNK))
        self.boot_btn.clicked.connect(self.toggle_boot)
        self.sc_btn = QPushButton("📌  Menu Iniciar")
        self.sc_btn.clicked.connect(self.make_shortcut)
        head.addWidget(self.boot_btn, 0, Qt.AlignmentFlag.AlignTop)
        head.addWidget(self.sc_btn, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(head)

        sr = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar ferramenta…")
        self.search.textChanged.connect(self.rebuild)
        sr.addWidget(self.search, 1)
        add = QPushButton("➕  Adicionar ferramenta", objectName="add")
        add.clicked.connect(self.add_tool)
        sr.addWidget(add)
        root.addLayout(sr)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.host = QWidget()
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(2, 4, 2, 4)
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.host)
        root.addWidget(self.scroll, 1)

        self.status = QLabel("", objectName="sub")
        root.addWidget(self.status)

        self.search.setFocus()
        self.rebuild()

    def all_tools(self):
        return BUILTIN + self.extra_tools

    def rebuild(self):
        q = self.search.text().lower().strip()
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        tools = [t for t in self.all_tools()
                 if not q or q in t[1].lower() or q in t[2].lower()]
        favs = self.cfg["favorites"]
        # favoritos primeiro, mantendo a ordem original dentro de cada grupo
        tools.sort(key=lambda t: (t[3] not in favs,))
        cols = 3
        row = 0
        col = 0
        # cabeçalho "Favoritos" se houver algum visível
        has_fav = any(t[3] in favs for t in tools)
        if has_fav and not q:
            lbl = QLabel("★ Favoritos", objectName="section")
            self.grid.addWidget(lbl, row, 0, 1, cols)
            row += 1
        inserted_all_header = False
        for t in tools:
            if has_fav and not q and t[3] not in favs and not inserted_all_header:
                if col != 0:
                    row += 1
                    col = 0
                self.grid.addWidget(QLabel("Todas", objectName="section"), row, 0, 1, cols)
                row += 1
                inserted_all_header = True
            self.grid.addWidget(Card(t, self, t[3] in favs), row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1
        self.sub.setText(f"{len(self.all_tools())} ferramentas, tudo offline. Clique pra abrir.")

    # ---- abrir ----
    def open_tool(self, card):
        if not card.exists:
            QMessageBox.warning(self, "Ops", f"Não achei:\n{card.path}")
            return
        try:
            if FROZEN:
                # no instalador: o próprio exe abre a ferramenta (Caixa.exe --tool <chave>)
                subprocess.Popen([sys.executable, "--tool", card.key])
            else:
                subprocess.Popen([pythonw(), card.path], cwd=os.path.dirname(card.path))
            self.status.setText("Abrindo " + card.tool[1] + "…")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Erro", str(e))

    # ---- favoritos ----
    def toggle_fav(self, key):
        favs = self.cfg["favorites"]
        if key in favs:
            favs.remove(key)
        else:
            favs.append(key)
        save_cfg(self.cfg)
        self.rebuild()

    # ---- adicionar / remover ferramenta ----
    def add_tool(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Escolha o programa da ferramenta", BASE, "Python (*.pyw *.py)")
        if not path:
            return
        folder_full = os.path.dirname(path)
        folder = os.path.basename(folder_full)
        script = os.path.basename(path)
        if folder in [t[3] for t in self.all_tools()]:
            QMessageBox.information(self, "Já tem", "Essa ferramenta já está na Caixa.")
            return
        name, ok = QInputDialog.getText(self, "Nome", "Nome da ferramenta:",
                                        text=folder.replace("-", " ").title())
        if not ok or not name.strip():
            return
        emoji, _ = QInputDialog.getText(self, "Ícone", "Um emoji pro ícone (opcional):", text="🧩")
        desc, _ = QInputDialog.getText(self, "Descrição", "Descrição curta (opcional):", text="")
        tool = (emoji.strip() or "🧩", name.strip(), desc.strip(), folder, script)
        self.extra_tools.append(tool)
        self.cfg["extra_tools"] = [list(t) for t in self.extra_tools]
        save_cfg(self.cfg)
        self.rebuild()
        self.status.setText(f"“{name}” adicionada!")

    def remove_tool(self, key):
        self.extra_tools = [t for t in self.extra_tools if t[3] != key]
        self.cfg["extra_tools"] = [list(t) for t in self.extra_tools]
        if key in self.cfg["favorites"]:
            self.cfg["favorites"].remove(key)
        save_cfg(self.cfg)
        self.rebuild()

    # ---- boot / atalho ----
    def toggle_boot(self):
        if self.boot_btn.isChecked():
            ok = self._make_lnk(BOOT_LNK)
            if ok:
                self.status.setText("Vai abrir junto com o Windows.")
            else:
                self.boot_btn.setChecked(False)
        else:
            try:
                os.remove(BOOT_LNK)
            except OSError:
                pass
            self.status.setText("Não abre mais no boot.")

    def make_shortcut(self):
        start = os.path.join(os.environ.get("APPDATA", ""),
                             r"Microsoft\Windows\Start Menu\Programs")
        if self._make_lnk(os.path.join(start, "Caixa de Ferramentas.lnk")):
            QMessageBox.information(self, "Pronto",
                                    "Atalho criado! Procure por “Caixa de Ferramentas” no Menu Iniciar.")

    def _make_lnk(self, lnk):
        if FROZEN:
            target = sys.executable
            arg = ""
        else:
            target = pythonw()
            arg = os.path.abspath(__file__)
        ps = (
            "$w = New-Object -ComObject WScript.Shell; "
            f"$s = $w.CreateShortcut('{lnk}'); "
            f"$s.TargetPath = '{target}'; "
            f"$s.Arguments = '\"{arg}\"'; "
            f"$s.WorkingDirectory = '{HERE}'; "
            f"$s.IconLocation = '{target}'; "
            "$s.Save()"
        )
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           check=True, capture_output=True, creationflags=0x08000000)
            return True
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Não deu", f"Não consegui criar o atalho:\n{e}")
            return False


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    w = Caixa()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
