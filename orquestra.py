"""🎼 Orquestra da Caixa (18/11/2026) — todos tocam juntos sem um atropelar o outro.

Substitui o carteiro (que colava texto nas janelas, roubava o foco e engasgava o PC).
Ninguém cola nada em janela: cada músico, AO TERMINAR UM TURNO, roda o gancho e recebe a próxima parte.

    python orquestra.py                      → painel: quem toca o quê, cotas, últimas feitas
    python orquestra.py --gancho grokbuild   → gancho de fim de turno (Grok CLI / Cursor chamam sozinhos)
    python orquestra.py --central pegar EU   → trava caixa.pyw/build_suite.py/AGENTS*.md pra EU (15 min)
    python orquestra.py --central soltar EU  → solta a trava
    python orquestra.py --resumo             → resumo do dia (o que ficou pronto)

Regras (partitura) — também no topo do AGENTS.md:
  1. Uma tarefa por músico; ninguém pega tarefa cuja PASTA outro músico está mexendo.
  2. Arquivos centrais (caixa.pyw, build_suite.py, AGENTS*.md, RUMO.md) só com a trava central.
  3. Só conta como feito o que passa no portão (portao.py); o maestro (Claude) revisa e fecha versão.
  4. Cota por músico: conta crítica = aquele músico descansa, os outros seguem.
"""
import json
import os
import sys
import time
from contextlib import contextmanager

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
LOG = os.path.join(HERE, "orquestra.log")
TRAVA_QUADRO = os.path.join(HERE, "tarefas.trava")
TRAVA_CENTRAL = os.path.join(HERE, "central.trava")
CENTRAIS = ["caixa.pyw", "build_suite.py", "AGENTS.md", "AGENTS_PROTOCOL.md", "RUMO.md"]
FMT = "%Y-%m-%d %H:%M"

# músicos: chave do quadro -> (nome, instrumento, palavras que dão prioridade na escolha da tarefa)
MUSICOS = {
    # 18/11: fila = VITRINE (os 27 programas que a pessoa baixaria); 🔧 Funcionar de nicho congelado
    "grokbuild": ("Grok CLI", "🎻 construtor", ["💊", "⭐ Vitrine", "🔥 Tendência", "⭐ Paridade", "🆕 Construir"]),
    "cursor": ("Cursor", "🎹 visual", ["🎹", "💊", "⭐ Vitrine", "tela", "Tela", "tema", "visual", "layout"]),
    "antigravity": ("Antigravity", "🥁 testador", ["🧪", "QA", "teste", "Teste", "↩️"]),
    "claude": ("Claude", "🎼 maestro", ["Portão", "integra", "versão"]),
    # reforço: mais janelas do Grok CLI (mesma conta SuperGrok), abertas pelo maestro quando precisa de velocidade
    "grokbuild2": ("Grok CLI 2", "🎻 construtor", ["💊", "⭐ Vitrine"]),
    "grokbuild3": ("Grok CLI 3", "🎻 construtor", ["💊", "⭐ Vitrine"]),
    "grokbuild4": ("Grok CLI 4", "🎻 construtor", ["💊", "⭐ Vitrine"]),
    "grokbuild5": ("Grok CLI 5", "🎻 construtor", ["💊", "⭐ Vitrine"]),
    "grokbuild6": ("Grok CLI 6", "🎻 construtor", ["💊", "⭐ Vitrine"]),
}


def log(t):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + t + "\n")
    except OSError:
        pass


