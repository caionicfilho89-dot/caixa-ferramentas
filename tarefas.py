"""Quadro de tarefas compartilhado — ninguém fica parado.

tarefas.json = lista de tarefas com quem PODE fazer. Um agente parado roda:
    python painel.py <eu> --pegar          → pega a próxima tarefa livre que combina com ele (fica marcada como dele)
    python painel.py <eu> --concluir T07 "o que ficou pronto"
    python tarefas.py                      → mostra o quadro
    python tarefas.py --nova "titulo" "detalhe" cursor,grokbuild   → acrescenta tarefa
O carteiro cutuca quem está parado há 10+ min; quando sobram < 5 livres, pede propostas ao Antigravity.
"""
import json
import os
import sys
import time
import re
import subprocess

# Rodando de dentro da pasta de trabalho de um agente (git worktree, ex.: C:/Users/caion/wt-antigravity)?
# Quadro/painel são UM SÓ: reexecuta o script da pasta PRINCIPAL (senão cada agente teria um quadro diferente).
def _principal(aqui):
    g = os.path.join(aqui, ".git")
    if os.path.isfile(g):
        with open(g, encoding="utf-8") as f:
            m = re.search(r"gitdir:\s*(.+?)[\\/]\.git[\\/]worktrees", f.read())
        if m:
            return os.path.normpath(m.group(1))
    return None


_P = _principal(os.path.dirname(os.path.abspath(__file__)))
if _P and __name__ == "__main__":
    os.environ.setdefault("CAIXA_WT", os.path.dirname(os.path.abspath(__file__)))
    sys.exit(subprocess.call([sys.executable, os.path.join(_P, os.path.basename(__file__))] + sys.argv[1:]))

HERE = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(HERE, "tarefas.json")
FMT = "%Y-%m-%d %H:%M"


def ler():
    """Lê o quadro. Falha de leitura NÃO vira "quadro vazio": em 11/11 21:59 uma leitura que falhou (arquivo
    sendo gravado por outro processo) devolveu [] e a tarefa nova foi gravada por cima de 88 tarefas."""
    if not os.path.exists(ARQ):
        return []
    erro = None
    for _ in range(20):
        try:
            with open(ARQ, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError) as e:
            erro = e
            time.sleep(0.15)
    raise RuntimeError(f"quadro (tarefas.json) ilegível agora, não vou fingir que está vazio: {erro}")


def salvar(ts):
    # trava de segurança: gravar um quadro que encolheu de repente (ex.: 88 → 1) é quase sempre bug
    try:
        with open(ARQ, encoding="utf-8") as f:
            antes = json.load(f)
        if len(antes) >= 10 and len(ts) < len(antes) * 0.5:
            raise RuntimeError(f"recusei gravar o quadro encolhendo de {len(antes)} para {len(ts)} tarefas")
        with open(ARQ + ".bak", "w", encoding="utf-8") as f:
            json.dump(antes, f, ensure_ascii=False, indent=1)
    except (OSError, ValueError):
        pass
    tmp = f"{ARQ}.{os.getpid()}.tmp"  # um tmp por processo: dois gravando juntos não se atropelam
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ts, f, ensure_ascii=False, indent=1)
    # Windows: substituir falha (WinError 32) se outro processo está lendo o tarefas.json naquele instante.
    # Antes isso derrubava o quadro_cheio (parou de criar tarefas às 21:53 de 11/11). Tenta por ~6 s.
    for tentativa in range(40):
        try:
            os.replace(tmp, ARQ)
            return
        except PermissionError:
            time.sleep(0.15)
    os.replace(tmp, ARQ)


def nova(titulo, detalhe, quem):
    ts = ler()
    n = 1 + max([int(t["id"][1:]) for t in ts] or [0])
    ts.append({"id": f"T{n:02d}", "titulo": titulo, "detalhe": detalhe, "quem": quem,
               "status": "livre", "por": "", "quando": time.strftime(FMT), "resultado": ""})
    salvar(ts)
    return f"T{n:02d}"


def pegar(agente):
    """Já tem uma em andamento? devolve ela. Senão marca a próxima livre que combina."""
    ts = ler()
    for t in ts:
        if t["status"] == "pegou" and t["por"] == agente:
            return t
    for t in ts:
        if t["status"] == "livre" and (agente in t["quem"] or "todos" in t["quem"]):
            if _outro_tem_mais_folga(agente, t):
                continue  # deixa pra quem tem mais cota sobrando (Caio: "os com menos tokens fazem menos")
            t.update(status="pegou", por=agente, quando=time.strftime(FMT))
            salvar(ts)
            return t
    return None


def _outro_tem_mais_folga(agente, t):
    """True se outro agente que também pode fazer a tarefa tem bem mais cota sobrando (>15 pontos) e a tarefa
    não está esperando há mais de 30 min (aí qualquer um pega, pra não travar)."""
    try:
        espera = (time.time() - time.mktime(time.strptime(t.get("quando", ""), FMT))) / 60
    except ValueError:
        espera = 0
    if espera > 30:
        return False
    try:
        import economia
        minha = economia.folga_do_agente(agente)
        for outro in t["quem"]:
            if outro != agente and outro != "todos" and economia.folga_do_agente(outro) > minha + 15:
                return True
    except Exception:  # noqa: BLE001
        pass
    return False


def concluir(agente, tid, resultado=""):
    """Marca como feita SE passar no portão de qualidade (portao.py). Recusado → {"recusado": motivo}."""
    try:
        import portao
        titulo = next((t["titulo"] for t in ler() if t["id"] == tid), "")
        motivo = portao.verificar(resultado, os.environ.get("CAIXA_WT") or HERE, titulo)
    except Exception as e:  # noqa: BLE001 — portão quebrado não pode travar o quadro
        motivo = ""
        print(f"(portão de qualidade com erro, deixei passar: {e})")
    if motivo:
        return {"recusado": motivo, "id": tid}
    ts = ler()
    for t in ts:
        if t["id"] == tid:
            t.update(status="feito", por=agente, quando=time.strftime(FMT), resultado=resultado[:2000])
            salvar(ts)
            return t
    return None


def livres_para(agente):
    return [t for t in ler() if t["status"] == "livre" and (agente in t["quem"] or "todos" in t["quem"])]


def mostrar():
    ts = ler()
    for st, ic in (("pegou", "🔨"), ("livre", "📋"), ("feito", "✅")):
        grupo = [t for t in ts if t["status"] == st]
        if st == "feito":
            grupo = grupo[-5:]
        for t in grupo:
            dono = f" ({t['por']})" if t["por"] else f" [pode: {', '.join(t['quem'])}]"
            print(f"{ic} {t['id']} {t['titulo']}{dono}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    a = sys.argv[1:]
    if a[:1] == ["--nova"] and len(a) >= 4:
        print("criada", nova(a[1], a[2], a[3].split(",")))
    mostrar()


if __name__ == "__main__":
    main()
