"""Carteiro dos agentes — entrega os pedidos do painel (python painel.py X --pedir Y "...") na hora,
sem o Caio precisar repassar.

Como cada um recebe:
  - Cursor, Antigravity e Cocaino (Grok Bot): o carteiro cola a mensagem na janela do app e aperta Enter.
    Entrega a qualquer momento (pedido do Caio); só espera ele ficar 3 s sem digitar e devolve a janela dele.
  - Grok CLI (grokbuild): pelo hook de parada do próprio Grok (~/.grok/hooks/carteiro.json). Quando ele
    termina uma resposta e tem pedido novo, o hook devolve {"decision":"block"} e ele continua já lendo o pedido.
    Não mexe em janela nenhuma (ele divide o terminal com o Claude).
  - Claude: lê o painel a cada passo (não precisa de entrega).

Uso:
  python carteiro.py                 # fica rodando (o iniciar_carteiro.vbs abre escondido no logon)
  python carteiro.py --uma-vez       # uma rodada só (teste)
  python carteiro.py --hook grokbuild   # usado pelo hook de parada do Grok CLI
  python carteiro.py --status        # mostra pendentes e entregues
"""
import ctypes
import re
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PAINEL = os.path.join(HERE, "painel")
ENTREGUES = os.path.join(HERE, "carteiro_entregues.json")
FISCAL = r"C:\Users\caion\fiscal-fabrica"
LOCK = os.path.join(FISCAL, "entregando.lock")  # o vigia respeita: não cutuca enquanto o carteiro entrega
LOG = os.path.join(HERE, "carteiro.log")
OCIOSO_MIN = 3  # Caio pediu entrega a todo momento: só espera ele parar de digitar (3 s)

NOMES = {"cursor": "Cursor", "antigravity": "Antigravity", "grok": "Cocaino (Grok Bot)",
         "grokbuild": "Grok CLI", "claude": "Claude"}


def log(t):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + t + "\n")
    except OSError:
        pass


def _id(de, p):
    return hashlib.sha1(f"{de}|{p.get('para')}|{p.get('quando')}|{p.get('texto')}".encode("utf-8")).hexdigest()[:12]


def _cadeiras_b():
    """Formação B: cadeiras ocupadas pelo Google (agy) — falam pelo correio, não por janela."""
    try:
        import formacao
        return formacao.cadeiras_b()
    except Exception:  # noqa: BLE001
        return set()


