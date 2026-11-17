"""Planejador de Sessao de Foco — logica de blocos deep work (nao e pomodoro generico).

Distribui tempo disponivel em blocos de foco com pausas estrategicas, aloca tarefas
por estimativa e gera agenda textual com aproveitamento.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

_LINHA_TAREFA = re.compile(
    r"^(?P<nome>.+?)(?:\s*[\(\[]?\s*(?P<min>\d+)\s*(?:min|m)?\s*[\)\]]?)?\s*$",
    re.IGNORECASE,
)


def parse_hora(txt: str) -> Tuple[int, int]:
    """'HH:MM' ou 'H:MM' -> (hora, minuto)."""
    s = (txt or "09:00").strip()
    if not s:
        s = "09:00"
    parts = s.split(":")
    if len(parts) != 2:
        raise ValueError("horario invalido; use HH:MM")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("horario fora do intervalo")
    return h, m


def fmt_hora(total_min: int) -> str:
    """Minutos desde meia-noite (pode passar de 24h no mesmo dia logico)."""
    h = (total_min // 60) % 24
    m = total_min % 60
    return f"{h:02d}:{m:02d}"


def somar_minutos(hora_base_min: int, offset: int) -> str:
    return fmt_hora(hora_base_min + offset)


@dataclass
class Tarefa:
    nome: str
    minutos_estimados: Optional[int] = None


@dataclass
class EventoAgenda:
    tipo: str  # "foco" | "pausa"
    inicio: str
    fim: str
    duracao_min: int
    rotulo: str = ""


@dataclass
class PlanoFoco:
    blocos_foco: int
    minutos_foco_total: int
    minutos_pausa_total: int
    minutos_sobra: int
    aproveitamento_pct: float
    agenda: List[EventoAgenda] = field(default_factory=list)
    tarefas_por_bloco: List[List[str]] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    resumo_linhas: List[str] = field(default_factory=list)


def parse_tarefas(texto: str) -> List[Tarefa]:
    out: List[Tarefa] = []
    for raw in (texto or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _LINHA_TAREFA.match(line)
        if not m:
            out.append(Tarefa(nome=line))
            continue
        nome = m.group("nome").strip().rstrip("-–—:").strip()
        mins = m.group("min")
        est = int(mins) if mins else None
        if nome:
            out.append(Tarefa(nome=nome, minutos_estimados=est))
    return out


def _contar_blocos(minutos_totais: int, bloco_foco: int, pausa: int) -> int:
    if minutos_totais <= 0 or bloco_foco <= 0:
        return 0
    if pausa < 0:
        raise ValueError("pausa nao pode ser negativa")
    # n*bloco + (n-1)*pausa <= total
    ciclo = bloco_foco + pausa
    if ciclo <= 0:
        return min(1, minutos_totais // bloco_foco)
    n = (minutos_totais + pausa) // ciclo
    while n > 0 and n * bloco_foco + (n - 1) * pausa > minutos_totais:
        n -= 1
    # pelo menos um bloco se couber o foco sozinho
    if n == 0 and minutos_totais >= bloco_foco:
        n = 1
    return int(n)


def _alocar_tarefas(
    tarefas: List[Tarefa], n_blocos: int, minutos_por_bloco: int
) -> Tuple[List[List[str]], List[str]]:
    avisos: List[str] = []
    slots: List[List[str]] = [[] for _ in range(max(n_blocos, 0))]
    if n_blocos <= 0:
        return slots, avisos

    restante_por_bloco = [minutos_por_bloco] * n_blocos
    bloco_atual = 0

    for t in tarefas:
        need = t.minutos_estimados or min(minutos_por_bloco, 25)
        if need > minutos_por_bloco:
            avisos.append(
                f'"{t.nome}" ({need} min) excede um bloco; sera fatiada em varios blocos.'
            )
        left = need
        while left > 0 and bloco_atual < n_blocos:
            cap = restante_por_bloco[bloco_atual]
            if cap <= 0:
                bloco_atual += 1
                continue
            usar = min(cap, left)
            if usar == need or left == need:
                label = t.nome if usar >= need else f"{t.nome} ({usar}/{need} min)"
            else:
                label = f"{t.nome} (cont. {need - left + usar}/{need} min)"
            slots[bloco_atual].append(label)
            restante_por_bloco[bloco_atual] -= usar
            left -= usar
            if restante_por_bloco[bloco_atual] <= 0:
                bloco_atual += 1
        if left > 0:
            avisos.append(f'Sobra de "{t.nome}": {left} min sem bloco disponivel.')

    return slots, avisos


def montar_plano(
    minutos_totais: int,
    bloco_foco_min: int,
    pausa_min: int,
    texto_tarefas: str = "",
    horario_inicio: str = "09:00",
) -> PlanoFoco:
    """
    Monta plano de deep work: quantos blocos cabem, agenda HH:MM e aproveitamento.

    Parametros
    ----------
    minutos_totais : janela total disponivel (ex. 180)
    bloco_foco_min : duracao de cada bloco de foco profundo
    pausa_min : pausa entre blocos (recuperacao, nao pomodoro fixo 5 min)
    texto_tarefas : uma tarefa por linha; estimativa opcional no fim (ex. "Relatorio 45")
    horario_inicio : inicio da agenda (HH:MM)
    """
    if minutos_totais < 0:
        raise ValueError("minutos totais invalidos")
    if bloco_foco_min <= 0:
        raise ValueError("bloco de foco deve ser > 0")

    h0, m0 = parse_hora(horario_inicio)
    base_min = h0 * 60 + m0

    n = _contar_blocos(minutos_totais, bloco_foco_min, pausa_min)
    min_foco = n * bloco_foco_min
    min_pausa = max(0, n - 1) * pausa_min if pausa_min > 0 else 0
    min_usado = min_foco + min_pausa
    sobra = max(0, minutos_totais - min_usado)

    agenda: List[EventoAgenda] = []
    cursor = 0
    for i in range(n):
        ini = somar_minutos(base_min, cursor)
        cursor += bloco_foco_min
        fim = somar_minutos(base_min, cursor)
        agenda.append(
            EventoAgenda(
                tipo="foco",
                inicio=ini,
                fim=fim,
                duracao_min=bloco_foco_min,
                rotulo=f"Bloco {i + 1} — foco profundo",
            )
        )
        if i < n - 1 and pausa_min > 0:
            ini_p = somar_minutos(base_min, cursor)
            cursor += pausa_min
            fim_p = somar_minutos(base_min, cursor)
            agenda.append(
                EventoAgenda(
                    tipo="pausa",
                    inicio=ini_p,
                    fim=fim_p,
                    duracao_min=pausa_min,
                    rotulo="Pausa ativa / descompressao",
                )
            )

    tarefas = parse_tarefas(texto_tarefas)
    por_bloco, avisos = _alocar_tarefas(tarefas, n, bloco_foco_min)
    for i, ev in enumerate(agenda):
        if ev.tipo != "foco":
            continue
        idx = sum(1 for e in agenda[:i] if e.tipo == "foco") - 1
        if 0 <= idx < len(por_bloco) and por_bloco[idx]:
            ev.rotulo += ": " + "; ".join(por_bloco[idx])

    aprov = (min_foco / min_usado * 100.0) if min_usado > 0 else 0.0

    resumo = [
        f"Blocos de foco     : {n}",
        f"Tempo em foco      : {min_foco} min ({min_foco / 60:.1f} h)",
        f"Tempo em pausas    : {min_pausa} min",
        f"Tempo estruturado  : {min_usado} min (sobra {sobra} min na janela)",
        f"Aproveitamento     : {aprov:.1f}% (foco / tempo com pausas)",
        f"Ciclo              : {bloco_foco_min} min foco + {pausa_min} min pausa",
    ]
    if tarefas:
        est_total = sum(t.minutos_estimados or 0 for t in tarefas)
        sem_est = sum(1 for t in tarefas if t.minutos_estimados is None)
        resumo.append(
            f"Tarefas            : {len(tarefas)} ({est_total} min estimados"
            + (f", {sem_est} sem estimativa)" if sem_est else ")")
        )

    return PlanoFoco(
        blocos_foco=n,
        minutos_foco_total=min_foco,
        minutos_pausa_total=min_pausa,
        minutos_sobra=sobra,
        aproveitamento_pct=round(aprov, 1),
        agenda=agenda,
        tarefas_por_bloco=por_bloco,
        avisos=avisos,
        resumo_linhas=resumo,
    )


def formatar_agenda(plano: PlanoFoco) -> str:
    lines = list(plano.resumo_linhas)
    lines.append("")
    lines.append("--- Agenda ---")
    for ev in plano.agenda:
        tag = "FOCO" if ev.tipo == "foco" else "PAUSA"
        lines.append(f"{ev.inicio}-{ev.fim}  [{tag:5}]  {ev.rotulo} ({ev.duracao_min} min)")
    if plano.avisos:
        lines.append("")
        lines.append("--- Avisos ---")
        lines.extend(plano.avisos)
    return "\n".join(lines)
