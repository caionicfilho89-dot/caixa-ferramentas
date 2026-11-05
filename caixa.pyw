"""Caixa de Ferramentas do Caio — um app só que reúne todas as ferramentas.

Mostra uma grade de cartões; clicar abre a ferramenta (cada uma roda no seu processo,
então nada interfere em nada). Busca no topo e botão pra criar atalho no Menu Iniciar.
Tudo offline.

Para adicionar uma ferramenta nova: é só pôr uma linha em TOOLS.
"""
import os
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)   # C:\Users\caion — onde ficam as pastas das ferramentas
ACCENT = "#7c5cff"

# (emoji, nome, descrição, pasta, script)
TOOLS = [
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
QPushButton { background:#222a38; border:0; border-radius:9px; padding:8px 12px; }
QPushButton:hover { background:#2d3550; }
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
    """Caminho do pythonw.exe (sem console). Cai pro python atual se não achar."""
    exe = sys.executable
    d = os.path.dirname(exe)
    for cand in (os.path.join(d, "pythonw.exe"), exe):
        if os.path.exists(cand):
            return cand
    return exe


class Card(QFrame):
    def __init__(self, tool, on_open):
        super().__init__(objectName="card")
        emoji, name, desc, folder, script = tool
        self.path = os.path.join(BASE, folder, script)
        self.exists = os.path.exists(self.path)
        self.on_open = on_open
        self.tool = tool
        self.setFixedSize(230, 118)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)
        top = QHBoxLayout()
        top.setSpacing(8)
        em = QLabel(emoji, objectName="emoji")
        nm = QLabel(name, objectName="name")
        nm.setWordWrap(True)
        top.addWidget(em)
        top.addWidget(nm, 1)
        lay.addLayout(top)
        d = QLabel(desc, objectName="desc")
        d.setWordWrap(True)
        lay.addWidget(d, 1)
        if not self.exists:
            lay.addWidget(QLabel("não encontrada", objectName="missing"))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.on_open(self)


class Caixa(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Caixa de Ferramentas do Caio")
        self.setWindowIcon(app_icon())
        self.resize(780, 640)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(10)
        head = QHBoxLayout()
        tt = QVBoxLayout()
        tt.setSpacing(2)
        tt.addWidget(QLabel("🧰 Caixa de Ferramentas", objectName="title"))
        tt.addWidget(QLabel(f"{len(TOOLS)} ferramentas, tudo offline. Clique pra abrir.", objectName="sub"))
        head.addLayout(tt)
        head.addStretch(1)
        self.shortcut_btn = QPushButton("📌  Atalho no Menu Iniciar")
        self.shortcut_btn.clicked.connect(self.make_shortcut)
        head.addWidget(self.shortcut_btn, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(head)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar ferramenta…")
        self.search.textChanged.connect(self.rebuild)
        root.addWidget(self.search)

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

    def rebuild(self):
        q = self.search.text().lower().strip()
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        cols = 3
        shown = [t for t in TOOLS if not q or q in t[1].lower() or q in t[2].lower()]
        for i, tool in enumerate(shown):
            self.grid.addWidget(Card(tool, self.open_tool), i // cols, i % cols)

    def open_tool(self, card):
        if not card.exists:
            QMessageBox.warning(self, "Ops", f"Não achei:\n{card.path}")
            return
        try:
            subprocess.Popen([pythonw(), card.path], cwd=os.path.dirname(card.path))
            self.status.setText("Abrindo " + card.tool[1] + "…")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Erro", str(e))

    def make_shortcut(self):
        """Cria um atalho no Menu Iniciar que abre a Caixa."""
        start = os.path.join(os.environ.get("APPDATA", ""),
                             r"Microsoft\Windows\Start Menu\Programs")
        lnk = os.path.join(start, "Caixa de Ferramentas.lnk")
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
                           check=True, capture_output=True,
                           creationflags=0x08000000)
            QMessageBox.information(self, "Pronto",
                                    "Atalho criado no Menu Iniciar!\nProcure por “Caixa de Ferramentas”.")
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Não deu", f"Não consegui criar o atalho:\n{e}")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    w = Caixa()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
