"""Robô apertador: abre uma ferramenta fora da tela, clica em TODOS os botões e anota os erros.

    python robo_botoes.py <pasta> <script>        # uma ferramenta (imprime JSON na última linha)

Segurança (nada destrutivo acontece de verdade, tudo vira "faria X"):
- apagar/mover/renomear arquivo, Lixeira, registro do Windows, rodar programa externo, abrir URL/arquivo,
  ctypes do Windows (papel de parede, desligar...), rede (sockets/urllib) → bloqueado e anotado
- caixas de mensagem/pergunta respondem "Não"/"Cancelar"; escolher arquivo devolve "nenhum"
- diálogos (QDialog.exec) fecham na hora; trabalho em thread tem 1,5 s pra terminar
- HOME/APPDATA/LOCALAPPDATA apontam pra uma pasta temporária: a ferramenta não toca nos dados do Caio
"""
import builtins
import importlib.machinery
import json
import os
import sys
import tempfile
import time
import traceback

pasta, script = sys.argv[1], sys.argv[2]
raiz = os.path.join(r"C:\Users\caion", pasta)
tmp = tempfile.mkdtemp(prefix="robo_")
for k in ("USERPROFILE", "HOME", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
    os.environ[k] = tmp
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["CAIXA_TESTE"] = "1"
sys.stdout.reconfigure(encoding="utf-8")

erros, bloqueados = [], []


def anota_bloqueio(o_que):
    if len(bloqueados) < 40:
        bloqueados.append(o_que)


# ── bloqueios de segurança ───────────────────────────────────────────────
import shutil  # noqa: E402
import subprocess  # noqa: E402
import webbrowser  # noqa: E402


def _nega(nome):
    def f(*a, **k):
        anota_bloqueio(f"{nome}{tuple(str(x)[:60] for x in a[:2])}")
        raise PermissionError(f"robô: {nome} bloqueado")
    return f


class _ProcFalso:
    returncode = 0
    stdout = b""
    stderr = b""
    pid = 0

    def __init__(self, *a, **k):
        anota_bloqueio(f"processo {str(a[0])[:80] if a else ''}")

    def communicate(self, *a, **k):
        return (b"", b"")

    def wait(self, *a, **k):
        return 0

    def poll(self):
        return 0

    def kill(self):
        pass

    terminate = kill

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _run_falso(*a, **k):
    anota_bloqueio(f"subprocess.run {str(a[0])[:80] if a else ''}")
    texto = k.get("text") or k.get("encoding") or k.get("universal_newlines")
    return subprocess.CompletedProcess(a[0] if a else [], 0, "" if texto else b"", "" if texto else b"")


subprocess.Popen = _ProcFalso
subprocess.run = _run_falso
subprocess.call = lambda *a, **k: (anota_bloqueio(f"subprocess.call {str(a[0])[:60] if a else ''}"), 0)[1]
subprocess.check_call = subprocess.call
subprocess.check_output = lambda *a, **k: (anota_bloqueio("subprocess.check_output"), b"")[1]
_TMP = os.path.normcase(os.path.realpath(tmp))


def _no_tmp(caminho):
    """Caminho dentro da pasta temporária do robô (HOME/APPDATA apontam pra lá)."""
    try:
        p = os.path.normcase(os.path.realpath(os.fspath(caminho)))
    except TypeError:
        return False
    return p == _TMP or p.startswith(_TMP + os.sep)


def _so_no_tmp(nome, original):
    """Apagar/mover/renomear vale DENTRO da pasta temporária (ex.: salvar com os.replace,
    o jeito seguro); fora dela, bloqueado e anotado. Sem isso as ferramentas trocavam o
    salvamento seguro por escrita direta só pra passar no robô (aconteceu no lote 2)."""
    def f(*a, **k):
        caminhos = [x for x in a[:2] if isinstance(x, (str, bytes, os.PathLike))]
        if caminhos and all(_no_tmp(c) for c in caminhos):
            return original(*a, **k)
        anota_bloqueio(f"{nome}{tuple(str(x)[:60] for x in a[:2])}")
        raise PermissionError(f"robô: {nome} bloqueado")
    return f


for nome in ("remove", "unlink", "rmdir", "removedirs", "rename", "replace"):
    if hasattr(os, nome):
        setattr(os, nome, _so_no_tmp(f"os.{nome}", getattr(os, nome)))
for nome in ("startfile", "system"):
    if hasattr(os, nome):
        setattr(os, nome, _nega(f"os.{nome}"))
for nome in ("rmtree", "move"):
    setattr(shutil, nome, _so_no_tmp(f"shutil.{nome}", getattr(shutil, nome)))
webbrowser.open = webbrowser.open_new = webbrowser.open_new_tab = lambda *a, **k: anota_bloqueio("abrir URL") or True
try:
    import send2trash
    send2trash.send2trash = _nega("send2trash")
except Exception:  # noqa: BLE001
    pass
try:
    import winreg
    for nome in ("SetValueEx", "SetValue", "DeleteValue", "DeleteKey", "CreateKey", "CreateKeyEx"):
        setattr(winreg, nome, _nega(f"winreg.{nome}"))
except Exception:  # noqa: BLE001
    pass
import socket  # noqa: E402
socket.socket.connect = _nega("socket.connect")
socket.create_connection = _nega("socket.create_connection")
import urllib.request  # noqa: E402
urllib.request.urlopen = _nega("urlopen")
import ctypes  # noqa: E402
try:
    _u32 = ctypes.windll.user32
    for nome in ("SystemParametersInfoW", "ExitWindowsEx", "LockWorkStation", "SetCursorPos", "keybd_event",
                 "mouse_event", "SendInput", "BlockInput", "SetForegroundWindow", "ShowWindow", "PostMessageW",
                 "SendMessageW", "MoveWindow", "SetWindowPos", "RegisterHotKey"):
        try:
            setattr(_u32, nome, (lambda n: (lambda *a, **k: anota_bloqueio(f"user32.{n}") or 0))(nome))
        except Exception:  # noqa: BLE001
            pass
except Exception:  # noqa: BLE001
    pass

# ── Qt: diálogos respondem sozinhos ──────────────────────────────────────
from PyQt6 import sip  # noqa: E402
from PyQt6.QtCore import QEvent, QThread, QTimer  # noqa: E402
from PyQt6.QtWidgets import (QAbstractButton, QApplication, QColorDialog, QDialog, QFileDialog,  # noqa: E402
                             QFontDialog, QInputDialog, QMainWindow, QMenu, QMessageBox, QWidget)

B = QMessageBox.StandardButton
for nome in ("information", "warning", "critical", "about", "aboutQt"):
    setattr(QMessageBox, nome, staticmethod(lambda *a, **k: B.Ok))
QMessageBox.question = staticmethod(lambda *a, **k: B.No)
QMessageBox.exec = lambda self, *a: int(B.Cancel.value) if hasattr(B.Cancel, "value") else 0
QDialog.exec = lambda self, *a: 0
QMenu.exec = lambda self, *a, **k: None
QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ("", ""))
QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: ([], ""))
QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: ("", ""))
QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: "")
QInputDialog.getText = staticmethod(lambda *a, **k: ("", False))
QInputDialog.getInt = staticmethod(lambda *a, **k: (0, False))
QInputDialog.getDouble = staticmethod(lambda *a, **k: (0.0, False))
QInputDialog.getItem = staticmethod(lambda *a, **k: ("", False))
QInputDialog.getMultiLineText = staticmethod(lambda *a, **k: ("", False))
QColorDialog.getColor = staticmethod(lambda *a, **k: __import__("PyQt6.QtGui", fromlist=["QColor"]).QColor())
QFontDialog.getFont = staticmethod(lambda *a, **k: (__import__("PyQt6.QtGui", fromlist=["QFont"]).QFont(), False))


