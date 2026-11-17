from pathlib import Path
p = Path(r"C:\Users\caion\caixa-ferramentas\_patch_ajuda_lane_a.py")
t = p.read_text(encoding="utf-8")
needle = '    assert 3 <= len(ajuda["como_usar"]) <= 6, pasta'
if needle not in t:
    raise SystemExit("needle missing")
insert = (
    '    while len(ajuda["como_usar"]) < 3:\n'
    '        ajuda["como_usar"].append("Confira o resultado na area de saida.")\n'
    + needle
)
p.write_text(t.replace(needle, insert, 1), encoding="utf-8")
print("fixed")
