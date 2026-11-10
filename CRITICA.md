# CRITICA.md — Grok Bot (critico/testador)
Atualizado: 2026-11-10 07:41:25 America/Sao_Paulo

## Correcoes F1 (historico)
- Q08 gabarito manual **08/05/2026** (20+20+22+22=84; 6o util mai=08). Enunciado: sem feriado, nao conta 02/01.
- 60/60 calculaveis; ambiguas fora; Q60 GiB/MiB; Q17=8/3; Q33 diarias; Q42 fracoes; Q50 preco cheio.
- Casos de teste no estilo do Caio, nao citacoes.

## Ambiguidades fora das 60
- ipva do meu carro / quanto rende a tinta -> pedir esclarecimento

## F2 — 15 chaves (historico)
`faxina-disco`, `organizador-downloads`, `print-anotador`, `area-transferencia`, `controle-garantias`, `controle-validade-remedios`, `controle-assinaturas`, `info-pc`, `calculadora-troco`, `calculadora-ipva`, `calculadora-rendimento-tinta`, `dias-uteis-pagamento`, `financas`, `kit-pdf`, `calculadora-botijao-gas`

## Historico F4 (preservado)
- **2026-11-09 ~20:37–20:38 −03** (adp_essenciais 20:36:59): **PASS=12 FAIL=48 ERRO=0 NAO_TESTADO=0 soma=60**. Q08=13/05 vs 08/05. Artefato: `grok_f4_historico_12_48.json`.
- **2026-11-09 ~20:56 −03** (adp_essenciais 20:52:16, respostas_core 20:36:42): juiz bruto 58/2; **inspecao PASS=60 FAIL=0**. Artefato: `grok_f4_reteste_2056_preservado.json`.
- **2026-11-10 ~02:40 −03** (353 adaptadores; respostas_core 21:26:40; adp_essenciais 22:29:50): juiz 58/2; **inspecao PASS=60 FAIL=0**; 0 diffs vs 20:56. Artefato: `grok_f4_reteste_0239.json`.

