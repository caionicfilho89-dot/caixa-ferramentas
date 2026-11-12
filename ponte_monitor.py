"""Ponte fábrica → Claude Code Monitor (o painel da fábrica desde 11/11).

O Monitor só lê Claude Code e Cursor sozinho. Pra não virar downgrade (pedido do Caio), esta ponte manda pra ele,
no MESMO formato dos ganchos oficiais (POST /api/hooks/event {hook_type, data}), o que os outros agentes fazem:
  - uma sessão por agente (Antigravity, Grok CLI, Cocaino, Gemini e as cadeiras Google da formação B);
  - pegou tarefa → UserPromptSubmit + PreToolUse("Tarefa") = trabalhando; concluiu → PostToolUse + Stop;
  - mensagem que o agente mandou no correio → PreToolUse/PostToolUse("Correio");
  - sessão "🏭 Fábrica da Caixa": alertas que o Caio precisa saber (cotas, recusas, travados, correio fora) → Notification.
O carteiro chama sincronizar() a cada 1 min. Estado em ponte_monitor.json. Teste: python ponte_monitor.py
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(HERE, "ponte_monitor.json")
DESCOBERTA = os.path.join(os.path.expanduser("~"), ".claude", ".agent-dashboard.json")
CWD = "C:/Users/caion/caixa-ferramentas"

# chave do painel -> (nome no Monitor, modelo, nativo no Monitor?)
AGENTES = {
    "antigravity": ("🧠 Antigravity", "gemini (Google AI Pro)", False),
    "grokbuild": ("🔌 Grok CLI", "grok-4.7", False),
    "grok": ("🧐 Cocaino", "grok", False),
    "gemini": ("✨ Gemini (revisor/planejador)", "gemini-3.8-flash", False),
    "cursor": ("🎨 Cursor", "grok-4.7", True),   # o app Cursor o Monitor já lê; na formação B a cadeira é agy → ponte
}


def _ler(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _porta():
    return int(_ler(DESCOBERTA, {}).get("port") or 4820)


def enviar(hook, data):
    corpo = json.dumps({"hook_type": hook, "data": data}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(f"http://127.0.0.1:{_porta()}/api/hooks/event", data=corpo, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status


def _sid(nome):
    """Uma sessão por agente por dia (o Monitor agrupa por dia; amanhã começa uma nova)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"caixa-fabrica/{nome}/{dt.date.today().isoformat()}"))


def _cadeiras_b():
    try:
        sys.path.insert(0, HERE)
        import formacao
        return formacao.cadeiras_b()
    except Exception:  # noqa: BLE001
        return set()


def _base(sid, evento, nome, modelo):
    return {"session_id": sid, "hook_event_name": evento, "cwd": CWD, "session_name": nome, "model": modelo}


def _garantir_sessao(est, sid, nome, modelo):
    if sid not in est["sessoes"]:
        enviar("SessionStart", dict(_base(sid, "SessionStart", nome, modelo), source="startup"))
        est["sessoes"][sid] = {"fazendo": "", "feitos": 0, "msgs": []}
    return est["sessoes"][sid]


