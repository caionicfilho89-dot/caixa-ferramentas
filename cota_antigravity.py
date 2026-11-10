"""Lê a cota AO VIVO do Antigravity pelo agy (ferramenta interna swarm/models, modelo mais barato).
Atualiza cotas_manuais.json["antigravity"] (janela curta). A cota SEMANAL só aparece no app: continua manual.
Uso: python cota_antigravity.py   (o carteiro roda a cada 30 min)"""
import json, os, re, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
AGY = os.path.join(os.environ["LOCALAPPDATA"], "agy", "bin", "agy.exe")
ARQ = os.path.join(HERE, "cotas_manuais.json")
PROMPT = ("Use the swarm tool with action models. Reply ONLY with one JSON object mapping each model name to "
          "{quota_remaining, quota_resets}. No other text.")


def ler():
    r = subprocess.run([AGY, "-p", PROMPT, "--model", "gemini-3.8-flash-low", "--print-timeout", "120s"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=170,
                       cwd=os.environ.get("TEMP", HERE), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    m = re.search(r"\{.*\}", r.stdout or "", re.S)
    if not m:
        raise RuntimeError("agy não devolveu JSON")
    return json.loads(m.group())


def pct(v):
    return float(str(v).strip().rstrip("%"))


def atualizar():
    dados = ler()
    flash = [v for k, v in dados.items() if k.startswith("gemini-3.8-flash")]
    argon = [v for k, v in dados.items() if k.startswith("gemini-4-argon")]
    try:
        with open(ARQ, encoding="utf-8") as f:
            cm = json.load(f)
    except (OSError, ValueError):
        cm = {}
    ag = cm.setdefault("antigravity", {})
    if flash:
        ag["gemini_5h_usado"] = round(100 - min(pct(v["quota_remaining"]) for v in flash))
        ag["gemini_5h_renova"] = flash[0].get("quota_resets")
    if argon:
        ag["argon_semana_usado"] = round(100 - min(pct(v["quota_remaining"]) for v in argon))
    ag["lido_auto"] = time.strftime("%d/%m %H:%M")
    with open(ARQ, "w", encoding="utf-8") as f:
        json.dump(cm, f, ensure_ascii=False, indent=1)
    return ag


if __name__ == "__main__":
    print(atualizar())
