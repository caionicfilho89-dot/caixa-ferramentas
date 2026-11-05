"""Empacota a Caixa + as 16 ferramentas num executável único (Caixa.exe) com PyInstaller.

Como funciona o exe gerado:
  Caixa.exe              -> abre a Caixa (grade de ferramentas)
  Caixa.exe --tool <k>   -> abre a ferramenta <k> (a Caixa chama isso ao clicar num cartão)
  Caixa.exe --selftest   -> importa todas as ferramentas e sai (teste de sanidade do build)

Passos: (1) junta todos os .py/.pyw das pastas das ferramentas num diretório "staged" plano
(os imports são achatados, ex. 'import finder'); (2) gera o entry app.py com o mapa de
ferramentas; (3) roda o PyInstaller (onedir, --windowed).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
STAGED = os.path.join(HERE, "staged")

# chave (pasta) -> script .pyw principal
TOOLS = {
    "kit-pdf": "kit_pdf.pyw",
    "faxina-disco": "faxina.pyw",
    "recupera-arquivos": "recupera.pyw",
    "limpa-metadados": "limpar_metadados.pyw",
    "qrcode-tool": "qrcode_tool.pyw",
    "print-anotador": "print_anotador.pyw",
    "conversor-imagens": "conversor_imagens.pyw",
    "cofre-senhas": "cofre_senhas.pyw",
    "gravador-tela": "gravador_tela.pyw",
    "conversor-av": "conversor_av.pyw",
    "capturador-cores": "capturador_cores.pyw",
    "extrator-texto": "extrator_texto.pyw",
    "busca-arquivos": "busca_arquivos.pyw",
    "renomeador": "renomeador.pyw",
    "area-transferencia": "area_transferencia.pyw",
    "rastreador-tempo": "rastreador_tempo.pyw",
    "gps-falso": "gps_falso.pyw",
    "ferramentas-br": "ferramentas_br.pyw",
}

# pacotes que precisam ser recolhidos inteiros (dados/submódulos) pro freeze funcionar
COLLECT_ALL = ["soundcard", "winrt", "winocr", "pillow_heif", "pikepdf", "segno",
               "send2trash", "piexif", "spellchecker"]


def stage():
    if os.path.exists(STAGED):
        shutil.rmtree(STAGED)
    os.makedirs(STAGED)
    copied = {}  # nome_arquivo -> origem (pra detectar colisão)
    modmap = {}  # chave -> nome_modulo da GUI

    for folder, script in TOOLS.items():
        src_dir = os.path.join(BASE, folder)
        if not os.path.isdir(src_dir):
            raise SystemExit(f"Pasta não encontrada: {src_dir}")
        for fn in os.listdir(src_dir):
            if not fn.endswith((".py", ".pyw")):
                continue
            src = os.path.join(src_dir, fn)
            # a GUI .pyw vira <nome>.py; os motores .py ficam iguais
            dst_name = fn[:-4] + ".py" if fn.endswith(".pyw") else fn
            dst = os.path.join(STAGED, dst_name)
            data = open(src, "rb").read()
            if dst_name in copied:
                if open(dst, "rb").read() != data:
                    raise SystemExit(f"COLISÃO de nome diferente: {dst_name} "
                                     f"({copied[dst_name]} x {src})")
                continue
            open(dst, "wb").write(data)
            copied[dst_name] = src
            if fn == script:
                modmap[folder] = dst_name[:-3]  # sem .py

    # caixa
    shutil.copyfile(os.path.join(HERE, "caixa.pyw"), os.path.join(STAGED, "caixa_ui.py"))
    _write_entry(modmap)
    return modmap, sorted(m[:-3] for m in copied)


def _write_entry(modmap):
    app = '''"""Entry point empacotado da Caixa de Ferramentas."""
import os
import sys

# no exe: deixa o ffmpeg empacotado visível pras ferramentas (gravador, conversor A/V)
if getattr(sys, "frozen", False):
    base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    os.environ["PATH"] = base + os.pathsep + os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")

MODMAP = %r

def _tool_main(key):
    mod = MODMAP.get(key)
    if not mod:
        raise SystemExit("ferramenta desconhecida: " + str(key))
    m = __import__(mod)
    m.main()

def main():
    argv = sys.argv
    if "--tool" in argv:
        i = argv.index("--tool")
        key = argv[i + 1] if i + 1 < len(argv) else ""
        _tool_main(key)
    elif "--selftest" in argv:
        ok = []
        bad = []
        for k, mod in MODMAP.items():
            try:
                __import__(mod)
                ok.append(mod)
            except Exception as e:  # noqa: BLE001
                bad.append((mod, repr(e)))
        print("OK:", len(ok))
        for mod, err in bad:
            print("FALHOU", mod, err)
        sys.exit(1 if bad else 0)
    else:
        import caixa_ui
        caixa_ui.main()

if __name__ == "__main__":
    main()
''' % (modmap,)
    open(os.path.join(STAGED, "app.py"), "w", encoding="utf-8").write(app)


def build(modmap, modules):
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--windowed",
           "--name", "Caixa", "--paths", STAGED,
           "--distpath", os.path.join(HERE, "dist"),
           "--workpath", os.path.join(HERE, "build_tmp"),
           "--specpath", HERE]
    ico = os.path.join(HERE, "caixa.ico")
    if os.path.exists(ico):
        cmd += ["--icon", ico]
    # empacota o ffmpeg (se estiver em vendor/) pras ferramentas de mídia funcionarem sozinhas
    ff = os.path.join(HERE, "vendor", "ffmpeg.exe")
    if os.path.exists(ff):
        cmd += ["--add-binary", ff + os.pathsep + "."]
    for mod in modules:
        cmd += ["--hidden-import", mod]
    for pkg in COLLECT_ALL:
        cmd += ["--collect-all", pkg]
    cmd.append(os.path.join(STAGED, "app.py"))
    print("Rodando PyInstaller…")
    r = subprocess.run(cmd)
    return r.returncode


if __name__ == "__main__":
    modmap, modules = stage()
    print("Staged:", len(modules), "módulos ·", len(modmap), "ferramentas")
    if "--stage-only" in sys.argv:
        sys.exit(0)
    rc = build(modmap, modules)
    exe = os.path.join(HERE, "dist", "Caixa", "Caixa.exe")
    print("PyInstaller rc:", rc, "| exe existe:", os.path.exists(exe))