def _pausados():
    """agentes_pausados.json: {"grok": "antigravity"} = Cocaino pausado, os pedidos dele vão pro Antigravity."""
    try:
        with open(os.path.join(HERE, "agentes_pausados.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def pendentes(para=None):
    """Pedidos ainda não entregues, agrupados por destinatário: {para: [(id, de, quando, texto)]}."""
    ja = set(_ler_entregues())
    saida = {}
    for arq in sorted(os.listdir(PAINEL)):
        if not arq.endswith(".json"):
            continue
        de = arq[:-5]
        try:
            with open(os.path.join(PAINEL, arq), encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            continue
        redir = _pausados()
        for p in d.get("pedidos", []):
            alvo = redir.get(p.get("para"), p.get("para"))
            if not alvo or (para and alvo != para):
                continue
            i = _id(de, p)
            if i not in ja:
                saida.setdefault(alvo, []).append((i, de, p.get("quando", ""), p.get("texto", "")))
    return saida


def _ler_entregues():
    try:
        with open(ENTREGUES, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def marcar(ids):
    ja = _ler_entregues()
    ja += [i for i in ids if i not in ja]
    with open(ENTREGUES, "w", encoding="utf-8") as f:
        json.dump(ja[-2000:], f)


def mensagem(para, itens):
    # Deixa claro no chat que é mensagem AUTOMÁTICA (não foi o Caio que digitou) e mantém o rodapé curto.
    linhas = [f"🤖 [automático · carteiro da Caixa, não foi o Caio que digitou] {len(itens)} pedido(s) pra você:"]
    for _i, de, quando, texto in itens:
        linhas.append(f"De {NOMES.get(de, de)} ({quando[11:16]}): {texto}")
    linhas.append(f"Ao terminar: python painel.py {para} --resolvido <quem pediu> (regras no RUMO.md).")
    # UMA linha só: com quebra de linha o Enter do Cursor/Antigravity só pula linha e não envia
    return " | ".join(" ".join(l.split()) for l in linhas)


# ------------------------------------------------------------------ entrega por janela (Windows)
class _LII(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def segundos_ocioso():
    lii = _LII()
    lii.cbSize = ctypes.sizeof(_LII)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    return (ctypes.windll.kernel32.GetTickCount() - lii.dwTime) / 1000.0


def _ps(script, *args):
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, *args],
                       capture_output=True, text=True, timeout=90,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return (r.stdout or "") + (r.stderr or "")


def _titulo_janela(processo):
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"(Get-Process '{processo}' -EA 0 | ? MainWindowTitle | select -First 1).MainWindowTitle"],
                       capture_output=True, text=True, timeout=30,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return (r.stdout or "").strip()


def entregar_janela(para, texto):
    arq = os.path.join(FISCAL, f"msg_carteiro_{para}.txt")
    with open(arq, "w", encoding="utf-8") as f:
        f.write(texto)
    # entregar.ps1 cola, envia e CONFERE (a caixa de texto tem que ficar vazia); senão não marca como entregue
    out = _ps(os.path.join(FISCAL, "entregar.ps1"), "-app", para, "-arquivo", arq)
    return ("ENVIADO" in out), out.strip()[-200:]


_ULTIMA_ENTREGA = {}  # agente -> time.time() da última entrega (modo econômico: no máx. 1 a cada 10 min)


def _economia_permite(para):
    """Modo economia (economia.py): crítico = não entrega; econômico = 1 entrega a cada 10 min por agente."""
    try:
        import economia
        nv = economia.nivel_do_agente(para)
    except Exception:  # noqa: BLE001
        return True
    if nv == "critico":
        return False
    if nv == "economico" and time.time() - _ULTIMA_ENTREGA.get(para, 0) < 600:
        return False
    return True


_ULTIMO_EMPURRAO = {}  # agente -> time.time(); no máx. 1 empurrão a cada 30 min por agente
PARADO_MIN = 5


def parados_com_tarefa():
    """Agentes sem 'fazendo' há 10+ min, sem pedido pendente, com tarefa livre no quadro → item de empurrão."""
    try:
        import tarefas
    except Exception:  # noqa: BLE001
        return {}
    pend = pendentes()
    saida = {}
    for ag in ("cursor", "antigravity", "grok", "grokbuild"):
        if ag in _pausados():
            continue
        d = {}
        try:
            with open(os.path.join(PAINEL, ag + ".json"), encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            pass
        fazendo = (d.get("fazendo") or "").lower()
        # "aguardando…", "esperando…", "parado", "idle" no campo fazendo = está PARADO de verdade
        ocupado = fazendo and not re.search(r"aguard|esperan|parad|idle|nada|sem tarefa|fila vazia", fazendo)
        if ocupado or ag in pend:
            continue
        try:
            parado = (time.time() - time.mktime(time.strptime(d.get("atualizado", ""), "%Y-%m-%d %H:%M"))) / 60
        except ValueError:
            parado = 999
        # quem tem menos cota é empurrado menos: normal 10 min, econômico 30 min (crítico já fica fora)
        try:
            import economia
            espera = 1800 if economia.nivel_do_agente(ag) == "economico" else 600
        except Exception:  # noqa: BLE001
            espera = 600
        if parado < PARADO_MIN or time.time() - _ULTIMO_EMPURRAO.get(ag, 0) < espera:
            continue
        livres = tarefas.livres_para(ag)
        if livres:
            saida[ag] = (int(parado), livres[0])
    return saida


def texto_empurrao(ag, minutos, t):
    return (f"🤖 [automático · carteiro da Caixa, não foi o Caio que digitou] Você está parado há {minutos} min e tem "
            f"tarefa livre no quadro (ex.: {t['id']} {t['titulo']}). Rode: cd C:/Users/caion/caixa-ferramentas; "
            f"python painel.py {ag} --pegar — e faça a que ele te der. Ao terminar: --concluir <ID> \"resultado\" "
            f"e --pegar de novo.")


def pedir_propostas_se_faltar():
    """Quadro quase vazio (< 5 livres) → pede 3 propostas ao Antigravity (no máx. 1 vez a cada 2 h)."""
    try:
        import tarefas
        livres = [t for t in tarefas.ler() if t["status"] == "livre"]
    except Exception:  # noqa: BLE001
        return
    # só conta como "faminto" quem pode trabalhar agora (não pausado, não em modo economia crítico)
    famintos = [ag for ag in ("cursor", "antigravity", "grok", "grokbuild")
                if ag not in _pausados() and _economia_permite(ag) and not tarefas.livres_para(ag)]
    if (len(livres) >= 5 and not famintos) or time.time() - _ULTIMO_EMPURRAO.get("_propostas", 0) < 3600:
        return
    _ULTIMO_EMPURRAO["_propostas"] = time.time()
    subprocess.run([sys.executable, os.path.join(HERE, "painel.py"), "claude", "--pedir", "antigravity",
                    f"Quadro: {len(livres)} livres; SEM tarefa pra: {', '.join(famintos) or 'ninguém'}. "
                    f"Crie 2 tarefas pra cada um desses — SÓ o que melhora o uso REAL do Caio: problemas do CRITICA.md, "
                    f"ferramentas que ele usa (config uses), a Tendência do dia, esconder as inúteis (T24). PROIBIDO: ligar "
                    f"adaptador de ferramenta de nicho (vinho, bolo, cronômetro de laps…). Sem tarefa útil? Não crie nada. ("
                    "TENDENCIAS.md, CRITICA.md) com: python tarefas.py --nova \"titulo\" \"detalhe\" agente1,agente2"],
                   capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log(f"quadro com {len(livres)} livres: pedi propostas ao Antigravity")


def empurrar_parados():
    if segundos_ocioso() < OCIOSO_MIN or os.path.exists(LOCK):
        return
    for ag, (minutos, t) in parados_com_tarefa().items():
        if ag == "grokbuild" or ag in _cadeiras_b() or not _economia_permite(ag):
            continue  # Grok CLI recebe pelo hook/loop; economia manda segurar
        ok, info = entregar_janela(ag, texto_empurrao(ag, minutos, t))
        if "OCUPADO" in info:
            continue
        _ULTIMO_EMPURRAO[ag] = time.time()
        log(f"{ag}: parado {minutos} min → empurrão pro quadro ({'ok' if ok else 'falhou: ' + info[-150:]})")


def fechar_testes_esquecidos(minutos=10):
    """Fecha janelas abertas por TESTE (linha de comando com --teste) há mais de N min. Nunca toca no que o Caio abriu."""
    ps = ("$lim=(Get-Date).AddMinutes(-%d); Get-CimInstance Win32_Process | "
          "? { $_.CommandLine -match ' --teste( |$)' -and $_.CreationDate -lt $lim } | "
          "%% { $p=Get-Process -Id $_.ProcessId -EA 0; if($p){ $p.CloseMainWindow()|Out-Null; Start-Sleep 2; "
          "if(-not $p.HasExited){ Stop-Process -Id $p.Id -Force }; $_.ProcessId } }") % minutos
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        fechados = [x for x in (r.stdout or "").split() if x.isdigit()]
        if fechados:
            log(f"faxina de teste: fechei {len(fechados)} janela(s) esquecida(s) aberta(s) por teste: {fechados}")
    except Exception as e:  # noqa: BLE001
        log(f"faxina de teste erro: {e}")


def rodada():
    pend = pendentes()
    alvos = [a for a in ("cursor", "antigravity", "grok") if a in pend and _economia_permite(a)
             and a not in _cadeiras_b()]
    if not alvos:
        return
    if segundos_ocioso() < OCIOSO_MIN:
        return  # Caio usando o PC: espera
    if os.path.exists(LOCK):
        return
    antes = ctypes.windll.user32.GetForegroundWindow()
    try:
        open(LOCK, "w").close()
        for para in alvos:
            if segundos_ocioso() < 2:  # Caio digitando agora: espera a próxima rodada
                log("Caio voltou ao PC, entrega adiada")
                break
            ok, info = entregar_janela(para, mensagem(para, pend[para]))
            if "OCUPADO" in info:  # agente trabalhando: não interrompe, entrega quando ele parar
                log(f"{para}: ocupado, {len(pend[para])} pedido(s) esperando ele parar")
                continue
            log(f"{para}: {'ENTREGUE' if ok else 'falhou'} {len(pend[para])} pedido(s) — {info}")
            if ok:
                marcar([i for i, *_ in pend[para]])
                _ULTIMA_ENTREGA[para] = time.time()
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass
        ctypes.windll.user32.SetForegroundWindow(antes)


def parados_com_tarefa_hook(para):
    """No fim de turno do Grok CLI: tem tarefa livre pra ele e ele não está com nenhuma em andamento?"""
    try:
        import tarefas
        if any(t["status"] == "pegou" and t["por"] == para for t in tarefas.ler()):
            return None
        livres = tarefas.livres_para(para)
        return livres[0] if livres else None
    except Exception:  # noqa: BLE001
        return None


def _continuar(para, texto):
    """Resposta do gancho de fim de turno no formato de cada agente: o agente CONTINUA sozinho com o texto."""
    if para == "cursor":
        print(json.dumps({"followup_message": texto}, ensure_ascii=False))
    else:
        print(json.dumps({"decision": "block", "reason": texto}, ensure_ascii=False))


def correio_novo(para):
    """Fábrica 2.0: mensagens NÃO lidas no Agent Mail (só espia, não marca como lida)."""
    try:
        import fabrica_mail
        return fabrica_mail.caixa(para), fabrica_mail.nome(para)
    except Exception as e:  # noqa: BLE001 — servidor fora do ar não pode travar o agente
        log(f"{para}: Agent Mail indisponível no gancho ({str(e)[:80]})")
        return [], para


def hook(para):
    """Gancho de fim de turno (Grok CLI e Cursor): correio novo, pedido ou tarefa livre → o agente continua."""
    try:
        sys.stdin.read()
    except Exception:  # noqa: BLE001
        pass
    msgs, eu = correio_novo(para)
    if msgs and _economia_permite(para):
        de = ", ".join(sorted({m.get("from", "?") for m in msgs}))
        _continuar(para, f"📬 [automático · fábrica] Você ({eu} no Agent Mail) tem {len(msgs)} mensagem(ns) não lida(s) "
                         f"de {de}. Use fetch_inbox(project_key=\"C:/Users/caion/caixa-ferramentas\", agent_name=\"{eu}\"), "
                         "faça o que pedirem, responda com reply_message e marque com acknowledge_message.")
        log(f"{para}: fim de turno → {len(msgs)} mensagem(ns) do Agent Mail")
        return
    itens = pendentes(para).get(para, [])
    if not itens and _economia_permite(para):
        p = parados_com_tarefa_hook(para)
        if p:
            _continuar(para, texto_empurrao(para, 0, p))
            log(f"{para}: fim de turno sem pedido → mandei pegar {p['id']} do quadro")
        return
    if itens and not _economia_permite(para):
        log(f"{para}: modo economia crítico, pedido segue guardado")
        return
    if itens:
        marcar([i for i, *_ in itens])
        log(f"{para}: ENTREGUE via hook {len(itens)} pedido(s)")
        _continuar(para, mensagem(para, itens))


_ULTIMO_CUTUCAO_CORREIO = {}


def acordar_com_correio():
    """Fábrica 2.0: correio novo pra agente de JANELA parado (Cursor/Antigravity) → cutucão CURTO ("veja seu correio").
    O conteúdo vai pelo Agent Mail; colar na janela vira só despertador (máx. 1 a cada 10 min por agente)."""
    if segundos_ocioso() < OCIOSO_MIN or os.path.exists(LOCK):
        return
    try:
        import fabrica_mail
    except Exception:  # noqa: BLE001
        return
    for ag in ("cursor", "antigravity"):
        if (ag in _pausados() or ag in _cadeiras_b() or not _economia_permite(ag)
                or time.time() - _ULTIMO_CUTUCAO_CORREIO.get(ag, 0) < 600):
            continue
        try:
            msgs = fabrica_mail.caixa(ag)
        except Exception:  # noqa: BLE001
            return
        if not msgs:
            continue
        eu = fabrica_mail.nome(ag)
        ok, info = entregar_janela(ag, f"📬 [automático · fábrica] Você ({eu}) tem {len(msgs)} mensagem(ns) no Agent Mail. "
                                       f"Use fetch_inbox(project_key=\"C:/Users/caion/caixa-ferramentas\", agent_name=\"{eu}\"), "
                                       "faça o que pedirem, responda com reply_message e marque com acknowledge_message.")
        if "OCUPADO" in info:
            continue
        _ULTIMO_CUTUCAO_CORREIO[ag] = time.time()
        log(f"{ag}: {len(msgs)} no correio → cutucão ({'ok' if ok else 'falhou: ' + info[-120:]})")


def ponte_cocaino():
    """Cocaino (Grok Bot) não aceita MCP: o carteiro lê o correio dele (PurpleCarp) e cola o texto na janela.
    Em reserva (agentes_pausados.json) → encaminha pro substituto pelo correio."""
    if "grok" in _cadeiras_b():
        return  # formação B: a cadeira do Cocaino é um agy com correio próprio
    try:
        import fabrica_mail
        msgs = fabrica_mail.caixa("grok")
    except Exception:  # noqa: BLE001
        return
    if not msgs:
        return
    subst = _pausados().get("grok")
    if subst:
        for m in msgs:
            fabrica_mail.enviar(m.get("from", "claude"), subst, "[encaminhado do Cocaino, em reserva] " + str(m.get("subject", "")),
                                str(m.get("body_md", "")))
            fabrica_mail.lida("grok", m["id"])
        log(f"Cocaino em reserva: {len(msgs)} mensagem(ns) encaminhada(s) pro {subst}")
        return
    if segundos_ocioso() < OCIOSO_MIN or os.path.exists(LOCK) or not _economia_permite("grok"):
        return
    texto = "\n\n".join(f"📬 De {fabrica_mail.apelido(m.get('from', '?'))} — {m.get('subject', '')}:\n{m.get('body_md', '')}"
                          for m in msgs[:5])
    texto += ("\n\n(Você não tem o correio MCP: pra responder, rode python C:/Users/caion/caixa-ferramentas/painel.py "
              "grok --pedir <agente> \"resposta\")")
    ok, info = entregar_janela("grok", texto)
    if ok:
        for m in msgs[:5]:
            fabrica_mail.lida("grok", m["id"])
    log(f"Cocaino: {len(msgs[:5])} mensagem(ns) do correio → janela ({'ok' if ok else 'falhou'})")


_tend_ultima_tentativa = 0.0


def garantir_tendencia():
    """Tendência TODO DIA (regra do Caio): se a do dia não saiu (agendamento das 08:00 falhou/PC dormindo),
    roda o radar; e garante uma tarefa no quadro pra construir a ferramenta e pôr na categoria 🔥 Tendências."""
    global _tend_ultima_tentativa
    if time.localtime().tm_hour < 8:
        return
    hoje = time.strftime("%d/%m/%Y")
    arq = os.path.join(HERE, "TENDENCIA_DO_DIA.md")
    try:
        topo = open(arq, encoding="utf-8").read(4000)
    except OSError:
        topo = ""
    if hoje not in (topo.splitlines()[0] if topo else ""):
        if time.time() - _tend_ultima_tentativa < 3600:
            return
        _tend_ultima_tentativa = time.time()
        log("tendência do dia não saiu — rodando o radar")
        try:
            subprocess.run([sys.executable.replace("pythonw", "python"), os.path.join(HERE, "tendencias.py")],
                           cwd=HERE, timeout=300, capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            topo = open(arq, encoding="utf-8").read(4000)
        except Exception as ex:  # noqa: BLE001
            log(f"radar de tendências falhou: {ex}")
            return
        if hoje not in (topo.splitlines()[0] if topo else ""):
            return
    m = re.search(r"\*\*Ideia:\*\*\s*\[(.+?)\]\((\S+?)\)", topo)
    if not m:
        return
    import tarefas
    dm = hoje[:5]
    titulo = f"🔥 Tendência do dia {dm}"
    if any(t["titulo"].startswith(titulo) for t in tarefas.ler()):
        return
    tid = tarefas.nova(f"{titulo}: {m.group(1)[:80]}",
                       "Siga TENDENCIA_DO_DIA.md (ideia, versão nossa do zero, offline, PyQt6, pt-BR). "
                       "Pronto e testado: integre na Caixa e ACRESCENTE a pasta em tendencias_caixa.json "
                       "(categoria 🔥 Tendências) + python tendencias.py --feita " + m.group(2) + ". "
                       "Se não couber: --feita e faça a próxima do TENDENCIAS.md.",
                       ["grokbuild", "antigravity"])
    log(f"tendência do dia {dm} virou tarefa {tid}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    a = sys.argv[1:]
    if a[:1] == ["--hook"]:
        try:
            hook(a[1] if len(a) > 1 else "grokbuild")
        except Exception as e:  # noqa: BLE001 — hook nunca pode travar o agente
            log(f"hook erro: {e}")
        return
    if a[:1] == ["--status"]:
        for para, itens in pendentes().items():
            print(f"{NOMES.get(para, para)}: {len(itens)} pendente(s)")
            for _i, de, q, t in itens:
                print(f"   de {de} {q}: {t[:90]}")
        print(f"ocioso há {segundos_ocioso():.0f}s; entregues registrados: {len(_ler_entregues())}")
        return
    if a[:1] == ["--uma-vez"]:
        rodada()
        return
    # UM carteiro só: em 11/11 havia 8 rodando juntos (reinícios que não fecharam o antigo) → avisos/entregas
    # duplicados e código velho sobrescrevendo o ECONOMIA.json. O mutex do Windows impede o 2º de subir.
    _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\CaixaFerramentasCarteiro")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        log("outro carteiro já está rodando — este não sobe")
        return
    log("carteiro iniciado")
    volta = 0
    while True:
        if volta % 6 == 0:  # a cada 3 min: mede as cotas e atualiza o modo economia
            try:
                import economia
                antes = {c: v.get("nivel") for c, v in economia._ler(economia.ESTADO, {}).get("contas", {}).items()}
                e = economia.atualizar()
                depois = {c: v.get("nivel") for c, v in e.get("contas", {}).items()}
                if antes != depois:
                    log(f"modo economia mudou: {antes} -> {depois}")
            except Exception as ex:  # noqa: BLE001
                log(f"economia erro: {ex}")
        volta += 1
        try:
            rodada()
            empurrar_parados()
            if volta % 2 == 0:  # a cada 1 min: Fábrica 2.0 (correio)
                acordar_com_correio()
                ponte_cocaino()
            if volta % 4 == 2:  # a cada 2 min: formação B — cadeira Google que fechou e tem trabalho → reabre
                try:
                    import importlib
                    import formacao
                    importlib.reload(formacao)  # sempre o código atual (11/11: abriu cadeira com versão velha)
                    formacao.garantir_b()
                except Exception as ex:  # noqa: BLE001
                    log(f"formação B: {ex}")
            if volta % 6 == 3:  # a cada 3 min: o Gemini atende o correio dele (numa thread: demora)
                import threading

                def _gemini_correio():
                    try:
                        import carteiro_ia
                        carteiro_ia.atender_correio()
                    except Exception as ex:  # noqa: BLE001
                        log(f"correio do Gemini: {ex}")
                threading.Thread(target=_gemini_correio, daemon=True).start()
            if volta % 60 == 0:  # a cada 30 min: cota ao vivo do Antigravity (agy), numa thread pra não travar
                import threading

                def _cota_ag():
                    try:
                        import cota_antigravity
                        cota_antigravity.atualizar()
                    except Exception as ex:  # noqa: BLE001
                        log(f"cota Antigravity: {ex}")
                threading.Thread(target=_cota_ag, daemon=True).start()
            if volta % 60 == 30:  # 1x por semana: print da tela Models do Antigravity (cota semanal), com o Caio longe
                try:
                    import cota_antigravity_semanal as cas
                    if cas.precisa() and segundos_ocioso() >= 120 and not os.path.exists(LOCK):
                        open(LOCK, "w").close()
                        try:
                            log(f"cota semanal Antigravity (print+OCR): {cas.atualizar()}% restante")
                        finally:
                            os.remove(LOCK)
                except Exception as ex:  # noqa: BLE001
                    log(f"cota semanal Antigravity: {ex}")
            if volta % 20 == 1:  # a cada 10 min: a tendência do dia tem que sair todo dia
                garantir_tendencia()
            if volta % 20 == 11:  # a cada 10 min: quadro sempre cheio (>= 3 livres por agente ativo)
                try:
                    import quadro_cheio
                    quadro_cheio.encher()
                except Exception as ex:  # noqa: BLE001
                    log(f"quadro cheio: {ex}")
            if volta % 20 == 15:  # a cada 10 min: o Gemini revisa a última tarefa concluída (numa thread: demora)
                import threading

                def _revisar():
                    try:
                        import carteiro_ia
                        carteiro_ia.revisar()
                    except Exception as ex:  # noqa: BLE001
                        log(f"revisor Gemini: {ex}")
                threading.Thread(target=_revisar, daemon=True).start()
            if volta % 4 == 0:
                pedir_propostas_se_faltar()
                fechar_testes_esquecidos()
        except Exception as e:  # noqa: BLE001
            log(f"erro: {e}")
        time.sleep(30)


if __name__ == "__main__":
    main()
