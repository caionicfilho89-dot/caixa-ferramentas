"""Portão de qualidade: tarefa só vira "feito" se passar aqui (padrão "test gating" dos orquestradores de agentes).

Chamado por tarefas.concluir(). Recusa (e a tarefa continua com o agente) quando:
  1. o trabalho foi feito em staged/ ou dist/ (cópia de build: o próximo build APAGA — aconteceu na T66);
  2. algum teste das pastas de ferramenta citadas no resultado falha;
  3. ferramenta NOVA (tem ENTREGA.json) não foi registrada na Caixa (BUILTIN em caixa.pyw) — aconteceu na T68;
  4. caixa.pyw / build_suite.py não compilam.
Uso manual:  python portao.py "texto do resultado"
"""
import json
import os
import py_compile
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)  # pastas das ferramentas são irmãs da caixa-ferramentas


def _chaves_catalogo():
    try:
        with open(os.path.join(HERE, "catalogo.json"), encoding="utf-8") as f:
            return {t["chave"] for t in json.load(f)["ferramentas"]}
    except (OSError, ValueError, KeyError):
        return set()


def pastas_citadas(resultado):
    """Pastas de ferramenta mencionadas: caminho C:\\Users\\caion\\<pasta> ou o nome-chave do catálogo."""
    achadas = []
    for m in re.finditer(r"[Cc]:[\\/]+Users[\\/]+caion[\\/]+([\w.-]+)", resultado):
        achadas.append(m.group(1))
    chaves = _chaves_catalogo()
    for tok in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)+", resultado.lower()):
        if tok in chaves:
            achadas.append(tok)
    vistas, saida = set(), []
    for p in achadas:
        d = os.path.join(BASE, p)
        if p.lower() not in vistas and p != os.path.basename(HERE) and os.path.isdir(d):
            vistas.add(p.lower())
            saida.append(p)
    return saida[:6]


