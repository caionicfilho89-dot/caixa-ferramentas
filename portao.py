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


def verificar(resultado, raiz=HERE, titulo=""):
    """'' = aprovado; senão o motivo da recusa (o agente lê e conserta).
    12/11: ritmo menor, QUALIDADE maior (pedido do Caio) — resultado vago ou sem teste não passa."""
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
    for p in pastas_citadas(resultado):
        erro = _rodar_testes(p)
        if erro:
            return "teste quebrado — " + erro
        if os.path.isfile(os.path.join(BASE, p, "ENTREGA.json")) and f'"{p}"' not in builtin:
            return (f"ferramenta nova '{p}' não está na Caixa: registre em BUILTIN (caixa.pyw) e TOOLS "
                    f"(build_suite.py) — e em tendencias_caixa.json se veio da tendência — e conclua de novo.")
    return ""


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    txt = " ".join(sys.argv[1:])
    print("pastas:", pastas_citadas(txt))
    print(verificar(txt) or "✅ aprovado")