def sincronizar():
    est = _ler(ESTADO, {})
    est.setdefault("sessoes", {})
    est.setdefault("alertas", [])
    b = _cadeiras_b()
    enviados = 0
    # ---- agentes
    for chave, (nome, modelo, nativo) in AGENTES.items():
        if nativo and chave not in b:
            continue  # o próprio Monitor já mostra
        if chave in b:
            nome, modelo = nome + " · cadeira Google (formação B)", "gemini (agy)"
        sid = _sid(nome)
        st = _garantir_sessao(est, sid, nome, modelo)
        p = _ler(os.path.join(HERE, "painel", f"{chave}.json"), {})
        fazendo = (p.get("fazendo") or "").strip()
        if fazendo and fazendo != st["fazendo"]:
            enviar("UserPromptSubmit", dict(_base(sid, "UserPromptSubmit", nome, modelo), prompt=fazendo))
            enviar("PreToolUse", dict(_base(sid, "PreToolUse", nome, modelo), tool_name="Tarefa",
                                      tool_input={"description": fazendo[:300]}))
            enviados += 2
        feitos = p.get("feitos", [])
        if len(feitos) > st["feitos"] and st["feitos"]:
            for f in feitos[st["feitos"] - len(feitos):] if len(feitos) - st["feitos"] <= 5 else feitos[-1:]:
                enviar("PostToolUse", dict(_base(sid, "PostToolUse", nome, modelo), tool_name="Tarefa",
                                           tool_input={"description": f[17:300]}, tool_response={"success": True}))
                enviados += 1
            if not fazendo:
                enviar("Stop", _base(sid, "Stop", nome, modelo))
                enviados += 1
        st["fazendo"], st["feitos"] = fazendo, len(feitos)
    # ---- correio: o que cada agente mandou vira ação "Correio" na sessão dele
    try:
        import fabrica_mail as fm
        vistos = set(est.get("msgs_vistas", []))
        for chave, (nome, modelo, nativo) in AGENTES.items():
            pass
        for destino in list(AGENTES) + ["claude"]:
            for m in fm.caixa(destino, so_novas=False, limite=10):
                if m.get("id") in vistos:
                    continue
                vistos.add(m.get("id"))
                de = fm.apelido(m.get("from", ""))
                chave_de = next((k for k, v in fm.AGENTES.items() if k == de), None)
                k = fm.AGENTES.get(chave_de, (None,))[0] if chave_de else None
                if k not in AGENTES or (AGENTES[k][2] and k not in b):
                    continue
                nome, modelo = AGENTES[k][0], AGENTES[k][1]
                if k in b:
                    nome, modelo = nome + " · cadeira Google (formação B)", "gemini (agy)"
                sid = _sid(nome)
                _garantir_sessao(est, sid, nome, modelo)
                txt = f"→ {fm.apelido(fm.nome(destino))}: {m.get('subject', '')}"[:200]
                enviar("PreToolUse", dict(_base(sid, "PreToolUse", nome, modelo), tool_name="Correio",
                                          tool_input={"description": txt}))
                enviar("PostToolUse", dict(_base(sid, "PostToolUse", nome, modelo), tool_name="Correio",
                                           tool_input={"description": txt}, tool_response={"success": True}))
                enviados += 2
        est["msgs_vistas"] = sorted(vistos)[-500:]
    except Exception:  # noqa: BLE001 — correio fora não derruba a ponte
        pass
    # ---- alertas da fábrica → notificações
    try:
        import importlib.util as iu
        spec = iu.spec_from_file_location("pa", os.path.join(HERE, "painel_adesivo.pyw"))
        pa = iu.module_from_spec(spec)
        spec.loader.exec_module(pa)
        d = pa.coletar()
        lista = pa.alertas(d, None, b)
        sid = _sid("🏭 Fábrica da Caixa")
        _garantir_sessao(est, sid, "🏭 Fábrica da Caixa — alertas", "fábrica")
        atuais = []
        import re as _re
        for nv, txt in lista:
            limpo = _re.sub(r"<[^>]+>", "", txt)
            atuais.append(limpo)
            if limpo not in est["alertas"]:
                enviar("Notification", dict(_base(sid, "Notification", "🏭 Fábrica da Caixa — alertas", "fábrica"),
                                            message=("🔴 " if nv == 2 else "🟡 " if nv == 1 else "🟢 ") + limpo,
                                            notification_type="fabrica"))
                enviados += 1
        est["alertas"] = atuais
    except Exception:  # noqa: BLE001
        pass
    with open(ESTADO, "w", encoding="utf-8") as f:
        json.dump(est, f, ensure_ascii=False, indent=1)
    return enviados


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    print("eventos enviados ao Monitor:", sincronizar())