def _rodar_testes(pasta):
    d = os.path.join(BASE, pasta)
    testes = sorted(f for f in os.listdir(d) if re.match(r"test_.*\.py$", f))
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONIOENCODING="utf-8", CAIXA_TESTE="1")
    for t in testes[:4]:
        try:
            r = subprocess.run([sys.executable, t], cwd=d, env=env, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=180,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except subprocess.TimeoutExpired:
            return f"{pasta}/{t} passou de 3 min (travou?)"
        if r.returncode != 0:
            fim = (r.stdout + r.stderr).strip()[-300:]
            return f"{pasta}/{t} FALHOU: …{fim}"
    return ""


def _script_da_pasta(pasta):
    """O .pyw registrado no BUILTIN pra essa pasta (ou o primeiro .pyw dela)."""
    try:
        with open(os.path.join(HERE, "caixa.pyw"), encoding="utf-8") as f:
            m = re.search(r'"' + re.escape(pasta) + r'",\s*"([^"]+\.pyw)"', f.read())
        if m:
            return m.group(1)
    except OSError:
        pass
    d = os.path.join(BASE, pasta)
    cands = sorted(f for f in os.listdir(d) if f.endswith(".pyw")) if os.path.isdir(d) else []
    return cands[0] if cands else ""


_STAR_RE = re.compile(r"^from (PyQt6\.\w+) import \*[ \t]*\r?$", re.M)


def _pyflakes_star(arqs):
    """Arquivos com `from PyQt6.X import *` (226 ferramentas em 17/11): tira o import *, roda o pyflakes
    na cópia e só acusa nome indefinido que também NÃO existe no módulo do Qt — esse é bug de verdade."""
    import importlib
    import tempfile
    ruins = []
    for arq in arqs:
        try:
            with open(arq, encoding="utf-8", errors="replace") as f:
                src = f.read()
        except OSError:
            continue
        mods = _STAR_RE.findall(src)
        if not mods:
            continue
        try:
            qt = set().union(*(dir(importlib.import_module(m)) for m in mods))
        except ImportError:
            continue
        with tempfile.TemporaryDirectory() as d:
            copia = os.path.join(d, os.path.basename(arq).replace(".pyw", ".py"))
            with open(copia, "w", encoding="utf-8") as f:
                f.write(_STAR_RE.sub("", src))
            try:
                r = subprocess.run([sys.executable, "-m", "pyflakes", copia], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=120,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except (subprocess.TimeoutExpired, OSError):
                continue
        for l in r.stdout.splitlines():
            m = re.search(r":(\d+):(?:\d+:?)? undefined name '(\w+)'", l)
            if m and m.group(2) not in qt:
                # o import * vira linha vazia na cópia: a numeração é a mesma do original
                ruins.append(f"{os.path.basename(arq)}:{m.group(1)}: undefined name '{m.group(2)}'")
    return ruins


def _pyflakes(pasta):
    """Nome indefinido derruba a ferramenta no pythonw/exe (erro no paintEvent/botão mata o app no PyQt6)."""
    d = os.path.join(BASE, pasta)
    arqs = [os.path.join(d, f) for f in os.listdir(d) if f.endswith((".py", ".pyw")) and not f.startswith("test")]
    if not arqs:
        return ""
    try:
        r = subprocess.run([sys.executable, "-m", "pyflakes", *arqs], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (subprocess.TimeoutExpired, OSError):
        return ""
    # "'from X import *' used; unable to detect undefined names" é aviso, não erro: o pyflakes desiste
    # de checar o arquivo. Pra não deixar bug escondido, checa uma cópia sem o import * (abaixo).
    ruins = [l for l in r.stdout.splitlines()
             if ("undefined name" in l and "unable to detect" not in l) or "syntax error" in l.lower()]
    ruins += _pyflakes_star(arqs)
    if ruins:
        return (f"{pasta}: pyflakes achou nome indefinido (isso DERRUBA o app no pythonw/exe): "
                + "; ".join(l.replace(d + os.sep, "") for l in ruins[:3]))
    return ""


_DRIBLE_RE = re.compile(
    r"CAIXA_TESTE[^\n]*\n(?:[ \t]*[^\n]*\n){0,2}?[^\n]*\.(?:setEnabled\(\s*False|setVisible\(\s*False|hide\(\)|setDisabled\(\s*True)")


def _drible(pasta):
    """Botão desligado/escondido só em modo de teste = o robô pula e ninguém confere (lote 2, 17/11)."""
    d = os.path.join(BASE, pasta)
    for f in os.listdir(d):
        if f.endswith((".py", ".pyw")) and not f.startswith("test"):
            try:
                with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                    if _DRIBLE_RE.search(fh.read()):
                        return (f"{pasta}/{f}: desliga/esconde botão quando CAIXA_TESTE=1 — o robô deixa de "
                                "conferir esse botão. Proibido (FUNCIONAR.md): conserte o botão de verdade; se for "
                                "botão com menu, o robô já aciona cada item do menu.")
            except OSError:
                pass
    return ""


def _robo(pasta):
    """Clica em todos os botões fora da tela (robo_botoes.py, com segurança) — tem que dar zero erro."""
    script = _script_da_pasta(pasta)
    if not script:
        return ""
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONIOENCODING="utf-8", CAIXA_TESTE="1")
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "robo_botoes.py"), pasta, script], env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        return f"{pasta}: o robô de botões travou 3 min (algum botão trava a janela)"
    linhas = [l for l in r.stdout.splitlines() if l.startswith("{")]
    if not linhas:
        return f"{pasta}: a ferramenta CAIU ao abrir/clicar (código {r.returncode}) — abra com pythonw e veja"
    try:
        res = json.loads(linhas[-1])
    except ValueError:
        return ""
    if not res.get("abriu"):
        return f"{pasta}: a janela não abriu: {(res.get('erros') or ['?'])[0]}"
    if res.get("erros"):
        return f"{pasta}: botão com erro (robo_botoes.py): " + " | ".join(res["erros"][:3])
    return ""


