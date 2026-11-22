"""Formação da fábrica: A (original) ou B (manobra: Google no lugar do SuperGrok).

Pedido do Caio (11/11/2026), que assumiu explicitamente o risco de agentes autônomos com aprovação automática:
o SuperGrok é dividido por Cursor + Grok CLI + Cocaino; quando ele aperta, os três assentos passam a ser ocupados
por agentes do GOOGLE (Gemini via agy, conta Gemini Pro — muita cota). O substituto SENTA NA MESMA CADEIRA: mesma
chave no painel/quadro (cursor/grokbuild/grok) e mesmo nome no correio (BrightWren/CopperIbis/PurpleCarp). Nada
mais na fábrica muda. Cota do Grok voltou → `python formacao.py A`.

    python formacao.py            # mostra a formação atual
    python formacao.py B          # liga a manobra (abre 3 abas do agy no Windows Terminal, janela "fabrica")
    python formacao.py A          # volta pro original (fecha as abas do agy, devolve as cadeiras)
O carteiro chama garantir_b() a cada 2 min: na B, cadeira cujo agy fechou e tem trabalho → reabre.

17/11/2026 — o Caio pediu pra fechar o carteiro: as janelas dos agentes abriam "toda hora". Causas e travas:
- cadeira que fecha sozinha (cota, erro) era reaberta a cada 2 min, em loop → espera crescente
  (5, 10, 20, 40, 80 min) quando fecha logo depois de aberta; depois de 5 fechamentos seguidos, desiste e avisa;
  não reabre com a cota da conta crítica
- "acordar" (matar e reabrir cadeira parada) não tinha teto → no máx. 3 vezes por cadeira a cada 2 h
- cada aba nova trazia o Windows Terminal da fábrica pra frente → a janela é minimizada logo depois de abrir
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(HERE, "formacao.json")
PAUSADOS = os.path.join(HERE, "agentes_pausados.json")
AGY = os.path.join(os.environ.get("LOCALAPPDATA", ""), "agy", "bin", "agy.exe")
RAIZ = "C:/Users/caion/caixa-ferramentas"
# Modelo das cadeiras: o padrão do agy (Gemini 4 Argon) ESGOTOU em 11/11 ("Individual quota reached").
# melhor_modelo() pergunta ao agy a cota de CADA modelo e escolhe o mais forte que ainda tem saldo (ordem abaixo).
PREFERENCIA = ["gemini-4-argon-high", "claude-opus-5-5-high", "gemini-4-argon-medium", "claude-sonnet-5-5-high",
               "gemini-3.8-flash-high", "gemini-3.8-flash-medium", "gpt-oss-120b-medium", "gemini-3.8-flash-low"]
MODELO = "gemini-3.8-flash-high"  # reserva se a consulta falhar (era o único com cota em 11/11)


def melhor_modelo(minimo=5.0):
    try:
        import cota_antigravity
        cotas = cota_antigravity.ler()
        for m in PREFERENCIA:
            if m in cotas and cota_antigravity.pct(cotas[m].get("quota_remaining", 0)) >= minimo:
                return m
    except Exception:  # noqa: BLE001
        pass
    return MODELO

# chave -> (nome que o Caio usa, nome no Agent Mail, papel da cadeira)
CADEIRAS = {
    "cursor": ("Cursor", "BrightWren", "VISUAL: telas, QSS, layout e usabilidade da Caixa (caixa_home.py, caixa_tema.py, GUIs)"),
    "grokbuild": ("Grok CLI", "CopperIbis", "BARRA + TENDÊNCIA DO DIA + integração na Caixa (BUILTIN/TOOLS); build só se pedirem"),
    "grok": ("Cocaino", "PurpleCarp", "CRÍTICO/TESTADOR: testar ferramentas DE VERDADE (abrir, usar, conferir contas) e anotar no CRITICA.md"),
}


def _ler(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _salvar(caminho, d):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def estado():
    return _ler(ARQ, {"formacao": "A"})


def cadeiras_b():
    """Chaves das cadeiras ocupadas pelo Google agora (vazio na formação A)."""
    e = estado()
    return set(e.get("cadeiras", {})) if e.get("formacao") == "B" else set()


def _prompt(chave):
    nome, mail, papel = CADEIRAS[chave]
    return (
        f"FORMAÇÃO B da fábrica da Caixa de Ferramentas do Caio (pt-BR). Você ocupa a CADEIRA DO {nome.upper()} "
        f"(o {nome} está sem cota). Para a fábrica você É o {nome}: no painel/quadro sua chave é '{chave}' "
        f"(python {RAIZ}/painel.py {chave} ...) e no Agent Mail (MCP agent-mail) você é {mail}, "
        f"project_key \"{RAIZ}\". Leia AGENTS.md (seção 📬 FÁBRICA 2.0) e RUMO.md antes.\n"
        f"Seu papel: {papel}.\n"
        "Trabalhe em CICLO CONTÍNUO, sem parar: 1) fetch_inbox e responda (reply_message + acknowledge_message); "
        f"2) python {RAIZ}/painel.py {chave} --pegar; 3) antes de editar arquivo da caixa-ferramentas, "
        "file_reservation_paths; 4) faça, rode os testes; 5) --concluir <ID> \"resultado citando a pasta\" (portão de "
        "qualidade: se recusar, conserte); 6) release_file_reservations e volte ao passo 1. "
        "Regras: só CÓDIGO-FONTE (nunca staged/ nem dist/), não buildar o .exe, nada pra golpe/ataque, não apagar "
        "arquivo do Caio. Quadro vazio e sem correio? Mande send_message pro AmberFern (Claude) e espere 5 min."
    )


def _pid_vivo(pid):
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
        if not h:
            return False
        cod = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(cod))
        ctypes.windll.kernel32.CloseHandle(h)
        return cod.value == 259
    except Exception:  # noqa: BLE001
        return False


def _cpu_arvore(pid):
    """Segundos de CPU do processo e dos filhos (o agy roda ferramentas em subprocessos)."""
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            f"$t=0; $ids=@({int(pid)}); $f=@(Get-CimInstance Win32_Process | Where-Object {{ $_.ParentProcessId -eq {int(pid)} }} | ForEach-Object ProcessId); "
                            "foreach ($i in $ids + $f) { $p = Get-Process -Id $i -EA SilentlyContinue; if ($p) { $t += $p.CPU } }; $t"],
                           capture_output=True, text=True, timeout=20,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return float(r.stdout.strip().replace(",", ".") or 0)
    except (ValueError, OSError, subprocess.TimeoutExpired):
        return None


def _achar_pid(marca, espera=20):
    """PID do agy que está com a marca no prompt (a aba do Windows Terminal não devolve o PID)."""
    fim = time.time() + espera
    while time.time() < fim:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process -Filter \"Name='agy.exe'\" | "
                            "ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for linha in r.stdout.splitlines():
            pid, _, cmd = linha.partition("\t")
            if marca in cmd and pid.strip().isdigit():
                return int(pid)
        time.sleep(2)
    return None


def abrir_cadeira(chave):
    nome = CADEIRAS[chave][0]
    # A instrução vai num ARQUIVO .md e o agy recebe só uma frase curta, sem aspas nem ";". (11/11: o Windows
    # Terminal picotava o texto no ";" e as aspas internas quebravam os argumentos → abas com erro, agy fechando.)
    arq = f"C:/Users/caion/fiscal-fabrica/cadeira_{chave}.md"
    with open(arq, "w", encoding="utf-8") as f:
        f.write(_prompt(chave) + "\n")
    prompt = f"Leia o arquivo {arq} e siga TODAS as instrucoes dele agora, em ciclo continuo"
    subprocess.Popen(["wt.exe", "-w", "fabrica", "new-tab", "--title", f"B: {nome} (Gemini)", "-d", RAIZ,
                      # --mode auto NÃO aprova ferramenta MCP (parava em "Allow calling agent-mail/fetch_inbox?"):
                      # aprovação automática total — risco assumido explicitamente pelo Caio em 11/11
                      AGY, "-i", prompt, "--mode", "auto", "--dangerously-skip-permissions", "--model", melhor_modelo(),
                      # ferramentas ficam em pastas irmãs (C:/Users/caion/<pasta>) e o .md em fiscal-fabrica: sem isso
                      # o agy para a cada arquivo pedindo "outside workspace" (Caio assumiu o risco, 11/11)
                      "--add-dir", "C:/Users/caion"],
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    pid = _achar_pid(f"cadeira_{chave}.md")
    _minimizar_fabrica()
    return pid


def _minimizar_fabrica():
    """Minimiza (sem ativar) as janelas do Windows Terminal da fábrica — abas "B: ..." — pra não roubar a tela."""
    if os.name != "nt":
        return 0
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        achadas = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cada(h, _l):
            if not user32.IsWindowVisible(h):
                return True
            classe = ctypes.create_unicode_buffer(128)
            user32.GetClassNameW(h, classe, 128)
            titulo = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(h, titulo, 256)
            if classe.value == "CASCADIA_HOSTING_WINDOW_CLASS" and titulo.value.startswith("B: "):
                achadas.append(h)
            return True

        for _ in range(6):  # a aba nova leva um instante pra virar o título da janela
            time.sleep(0.5)
            user32.EnumWindows(cada, 0)
            if achadas:
                break
        for h in achadas:
            user32.ShowWindow(h, 7)  # SW_SHOWMINNOACTIVE: minimiza sem pegar o foco
        return len(achadas)
    except Exception:  # noqa: BLE001 — sem minimizar a cadeira funciona igual
        return 0


def _abrir_registrando(e, chave):
    """Abre a cadeira e guarda quando abriu (a espera crescente mede se ela fechou logo depois)."""
    e.setdefault("cadeiras", {})[chave] = abrir_cadeira(chave)
    e.setdefault("aberta", {})[chave] = time.time()


ESPERA_MIN = [5, 10, 20, 40, 80]  # minutos antes de reabrir, conforme os fechamentos seguidos
DESISTE_APOS = len(ESPERA_MIN)
FECHOU_LOGO = 600  # cadeira que morre em menos de 10 min depois de aberta conta como "fechou logo"
ACORDAR_MAX, ACORDAR_JANELA = 3, 7200  # no máx. 3 "acordar" por cadeira a cada 2 h


def _pode_reabrir(e, chave, agora=None):
    """Decide se a cadeira que fechou pode ser reaberta agora. Atualiza a contagem de fechamentos seguidos.

    Devolve (pode, motivo)."""
    agora = agora or time.time()
    aberta = (e.get("aberta") or {}).get(chave, 0)
    rep = e.setdefault("reabrir", {}).setdefault(chave, {"seguidos": 0, "visto": 0})
    # conta este fechamento uma vez só (o carteiro olha a cada 2 min)
    if rep.get("visto", 0) < aberta or not rep.get("visto"):
        rep["seguidos"] = rep.get("seguidos", 0) + 1 if aberta and agora - aberta < FECHOU_LOGO else 0
        rep["visto"] = agora
    n = rep["seguidos"]
    if n >= DESISTE_APOS:
        return False, f"fechou {n} vezes seguidas logo depois de abrir — desisti; reabra com `python formacao.py B`"
    espera = ESPERA_MIN[n - 1] * 60 if n else 0
    if agora - aberta < espera:
        return False, f"espera {ESPERA_MIN[n - 1]} min ({n} fechamento(s) seguido(s))"
    return True, ""


def _pode_acordar(e, chave, agora=None):
    agora = agora or time.time()
    lista = [t for t in (e.get("acordadas") or {}).get(chave, []) if agora - t < ACORDAR_JANELA]
    e.setdefault("acordadas", {})[chave] = lista
    return len(lista) < ACORDAR_MAX


def _avisar(texto):
    try:
        import carteiro
        carteiro.log("formação: " + texto)
    except Exception:  # noqa: BLE001
        print(texto)


def ligar_b():
    e = estado()
    if e.get("formacao") == "B":
        return "já está na formação B"
    pausados = _ler(PAUSADOS, {})
    e = {"formacao": "B", "desde": time.strftime("%Y-%m-%d %H:%M"), "pausados_antes": pausados, "cadeiras": {}}
    _salvar(PAUSADOS, {k: v for k, v in pausados.items() if k not in CADEIRAS})  # Cocaino volta (com motor Google)
    for chave in CADEIRAS:
        _abrir_registrando(e, chave)
    _salvar(ARQ, e)
    _avisar(f"FORMAÇÃO B ligada: Google nas cadeiras {', '.join(CADEIRAS)} (pids {e['cadeiras']})")
    return e


def voltar_a():
    e = estado()
    if e.get("formacao") != "B":
        return "já está na formação A"
    for _chave, pid in (e.get("cadeiras") or {}).items():
        if pid and _pid_vivo(pid):
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    _salvar(PAUSADOS, e.get("pausados_antes", {}))
    _salvar(ARQ, {"formacao": "A", "desde": time.strftime("%Y-%m-%d %H:%M"), "b_durou_desde": e.get("desde")})
    _avisar("FORMAÇÃO A de volta: cadeiras devolvidas pro Cursor, Grok CLI e Cocaino")
    return "formação A"


def garantir_b():
    """Na B: cadeira cujo agy fechou e que tem correio/tarefa → reabre (no máx. 1 por chamada)."""
    e = estado()
    if e.get("formacao") != "B":
        return
    for chave, pid in list(e.get("cadeiras", {}).items()):
        if pid and _pid_vivo(pid):
            # viva mas PARADA: depois de uma cota crítica o painel manda "PARE até liberar" e ninguém acorda
            # a cadeira (agy não tem gancho de fim de turno). 11/11: 4 h paradas com a cota já liberada.
            try:
                import economia
                p = _ler(os.path.join(HERE, "painel", f"{chave}.json"), {})
                parada = (time.time() - time.mktime(time.strptime(p.get("atualizado", ""), "%Y-%m-%d %H:%M"))) / 60
            except (ValueError, OverflowError):
                parada = 9999
            except Exception:  # noqa: BLE001
                continue
            ultimo = (e.get("acordou") or {}).get(chave, 0)
            # ocioso de verdade = processo do agy (e filhos) sem gastar CPU desde a última olhada (2 min).
            # Assim acorda em ~15 min em vez de 40, sem interromper quem está numa tarefa longa.
            cpu = _cpu_arvore(pid)
            cpu_antes = (e.get("cpu") or {}).get(chave)
            e.setdefault("cpu", {})[chave] = cpu
            _salvar(ARQ, e)
            # parado o agy ainda gasta ~0,16 s/5 s (tela redesenhando) ≈ 4 s em 2 min; rodando teste/ferramenta gasta bem mais
            ocioso = cpu_antes is not None and cpu is not None and cpu - cpu_antes < 6.0
            limite = 15 if ocioso else 40
            if parada < limite or time.time() - ultimo < 900 or economia.nivel_do_agente(chave) == "critico":
                continue
            if not _pode_acordar(e, chave):
                _salvar(ARQ, e)
                continue  # já acordou 3 vezes nas últimas 2 h: deixa quieta
            try:
                import tarefas
                if not tarefas.livres_para(chave):
                    continue
            except Exception:  # noqa: BLE001
                continue
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            e.setdefault("acordou", {})[chave] = time.time()
            e["acordadas"][chave].append(time.time())
            _abrir_registrando(e, chave)
            _salvar(ARQ, e)
            _avisar(f"cadeira {chave} (Google) estava parada há {int(parada)} min com tarefa livre → reiniciei pra acordar"
                    f" ({len(e['acordadas'][chave])}/{ACORDAR_MAX} nas últimas 2 h)")
            return
        if pid and _pid_vivo(pid):
            # viva há 30+ min: zera a contagem de fechamentos seguidos
            if time.time() - (e.get("aberta") or {}).get(chave, 0) > 1800 and (e.get("reabrir") or {}).get(chave):
                e["reabrir"][chave] = {"seguidos": 0, "visto": 0}
                _salvar(ARQ, e)
            continue
        try:
            import fabrica_mail
            import tarefas
            tem = bool(fabrica_mail.caixa(chave)) or bool(tarefas.livres_para(chave)) or any(
                t["status"] == "pegou" and t["por"] == chave for t in tarefas.ler())
        except Exception:  # noqa: BLE001
            tem = True
        if not tem:
            continue
        try:
            import economia
            if economia.nivel_do_agente(chave) == "critico":
                continue  # sem cota: reabrir só faria a cadeira fechar de novo
        except Exception:  # noqa: BLE001
            pass
        pode, motivo = _pode_reabrir(e, chave)
        if not pode:
            rep = e["reabrir"][chave]
            if rep.get("avisado") != motivo:  # avisa uma vez por situação, não a cada 2 min
                rep["avisado"] = motivo
                _avisar(f"cadeira {chave} (Google) fechou — não reabri: {motivo}")
            _salvar(ARQ, e)
            continue
        _abrir_registrando(e, chave)
        _salvar(ARQ, e)
        _avisar(f"cadeira {chave} (Google) tinha fechado e tem trabalho → reabri")
        return


def _nivel_conta(conta):
    est = _ler(os.path.join(HERE, "ECONOMIA.json"), {})
    return (est.get("contas") or {}).get(conta, {}).get("nivel", "normal")


def auto():
    """Regra do Caio (12/11): cada cadeira usa SEMPRE a IA que tem cota. Sem perguntar A ou B.
    Original (SuperGrok) crítica e Google com folga → cadeira vai pro Google; Google crítico e original com
    folga → cadeira volta pro agente original. Mínimo 30 min entre trocas da mesma cadeira (sem pingue-pongue)."""
    e = estado()
    cad = dict(e.get("cadeiras") or {}) if e.get("formacao") == "B" else {}
    troca = e.get("trocou") or {}
    grok, google = _nivel_conta("grok"), _nivel_conta("google")
    mudou = []
    for chave in CADEIRAS:
        if time.time() - troca.get(chave, 0) < 1800:
            continue
        no_google = chave in cad
        if not no_google and grok == "critico" and google != "critico":
            cad[chave] = abrir_cadeira(chave)
            e.setdefault("aberta", {})[chave] = time.time()
            mudou.append(f"{chave} → Google")
        elif no_google and google == "critico" and grok != "critico":
            pid = cad.pop(chave)
            if pid and _pid_vivo(pid):
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            mudou.append(f"{chave} → original (Grok)")
        else:
            continue
        troca[chave] = time.time()
    if not mudou:
        return []
    novo = {"formacao": "B" if cad else "A", "desde": e.get("desde") or time.strftime("%Y-%m-%d %H:%M"),
            "pausados_antes": e.get("pausados_antes", {}), "cadeiras": cad, "trocou": troca,
            "acordou": e.get("acordou", {}), "acordadas": e.get("acordadas", {}),
            "aberta": e.get("aberta", {}), "reabrir": e.get("reabrir", {})}
    if not cad:  # todas de volta: devolve a reserva do Cocaino como era antes da manobra
        _salvar(PAUSADOS, e.get("pausados_antes", {}))
    _salvar(ARQ, novo)
    _avisar(f"troca automática (SuperGrok {grok}, Google {google}): " + ", ".join(mudou))
    return mudou


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    a = sys.argv[1:]
    if a[:1] == ["B"]:
        print(ligar_b())
    elif a[:1] == ["A"]:
        print(voltar_a())
    else:
        e = estado()
        print(f"Formação {e.get('formacao')} desde {e.get('desde', '?')}")
        for chave, pid in (e.get("cadeiras") or {}).items():
            print(f"  {chave}: agy pid {pid} {'vivo' if pid and _pid_vivo(pid) else 'FECHADO'}")