def gancho(tipo, valor, tb):
    if isinstance(valor, PermissionError) and "robô:" in str(valor):
        return  # foi o bloqueio de segurança, não defeito
    pilha = traceback.extract_tb(tb)
    local = next((f"{os.path.basename(f.filename)}:{f.lineno} {f.name}" for f in reversed(pilha)
                  if f.filename.startswith(raiz)), "?")
    erros.append(f"{tipo.__name__}: {str(valor)[:140]} @ {local}")


sys.excepthook = gancho
threading_hook = None
import threading  # noqa: E402
threading.excepthook = lambda a: gancho(a.exc_type, a.exc_value, a.exc_traceback)

# ── abre e aperta ────────────────────────────────────────────────────────
sys.path.insert(0, raiz)
os.chdir(raiz)
app = QApplication.instance() or QApplication([])
resultado = {"pasta": pasta, "abriu": False, "botoes": 0, "erros": erros, "bloqueados": bloqueados}
try:
    mod = importlib.machinery.SourceFileLoader("ferramenta_robo", os.path.join(raiz, script)).load_module()
    vals = list(vars(mod).values())
    classes = [v for v in vals if isinstance(v, type) and issubclass(v, (QMainWindow, QWidget))
               and v.__module__ == mod.__name__]
    classes.sort(key=lambda c: (issubclass(c, QMainWindow), vals.index(c)))
    janela = None
    for cls in reversed(classes):
        try:
            janela = cls()
            break
        except TypeError:
            continue
    if janela is None:
        raise RuntimeError("sem janela sem argumentos")
    janela.show()
    resultado["abriu"] = True

    def gira(seg):
        fim = time.time() + seg
        while time.time() < fim:
            app.processEvents()
            app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.01)

    gira(0.3)
    vistos = set()
    for _rodada in range(2):  # botões que aparecem depois de outros cliques
        for b in janela.findChildren(QAbstractButton):
            # Clique anterior pode ter feito deleteLater. Sem esvaziar a fila,
            # o próximo click() é num C++ já morto e o processo leva access violation.
            if sip.isdeleted(b):
                continue
            if id(b) in vistos or not b.isEnabled():
                continue
            # Botão interno do Qt (ex.: qt_menubar_ext_button). O clique abre um
            # menu modal no C++, que o patch de QMenu.exec não alcança, e a janela
            # fica presa fora da tela. Não é botão da ferramenta.
            if (b.objectName() or "").startswith("qt_"):
                continue
            vistos.add(id(b))
            texto = (b.text() or b.toolTip() or b.objectName() or "?").strip()[:40]
            if any(p in texto.lower() for p in ("sair", "fechar", "quit", "exit")):
                continue
            antes = len(erros)
            menu = b.menu() if hasattr(b, "menu") else None
            if menu is not None:
                # Botão com menu: abrir o menu trava (exec modal no C++). Aciona cada item
                # do menu, que é o que o Caio clicaria, inclusive os de submenus.
                pilha = [menu]
                while pilha:
                    m = pilha.pop()
                    for acao in m.actions():
                        if acao.menu() is not None:
                            pilha.append(acao.menu())
                        elif acao.isEnabled() and not acao.isSeparator():
                            try:
                                acao.trigger()
                            except Exception:  # noqa: BLE001
                                gancho(*sys.exc_info())
                            gira(0.05)
                            resultado["botoes"] += 1
            else:
                try:
                    b.click()
                except Exception:  # noqa: BLE001
                    gancho(*sys.exc_info())
            gira(0.05)
            for e in erros[antes:]:
                erros[erros.index(e)] = f"[{texto}] {e}"
            resultado["botoes"] += 1
            if resultado["botoes"] >= 120:
                break
    gira(1.5)  # threads e timers terminarem
except Exception:  # noqa: BLE001
    gancho(*sys.exc_info())
print(json.dumps(resultado, ensure_ascii=False), flush=True)
sys.stdout.flush()
os._exit(0)
