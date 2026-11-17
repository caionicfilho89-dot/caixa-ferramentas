# sync_agentes.ps1 — Fecha e reabre os apps de agente pra pegarem as regras novas.
#
# Por que: os agents (Antigravity, Cursor, Grok Bot) leem AGENTS_PROTOCOL.md / CLAUDE.md /
# CATALOGO.md quando abrem. Depois de mexer nessas instrucoes, reiniciar faz eles pegarem
# as atitudes corretas (ex.: consultar o catalogo antes de inventar ferramenta).
#
# O que faz, em ordem:
#   1) Regenera CATALOGO.md + catalogo.json a partir do codigo (python catalogo.py).
#   2) Fecha cada app de agente.
#   3) Reabre: os editores ja apontando pra pasta da Caixa (releem os .md); o Grok Bot normal.
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File sync_agentes.ps1          # fecha educado (seguro)
#   powershell -ExecutionPolicy Bypass -File sync_agentes.ps1 -Force   # mata na marra
#   powershell -ExecutionPolicy Bypass -File sync_agentes.ps1 -SemReabrir   # so fecha
#
param(
    [switch]$Force,        # mata o processo na marra (pode perder trabalho nao salvo)
    [switch]$SemReabrir,   # so fecha, nao reabre
    [int]$EsperaSeg = 8    # quanto espera o fechamento educado antes de desistir/forcar
)

$ErrorActionPreference = "SilentlyContinue"
$RAIZ   = "C:\Users\caion\caixa-ferramentas"
$PYTHON = "C:\Python313\python.exe"

# --- Apps de agente a reiniciar. Edite aqui pra incluir/excluir. -------------
# Processo | caminho do .exe | abrir na pasta da Caixa? (editores sim; chat nao)
$APPS = @(
    @{ Nome = "Antigravity"; Exe = "C:\Users\caion\AppData\Local\Programs\antigravity\Antigravity.exe"; AbrePasta = $true  },
    @{ Nome = "Cursor";      Exe = "C:\Users\caion\AppData\Local\Programs\cursor\Cursor.exe";           AbrePasta = $true  },
    @{ Nome = "Grok Bot";    Exe = "C:\Program Files\Grok Bot\Grok Bot.exe";                            AbrePasta = $false }
)

function Linha($txt) { Write-Host $txt }

Linha ""
Linha "=== SYNC AGENTES — Caixa de Ferramentas ==="

# 1) Catalogo sempre atual antes de reabrir -----------------------------------
Linha ""
Linha ">> Regenerando o catalogo (CATALOGO.md + catalogo.json)..."
Push-Location $RAIZ
$env:PYTHONIOENCODING = "utf-8"
& $PYTHON "$RAIZ\catalogo.py"
Pop-Location

# Guarda quais estavam abertos, pra so reabrir esses ---------------------------
$paraReabrir = @()

foreach ($app in $APPS) {
    $nome = $app.Nome
    $procs = Get-Process -Name $nome -ErrorAction SilentlyContinue
    if (-not $procs) {
        Linha ""
        Linha ">> $nome : nao estava aberto — pulando."
        continue
    }

    $paraReabrir += $app
    Linha ""
    Linha (">> $nome : {0} processo(s) aberto(s)." -f $procs.Count)

    if ($Force) {
        Linha "   forcando fechamento (-Force)..."
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    else {
        # fechamento educado: pede pra janela principal fechar
        foreach ($p in $procs) {
            if ($p.MainWindowHandle -ne 0) { [void]$p.CloseMainWindow() }
        }
        # espera o app encerrar sozinho
        $fim = (Get-Date).AddSeconds($EsperaSeg)
        while ((Get-Date) -lt $fim -and (Get-Process -Name $nome -ErrorAction SilentlyContinue)) {
            Start-Sleep -Milliseconds 400
        }
        $sobra = Get-Process -Name $nome -ErrorAction SilentlyContinue
        if ($sobra) {
            Linha "   ! $nome ainda aberto (provavel aba nao salva pedindo confirmacao)."
            Linha "     Salve/feche na mao, ou rode de novo com -Force. NAO vou matar."
            # tira da lista de reabrir pra nao duplicar janela
            $paraReabrir = $paraReabrir | Where-Object { $_.Nome -ne $nome }
        }
        else {
            Linha "   fechado."
        }
    }
}

if ($SemReabrir) {
    Linha ""
    Linha "=== Pronto (so fechei, -SemReabrir). ==="
    return
}

# 2) Reabrir -------------------------------------------------------------------
Start-Sleep -Milliseconds 800
foreach ($app in $paraReabrir) {
    $nome = $app.Nome
    $exe  = $app.Exe
    if (-not (Test-Path $exe)) {
        Linha ""
        Linha "   ! $nome : nao achei o .exe em '$exe' — reabra na mao."
        continue
    }
    Linha ""
    if ($app.AbrePasta) {
        Linha ">> Reabrindo $nome na pasta da Caixa..."
        Start-Process -FilePath $exe -ArgumentList "`"$RAIZ`""
    }
    else {
        Linha ">> Reabrindo $nome..."
        Start-Process -FilePath $exe
    }
}

Linha ""
Linha "=== Pronto. Agents reiniciados — vao reler o protocolo + catalogo. ==="
Linha ""
