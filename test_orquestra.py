"""Teste da orquestra numa CÓPIA do quadro (o tarefas.json real não é tocado).
1) 12 processos pegando ao mesmo tempo: nenhuma tarefa com dois donos, nenhuma pasta com dois músicos.
2) gancho devolve a tarefa certa no formato certo (Grok = decision/block, Cursor = followup_message).
3) trava central: só um por vez.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def montar():
    d = tempfile.mkdtemp(prefix="orq_")
    for f in ("orquestra.py", "tarefas.py"):
        shutil.copy(os.path.join(HERE, f), d)
    ts = []
    for i in range(1, 9):  # pares de tarefas na MESMA pasta: só um músico por pasta
        ts.append({"id": f"T{i:02d}", "titulo": f"🔧 Funcionar lote {i}", "detalhe": "x",
                   "quem": "cursor grokbuild antigravity", "status": "livre", "por": "",
                   "quando": "2026-11-18 10:00", "resultado": "", "pastas": [f"pasta-{(i + 1) // 2}"]})
    ts.append({"id": "T09", "titulo": "⭐ Paridade [x]", "detalhe": "y", "quem": ["grokbuild"],
               "status": "livre", "por": "", "quando": "2026-11-18 10:00", "resultado": "", "pastas": ["pasta-x"]})
    with open(os.path.join(d, "tarefas.json"), "w", encoding="utf-8") as f:
        json.dump(ts, f)
    return d


def main():
    d = montar()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    cod = "import sys,orquestra; t,_=orquestra.pegar(sys.argv[1]); print(t['id'] if t else '-')"
    procs = [subprocess.Popen([sys.executable, "-c", cod, ag], cwd=d, env=env, stdout=subprocess.PIPE, text=True, encoding="utf-8")
             for ag in ["grokbuild", "cursor", "antigravity"] * 4]
    for p in procs:
        p.wait()
    ts = json.load(open(os.path.join(d, "tarefas.json"), encoding="utf-8"))
    pegas = [t for t in ts if t["status"] == "pegou"]
    donos = {}
    for t in pegas:
        for p in t["pastas"]:
            donos.setdefault(p, set()).add(t["por"])
    assert len({t["por"] for t in pegas}) == len(pegas) == 3, f"cada músico 1 tarefa: {[(t['id'], t['por']) for t in pegas]}"
    assert all(len(v) == 1 for v in donos.values()), f"pasta com 2 músicos: {donos}"
    g = next(t for t in pegas if t["por"] == "grokbuild")
    assert g["id"] == "T09", f"Grok devia pegar a ⭐ Paridade primeiro (instrumento dele), pegou {g['id']}"
    print("1 ok: 12 pegadas simultâneas →", [(t["id"], t["por"], t["pastas"][0]) for t in pegas])

    for ag, chave in (("grokbuild", "decision"), ("cursor", "followup_message")):
        r = subprocess.run([sys.executable, "-c", f"import orquestra; orquestra._cota_ok=lambda a: True; orquestra.gancho('{ag}')"],
                           cwd=d, env=env, input="{}", capture_output=True, text=True, encoding="utf-8")
        out = json.loads(r.stdout)
        assert chave in out, (ag, r.stdout, r.stderr)
        print(f"2 ok: gancho {ag} → {chave}: {str(out)[:110]}…")

    c = lambda *a: subprocess.run([sys.executable, "orquestra.py", "--central", *a], cwd=d, env=env, capture_output=True, text=True, encoding="utf-8").returncode
    assert c("pegar", "cursor") == 0 and c("pegar", "grokbuild") == 1 and c("soltar", "cursor") == 0 and c("pegar", "grokbuild") == 0
    print("3 ok: trava central — um por vez")
    shutil.rmtree(d, ignore_errors=True)
    print("TUDO OK")


if __name__ == "__main__":
    main()
