@echo off
rem Radar diario de tendencias (Agendador: "Caixa - Radar de Tendencias", 08:00)
cd /d C:\Users\caion\caixa-ferramentas
C:\Python313\python.exe tendencias.py > tendencias.log 2>&1
for %%A in (grokbuild cursor antigravity) do C:\Python313\python.exe painel.py claude --pedir %%A "TENDENCIA_DO_DIA.md nova (radar 08:00). Fila acabou? Faca ela - regras no RUMO.md" >> tendencias.log 2>&1