## F3 — visual REAL do exe 2026-11-10 (America/Sao_Paulo)
- Alvo: `C:\Users\caion\AppData\Local\Programs\CaixaFerramentas\Caixa.exe` mtime **2026-11-10 07:24:35**, tamanho 107.575.541 bytes. Cursor declara v1.5.0; **FileVersion/ProductVersion do exe estao vazios**.
- Tela real do mambo: **1920×1080** (working 1920×1032). Metodo: Start-Process como atalho, tempo ate MainWindow, PrintWindow (CopyFromScreen so e fiel com janela na frente). Prints em `C:\Users\caion\fiscal-fabrica\grok_f3\` (copia no box `/workspace/grok_f3/`).
- 1a abertura: pid 19896 as **07:30:26 −03**; janela **2175 ms**; titulo `Caixa de Ferramentas do Caio`. Tamanho inicial **1296×1244** (base 1329 > 1080 — transborda a tela). Abriu **atras** das janelas ja abertas; CopyFromScreen inicial nao mostrou a Caixa; PrintWindow sim (`01_janela_printwindow.png`).
- 2a abertura (apos a 1a sessao encerrar): pid 17152 as 07:38:55; janela em **947 ms**. Pedido MoveWindow 1366×768 resultou em **1366×902** (altura minima ~902, nao cabe em laptop 768).
- Foco ao abrir: **campo de busca SEM foco de teclado** (`HasKeyboardFocus=False`).
- App fechado no fim: todos os processos Caixa desta sessao (principal + ferramentas filhas). residual=0.

### O que funciona
- Abre rapido (~1–2 s), tema escuro legivel, textos da Hoje em portugues (Bom dia, terca 10/11, acentos na maior parte).
- Sensores de **AGORA NO SEU PC** parecem dados reais, nao inventados: Disco C 206,2 GB livres (54% de 446 GB) + aviso da pasta Temp; Downloads 3 arquivos soltos / instaladores velhos; 120 prints (ultima 09/11 20:20); Pudim IPTV `Uma Familia da Pesada`. Ver `01_janela_printwindow.png`.
- Os **15 atalhos F2** estao todos na Hoje (chaves batem com o historico F2).
- Barra calcula certo no motor/UIA (ver tabela). Esc limpa a busca e some o resultado (campo volta ao placeholder). `05_apos_esc_pw.png`.
- Negativos: `ipva do meu carro` pede valor e estado; typo `praa` ainda acerta 26,50; `dividir 10 por 0` mostra `Nao e possivel dividir por zero` ja no debounce, sem Enter (`05_N03_sem_enter_pw.png`). Reproducao isolada de div/0 **nao** derrubou o app.
- Abrir **Info do PC** funcionou: janela propria, dados reais do MAMBO (Win 11 Pro, usuario caion), aviso de so leitura/offline. Print: `05_tool_infopc_win1_pw.png` (screenshot cedo, ainda `Lendo... 1 de 9`).
- **Calculadora de Troco** abre e calcula (defaults 50,00−37,80=12,20). Print: `05_tool_troco_win3_pw.png`.
- Sem travamento visivel na 2a sessao (Responding=True).

### O que e ruim (com evidencia)
1. **Fonte da resposta na barra some ponto e virgula.** UIA de Q10 e `1.030,30`; o pixel da tela e `1 030 30`. Q56: UIA `gorjeta 37,20; total 285,20`; tela `gorjeta 37 20 · total 285 20`. Zoom 5x: `/workspace/grok_f3/crop_Q10_valor_x5.png`, `crop_Q56_valor_x5.png`. Na ferramenta Finanças os mesmos `R$ 3.663,33` aparecem corretos — o bug e a fonte do card da barra, nao o motor.
2. **Layout da Hoje quebra o que o Caio mais precisa.** Em 1280×1000 / 1366×902 a faixa `AGORA NO SEU PC` tem viewport minusculo (~60–158 px) com scrollbar fina: em 1366 so o titulo Disco/Downloads aparece, **sem os GB**. Prints e IPTV somem. Ver `03_hoje_1366x768_pw.png` vs `01_janela_printwindow.png`. Janela padrao 1244 px de altura transborda 1080p; altura minima 902 transborda 768p.
3. **Enter na busca abre ferramenta**, mesmo com a resposta ja na lista (debounce). Status `Abrindo Financas...` em Q01/Q10/Q56 e tambem em `dividir 10 por 0` (abriu `Financas Pessoais` sem o usuario pedir). Um clique em Troco abriu **duas** janelas `Calculadora de Troco` (pids 19176 e 22648). Clique UIA em Garantias abriu `Organizador de Pastas` (pid 1972, 07:39:09).
4. **Card de resultado e estreito e esconde a conta.** So titulo + valor; o detalhe (`20% de 350,00 = 70`) esta no UIA mas nao no card. Lista de extras tem scrollbar minuscula. Q10 traz lixo: `conversor-unidades` `1 mes = 1 mes`; Q56 2a carta despeja `gorjeta: 37.199999999999996`.
5. **Aba Todas (topo) nao trocou a tela** — depois do clique a Hoje (Bom dia + sensores + atalhos) continuou. `05_aba_todas_pw.png`. Botao `Todas as ferramentas` e fantasma, contraste baixo. Busca nao nasce com foco. Janela abre atras das outras.
- Troco interno: resultado `R$ 12.20` com ponto (deveria 12,20); texto `Sugestao de pecas` sem acento. A 1a sessao (pid 19896) encerrou apos a serie de Enter que dispara ferramentas; **nao afirmo crash de div/0** (nao reproduziu isolado).

### Tabela GUI — 8 perguntas + 3 negativas
| ID | Input (resumo) | Esperado | UIA/resposta | Visual | Status |
|---|---|---|---|---|---|
| Q01 | quanto e 20% de 350? | 70 | 70 | 70 ok | PASS valor |
| Q05 | regra de 3, 5 pacotes 37,50 -> 8 | 60,00 | 60,00 | card ok, virgula a confirmar na fonte | PASS valor |
| Q08 | 90 dias uteis sem feriado | 08/05/2026 | 08/05/2026 | data ok | PASS |
| Q10 | compostos 1000 a 1% 3 meses | 1.030,30 | 1.030,30 | **1 030 30** (`.` e `,` ausentes) | PASS motor / FAIL visual |
| Q56 | gorjeta 15% conta 248,00 | 37,20 e 285,20 | gorjeta 37,20; total 285,20 | **virgulas ausentes**; 2a carta com float cru | PASS motor / FAIL visual |
| Q57 | 3 camisetas 49,90 + frete 19,90 | 169,60 | 169,60 | (mesmo risco de fonte) | PASS valor |
| Q60 | 16 GiB / 4 MiB | 4.096 | 4.096 | (risco do `.` milhar) | PASS valor |
| Q02 | troco 100 pra 73,50 | 26,50 | 26,50 | (risco da virgula) | PASS valor |
| N01 | ipva do meu carro | pedir dado | pede valor e estado | ok, mas Enter tentou abrir IPVA | PASS pedido |
| N02 | troco de 100 praa 73,50 (typo) | 26,50 ou esclarecer | 26,50 | tolerou typo | PASS |
| N03 | dividir 10 por 0 | nao dividir por zero | Nao e possivel dividir por zero | ok; Enter ainda abriu Financas | PASS mensagem |

- Contagem das 8 do gabarito na GUI: **8/8 valor correto no motor/UIA**; **pelo menos 2/8 (Q10, Q56) com falha visual grave de pontuacao**. Negativas 3/3 mensagem adequada. Fallback 'Abrir ferramenta' so como botao do card, nao no lugar da resposta.

### Top 5 correcoes (uso do Caio)
1. **[ALTA][Cursor UI]** Trocar a fonte do valor na barra para uma que desenhe `.` e `,` (e R$). Sem isso o Caio le 1030,30 como 1 030 30.
2. **[ALTA][Cursor UI]** Layout da Hoje: sensores com altura de verdade em 1366×768 e 1920×1080; janela padrao que caiba na tela (max 1080 e 768); nao esconder GB livres numa faixa de 60 px.
3. **[ALTA][Cursor UI]** Enter na busca NAO deve abrir ferramenta automaticamente (a resposta ja aparece no debounce). Evitar janela duplicada e abertura da ferramenta errada.
4. **[MEDIA][Cursor UI + Antigravity motor]** Card deve mostrar o detalhe da conta; nao listar dump de float nem `1 mes = 1 mes`.
5. **[MEDIA][Cursor UI]** Aba Todas tem que trocar a tela; foco inicial na busca; janela na frente; botao `Todas as ferramentas` com contraste; acentos em `Sugestao de pecas`; virgula BR no resultado do Troco (`12,20` nao `12.20`).

### Pedidos
- Cursor: itens 1–3 e 5 (UI/exe 07:24). Inclui FileVersion vazio no exe que eles geraram.
- Antigravity: lixo na 2a/3a carta (Q10 conversor tautologico; Q56 floats).
- Claude: sem pedido novo de integracao alem do que o Cursor ja empacotou; F3 do exe 07:24 esta feito.

### Prints representativos
- `C:\Users\caion\fiscal-fabrica\grok_f3\01_janela_printwindow.png` (Hoje completa, 4 sensores) — box `/workspace/grok_f3/01_janela_printwindow.png`
- `...\03_hoje_1366x768_pw.png` (sensores cortados) — box `/workspace/grok_f3/03_hoje_1366x768_pw.png`
- `...\04_busca_Q10_pw.png` + zoom `crop_Q10_valor_x5.png` (1 030 30) — box `/workspace/grok_f3/`
- `...\05_N03_apos_enter_pw.png` (div/0 ok + Abrindo Financas)

### Cobertura F3
- Coberto: abertura cronometrada, Hoje, barra 8+3 perguntas com print+UIA, Esc, Enter, 1366 vs 1080, 3 ferramentas (Info, Troco, e clique Garantias), aba Todas, portugues, foco, encerramento.
- Nao coberto de verdade: atalho global Ctrl+Espaco; `Abrir no boot` / `Menu Iniciar` (nao cliquei — evitei mudar startup do Windows); trocar resolucao do SO (so redimensionei a janela); leitura completa do Info do PC (print ainda em Lendo 1/9).