def verificar(resultado, raiz=HERE, titulo="", obrigatorias=()):
    """'' = aprovado; senão o motivo da recusa (o agente lê e conserta).
    12/11: ritmo menor, QUALIDADE maior (pedido do Caio) — resultado vago ou sem teste não passa.
    17/11: `obrigatorias` = pastas do lote (campo "pastas" da tarefa): todas são conferidas, sem o
    limite de 6 das citadas — antes, 2 das 8 ferramentas de cada lote passavam sem checagem."""
    texto = (resultado or "").strip()
    if len(texto) < 60:
        return ("resultado vago demais: descreva O QUE mudou, EM QUAL pasta/arquivo e COMO testou "
                "(ex.: 'C:/Users/caion/x: corrigi Y; test_x.py 12 OK; conferi 2 contas na mão').")
    if not re.search(r"test|teste|conferi|confer|selftest|ok|passou|passaram", texto, re.I):
        return "faltou dizer como você testou (teste rodado, resultado, ou conferência feita na mão)."
    if "QA lote" in titulo and len(pastas_citadas(texto)) < 5:
        return ("lote de QA precisa citar as 5 pastas testadas (C:/Users/caion/<pasta>); o portão roda os testes "
                f"delas — só achei {len(pastas_citadas(texto))}.")
    if re.search(r"(^|[\s\\/'\"`(])(staged|dist)[\\/]", resultado):
        return ("você editou staged/ ou dist/ — é cópia de build, o próximo build APAGA. Faça a mudança no "
                "CÓDIGO-FONTE (pasta da ferramenta C:/Users/caion/<pasta> ou o .py da caixa-ferramentas) e conclua de novo.")
    for arq in ("caixa.pyw", "build_suite.py"):
        try:
            py_compile.compile(os.path.join(raiz, arq), doraise=True)
        except py_compile.PyCompileError as e:
            return f"{arq} não compila: {str(e)[-200:]}"
    try:
        with open(os.path.join(raiz, "caixa.pyw"), encoding="utf-8") as f:
            builtin = f.read()
    except OSError:
        builtin = ""
    conferir = list(obrigatorias)
    for p in pastas_citadas(resultado):
        if p.lower() not in {x.lower() for x in conferir}:
            conferir.append(p)
    for p in conferir:
        if not os.path.isdir(os.path.join(BASE, p)):
            return f"pasta do lote não existe: C:/Users/caion/{p} — confira o nome e conclua de novo."
        erro = _rodar_testes(p)
        if erro:
            return "teste quebrado — " + erro
        erro = _drible(p) or _pyflakes(p) or _robo(p)  # FUNCIONAR.md (17/11): nada de botão quebrado nem app que cai
        if erro:
            return erro
        if os.path.isfile(os.path.join(BASE, p, "ENTREGA.json")) and f'"{p}"' not in builtin:
            return (f"ferramenta nova '{p}' não está na Caixa: registre em BUILTIN (caixa.pyw) e TOOLS "
                    f"(build_suite.py) — e em tendencias_caixa.json se veio da tendência — e conclua de novo.")
    return ""


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    # python portao.py "resultado"            ou   python portao.py --tarefa T377
    if sys.argv[1:2] == ["--tarefa"]:
        import tarefas
        t = next(x for x in tarefas.ler() if x["id"] == sys.argv[2])
        txt, obrig = t.get("resultado", ""), t.get("pastas") or []
        print("pastas do lote:", obrig)
        print(verificar(txt, HERE, t.get("titulo", ""), obrig) or "✅ aprovado")
    else:
        txt = " ".join(sys.argv[1:])
        print("pastas:", pastas_citadas(txt))
        print(verificar(txt) or "✅ aprovado")
