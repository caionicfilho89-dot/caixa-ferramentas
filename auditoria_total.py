"""Auditoria funcional de TODAS as ferramentas da Caixa (17/11/2026, pedido do Caio: "faz todas funcionar").

Para cada ferramenta do BUILTIN, em paralelo:
  1. roda os test_*.py da pasta (offscreen, CAIXA_TESTE=1, timeout 120 s cada)
  2. abre a janela principal fora da tela (build_tmp/abre_vazia.py) e vê se quebra
Junta com caca_fake.json (ferramentas que caem em resultado falso) e grava auditoria_total.json:
  [{pasta, nome, testes: ok|falhou|sem_teste, erro_teste, janela: ok|quebrou, erro_janela, fake: bool}]

    python auditoria_total.py            # tudo (demora)
    python auditoria_total.py --pastas a,b
"""
import ast
import concurrent.futures as cf
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
ABRE = os.path.join(HERE, "build_tmp", "abre_vazia.py")
ENV = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONIOENCODING="utf-8", CAIXA_TESTE="1")


def ferramentas():
    arv = ast.parse(open(os.path.join(HERE, "caixa.pyw"), encoding="utf-8").read())
    for no in ast.walk(arv):
        if isinstance(no, ast.Assign) and any(getattr(t, "id", "") == "BUILTIN" for t in no.targets):
            return [tuple(e.value for e in t.elts) for t in no.value.elts]
    return []


def roda(cmd, cwd, timeout=120):
    try:
        r = subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, creationflags=0x08000000)
        return r.returncode, (r.stdout + "\n" + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return 99, "TIMEOUT"
    except Exception as e:  # noqa: BLE001
        return 98, repr(e)


def ultima_linha_util(txt):
    linhas = [l for l in txt.splitlines() if l.strip()]
    for l in reversed(linhas):
        if "Error" in l or "error" in l or "FAILED" in l or "Traceback" in l or "assert" in l.lower():
            return l.strip()[:200]
    return (linhas[-1].strip()[:200] if linhas else "")


def auditar(tool):
    emoji, nome, desc, pasta, script = tool[:5]
    raiz = os.path.join(BASE, pasta)
    r = {"pasta": pasta, "nome": nome, "script": script}
    if not os.path.isdir(raiz):
        r.update(testes="sem_pasta", janela="sem_pasta")
        return r
    testes = sorted(glob.glob(os.path.join(raiz, "test_*.py")))
    if not testes:
        r["testes"] = "sem_teste"
    else:
        falhas = []
        for t in testes:
            rc, out = roda([sys.executable, os.path.basename(t)], raiz)
            if rc != 0:
                falhas.append(f"{os.path.basename(t)}: {ultima_linha_util(out)}")
        r["testes"] = "falhou" if falhas else "ok"
        if falhas:
            r["erro_teste"] = falhas[:3]
    rc, out = roda([sys.executable, ABRE, pasta, script], HERE, timeout=60)
    r["janela"] = "ok" if rc == 0 else "quebrou"
    r["janela_info"] = ultima_linha_util(out)
    return r


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tools = ferramentas()
    if "--pastas" in sys.argv:
        quero = set(sys.argv[sys.argv.index("--pastas") + 1].split(","))
        tools = [t for t in tools if t[3] in quero]
    fake = {f["pasta"] for f in json.load(open(os.path.join(HERE, "caca_fake.json"), encoding="utf-8"))} \
        if os.path.exists(os.path.join(HERE, "caca_fake.json")) else set()
    res = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for i, r in enumerate(ex.map(auditar, tools), 1):
            r["fake"] = r["pasta"] in fake
            res.append(r)
            if i % 50 == 0:
                print(f"{i}/{len(tools)}", flush=True)
    json.dump(res, open(os.path.join(HERE, "auditoria_total.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    falhou = [r for r in res if r.get("testes") == "falhou"]
    quebrou = [r for r in res if r.get("janela") == "quebrou"]
    print(f"\nTOTAL {len(res)} | testes falhando: {len(falhou)} | janela quebra ao abrir: {len(quebrou)} | "
          f"sem teste: {sum(r.get('testes') == 'sem_teste' for r in res)} | resultado falso: {sum(r['fake'] for r in res)}")


if __name__ == "__main__":
    main()
