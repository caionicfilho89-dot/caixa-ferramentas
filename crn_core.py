# -*- coding: utf-8 -*-
"""Motor real do Estúdio de Cronometragem, Laps de Tempo & Relógio de Xadrez FIDE (estudio-cronometro)."""

import time


def format_milliseconds(total_ms: int) -> str:
    """Formata milissegundos inteiros em MM:SS.mmm."""
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    seconds = total_seconds % 60
    minutes = (total_seconds // 60) % 60
    hours = total_seconds // 3600
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"
    return f"{minutes:02d}:{seconds:02d}.{ms:03d}"


class ChessClockState:
    """Gerenciador de tempo para Relógio de Xadrez com incremento Fischer."""
    def __init__(self, initial_minutes: int = 5, increment_seconds: int = 3):
        self.initial_ms = initial_minutes * 60 * 1000
        self.inc_ms = increment_seconds * 1000
        self.white_ms = self.initial_ms
        self.black_ms = self.initial_ms
        self.active_turn = "w"  # 'w' ou 'b'
        self.last_switch_ts = None
        self.is_running = False

    def start(self):
        self.is_running = True
        self.last_switch_ts = time.perf_counter()

    def pause(self):
        self._update_current_player()
        self.is_running = False
        self.last_switch_ts = None

    def switch_turn(self):
        """Passa a vez, soma o incremento (Fischer) ao jogador que acabou de mover."""
        if not self.is_running:
            self.start()
            return

        self._update_current_player()
        if self.active_turn == "w":
            self.white_ms += self.inc_ms
            self.active_turn = "b"
        else:
            self.black_ms += self.inc_ms
            self.active_turn = "w"
        self.last_switch_ts = time.perf_counter()

    def _update_current_player(self):
        if self.is_running and self.last_switch_ts is not None:
            now = time.perf_counter()
            elapsed_ms = int((now - self.last_switch_ts) * 1000)
            if self.active_turn == "w":
                self.white_ms = max(0, self.white_ms - elapsed_ms)
            else:
                self.black_ms = max(0, self.black_ms - elapsed_ms)
            self.last_switch_ts = now

    def get_times(self) -> tuple[int, int, str]:
        self._update_current_player()
        return self.white_ms, self.black_ms, self.active_turn
