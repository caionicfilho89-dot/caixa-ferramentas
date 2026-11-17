# -*- coding: utf-8 -*-
"""
spl_core.py — Splines cúbicos naturais e Catmull–Rom.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple


def natural_cubic_spline(xs: Sequence[float], ys: Sequence[float]) -> Dict[str, Any]:
    """
    Coeficientes por segmento i: Si(x) = a_i + b_i dx + c_i dx² + d_i dx³
    com dx = x - x_i. Condições de extremo: S''=0 (natural).
    """
    pts = sorted(zip(xs, ys), key=lambda t: t[0])
    xs2 = [p[0] for p in pts]
    ys2 = [p[1] for p in pts]
    n = len(xs2) - 1
    if n < 1:
        raise ValueError("Precisa de pelo menos 2 pontos.")
    for i in range(1, len(xs2)):
        if xs2[i] <= xs2[i - 1]:
            raise ValueError("xs devem ser estritamente crescentes.")

    h = [xs2[i + 1] - xs2[i] for i in range(n)]
    # sistema tridiagonal para m_i = S''(x_i)
    a = [0.0] * (n + 1)
    b = [0.0] * (n + 1)
    c = [0.0] * (n + 1)
    d = [0.0] * (n + 1)
    b[0] = 1.0
    d[0] = 0.0
    b[n] = 1.0
    d[n] = 0.0
    for i in range(1, n):
        a[i] = h[i - 1]
        b[i] = 2.0 * (h[i - 1] + h[i])
        c[i] = h[i]
        d[i] = 6.0 * ((ys2[i + 1] - ys2[i]) / h[i] - (ys2[i] - ys2[i - 1]) / h[i - 1])

    m = _thomas(a, b, c, d)

    segs = []
    for i in range(n):
        ai = ys2[i]
        bi = (ys2[i + 1] - ys2[i]) / h[i] - h[i] * (2 * m[i] + m[i + 1]) / 6.0
        ci = m[i] / 2.0
        di = (m[i + 1] - m[i]) / (6.0 * h[i])
        segs.append({"x0": xs2[i], "x1": xs2[i + 1], "a": ai, "b": bi, "c": ci, "d": di})

    return {"xs": xs2, "ys": ys2, "segments": segs, "second_deriv": m}


def evaluate_spline(spline: Dict[str, Any], x: float) -> float:
    segs = spline["segments"]
    if x <= segs[0]["x0"]:
        s = segs[0]
    elif x >= segs[-1]["x1"]:
        s = segs[-1]
    else:
        s = segs[0]
        for cand in segs:
            if cand["x0"] <= x <= cand["x1"]:
                s = cand
                break
    dx = x - s["x0"]
    return s["a"] + s["b"] * dx + s["c"] * dx * dx + s["d"] * dx * dx * dx


def sample_spline(spline: Dict[str, Any], n: int = 200) -> List[Tuple[float, float]]:
    xs = spline["xs"]
    if n < 2:
        n = 2
    out = []
    x0, x1 = xs[0], xs[-1]
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        out.append((x, evaluate_spline(spline, x)))
    return out


def catmull_rom(points: Sequence[Tuple[float, float]], n_per_seg: int = 20, tau: float = 0.5) -> List[Tuple[float, float]]:
    """
    Catmull–Rom centrípeta/chordal simplificada (tau=0.5 → centripetal-ish tension).
    points: lista (x,y) na ordem do parâmetro.
    """
    pts = list(points)
    if len(pts) < 2:
        raise ValueError("Precisa de ≥ 2 pontos.")
    # duplica extremos
    p = [pts[0]] + pts + [pts[-1]]
    curve: List[Tuple[float, float]] = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for j in range(n_per_seg):
            t = j / n_per_seg
            curve.append(_cr_point(p0, p1, p2, p3, t, tau))
    curve.append(pts[-1])
    return curve


def _cr_point(p0, p1, p2, p3, t, tau):
    t2 = t * t
    t3 = t2 * t
    # forma com tensão tau (Cardinal spline; tau=0.5 ≈ Catmull-Rom)
    a0 = -tau * t3 + 2 * tau * t2 - tau * t
    a1 = (2 - tau) * t3 + (tau - 3) * t2 + 1
    a2 = (tau - 2) * t3 + (3 - 2 * tau) * t2 + tau * t
    a3 = tau * t3 - tau * t2
    x = a0 * p0[0] + a1 * p1[0] + a2 * p2[0] + a3 * p3[0]
    y = a0 * p0[1] + a1 * p1[1] + a2 * p2[1] + a3 * p3[1]
    return (x, y)


def parse_xy_table(text: str) -> Tuple[List[float], List[float]]:
    xs, ys = [], []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.replace(";", " ").replace(",", " ").split()
        if len(parts) < 2:
            continue
        xs.append(float(parts[0].replace(",", ".")))
        ys.append(float(parts[1].replace(",", ".")))
    return xs, ys


def _thomas(a, b, c, d) -> List[float]:
    """Resolve tridiagonal Ax=d (a sub, b diag, c super)."""
    n = len(d)
    cp = [0.0] * n
    dp = [0.0] * n
    cp[0] = c[0] / b[0]
    dp[0] = d[0] / b[0]
    for i in range(1, n):
        denom = b[i] - a[i] * cp[i - 1]
        cp[i] = 0.0 if i == n - 1 else c[i] / denom
        dp[i] = (d[i] - a[i] * dp[i - 1]) / denom
    x = [0.0] * n
    x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x
