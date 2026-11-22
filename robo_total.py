"""Roda o robô apertador (robo_botoes.py) em TODAS as ferramentas e grava robo_total.json.

    python robo_total.py               # 769 ferramentas, 6 por vez
    python robo_total.py --pastas a,b
"""
import ast
import concurrent.futures as cf
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", QT_QPA_PLATFORM="offscreen", CAIXA_TESTE="1")


def ferramentas():
    arv = ast.parse(open(os.path.join(HERE, "caixa.pyw"), encoding="utf-8").read())
    for no in ast.walk(arv):
        if isinstance(no, ast.Assign) and any(getattr(t, "id", "") == "BUILTIN" for t in no.targets):
            return [tuple(e.value for e in t.elts) for t in no.value.elts]
    return []


def um(tool):
    pasta, script = tool[3], tool[4]
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "robo_botoes.py"), pasta, script], env=ENV,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=150,
                           creationflags=0x08000000)
        linhas = [l for l in r.stdout.splitlines() if l.startswith("{")]
        if linhas:
            res = json.loads(linhas[-1])
        else:
            res = {"pasta": pasta, "abriu": False, "botoes": 0, "bloqueados": [],
                   "erros": [f"CAIU (código {r.returncode}): {(r.stderr or '').strip().splitlines()[-1:] }"]}
    except subprocess.TimeoutExpired:
        res = {"pasta": pasta, "abriu": None, "botoes": 0, "bloqueados": [], "erros": ["TRAVOU (150 s)"]}
    res["nome"] = tool[1]
    return res


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tools = ferramentas()
    if "--pastas" in sys.argv:
        quero = set(sys.argv[sys.argv.index("--pastas") + 1].split(","))
        tools = [t for t in tools if t[3] in quero]
    res = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for i, r in enumerate(ex.map(um, tools), 1):
            res.append(r)
            if i % 50 == 0:
                print(f"{i}/{len(tools)}", flush=True)
    json.dump(res, open(os.path.join(HERE, "robo_total.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ruins = [r for r in res if r["erros"]]
    print(f"\nTOTAL {len(res)} | com erro ao clicar/abrir: {len(ruins)} | "
          f"botões clicados: {sum(r['botoes'] for r in res)}")


if __name__ == "__main__":
    main()
