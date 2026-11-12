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
    return _achar_pid(f"cadeira_{chave}.md")


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
        e["cadeiras"][chave] = abrir_cadeira(chave)
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
            if parada < 40 or time.time() - ultimo < 1800 or economia.nivel_do_agente(chave) == "critico":
                continue
            try:
                import tarefas
                if not tarefas.livres_para(chave):
                    continue
            except Exception:  # noqa: BLE001
                continue
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            e.setdefault("acordou", {})[chave] = time.time()
            e["cadeiras"][chave] = abrir_cadeira(chave)
            _salvar(ARQ, e)
            _avisar(f"cadeira {chave} (Google) estava parada há {int(parada)} min com tarefa livre → reiniciei pra acordar")
            return
        if pid and _pid_vivo(pid):
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
        e["cadeiras"][chave] = abrir_cadeira(chave)
        _salvar(ARQ, e)
        _avisar(f"cadeira {chave} (Google) tinha fechado e tem trabalho → reabri")
        return


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