@contextmanager
def trava(caminho, espera=20, velha=60):
    """Trava entre processos (arquivo criado com O_EXCL). Trava largada por processo morto expira em `velha` s."""
    fim = time.time() + espera
    while True:
        try:
            fd = os.open(caminho, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except (FileExistsError, PermissionError):  # Windows: trava sendo apagada naquele instante = ocupada
            try:
                if time.time() - os.path.getmtime(caminho) > velha:
                    os.remove(caminho)
                    continue
            except OSError:
                pass
            if time.time() > fim:
                raise TimeoutError(f"trava ocupada: {caminho}")
            time.sleep(0.1)
    try:
        yield
    finally:
        try:
            os.remove(caminho)
        except OSError:
            pass


def _quem(t):
    q = t.get("quem") or []
    return q.split() if isinstance(q, str) else list(q)


def _pastas(t):
    """Pastas da tarefa: campo "pastas" ou, se vazio, o [nome-da-pasta] do título (ex.: ⭐ Paridade [player-musica])."""
    ps = {p.strip().lower() for p in (t.get("pastas") or []) if p and p.strip()}
    if not ps:
        import re
        ps = {m.lower() for m in re.findall(r"\[([\w.-]+)\]", t.get("titulo", ""))}
    return ps


def _cota_ok(agente):
    """Atualiza o ECONOMIA.json se estiver velho (ninguém mais roda em segundo plano) e diz se o músico pode tocar."""
    try:
        import economia
        est = os.path.join(HERE, "ECONOMIA.json")
        if not os.path.exists(est) or time.time() - os.path.getmtime(est) > 15 * 60:
            economia.atualizar()
        base = agente.rstrip("0123456789")  # grokbuild2/3/4 = mesma conta do grokbuild
        return economia.nivel_do_agente(base) != "critico"
    except Exception as e:  # noqa: BLE001 — medidor quebrado não pode calar a orquestra
        log(f"cota de {agente}: medidor com erro ({str(e)[:80]}), deixei tocar")
        return True


def escolher(agente, ts):
    """Próxima tarefa livre pro músico: combina com ele, NÃO mexe em pasta que outro está mexendo,
    e as do instrumento dele vêm primeiro."""
    ocupadas = set()
    for t in ts:
        if t["status"] == "pegou" and t.get("por") != agente:
            ocupadas |= _pastas(t)
    prefer = MUSICOS.get(agente, ("", "", []))[2]
    feitas = {t["id"] for t in ts if t["status"] == "feito"}
    candidatas = []
    for i, t in enumerate(ts):
        if t["status"] != "livre":
            continue
        if any(d not in feitas for d in (t.get("depois") or [])):
            continue  # ordem da partitura: só entra depois das tarefas de que depende
        q = _quem(t)
        if agente not in q and "todos" not in q:
            continue
        if _pastas(t) & ocupadas:
            continue
        nota = next((k for k, p in enumerate(prefer) if p in t.get("titulo", "")), len(prefer))
        candidatas.append((nota, i, t))
    candidatas.sort(key=lambda x: (x[0], x[1]))
    return candidatas[0][2] if candidatas else None


def pegar(agente):
    """Atômico: lê, escolhe e grava DENTRO da trava do quadro — dois músicos nunca pegam a mesma tarefa."""
    import tarefas
    with trava(TRAVA_QUADRO):
        ts = tarefas.ler()
        for t in ts:
            if t["status"] == "pegou" and t.get("por") == agente:
                return t, False
        t = escolher(agente, ts)
        if not t:
            return None, False
        t.update(status="pegou", por=agente, quando=time.strftime(FMT))
        tarefas.salvar(ts)
        return t, True


def _responder(agente, texto):
    if agente == "cursor":
        print(json.dumps({"followup_message": texto}, ensure_ascii=False))
    else:
        print(json.dumps({"decision": "block", "reason": texto}, ensure_ascii=False))


def gancho(agente):
    """Fim de turno: pedido pendente > tarefa em andamento > próxima tarefa. Nada pra fazer = fica quieto."""
    try:
        sys.stdin.read()
    except Exception:  # noqa: BLE001
        pass
    if not _cota_ok(agente):
        log(f"{agente}: conta crítica — descansando (os outros seguem)")
        return
    nome = MUSICOS.get(agente, (agente,))[0]
    cab = f"🎼 [automático · orquestra da Caixa, não foi o Caio que digitou] {nome}:"
    try:
        import carteiro
        itens = carteiro.pendentes(agente).get(agente, [])
    except Exception:  # noqa: BLE001
        itens = []
    if itens:
        carteiro.marcar([i for i, *_ in itens])
        log(f"{agente}: {len(itens)} pedido(s) entregue(s) no fim de turno")
        _responder(agente, carteiro.mensagem(agente, itens))
        return
    try:
        t, nova = pegar(agente)
    except TimeoutError:
        log(f"{agente}: quadro ocupado, tento no próximo turno")
        return
    if not t:
        log(f"{agente}: nenhuma tarefa livre pra ele — descansando")
        return
    pastas = ", ".join(sorted(_pastas(t))) or "as citadas no detalhe"
    regra = (f"Mexa SÓ em: {pastas}. Arquivos centrais (caixa.pyw, build_suite.py, AGENTS*.md, RUMO.md) só com "
             f"`python orquestra.py --central pegar {agente}` e solte depois com `--central soltar {agente}`. "
             f"Ao terminar: `python painel.py {agente} --concluir {t['id']} \"o que ficou pronto\"` (o portão testa).")
    if nova:
        log(f"{agente}: pegou {t['id']} {t['titulo'][:60]}")
        _responder(agente, f"{cab} sua próxima parte é {t['id']} — {t['titulo']}. {t.get('detalhe', '')[:600]} | {regra}")
    else:
        log(f"{agente}: lembrado de terminar {t['id']}")
        _responder(agente, f"{cab} você ainda está com {t['id']} — {t['titulo']}. Termine e conclua. "
                           f"Se travou de verdade, explique no --concluir pra outro pegar. | {regra}")


def central(acao, agente):
    """Trava dos arquivos centrais: um músico por vez (expira em 15 min se esquecerem)."""
    if acao == "pegar":
        try:
            with trava(TRAVA_CENTRAL + ".x", espera=5):
                if os.path.exists(TRAVA_CENTRAL):
                    with open(TRAVA_CENTRAL, encoding="utf-8") as f:
                        dono, quando = (f.read().split("|") + ["", "0"])[:2]
                    if dono and dono != agente and time.time() - float(quando or 0) < 15 * 60:
                        print(f"⏳ arquivos centrais com {dono}. Espere e tente de novo em 1-2 min "
                              f"(ou adiante a sua parte nas pastas da sua tarefa).")
                        return 1
                with open(TRAVA_CENTRAL, "w", encoding="utf-8") as f:
                    f.write(f"{agente}|{time.time()}")
        except TimeoutError:
            print("⏳ tente de novo em instantes")
            return 1
        log(f"{agente}: pegou a trava central")
        print(f"✅ arquivos centrais com você ({agente}) por até 15 min. RELEIA antes de editar, "
              f"acrescente no FIM das listas e solte com --central soltar {agente}.")
        return 0
    if acao == "soltar":
        try:
            with open(TRAVA_CENTRAL, encoding="utf-8") as f:
                dono = f.read().split("|")[0]
            if dono == agente:
                os.remove(TRAVA_CENTRAL)
                log(f"{agente}: soltou a trava central")
        except OSError:
            pass
        print("✅ solto")
        return 0
    print("uso: --central pegar|soltar EU")
    return 2


def resumo(dia=None):
    import tarefas
    dia = dia or time.strftime("%Y-%m-%d")
    feitas = [t for t in tarefas.ler() if t["status"] == "feito" and t.get("quando", "").startswith(dia)]
    linhas = [f"🎼 Resumo da orquestra — {dia}: {len(feitas)} parte(s) pronta(s)"]
    for t in feitas:
        linhas.append(f"  ✅ {t['id']} ({MUSICOS.get(t.get('por'), (t.get('por'),))[0]}) {t['titulo'][:80]}")
    return "\n".join(linhas)


def painel():
    import tarefas
    ts = tarefas.ler()
    try:
        import economia
        est = economia._ler(os.path.join(HERE, "ECONOMIA.json"), {})
    except Exception:  # noqa: BLE001
        economia, est = None, {}
    print("🎼 ORQUESTRA DA CAIXA")
    for ag, (nome, inst, _p) in MUSICOS.items():
        t = next((x for x in ts if x["status"] == "pegou" and x.get("por") == ag), None)
        nv = economia.nivel_do_agente(ag.rstrip("0123456789"), est) if economia else "?"
        ic = {"normal": "🟢", "economico": "🟡", "critico": "🔴"}.get(nv, "⚪")
        print(f"  {ic} {inst:14} {nome:12} → {t['id'] + ' ' + t['titulo'][:60] if t else '(sem tarefa)'}")
    if os.path.exists(TRAVA_CENTRAL):
        print("  🔒 arquivos centrais com:", open(TRAVA_CENTRAL, encoding="utf-8").read().split("|")[0])
    print(f"  📋 livres: {sum(1 for x in ts if x['status'] == 'livre')}")
    print(resumo())


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    a = sys.argv[1:]
    if a[:1] == ["--gancho"] and len(a) >= 2:
        # vários Grok CLI ao mesmo tempo: o gancho é um só (~/.grok/hooks), então cada janela
        # diz quem é pela variável ORQ_EU (grokbuild2, grokbuild3…) — herdada pelo processo do gancho
        gancho(os.environ.get("ORQ_EU") or a[1])
        return 0
    if a[:1] == ["--central"] and len(a) >= 3:
        return central(a[1], a[2])
    if a[:1] == ["--resumo"]:
        print(resumo(a[1] if len(a) > 1 else None))
        return 0
    painel()
    return 0


if __name__ == "__main__":
    sys.exit(main())
