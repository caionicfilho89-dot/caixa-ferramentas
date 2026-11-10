"""Cota SEMANAL do Antigravity (Gemini) — só aparece na tela Settings → Models do app.
Tira o print (fiscal-fabrica/print_cota_antigravity.ps1), lê com o OCR do Windows (winocr, pt-BR) e grava
cotas_manuais.json["antigravity"]["gemini_semana_usado"]. O carteiro roda 1x a cada 7 dias com o Caio longe do PC.
Uso: python cota_antigravity_semanal.py [--forcar]"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ARQ = os.path.join(HERE, "cotas_manuais.json")
PS = r"C:\Users\caion\fiscal-fabrica\print_cota_antigravity.ps1"
IMG = os.path.join(os.environ.get("TEMP", HERE), "ag_models.png")


def _ocr(img, box, escala=4):
    import winocr
    from PIL import ImageOps
    c = ImageOps.invert(img.crop(box).convert("L")).convert("RGBA")
    c = c.resize((c.width * escala, c.height * escala))
    r = winocr.recognize_pil_sync(c, "pt-BR")
    return (r["text"] if isinstance(r, dict) else r.text).strip()


def ler_print(caminho=IMG):
    from PIL import Image
    img = Image.open(caminho).convert("RGB")
    if "gemini" not in _ocr(img, (268, 450, 600, 475)).lower() or "weekly" not in _ocr(img, (268, 488, 600, 512)).lower():
        raise RuntimeError("a tela capturada não é a Models & Usage (layout mudou?)")
    for box in [(800, 498, 840, 518), (797, 496, 842, 520), (795, 495, 845, 523), (790, 492, 848, 525)]:
        m = re.search(r"(\d{1,3})\s*%", _ocr(img, box))
        if m and 0 <= int(m.group(1)) <= 100:
            return int(m.group(1))
    raise RuntimeError("não consegui ler a porcentagem semanal")


def precisa(dias=7):
    try:
        with open(ARQ, encoding="utf-8") as f:
            ag = json.load(f).get("antigravity", {})
        return time.time() - ag.get("semana_lida_em", 0) > dias * 86400
    except (OSError, ValueError):
        return True


def atualizar():
    out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", PS, IMG],
                         capture_output=True, text=True, timeout=60,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
    if "OK" not in out:
        raise RuntimeError(out.strip()[-120:])
    restante = ler_print()
    with open(ARQ, encoding="utf-8") as f:
        cm = json.load(f)
    ag = cm.setdefault("antigravity", {})
    ag.update(gemini_semana_usado=100 - restante, lido=time.strftime("%d/%m %H:%M") + " (auto)",
              semana_lida_em=time.time())
    with open(ARQ, "w", encoding="utf-8") as f:
        json.dump(cm, f, ensure_ascii=False, indent=1)
    return restante


if __name__ == "__main__":
    if "--forcar" in sys.argv or precisa():
        print("Gemini semana restante:", atualizar(), "%")
    else:
        print("lida há menos de 7 dias; use --forcar")
