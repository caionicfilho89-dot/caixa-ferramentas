"""Caça ferramentas que mostram resultado FALSO como se fosse real (exemplo/demo carregado sozinho,
valores sorteados no lugar de medição, "simulação" quando a função real falha).

    python caca_fake.py            # lista as suspeitas, mais graves primeiro
    python caca_fake.py --json     # grava caca_fake.json

Heurística (não executa nada): lê os .py/.pyw de cada pasta do BUILTIN (sem os testes) e pontua
- demo/exemplo chamado no __init__ ou no fallback de erro/sem resultado (grave)
- textos "demonstrativo", "fictício", "simulado", "dados de exemplo" na tela (médio)
- random.* em ferramenta que diz medir algo real (rede, sensor, velocidade, cpu, disco…) (médio)
"""
import ast
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)

# nome de função que carrega dado de mentira (não pega "simular"/"_simulate", que são cálculos legítimos)
DEMO_NOME = re.compile(r"(demo|exemplo|example|sample|fake|dummy|simulad[oa]|mock_?dados|dados_?mock)", re.I)
# texto que admite resultado de mentira na tela
TEXTO_FAKE = re.compile(r"(demonstrativ|dados de exemplo|modo demo|modo demonstra|valores de exemplo|"
                        r"exemplo de demonstra|dados falsos|n[aã]o s[aã]o reais|"
                        r"(?:digitaliza[cç][aã]o|leitura|medi[cç][aã]o|resultado|scan|varredura|teste|dados?) simulad[oa]s?)", re.I)
MEDE_REAL = re.compile(r"(rede|wi-?fi|ping|velocidade|speed|sensor|cpu|gpu|mem[oó]ria|disco|bateria|temperatura|"
                       r"monitor|scanner|scan|porta|lat[eê]ncia|bluetooth|usb|processo|sistema|hardware)", re.I)


def ferramentas():
    src = open(os.path.join(HERE, "caixa.pyw"), encoding="utf-8").read()
    arv = ast.parse(src)
    for no in ast.walk(arv):
        if isinstance(no, ast.Assign) and any(getattr(t, "id", "") == "BUILTIN" for t in no.targets):
            return [tuple(e.value for e in t.elts) for t in no.value.elts]
    return []


class Visita(ast.NodeVisitor):
    """Acha chamadas a funções com nome de demo dentro de __init__ ou de blocos de fallback."""

    def __init__(self):
        self.achados = []
        self.pilha = []

    def visit_FunctionDef(self, no):
        self.pilha.append(no.name)
        self.generic_visit(no)
        self.pilha.pop()

    def _contexto(self):
        return self.pilha[-1] if self.pilha else "<módulo>"

    def visit_Call(self, no):
        nome = getattr(no.func, "attr", None) or getattr(no.func, "id", None) or ""
        if DEMO_NOME.search(nome) and not nome.lower().startswith("setplaceholder"):
            ctx = self._contexto()
            # demo disparado sozinho: no __init__/setup, ou com silent=True (fallback)
            sozinho = ctx in ("__init__", "setup_ui", "_build_ui", "build_ui", "showEvent") or any(
                k.arg == "silent" for k in no.keywords)
            self.achados.append((no.lineno, nome, ctx, sozinho))
        self.generic_visit(no)

    def visit_If(self, no):
        if isinstance(no.test, ast.UnaryOp) and isinstance(no.test.op, ast.Not):
            for sub in no.body:
                for c in ast.walk(sub):
                    if isinstance(c, ast.Call):
                        nome = getattr(c.func, "attr", None) or getattr(c.func, "id", None) or ""
                        if DEMO_NOME.search(nome):
                            self.achados.append((c.lineno, nome, "if not (sem resultado)", True))
        self.generic_visit(no)

    def visit_ExceptHandler(self, no):
        for sub in ast.walk(no):
            if isinstance(sub, ast.Call):
                nome = getattr(sub.func, "attr", None) or getattr(sub.func, "id", None) or ""
                if DEMO_NOME.search(nome):
                    self.achados.append((sub.lineno, nome, "except", True))
        self.generic_visit(no)


def analisar(tool):
    emoji, nome, desc, pasta, script = tool[:5]
    raiz = os.path.join(BASE, pasta)
    if not os.path.isdir(raiz):
        return None
    pontos, provas = 0, []
    for arq in sorted(os.listdir(raiz)):
        if not arq.endswith((".py", ".pyw")) or arq.startswith("test"):
            continue
        caminho = os.path.join(raiz, arq)
        try:
            src = open(caminho, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        try:
            v = Visita()
            v.visit(ast.parse(src))
            for linha, fn, ctx, sozinho in v.achados:
                if sozinho:
                    pontos += 5
                    provas.append(f"{arq}:{linha} chama {fn}() sozinho ({ctx})")
        except SyntaxError:
            pass
        for m in TEXTO_FAKE.finditer(src):
            linha = src.count("\n", 0, m.start()) + 1
            trecho = src.splitlines()[linha - 1].strip()
            if "setPlaceholderText" in trecho or trecho.startswith("#") or "placeholderText" in trecho:
                continue
            pontos += 2
            provas.append(f"{arq}:{linha} {trecho[:110]}")
        if MEDE_REAL.search(nome + " " + desc) and re.search(r"\brandom\.(random|randint|uniform|choice|gauss)\(", src):
            for m in re.finditer(r"\brandom\.(random|randint|uniform|choice|gauss)\(", src):
                linha = src.count("\n", 0, m.start()) + 1
                pontos += 2
                provas.append(f"{arq}:{linha} sorteia valor: {src.splitlines()[linha - 1].strip()[:100]}")
                break
    if not pontos:
        return None
    return {"emoji": emoji, "nome": nome, "pasta": pasta, "pontos": pontos, "provas": provas[:8]}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = [r for r in (analisar(t) for t in ferramentas()) if r]
    res.sort(key=lambda r: -r["pontos"])
    if "--json" in sys.argv:
        json.dump(res, open(os.path.join(HERE, "caca_fake.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(res)} ferramentas suspeitas")
    for r in res:
        print(f"\n[{r['pontos']:3d}] {r['emoji']} {r['nome']}  ({r['pasta']})")
        for p in r["provas"]:
            print("      ", p)


if __name__ == "__main__":
    main()
