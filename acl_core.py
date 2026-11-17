# -*- coding: utf-8 -*-
"""Motor do Inspetor ACL NTFS (sem UI).

Le ACLs via Get-Acl / icacls, resume dono e regras, e pode aplicar heranca
basica com icacls (reset/herdar) sob confirmacao do usuario na GUI.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass


def _ensure_windows():
    if os.name != "nt":
        raise OSError("ACL NTFS so no Windows")


def _ps(cmd: str) -> str:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        raise OSError((r.stderr or r.stdout or "falha PowerShell").strip())
    return r.stdout


def ler_acl(path: str) -> dict:
    """Retorna dono + lista de Access rules."""
    _ensure_windows()
    path = os.path.abspath(path)
    if not os.path.lexists(path):
        raise FileNotFoundError(path)
    ps_path = path.replace("'", "''")
    script = f"""
$p = '{ps_path}'
$a = Get-Acl -LiteralPath $p
$rules = @()
foreach ($r in $a.Access) {{
  $rules += [PSCustomObject]@{{
    Identity = $r.IdentityReference.Value
    Rights = $r.FileSystemRights.ToString()
    Type = $r.AccessControlType.ToString()
    Inherited = [bool]$r.IsInherited
    Propagation = $r.PropagationFlags.ToString()
    Inheritance = $r.InheritanceFlags.ToString()
  }}
}}
[PSCustomObject]@{{
  Path = $p
  Owner = $a.Owner
  Group = $a.Group
  AreAccessRulesProtected = [bool]$a.AreAccessRulesProtected
  Rules = $rules
}} | ConvertTo-Json -Depth 4 -Compress
"""
    raw = _ps(script).strip()
    data = json.loads(raw)
    rules = data.get("Rules") or []
    if isinstance(rules, dict):
        rules = [rules]
    return {
        "path": data.get("Path", path),
        "dono": data.get("Owner"),
        "grupo": data.get("Group"),
        "protegido": bool(data.get("AreAccessRulesProtected")),
        "regras": [
            {
                "identidade": r.get("Identity"),
                "direitos": r.get("Rights"),
                "tipo": r.get("Type"),
                "herdada": bool(r.get("Inherited")),
                "propagacao": r.get("Propagation"),
                "heranca": r.get("Inheritance"),
            }
            for r in rules
        ],
    }


def icacls_texto(path: str) -> str:
    _ensure_windows()
    path = os.path.abspath(path)
    r = subprocess.run(
        ["icacls", path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        raise OSError((r.stderr or r.stdout or "icacls falhou").strip())
    return (r.stdout or "").strip()


def format_acl(info: dict) -> str:
    lines = [
        f"Caminho : {info['path']}",
        f"Dono    : {info['dono']}",
        f"Grupo   : {info['grupo']}",
        f"Herdado bloqueado (protegido): {'sim' if info['protegido'] else 'nao'}",
        f"Regras  : {len(info['regras'])}",
        "",
    ]
    for i, r in enumerate(info["regras"], 1):
        herd = "herdada" if r["herdada"] else "explicita"
        lines.append(f"{i}. [{r['tipo']}] {r['identidade']}")
        lines.append(f"   direitos: {r['direitos']}")
        lines.append(f"   {herd} | heranca={r['heranca']} | prop={r['propagacao']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def resetar_heranca(path: str, remover_explicitas: bool = True) -> str:
    """icacls /reset — reaplica heranca do pai."""
    _ensure_windows()
    path = os.path.abspath(path)
    args = ["icacls", path, "/reset"]
    if not remover_explicitas:
        # /reset ja limpa; manter so documentado
        pass
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        raise OSError(out.strip() or "icacls /reset falhou")
    return out.strip()


def conceder_leitura(path: str, usuario: str) -> str:
    """Concede (OI)(CI)R ao usuario/grupo (icacls /grant)."""
    _ensure_windows()
    path = os.path.abspath(path)
    if not usuario or any(c in usuario for c in '|"&<>'):
        raise ValueError("usuario invalido")
    grant = f"{usuario}:(R)"
    r = subprocess.run(
        ["icacls", path, "/grant", grant],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        raise OSError(out.strip() or "icacls /grant falhou")
    return out.strip()


def resumir_por_identidade(info: dict) -> dict[str, list[str]]:
    """Agrupa direitos por identidade."""
    m: dict[str, list[str]] = {}
    for r in info["regras"]:
        m.setdefault(r["identidade"], []).append(f"{r['tipo']}:{r['direitos']}")
    return m
