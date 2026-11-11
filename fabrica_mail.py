"""Cliente do MCP Agent Mail (servidor local http://127.0.0.1:8765/mcp/) pra quem NÃO é agente MCP:
carteiro (script), Gemini (carteiro_ia), ponte do Cocaino (Grok Bot não aceita MCP) e o painel.

Fábrica 2.0 (11/11): os agentes conversam pelo Agent Mail (caixa de entrada, threads, reserva de arquivo)
em vez do carteiro colar texto nas janelas. Usa o SDK oficial `mcp`.

    python fabrica_mail.py --ferramentas                 # lista as ferramentas e parâmetros
    python fabrica_mail.py --setup                       # cria o projeto e registra os 6 agentes
    python fabrica_mail.py --caixa Cursor                # mensagens de um agente
    python fabrica_mail.py --enviar Claude Cursor "assunto" "texto"
"""
import asyncio
import json
import os
import sys

URL = os.environ.get("AGENT_MAIL_URL", "http://127.0.0.1:8765/mcp/")
PROJETO = "C:/Users/caion/caixa-ferramentas"   # project_key do Agent Mail = caminho absoluto do repo

# nome no Agent Mail -> (chave no painel/quadro, programa, modelo)
AGENTES = {
    "Claude": ("claude", "claude-code", "claude-opus-5-5"),
    "Cursor": ("cursor", "cursor", "grok-4.7"),
    "Antigravity": ("antigravity", "antigravity", "gemini"),
    "GrokCLI": ("grokbuild", "grok-cli", "grok-4.7"),
    "Cocaino": ("grok", "grok-bot", "grok"),
    "Gemini": ("gemini", "gemini-agy", "gemini-3.8-flash"),
}
NOMES_ARQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agentes_mail.json")


def _nomes():
    """Agent Mail exige nome adjetivo+substantivo (ex.: BlueLake): ele gera no --setup e guardamos aqui."""
    try:
        with open(NOMES_ARQ, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


CHAVE_PARA_NOME = {}  # 'cursor' -> 'BlueLake' (preenchido do agentes_mail.json)
CHAVE_PARA_NOME.update(_nomes())


async def _chamar(ferramenta, args):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    async with streamablehttp_client(URL) as (ler, escrever, _):
        async with ClientSession(ler, escrever) as s:
            await s.initialize()
            r = await s.call_tool(ferramenta, args)
            txt = "\n".join(getattr(c, "text", "") for c in r.content)
            try:
                dados = json.loads(txt)
            except ValueError:
                dados = txt
            if r.isError:
                raise RuntimeError(f"{ferramenta}: {txt[:400]}")
            return dados


def chamar(ferramenta, **args):
    return asyncio.run(_chamar(ferramenta, args))


async def _ferramentas():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    async with streamablehttp_client(URL) as (ler, escrever, _):
        async with ClientSession(ler, escrever) as s:
            await s.initialize()
            return (await s.list_tools()).tools


def ferramentas():
    return asyncio.run(_ferramentas())


def nome(agente):
    """Aceita 'cursor' (chave do painel), 'Cursor' (apelido) ou o nome do Agent Mail (ex.: BlueLake)."""
    if agente in AGENTES:
        agente = AGENTES[agente][0]
    return CHAVE_PARA_NOME.get(agente, agente)


def apelido(nome_mail):
    """'BlueLake' -> 'Cursor' (pra mostrar pro Caio)."""
    for ap, (chave, *_r) in AGENTES.items():
        if CHAVE_PARA_NOME.get(chave) == nome_mail:
            return ap
    return nome_mail


def setup():
    saida = [chamar("ensure_project", human_key=PROJETO)]
    nomes = _nomes()
    for ap, (chave, prog, modelo) in AGENTES.items():
        args = dict(project_key=PROJETO, program=prog, model=modelo,
                    task_description=f"{ap} da fábrica da Caixa de Ferramentas (painel: {chave})")
        if nomes.get(chave):
            args["name"] = nomes[chave]
        r = chamar("register_agent", **args)
        nomes[chave] = (r.get("name") if isinstance(r, dict) else None) or nomes.get(chave)
        saida.append(f"{ap} = {nomes[chave]}")
    with open(NOMES_ARQ, "w", encoding="utf-8") as f:
        json.dump(nomes, f, ensure_ascii=False, indent=1)
    CHAVE_PARA_NOME.update(nomes)
    return saida


def enviar(de, para, assunto, texto, thread=None, importancia="normal"):
    para = [nome(p) for p in (para if isinstance(para, (list, tuple)) else [para])]
    args = dict(project_key=PROJETO, sender_name=nome(de), to=para, subject=assunto, body_md=texto,
                importance=importancia)
    if thread:
        args["thread_id"] = thread
    return chamar("send_message", **args)


def caixa(agente, so_novas=True, limite=20, marcar_lida=False):
    """Espia a caixa (por padrão NÃO marca como lida: quem marca é o próprio agente ao ler/responder)."""
    r = chamar("fetch_inbox", project_key=PROJETO, agent_name=nome(agente), unread_only=so_novas,
               include_bodies=True, limit=limite, mark_read=marcar_lida)
    msgs = r.get("messages", r.get("result", r)) if isinstance(r, dict) else r
    return msgs if isinstance(msgs, list) else []


def lida(agente, msg_id):
    return chamar("acknowledge_message", project_key=PROJETO, agent_name=nome(agente), message_id=msg_id)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    a = sys.argv[1:]
    if a[:1] == ["--ferramentas"]:
        for t in ferramentas():
            props = (t.inputSchema or {}).get("properties", {})
            req = (t.inputSchema or {}).get("required", [])
            if not a[1:] or t.name in a[1:]:
                print(f"{t.name}({', '.join((p + '*' if p in req else p) for p in props)})")
    elif a[:1] == ["--setup"]:
        print(json.dumps(setup(), ensure_ascii=False, indent=1)[:2000])
    elif a[:1] == ["--caixa"] and len(a) > 1:
        print(json.dumps(caixa(a[1], so_novas=False), ensure_ascii=False, indent=1)[:3000])
    elif a[:1] == ["--enviar"] and len(a) >= 5:
        print(enviar(a[1], a[2].split(","), a[3], a[4]))
    else:
        print(__doc__)
