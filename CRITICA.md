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

---

## T317 — Avaliação Crítica & Paridade [kit-pdf] (2026-11-16)
- **Alvo:** `C:\Users\caion\kit-pdf` (substituto de PDF24 / CutePDF / Foxit / SumatraPDF / Acrobat Reader).
- **Status da Paridade:**
  - **Tinha:** Leitor PDF nativo com QPdfView e QPdfDocument, juntar (merge), separar/extrair (split), girar (rotate), comprimir (compressão sem perda + downscale JPEG via pikepdf), imagens↔PDF, extrair texto em TXT, proteção/desbloqueio por senha AES, marca d'água diagonal configurável, numeração de páginas com formatação e metadados.
  - **Fiz agora:**
    1. *Excluir Páginas:* Operação `delete_pages` e ferramenta `op_delete` permitindo excluir páginas indesejadas (ex.: `2, 4-6`) mantendo as demais sem forçar o usuário a calcular intervalos reversos na mão (paridade direta PDF24).
    2. *Extração de Imagens Embutidas Nativas:* Operação `extract_embedded_images` e ferramenta `op_extract_img` que extrai imagens originais incorporadas diretamente do stream do PDF em alta fidelidade sem rasterizar a página inteira em bitmap.
    3. *Navegação e Atalhos Profissionais no Leitor (Sumatra/Acrobat):* Atalho `Ctrl+F` para focar imediatamente na busca, `Home` (primeira página), `End` (última página), `PageUp`/`PageDown` (navegação sequencial), atalhos de zoom `Ctrl++`, `Ctrl+=`, `Ctrl+-`, `Ctrl+0` e botão/método `📸 Exportar Página` para salvar a página atual como imagem PNG/JPG em alta resolução.
    4. *Ajuste de Interface:* Janela redimensionada para 660×780 para comportar confortavelmente as 14 ferramentas em grid 2×7, além de menus de contexto no clique com botão direito.
  - **Falta:** OCR de texto em PDFs escaneados dentro do próprio kit-pdf (já coberto pelo `extrator-texto` e `scanner-documentos`).
  - **Testes Realizados:** 8 suítes completas em `test_pdfops.py` cobrindo exclusão de páginas, extração de imagens embutidas, marca d'água, numeração, rotação em memória, busca textual, atalhos do leitor e exportação de páginas, passando 100%. Execução via `CAIXA_TESTE=1` com saída limpa (código 0) e residual 0. Validação de staging com 1610 módulos e 767 ferramentas com selftest `OK: 767`.

---

## T318 — Avaliação Crítica & Paridade [conversor-av] (2026-11-16)
- **Alvo:** `C:\Users\caion\conversor-av` (substituto do HandBrake / Format Factory).
- **Status da Paridade:**
  - **Tinha:** Conversão em lote com tabela detalhada estilo HandBrake, presets prontos para WhatsApp, Discord, YouTube 1080p, Redes Sociais, H.265/HEVC, 4K UHD e extração de áudio MP3/Original sem perda, corte de trecho por tempo (início/fim), leitura assíncrona de metadados via ffprobe e barra dupla de progresso real em tempo real (`-progress pipe:1`).
  - **Fiz agora:**
    1. *Rotação de Vídeo (Rotation & Flip):* Suporte completo a girar vídeos gravados invertidos ou em orientação incorreta de celular (90° horário com `transpose=1`, 180° invertido com `transpose=1,transpose=1` e 270° anti-horário com `transpose=2`), combinando filtros perfeitamente com redimensionamento de escala.
    2. *Ajuste de Volume / Ganho de Áudio:* Controle de ganho sonoro via filtro `-af volume=X` configurável de 50% até 200% (amplificação de aulas/áudios baixos ou atenuação).
    3. *Formato e Preset de GIF Animado:* Formato `"GIF Animado"` e preset `"🎞️ GIF Animado (Clipe 15fps)"` com filtro de 15 fps e redimensionamento Lanczos para geração de clipes leves e memes sem som.
    4. *Controles na Interface:* Comboboxes dedicados de "Girar vídeo" e "Volume do áudio" integrados ao painel e repassados de forma transparente à thread de lote `ConvTask`.
  - **Falta:** Queima de legendas externas `.srt` sobrepostas ao vídeo durante a recodificação (já existe no `editor-legendas` e reprodução no `player-video`).
  - **Testes Realizados:** 12 testes automatizados em `test_avconv.py` cobrindo conversão HMS, anti-colisão de nomes de saída, comandos de rotação (90°/180°/270°), ganho de volume, GIF animado, presets HandBrake, fallback de media info, tabela em lote e smoke test offscreen de GUI com `CAIXA_TESTE=1` exit 0 e residual 0. Validação de staging com 1612 módulos e 768 ferramentas com selftest `OK: 768`.

---

## T320 — Avaliação Crítica & Paridade [print-anotador] (2026-11-16)
- **Alvo:** `C:\Users\caion\print-anotador` (substituto de Greenshot / ShareX / Captura e Esboço do Windows).
- **Status da Paridade:**
  - **Tinha:** Captura de tela inteira multimonitor (`mss`), captura de área interativa com lupa e cruz de precisão, captura com atraso (3s), captura de janela ativa do Windows (`GetForegroundWindow` / `GetWindowRect`), editor completo de anotações com ferramentas: retângulo vazado, elipse, seta direcional calculada, linha, caneta livre, texto com ou sem caixa de fundo, marcador de passos sequencial (1, 2, 3…), marca-texto semitransparente, tarja sólida de censura, borrão/pixelado (mosaico estilo ShareX/Lightshot), balão de chamada com ponta direcional, recorte (crop), aplicação de moldura com sombra suave (Drop Shadow profissional), atalhos de teclado completos, cópia e salvamento num clique com feedback visual.
  - **Fiz agora:**
    1. *Carimbos Visuais Rápidos (Stamps estilo ShareX/Greenshot):* Ferramenta `stamp` com seleção de badges populares (`✅ OK`, `❌ ERRO`, `⚠️ ATENÇÃO`, `💡 DICA`, `⭐ DESTAQUE`, `❓ DÚVIDA`) renderizados com visual moderno arredondado, borda de destaque e contraste automático.
    2. *Extração Nativa de Texto OCR no Editor (OCR estilo ShareX / PowerToys Text Extractor):* Integração direta com `winocr` (Windows Media OCR nativo em pt-BR) permitindo extrair qualquer texto contido na captura/print com um clique no botão `📝 OCR Texto` ou atalho `Ctrl+T`, copiando o texto reconhecido automaticamente para a área de transferência do Windows e exibindo notificação na barra de status.
    3. *Conversão de Imagem In-Memory:* Função auxiliar `qimage_to_pil` sem tocar no disco para máxima velocidade e privacidade.
  - **Falta:** Envio/upload automático para Imgur/nuvem (propositalmente mantido 100% local e privado para segurança de dados do usuário).
  - **Testes Realizados:** 16 testes automatizados em `test_print_anotador.py` cobrindo argumentos CLI, título da janela, blur, highlight, tarja, salvamento rápido num clique, rotação, zoom in/out/reset, callout, drop shadow, feedback visual, renderização de carimbos e extração OCR com fallback seguro. Smoke test com `CAIXA_TESTE=1` com saída limpa (código 0) e residual 0. Validação de staging com 1612 módulos e 768 ferramentas com selftest `OK: 768`.

---

## T322 — Avaliação Crítica & Paridade [editor-imagem] (2026-11-16)
- **Alvo:** `C:\Users\caion\editor-imagem` (substituto de Paint.NET / GIMP / PhotoScape X).
- **Status da Paridade:**
  - **Tinha:** Cortar com proporções livres e fixas (1:1, 4:3, 16:9, 9:16), redimensionar por pixels e porcentagem com trava de proporção, girar (90° horário/anti-horário, 180°, espelhar H/V, rotação em ângulo livre com cantos transparentes ou coloridos), ajustes completos (brilho, contraste, saturação, nitidez, temperatura e auto contraste otimizado), filtros básicos (P&B, Sépia, Inverter, Desfoque, Vintage, Auto Contraste, Bordas, Relevo), marca d'água (texto e logo), bordas e cantos arredondados, ocultação por blur e pixelização, texto livre com contorno e desenho de formas (Pincel contínuo, Retângulo, Elipse, Linha, Seta, Marca-texto), e gerenciamento completo de camadas (nova camada, inserir foto, duplicar, excluir, ordenar, 8 modos de mesclagem, opacidade, offset x/y, centralizar e achatar com desfazer/refazer).
  - **Fiz agora:**
    1. *Balde de Tinta / Preenchimento de Região (Flood Fill estilo Paint.NET / GIMP):* Ferramenta `draw_floodfill` com `ImageDraw.floodfill` nativo de alta performance no Pillow, com controle dinâmico de tolerância euclidiana de cor (0 a 100), opacidade e suporte pleno a imagens RGB e RGBA, integrada na aba Desenhar com slider de tolerância exibido sob demanda.
    2. *Conta-gotas / Pipeta (Color Picker / Eyedropper estilo Paint.NET / PhotoScape X):* Ferramenta `pick_color` e botão `🧪 Pipeta` integrado na paleta de cores. Clique no canvas em qualquer ponto da imagem amostra o pixel exato, atualiza a cor ativa em hex `#RRGGBB` e reflete imediatamente nos botões de cor para uso em Pincel, Formas e Balde de Tinta.
    3. *Filtro de Vinheta (Vignette clássica do PhotoScape X):* Efeito de vinheta radial suave `vignette` que preserva o centro luminoso e escurece bordas e cantos progressivamente via gradiente radial e interpolação bicúbica, registrado na grade dinâmica de filtros de 1-clique.
  - **Falta:** Varinha mágica de seleção poligonal/livre (lasso/magic wand) para recortes não retangulares complexos (recorte regular e flood fill cobrem a grande maioria dos fluxos desktop).
  - **Testes Realizados:** 10 baterias completas em `test_ei.py` cobrindo geometria, corte, redimensionamento, rotação livre, proporção, filtros e vinheta, marca d'água, bordas, desenho de formas, pincel, camadas, flood fill com tolerância, conta-gotas com clamping de borda e fluxo de GUI offscreen. Smoke test com `CAIXA_TESTE=1` com saída limpa (código 0) e residual 0. Validação de staging com 1614 módulos e 769 ferramentas com selftest `OK: 769`.

---

## T324 — Avaliação Crítica & Paridade [conversor-imagens] (2026-11-16)
- **Alvo:** `C:\Users\caion\conversor-imagens` (substituto das Extensões HEIF/WebP/RAW + conversores de imagem).
- **Status da Paridade:**
  - **Tinha:** Conversão em lote com lista de arquivos e suporte a arrastar pastas inteiras (recursivo), suporte a formatos normais (JPG, PNG, WEBP, BMP, GIF, TIFF, ICO), celulares (HEIC, HEIF, HIF, AVIF) e RAW de câmeras profissionais (DNG, CR2, CR3, NEF, ARW, ORF, RW2, PEF, RAF, CRW, MRW, SR2, SRF, X3F com rawpy e fallback de JPEG embutido), presets de redimensionamento proporcional (4K, Full HD, WhatsApp, Web, porcentagens 75%/50%/25%), rotação (90°, 180°, 270°) e espelhamento horizontal/vertical, filtro preto e branco (escala de cinza), controle de qualidade e pré-visualização ao vivo com metadados.
  - **Fiz agora:**
    1. *Compressão Inteligente por Limite de Tamanho Máximo (Max KB):* Busca binária automática de qualidade (10–95) para que arquivos convertidos caibam perfeitamente no teto estipulado pelo usuário (ex: max 500 KB, 1000 KB para portais de envio, concursos ou WhatsApp) sem tentativa e erro manual.
    2. *Correção de Orientação EXIF ao Preservar Metadados:* Atualização atômica da tag EXIF 0x0112 para orientação 1 (normal) quando `keep_metadata=True`, eliminando o bug de dupla rotação onde fotos já transpostas saíam deitadas ou de ponta-cabeça em visualizadores externos.
    3. *Ícones Windows Multi-Resolução ICO:* Geração de arquivos `.ico` autênticos contendo todas as resoluções padrão do Windows `[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]`.
    4. *Sufixo Personalizado e Modo Sobrescrever:* Customização de sufixo opcional (ex: `_convertida`) e opção de sobrescrever arquivos existentes na pasta de saída.
    5. *Resumo de Economia e Atalhos:* Cálculo percentual do ganho de compressão `(bytes_in → bytes_out · XX% menor)` na barra de status e atalho global `Ctrl+A` para seleção de todos os itens da lista.
  - **Falta:** Conversão direta de vídeos/GIF animado para sequência de frames (já coberto pelo `conversor-av` e `estudios-gif`).
  - **Testes Realizados:** 15 testes automatizados em `test_imgconv.py` cobrindo conversão JPG/WEBP/PDF/ICO multi-resolução, compressão por target KB, prefixo/sufixo/sobrescrita, preservação e correção de orientação EXIF, rotação/flip, escala de cinza e smoke test da GUI com atalhos. Staging com 1614 módulos e 769 ferramentas com selftest `OK: 769`.

---

## T325 — Avaliação Crítica & Paridade [cofre-senhas] (2026-11-16)
- **Alvo:** `C:\Users\caion\cofre-senhas` (substituto de KeePass / KeePassXC / Bitwarden / 1Password / SafeInCloud).
- **Status da Paridade:**
  - **Tinha:** Gerador de senhas aleatórias por tamanho e classes de caracteres (minúsculas, maiúsculas, dígitos, símbolos, filtro anti-ambíguos) com medição de entropia em bits, gerador de frases-senha (Diceware) em português com separador, capitalização e número final, cofre criptografado com Fernet (AES-128-CBC + HMAC autenticado) derivado por PBKDF2-HMAC-SHA256 (600.000 iterações + salt de 16 bytes), CRUD completo de entradas (título, usuário, site, senha, notas), cópia de senha com limpeza automática da área de transferência após 20 segundos (`copy_clearing`), cópia de usuário, busca em tempo real com filtragem instantânea, importação e exportação em JSON e CSV, e auditoria de segurança (senhas fracas, reutilizadas e score de saúde 0–100%).
  - **Fiz agora:**
    1. *Autenticador 2FA / TOTP Integrado por Conta (RFC 6238 estilo Bitwarden / 1Password / KeePassXC):* Implementação criptográfica nativa do algoritmo TOTP (HMAC-SHA1 em contador de 30 segundos com chave Base32 e truncamento dinâmico), campo dedicado na criação/edição de entradas, exibição visual do código `123 456` com contagem regressiva em tempo real via timer de 1s, e botão de cópia com 1 clique `🔑 Copiar 2FA` com limpeza segura do clipboard.
    2. *Troca de Senha-Mestra com Re-criptografia Completa (`🔑 Alterar Mestra`):* Diálogo seguro na interface para alteração da senha-mestra, exigindo confirmação da senha atual e validação dupla da nova senha (mín. 6 caracteres), gerando novo salt criptográfico aleatório e re-cifrando todo o cofre.
    3. *Bloqueio Rápido do Cofre (`🔒 Bloquear`):* Botão de travamento instantâneo que limpa credenciais da tela e memória e solicita a senha-mestra para reabertura sem necessidade de fechar e reabrir o aplicativo.
    4. *Preservação de 2FA em Backup e Migração:* Suporte a campos TOTP em importação/exportação tanto em JSON quanto em CSV.
  - **Falta:** Preenchimento automático no navegador via extensão (propositalmente mantido como aplicativo local independente e seguro no PC sem conexões de rede).
  - **Testes Realizados:** 11 baterias de testes em `test_cs.py` cobrindo gerador aleatório, força da senha, criação/carregamento/recusa por senha incorreta, busca e filtro, exportação/importação JSON e CSV, frase-senha Diceware, auditoria de senhas, vetores oficiais de teste da RFC 6238 para TOTP (timestamps 59, 1111111109, 1111111111, 1234567890, 2000000000), normalização de segredos Base32, alteração de senha-mestra com invalidação da antiga, cópia de 2FA no clipboard e smoke test de GUI com `CAIXA_TESTE=1` exit 0 e residual 0. Staging com 1614 módulos e 769 ferramentas com selftest `OK: 769`.

---

## T327 — Avaliação Crítica & Paridade [renomeador] (2026-11-16)
- **Alvo:** `C:\Users\caion\renomeador` (substituto do PowerToys PowerRename).
- **Status da Paridade:**
  - **Tinha:** Prévia interativa em tempo real com tabela de nomes atuais vs novos nomes, indicação visual em verde para alterados e vermelho para conflitos, localização e substituição por texto ou expressão regular (regex com suporte a $1, $2), ignorar maiúsculas/minúsculas, modelos com curingas (`{nome}`, `{n}`, `<001>`, `{data}`, `{pasta}`, `{ext}`), prefixo e sufixo configuráveis, alteração de caixa (minúsculas, MAIÚSCULAS, Title Case, Sentence case), data EXIF da foto ou modificação, execução em duas fases protegendo contra colisão ou perda de arquivos, histórico de desfazer (Undo / Ctrl+Z), suporte a arrastar pastas inteiras (recursivo) e seleção por checkboxes individuais ou botões Todos/Nenhum.
  - **Fiz agora:**
    1. *Formatações Avançadas de Caixa (snake_case, kebab-case e camelCase estilo PowerRename):* Novas transformações completas de case de nomenclatura para desenvolvedores e organização profissional de arquivos.
    2. *Remoção Automática de Acentos (Strip Accents / Sanitização ASCII):* Checkbox "Sem acentos" com normalização Unicode NFKD para limpeza de acentos e caracteres diacríticos (ex: `relatório_férias.pdf` → `relatorio_ferias.pdf`).
    3. *Passo da Numeração Configurável (`step`):* Controle dedicado de incremento de passo do contador sequencial (ex: passo 2, 5, 10).
    4. *Filtro de Exibição da Tabela de Prévia:* Seletor rápido para exibir "Todos os arquivos", "Apenas alterados" ou "Apenas com conflito / erro", permitindo inspecionar e isolar conflitos em listas com centenas de arquivos instantaneamente.
  - **Falta:** Nenhuma das funções essenciais do PowerRename (todas presentes com prévia, numeração, EXIF, regex, desfazer e drag-and-drop).
  - **Testes Realizados:** 8 baterias de testes em `test_rename_engine.py` cobrindo numeração sequencial e tags `<001>`, regex com grupos de captura `$1..$3`, aplicação em duas fases, desfazer via GUI, varredura de pastas recursiva, transformações de case (snake, kebab, camel), remoção de acentos isolada e combinada, passo do contador e novos controles da interface com filtros de tabela. Staging com 1614 módulos e 769 ferramentas com selftest `OK: 769`.

---

## T329 — Avaliação Crítica & Paridade [extrator-texto] (2026-11-16)
- **Alvo:** `C:\Users\caion\extrator-texto` (substituto do PowerToys Text Extractor).
- **Status da Paridade:**
  - **Tinha:** Seleção de área retangular da tela com overlay congelado e atalho global F9 (ou botão na interface), OCR nativo Windows 10/11 pt-BR (`winocr`) com suporte a múltiplos idiomas instalados, auto-inversão de contraste para imagens com fundo escuro, upscale bicúbico automático para textos pequenos, cópia direta e imediata do texto extraído para a área de transferência do Windows, carregamento de imagens existentes por arquivo (Open), drag-and-drop ou Ctrl+V, modo tabela TSV (reconhecendo linhas e colunas alinhadas para colar direto no Excel) e modo acumulador de capturas sucessivas.
  - **Fiz agora:**
    1. *Remoção Inteligente de Hifenização de Fim de Linha (`dehyphenate` / "Juntar hífens"):* Tratamento automatizado de palavras quebradas com hífen no final de linha em scans, livros e documentos PDF (ex: `apli-\ncação` → `aplicação`), solucionando o principal transtorno de extração de texto em OCR desktop.
    2. *Filtros Rápidos de Conteúdo Especializado:* Seletor com filtros instantâneos para extrair unicamente o que interessa da captura: "Tudo", "Apenas URLs" (links `http`/`https`/`www`), "Apenas E-mails" ou "Apenas Números" (valores, códigos e dígitos).
    3. *Miniatura Visual da Captura (Thumbnail Preview):* Exibição visual da imagem capturada ou colada na barra de status da janela, permitindo ao usuário conferir visualmente a área selecionada e o enquadramento sem precisar abrir outro visualizador.
    4. *Reaplicação Dinâmica e Feedback Visual:* Re-formatação e filtragem instantânea ao alternar as opções na interface sem necessidade de refazer a captura da tela.
  - **Falta:** Nenhuma das funções essenciais do PowerToys Text Extractor (superado com filtros especializados, des-hifenização e modo tabela TSV).
  - **Testes Realizados:** 11 testes em `test_ocr.py` cobrindo OCR com imagem sintética, inversão de tema escuro, modo tabela TSV, união de hífens (`dehyphenate`), filtros de URLs/emails/números, thumbnail na GUI, modo acumulado e smoke test offscreen com `CAIXA_TESTE=1` retornando exit 0 e residual 0. Staging com 1614 módulos e 769 ferramentas com selftest `OK: 769`.

---

## T330 — Avaliação Crítica & Paridade [faxina-disco] (2026-11-16)
- **Alvo:** `C:\Users\caion\faxina-disco` (substituto do WinDirStat / WizTree / CCleaner / Glary / Advanced SystemCare / PC Manager).
- **Status da Paridade:**
  - **Tinha:** Varredura recursiva multi-thread com árvore navegável de pastas com porcentagem e barra gráfica, barra segmentada de proporção ocupada por extensão/tipo de arquivo, tabela de tipos com contagem/tamanho/porcentagem, aba de maiores arquivos com busca e filtro em tempo real, detecção de duplicados em dois estágios (tamanho + SHA-256 parcial/completo) com presets inteligentes por tipo (Vídeos, Fotos, Músicas, Docs, Compactados, Todos) e seleção automática (manter mais recente, mais antigo, menor caminho, maior caminho), envio seguro para Lixeira do Windows via `SHFileOperationW`, exportação de relatório em CSV e limpeza rápida de categorias de lixo/cache (%TEMP%, Thumbcache, Crash Dumps, Browser Cache, WER, Logs, Lixeira).
  - **Fiz agora:**
    1. *Visualizador Treemap 2D Interativo (estilo WinDirStat / WizTree):* Implementação nativa do algoritmo `layout_treemap` particionando recursivamente a área do retângulo em blocos proporcionais ao tamanho de cada arquivo no disco, com paleta de cores mapeada por extensão, realce visual em hover, tooltips detalhados (nome, tamanho legível, extensão, caminho completo da pasta) e duplo-clique para abrir o arquivo no Explorer ou clique simples para inspecionar.
    2. *Novas Categorias de Limpeza Rápida do Sistema:*
       - `win_update`: Varredura e higienização segura de cache e instaladores acumulados de atualizações do Windows Update (`%SystemRoot%\SoftwareDistribution\Download`).
       - `downloads_old`: Detecção de instaladores, pacotes e imagens de disco obsoletos esquecidos na pasta Downloads do usuário (`.exe`, `.msi`, `.iso`, `.zip`, `.rar`, etc.).
    3. *Integração Fluida na Interface com QSplitter:* A aba "📊 Tipos & Gráfico" agora conta com divisor vertical redimensionável contendo a lista de extensões no topo e o mapa Treemap 2D abaixo, com atualização atômica e limpeza durante novas varreduras.
  - **Falta:** Desfragmentação de disco (não recomendada em discos modernos SSD/NVMe sob risco de desgaste prematuro de células flash, onde o Windows já executa o comando TRIM nativo).
  - **Testes Realizados:** 22 testes automatizados em `test_fxd_pasta.py` cobrindo particionamento do algoritmo Treemap 2D, novas regras e filtros de categorias estendidas (`win_update` e `downloads_old`), renderização via `QPainter`, clique e duplo clique do widget `DiskTreemapWidget`, integração com `Faxina` na aba de tipos, e smoke test offscreen com `CAIXA_TESTE=1` com encerramento limpo (exit code 0). Staging com 1614 módulos e 769 ferramentas com selftest `OK: 769`.

---

## T332 — Avaliação Crítica & Paridade [rede] (2026-11-16)
- **Alvo:** `C:\Users\caion\rede` (substituto de Speedtest by Ookla / Advanced IP Scanner).
- **Status da Paridade:**
  - **Tinha:** Diagnóstico da conexão do usuário (IP local, gateway, adaptadores, Wi-Fi com SSID/sinal/canal/taxas e IP público com provedor e geolocalização aproximada); ping com gráfico de latência em tempo real e alvos rápidos; rastreamento de rota salto a salto (traceroute); resolução DNS; varredura de dispositivos na rede local por ARP e sondas rápidas em sub-rede /24 com fabricante por OUI e portas padrão (80, 443, 445, 22, 3389); menu de contexto com ping, web admin, compartilhamento SMB e cópia; exportação de dispositivos em CSV e JSON; e teste de velocidade com Cloudflare medindo latência, download e upload.
  - **Fiz agora:**
    1. *Wake-on-LAN (WOL estilo Advanced IP Scanner):* Implementação nativa da função `send_wake_on_lan(mac)` enviando o pacote Magic Packet UDP broadcast (porta 9) para acordar computadores e servidores na rede local diretamente do menu de contexto com feedback visual.
    2. *Classificação Inteligente de Dispositivos por Categoria e Ícones:* Algoritmo `classify_device(dev)` que categoriza automaticamente os hosts descobertos entre "🌐 Roteador / Gateway", "🖨️ Impressora de Rede" (suporte a portas 9100 RAW, 631 IPP, 515 LPD e fabricantes Brother/Epson/Canon/Xerox/HP), "💾 Servidor / NAS" (Synology, QNAP, Western Digital), "📺 Smart TV / Streaming" (Roku, Samsung Tizen, LG WebOS, Chromecast, FireTV, AppleTV), "📱 Dispositivo Móvel" (MAC privado, Apple, Xiaomi, Motorola, Android), "💡 IoT / Automação" (Espressif, Tuya, Philips Hue, Intelbras) e "🖥️ Computador / Notebook" (Dell, Lenovo, HP, Este PC).
    3. *Suporte a Varredura por Faixa Flexível de IPs (`parse_ip_range`):* Suporte no campo de sub-rede a faixas personalizadas como `192.168.1.1-50`, `192.168.1.10 - 192.168.1.30` ou sub-redes CIDR `192.168.1.0/24`.
    4. *Pico de Velocidade e Taxas Instantâneas (Speedtest by Ookla):* Rastreamento em tempo real da velocidade máxima de pico atingida durante o download (`dl_peak`) e upload (`ul_peak`), com badges dedicados na interface ("Pico Down" e "Pico Up").
    5. *Presets de Intensidade do Teste de Velocidade:* Seletor rápido de intensidade: "⚡ Teste Padrão (25 MB / 2 MB)", "🚀 Teste Rápido (10 MB / 1 MB)" e "🔥 Teste Intenso (50 MB / 5 MB)" para conexões de alta velocidade e fibra óptica.
    6. *Veredito Automatizado de Aptidão da Conexão:* Avaliação inteligente da conexão (`speedtest_verdict`) analisando se a rede é adequada para Streaming 4K UHD, Jogos Competitivos (baixo ping e jitter estável), Chamadas HD / Home Office e Backup em Nuvem, com resumo copiado na íntegra para a área de transferência.
  - **Falta:** Nenhuma das funções essenciais do Speedtest by Ookla e do Advanced IP Scanner (todas cobertas 100% de forma nativa e offline).
  - **Testes Realizados:** 19 testes em `test_rd.py` cobrindo Wake-on-LAN (geração do pacote Magic Packet e socket broadcast UDP), classificação de dispositivos por categoria e serviço, interpretação de faixas flexíveis de IP, veredito de aptidão da conexão, presets de velocidade com pico de Mbps, novas portas de impressora (9100, 631, 515), badges e menu de contexto na GUI. Smoke test offscreen com `CAIXA_TESTE=1` retornando exit code 0 e residual 0. Staging com 1614 módulos e 769 ferramentas com selftest `OK: 769`.

## T336 Paridade player-musica (auditoria Grok) (2026-11-17 01:23–01:27 America/Sao_Paulo)

Auditoria de paridade de `C:\Users\caion\player-musica` contra AIMP / foobar2000 / MusicBee / Winamp. **Só leitura e teste; nenhum código da pasta foi alterado** (Grok é crítico/testador). Harness e captura em `C:\Users\caion\fiscal-fabrica\grok_t336\`. GUI aberta com `CAIXA_TESTE=1`, banco isolado (`biblioteca_teste.db`) e `silent=True` (sem áudio, sem varrer a pasta Música do Caio). Janela pid **948** titulada "Player de Música"; PrintWindow 1260×759 salvo em `player_musica.png`. IPTV pid **12428**, Caixa.exe --ponte **12996**, CaixaTela **20516**, pythonw do Caio (painel 22976, TV 19528, carteiro 8112) intocados; residual meu = 0.

**Testes** (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `QT_QPA_PLATFORM=offscreen`): `test_pm.py` — **9 passed, 1 error**. O erro é de fixture, não de hang: `test_sleep_timer_speed_and_visualizer(tmp)` declara `tmp` sem default (`tmp=None` como os outros testes), e o pytest procura um fixture `tmp` que não existe (`test_pm.py:626`). Os 9 restantes passam, inclusive equalizador, atalhos/AppCommand, pastas e playlists.

### Itens da vitrine

| Item | Veredito | Evidência |
|------|----------|-----------|
| Biblioteca por pasta | **tinha** | Core `Library.add_folder` / `folders` / `scan` / `tracks(..., folder=)` em `mu_core.py:232–296`. GUI: botão "➕ Pasta" (`player_musica.pyw:811`), diálogo "Escolha a pasta de músicas" (`:1351`), aba **Pastas** no nav (`:820`). Teste `test_folder_library_drag_drop_cli` passou. Screenshot: nav com Pastas, "+ Pasta", "Atualizar". Com `CAIXA_TESTE=1` o `first_scan` automático da pasta Música do usuário é pulado (`:782`). |
| Playlist | **tinha** | Core: criar/renomear/excluir, itens, reordenar, import/export `.m3u8` (`mu_core.py:336–391`, `export_m3u8`/`import_m3u8 :451–465`). GUI: aba Playlists, "Nova playlist", importar/exportar, "Mover acima/abaixo" (`player_musica.pyw:984–1015`). Testes `test_core` (playlists) e `test_track_details_playlist_reorder_and_folder_filter` passaram. Screenshot: item "Playlists" no nav (rótulo em inglês, ver pt-BR). |
| Equalizador | **está ruim** (UI tinha; áudio não) | Há página "🎚️ Equalizador", 10 frequências `EQ_FREQS` 31–16000 Hz, presets pt-BR (Rock, Pop, Bass Boost…) e pré-amp (`mu_core.py:619–668`, `_build_eq_page` em `player_musica.pyw:1023`). Porém `Equalizer.effective_multiplier` (`mu_core.py:662–668`) só faz a **média** dos ganhos + preamp e vira um fator de volume; `_apply_volume` (`player_musica.pyw:1694–1698`) aplica isso em `QAudioOutput.setVolume`. Não há filtro por banda (DSP). Em AIMP/foobar/Winamp o EQ muda o timbre; aqui Bass Boost e Treble Boost só alteram o volume médio. Teste `test_equalizer_core` / `test_equalizer_gui_and_shortcuts` passaram porque testam o modelo e a UI, não o espectro. Screenshot: item Equalizador no nav. |
| Atalhos de mídia do teclado | **tinha** | `HOTKEYS` com `VK_MEDIA_PLAY_PAUSE/NEXT/PREV/STOP` e Ctrl+Alt (`player_musica.pyw:52–63`); `RegisterHotKey` (`:2116`); `nativeEvent` trata `WM_HOTKEY` e `WM_APPCOMMAND` play/pause/next/prev/stop/mute/vol (`:2147–2193`); `QShortcut` das teclas Media* (`:2071–2109`). Teste `test_global_hotkeys_and_media_appcommand` passou. Não disparei tecla física nesta auditoria (sem som). |
| Visual pt-BR | **tinha** (detalhe menor) | Título e chrome em português: "Player de Música", "Buscar por título, artista ou álbum...", "Nenhuma música encontrada", "Tocando agora", "A seguir", colunas Título/Artista/Álbum/Ano/Duração, botões Pasta/Atualizar (screenshot). Mistura residual em inglês: item de nav "Playlists"; na página do EQ, "Preset:" e "Resetar (Flat)"; tooltip "Sleep Timer". |
| Tema escuro | **tinha** | QSS `background:#11131a; color:#e7e9f0` (`player_musica.pyw:26–50`), aplicado em `main` (`:2269`) e no harness da auditoria. Screenshot confirma fundo escuro, acento roxo, contraste legível. |
| Sem travar | **tinha** (nesta abertura) | 9 testes offscreen em ~1,9 s; janela abriu em ~3 s, PrintWindow ok, fechou pelo PID 948 sem residual. O erro do 10º teste é de fixture, não de travamento. |

### Prioridade para o construtor (1–2 itens)

1. **Equalizador de verdade (o mais importante):** aplicar ganho por banda (filtros / DSP), não um multiplicador de volume pela média dos dB. Manter a UI e os presets que já existem.
2. **Teste quebrado no pytest:** em `test_pm.py:626`, usar `tmp=None` (como os outros testes) ou um fixture `tmp_path`, para a suíte fechar 10/10. Não é item da vitrine, mas trava o portão de qualidade.

Sem `--pedir` de correção além do encaminhamento ao construtor. Sem git, sem alteração de código da ferramenta.

## T345 Paridade editor-texto (auditoria Grok) (2026-11-17 01:30–01:37 America/Sao_Paulo)

Auditoria de paridade de `C:\Users\caion\editor-texto` contra Notepad++. **Só leitura e teste; nenhum código da pasta foi alterado** (Grok é crítico/testador). Harness, arquivos de teste e captura em `C:\Users\caion\fiscal-fabrica\grok_t345\`. GUI aberta com `CAIXA_TESTE=1` e sessão isolada (`sessao_gui.json` / `sessao_ciclo_gui.json`); nunca abri nem gravei arquivos reais do Caio. Janela pid **28460** titulada "Editor de Texto — Notepad++"; PrintWindow 1196×779 salvo em `editor_texto.png` (cópia em `/workspace/grok_t345/`). IPTV pid **12428**, Caixa.exe --ponte **12996**, CaixaTela **20516**, pythonw do Caio (painel 22976, TV 19528, carteiro 8112) intocados; residual meu = 0.

**Testes** (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `QT_QPA_PLATFORM=offscreen`): `test_npp.py` — **5 passed** em 0,12 s (codificações, regex, estatísticas/linguagens, sessão no core, smoke GUI de abas/busca/encoding).

### Incidente no arquivo de sessão padrão (importante)

`NppMainWindow` restaura e, no `closeEvent` (`npp_gui.pyw:1009–1035`), grava sempre em `Path.home() / ".caixa_editor_sessao.json"` (`npp_core.py:81–83`). O teste `test_gui_smoke_e_abas` instancia essa janela **sem isolar o caminho**, então o `w.close()` do pytest reescreve a sessão real do usuário.

Neste micro: o pytest das 01:32 (America/Sao_Paulo) regravou `C:\Users\caion\.caixa_editor_sessao.json` (326 bytes) com a aba de teste "Novo 1" (texto do próprio teste, com "producao"). Cópia de sombra de 16/11 22:05 já tinha **o mesmo conteúdo** (hash idêntico, gravado em 16/11 21:37 America/Sao_Paulo) — ou seja, o rascunho de teste já estava lá (provavelmente de uma execução anterior do mesmo teste); não havia versão recuperável com texto distinto do Caio. Backup do estado atual em `grok_t345\backup_sessao_apos_pytest.json`. Não apaguei nem alterei de novo o arquivo vivo. Os testes de GUI seguintes usaram sessão isolada; o hash do arquivo vivo permaneceu `4fd100b2…eb7f9ae7`.

### Itens da vitrine

| Item | Veredito | Evidência |
|------|----------|-----------|
| Abas | **tinha** | `QTabWidget` com abas fecháveis e móveis (`npp_gui.pyw:390–394`), Novo (`Ctrl+N`), Fechar Aba Atual, sempre ao menos uma aba. Teste `test_gui_smoke_e_abas` passou (cria/fecha aba). Screenshot: abas "Novo 1", "amostra.py", "Rascunho T345". |
| Destaque de sintaxe | **tinha** (limitado vs Notepad++) | `NppSyntaxHighlighter` (`:206–275`) com palavras-chave para python/javascript/sql/c_cpp/html, números, strings e comentários de linha. O print de `amostra.py` mostra `def`/`return` roxos, `ola` azul, `42` laranja, string verde e comentários cinza itálico. Limitações: não há comentário de bloco `/* */`; palavras SQL só batem em maiúsculas; CSS/JSON/Markdown/shell/ini não têm lista de keywords; Markdown está em `EXTENSOES_LINGUAGEM` mas não no menu Linguagem; `highlightBlock` é por linha (comentário HTML multilinha falha). |
| Localizar/substituir com regex | **tinha** | Core `localizar_ocorrencias` / `substituir_tudo` com flags caso, palavra inteira e regex + backreference (`npp_core.py:174–225`). Conferência independente: `\d{2}/\d{2}/\d{4}` acha `15/11/2026` e `25/12/2026`; troca para `ANO-\1` gera dois `ANO-2026`. GUI: barra "Localizar/Substituir", F3 / Shift+F3, Ctrl+F / Ctrl+H, checkbox ".* (Regex)" (visível no print). Teste GUI de substituir "teste"→"producao" passou. Só atua na aba atual (sem "Localizar nos arquivos" / em todas as abas, como no N++). |
| Codificação UTF-8 / ANSI | **tinha** (autodetect UTF-16 ruim) | Mapa UTF-8, UTF-8 com BOM, ANSI CP1252, ASCII, UTF-16 LE (`npp_core.py:13–19`). Roundtrip independente em `grok_t345`: UTF-8, UTF-8 BOM e ANSI preservam acentos e são autodetectados corretamente; menu Codificação e status "UTF-8" no print. **UTF-16 LE:** `salvar_arquivo` usa o codec `utf-16-le` **sem BOM**; `detectar_codificacao` só reconhece `\xff\xfe`. Sem encoding explícita o arquivo é lido como ANSI e os acentos corrompem. O teste oficial passa porque lê com `codificacao="UTF-16 LE"`. Outro risco: `encode(..., errors="replace")` no save ANSI troca caracteres sem mapa (ex.: emoji) por `?` sem aviso. `_definir_codificacao` só muda o rótulo da próxima gravação (não relê os bytes; no N++ há "Codificar" vs "Converter"). |
| Não perder texto ao fechar | **tinha** (fechar a janela); falha ao fechar aba e no teste | `closeEvent` grava título, caminho, conteúdo, cursor, encoding e linguagem da sessão; `_restaurar_sessao` reabre as abas. Ciclo offscreen isolado: rascunho não salvo sobreviveu ao `close()` e voltou na reabertura; arquivo vivo intocado. Porém: fechar uma **aba** (`_fechar_aba_por_indice`, `:704–715`) descarta o texto sem pergunta e sem gravar sessão (só o fechar da janela persiste). Não há autosave periódico nem recuperação de crash (o N++ tem backup). E o teste GUI, como no incidente acima, pode apagar a sessão real do usuário. |
| Visual pt-BR | **tinha** | Título "Editor de Texto — Notepad++"; menus Arquivo / Editar / Localizar / Codificação / Linguagem; barra Novo, Abrir, Salvar, Salvar Todos, Localizar, Substituir, Estatísticas; busca "Localizar:", "Substituir:", "Anterior", "Próximo", "Substituir Tudo", "Aa (Caso)", "Palavra", "Regex"; status Ln/Col/Sel/Linhas/UTF-8/Windows (CRLF)/Python (screenshot). Detalhe menor: o status da linguagem usa `.capitalize()`, então `c_cpp` viraria "C_cpp". |
| Tema escuro | **tinha** (QSS `#11131a`; print confirma) | |
| Sem travar | **tinha** (nesta abertura) | 5 testes em 0,12 s; janela abriu, PrintWindow ok, fechou pelo PID 28460 (WM_CLOSE) sem residual. |

### Prioridade para o construtor (1–2 itens)

1. **Isolar a sessão no teste GUI (o mais importante / perigoso):** em `test_gui_smoke_e_abas`, apontar `NppCore.caminho_sessao_padrao` para um arquivo temporário (como já faz `test_sessao_nao_perde_texto`), para o pytest nunca mais reescrever `~\.caixa_editor_sessao.json`. Isso pode apagar rascunhos reais do usuário.
2. **UTF-16 LE com BOM + detecção:** gravar BOM `\xff\xfe` ao salvar em UTF-16 LE e/ou detectar UTF-16 por heurística de nulos, para o autodetect não reler o arquivo como ANSI. (Complemento útil: não usar `errors="replace"` silencioso no save ANSI; e, no fechar de aba, perguntar ou persistir o rascunho na sessão.)

Sem `--pedir` de correção além do encaminhamento ao construtor. Sem git, sem alteração de código da ferramenta.

## T348 Paridade conversor-av (auditoria Grok) (2026-11-17 01:39–01:42 America/Sao_Paulo)

Auditoria de paridade de `C:\Users\caion\conversor-av` contra HandBrake. **Só leitura e teste; nenhum código da pasta foi alterado** (Grok é crítico/testador). Harness, clipe gerado e captura em `C:\Users\caion\fiscal-fabrica\grok_t348\`. Nunca converti vídeos reais do Caio. GUI com `CAIXA_TESTE=1` (sem chamar `main()`, que fecha sozinho em 100 ms). Janela pid **20220** titulada "Conversor de Áudio/Vídeo"; PrintWindow 919×719 salvo em `conversor_av.png` (cópia em `/workspace/grok_t348/`). IPTV pid **12428**, Caixa.exe --ponte **12996**, CaixaTela **20516**, pythonw do Caio (painel 22976, TV 19528, carteiro 8112) intocados; residual meu = 0.

**Varredura de caminhos antes do pytest (regra nova):** `rg`/varredura em `test_avconv.py`, `avconv.py` e `conversor_av.pyw` por `Path.home()`, `AppData`, `USERPROFILE`, `expanduser`. Nenhum teste grava na casa do Caio. `test_out_name_sem_colisao` usa a string `"C:/musicas/audio.wav"` só como nome de origem; a escrita vai para `tempfile.TemporaryDirectory()`. GUI `closeEvent` só cancela a thread, não persiste sessão. Por isso rodei a suíte original no lugar. **12 passed** em 0,90 s (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `QT_QPA_PLATFORM=offscreen`). Os testes oficiais são na maioria *dry-run* (`build_cmd`); nenhum chama `convert()` de verdade.

### Itens da vitrine

| Item | Veredito | Evidência |
|------|----------|-----------|
| Converter vídeo e áudio em lote | **tinha** | Tabela de fila com colunas Arquivo/Duração/Tamanho/Resolução/Destino/Status, Adicionar Arquivos/Pasta, subir/descer, `ConvTask` percorre a lista (`conversor_av.pyw:128–176`, `run_convert :713`). Teste `test_gui_batch_table_operations` passou. Screenshot: `clip_t348.mp4` na fila, botão "Iniciar Conversão em Lote". Destino padrão: mesma pasta da origem (rótulo explícito); `out_name` nunca sobrescreve (usa ` (2)`). |
| Presets (WhatsApp, celular, 1080p) | **tinha** | Os três pedidos existem, além de vários outros (H.265, 4K, Discord, YouTube 1080p, voz, GIF, mudo, web 30 fps) em `avconv.py:82–212`. Conferência independente dos comandos: WhatsApp/Celular = `scale='min(1280,iw)':-2`; 1080p = `scale='min(1920,iw)':-2` + CRF 18 + faststart. GUI troca formato e trava o combo no preset (testes passaram). Screenshot: preset "WhatsApp / Leve (MP4 720p)" e descrição "Vídeo leve até 720p (H.264 CRF 28 + AAC 128k)". Há nomes duplicados (ex.: "WhatsApp (limite 16MB…)" e "📱 WhatsApp / Leve"), o que polui o combo. O preset "Stories / Reels (1080p)" não define `max_width`. |
| Cortar trecho | **tinha** | Checkbox "Cortar um trecho específico", campos De/Até, atalhos 00:00 e Fim (`:296–326`). `build_cmd` emite `-ss` / `-to` (`avconv.py:399–404`). Clipe de 3 s gerado com ffmpeg só em `grok_t348`: corte `00:01`–`00:02` via `convert()` gerou `out\clip_t348.mp4` com duração **1,0 s** (semântica de `-to` correta neste caso). Screenshot mostra o corte marcado. |
| Extrair áudio | **tinha** | Presets "🎧 Extrair Áudio (MP3 192 kbps)" e "⚡ Extrair Áudio Original (Cópia Sem Perda)"; botão "Extrair Áudio Rápido (MP3)". `build_cmd` usa `-vn` + libmp3lame. Conversão real do clipe de teste: `out\clip_t348.mp3` (73 497 bytes, duração 3,0 s). |
| Progresso real | **tinha** | `convert()` lê `-progress pipe:1` e `out_time_ms` contra a duração (`avconv.py:474`, `:518–552`). GUI tem duas barras ("Arquivo atual" e "Progresso geral") atualizadas em `_on_file_prog` / `_on_batch_prog`. No clipe curto, o callback chegou a `frac=1.0` com `speed=86.5x` (MP3) e `22.3x` (corte); em 3 s quase não há frações intermediárias, o que é esperado. A suíte oficial não exercita esse caminho. |
| Visual pt-BR | **tinha** | Título "Conversor de Áudio/Vídeo"; textos "Conversão em lote…", Adicionar Arquivos/Pasta, Preset rápido, Converter para, Qualidade, Girar vídeo, Volume do áudio, Cortar, Salvar, Iniciar Conversão em Lote, Cancelar (screenshot). |
| Tema escuro | **tinha** (QSS `#11131a`; print confirma) | |
| Sem travar | **tinha** (nesta abertura) | 12 testes em 0,90 s; geração do clipe + 2 conversões leves em ~1,3 s; janela abriu, PrintWindow ok, fechou pelo PID 20220 sem residual. |

### Prioridade para o construtor (1–2 itens)

1. **Teste de conversão real com clipe minúsculo em tempfile** (o mais útil agora): a suíte só monta a linha de comando. Incluir um caso que gera ~2–3 s com ffmpeg, chama `convert()` (extrair MP3 e cortar 1 s) e confere duração, pasta de saída e callback de progresso. Não usar arquivos do usuário.
2. **Limpar presets repetidos e completar o de Stories/Reels:** unificar os dois WhatsApp/Discord no combo e pôr `max_width` no preset "📹 Redes Sociais / Stories / Reels (1080p)", que hoje não escala.

Aviso já visto na T345 (para o construtor, não é desta pasta): `test_gui_smoke_e_abas` em `C:\Users\caion\editor-texto` grava em `~\.caixa_editor_sessao.json` (sessão real do usuário). Isolar o caminho da sessão nesse teste.

Sem `--pedir` de correção além do encaminhamento ao construtor. Sem git, sem alteração de código da ferramenta.

## T349 Paridade gravador-tela (auditoria Grok) (2026-11-17 01:43–01:48 America/Sao_Paulo)

Auditoria de paridade de `C:\Users\caion\gravador-tela` contra OBS Studio / Loom / Nimbus. **Só leitura e teste; nenhum código da pasta foi alterado** (Grok é crítico/testador). Harness e artefatos em `C:\Users\caion\fiscal-fabrica\grok_t349\`.

**Privacidade:** não gravei a tela, o microfone nem a webcam do Caio. A única captura real foi **2,2 s, sem áudio**, de uma janela magenta minha (320×240, título `T349_TESTE_GROK`), salva em `grok_t349\cap\regiao_2s.mp4`. O quadro extraído (`cap\frame.png`) mostra só esse padrão de teste ("T349 TESTE / NAO E A TELA DO CAIO"), sem a área de trabalho do Caio.

**Scan de caminhos antes do pytest:** o destino padrão é `~/Videos` (`gravador_tela.pyw`, `out_dir` na inicialização; `check_recorder_prerequisites` / `default_out_dir`). O teste `test_simulated_recording_states_flow_countdown_recording_paused_saved` instancia `Gravador()` e o `DummyRecorder.stop()` grava um MP4 falso de 2004 bytes nesse diretório. **Não rodei a suíte no ambiente real.** Rodei com HOME / USERPROFILE / APPDATA / LOCALAPPDATA / TEMP isolados em `grok_t349\fakehome`, e com `play_cue` silenciado só no harness (o original não respeita `CAIXA_TESTE=1` e chama `winsound.Beep`). Resultado: **13 passed** em 0,55 s (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`). O artefato caiu só em `fakehome\Videos\gravacao_2026-11-17_01-45-58.mp4` (2004 bytes). A pasta real `C:\Users\caion\Videos` já tinha **17** `gravacao_*.mp4` de 2004 bytes (15–16/11), lixo do mesmo teste em rodadas anteriores. Não apaguei nada. Depois desta auditoria a contagem continua 17.

GUI aberta com `CAIXA_TESTE=1` (sem `RegisterHotKey` global), `out_dir` = `grok_t349\out`, microfone e feedback sonoro desligados, modo 1280×720, **sem iniciar gravação**. PrintWindow da janela "Gravador de Tela" 579×649 salvo em `gravador_tela.png` (cópia em `/workspace/grok_t349/`). Fechada por WM_CLOSE; residual meu = 0 (sem ffmpeg, sem overlay, sem atalho global). Processos do Caio intocados: IPTV **12428**, Caixa.exe --ponte **12996**, CaixaTela **20516**, pythonw painel **22976**, TV **19528**, carteiro **8112**.

Dry-run `_video_cmd()` (região 10,20 / 320×240, qualidade alta, sem cursor): `gdigrab` + `-offset_x 10 -offset_y 20 -video_size 320x240` + libx264 CRF 18, `draw_mouse 0`. No modo GIF o Recorder desliga áudio e microfone. ffmpeg presente; loopback de sistema disponível. Não listei nomes de microfone nem títulos de janelas do Caio.

### Itens da vitrine

| Item | Veredito | Evidência |
|------|----------|-----------|
| Tela ou área | **tinha** | Presets: Tela inteira, 1920×1080, 1280×720, 854×480, 1080×1080, 1080×1920, "Janela de aplicativo…", "Área personalizada…". Screenshot: "Gravar: 1280 × 720 (HD 720p)", "Área fixada: 1280 × 720 (em 320, 180)". `_video_cmd` com offset/tamanho. Captura real 2,2 s da *minha* janela 320×240: h264 320×240, 5818 bytes; o frame é só o padrão magenta de teste. |
| Som do sistema + microfone | **tinha** (código/UI; áudio real não exercitado por privacidade) | Checkbox "Gravar o som do sistema (alto-falantes)" ligado por padrão; "Gravar o microfone" desligado por padrão + botão "Testar". Loopback (`soundcard`) + `_AudioWriter` + `mix_wav_files`. `test_microphone_input` é no-op com `CAIXA_TESTE=1`. GIF desliga áudio. |
| MP4 e GIF | **tinha** | Combo "Salvar como: MP4 (vídeo)" / GIF; extensão e flag `as_gif` no Recorder. Captura real só em MP4; o caminho GIF ficou na suíte e no código. |
| Atalho começar/parar | **tinha** | Combo "Atalhos: F9 / F10 (Padrão)"; botão "Começar a gravar (F9)"; "Pausar". Esquemas F9/F10, Ctrl+Shift+R e Ctrl+Alt+R. `RegisterHotKey` é pulado com `CAIXA_TESTE=1`; nesta abertura não ficou atalho global nem overlay ativo. |
| Contagem regressiva | **tinha** | Spin 0–10 s, padrão **3 s** no screenshot. Overlay e cancelamento (F10/Esc) no código; testes de countdown passaram. |
| Visual pt-BR | **tinha** | Título "Gravador de Tela"; textos "Grava a tela toda ou uma área, em MP4 ou GIF, com som do sistema, microfone e pausa", Gravar, Salvar como, Qualidade, FPS, Contagem regressiva, Atalhos, microfone, cursor, Feedback sonoro, Esconder esta janela, Pasta/Abrir, Começar a gravar, Pausar (screenshot). |
| Tema escuro | **tinha** (QSS `#11131a`; print confirma) | |
| Sem travar | **tinha** (nesta abertura) | 13 testes em 0,55 s; janela abriu, PrintWindow ok, fechou sem residual; captura de 2,2 s parou sozinha, sem ffmpeg leftover. |

### Prioridade para o construtor (1–2 itens)

1. **Isolar `test_simulated_recording_states_flow_countdown_recording_paused_saved`:** o `DummyRecorder` grava em `~/Videos`. Já existem 17 arquivos `gravacao_*.mp4` de 2004 bytes nessa pasta, de rodadas anteriores do mesmo teste. Usar tempfile / pasta isolada. **Não apaguei os 17** (Grok não apaga arquivo do usuário).
2. **`play_cue` deve respeitar `CAIXA_TESTE=1`:** o beep (`winsound.Beep`) toca mesmo em teste. Silenciei só no harness desta auditoria.

Aviso já visto na T345 (para o construtor, não é desta pasta): `test_gui_smoke_e_abas` em `C:\Users\caion\editor-texto` grava em `~\.caixa_editor_sessao.json` (sessão real do usuário). Isolar o caminho da sessão nesse teste.

Sem `--pedir` de correção além do encaminhamento ao construtor. Sem git, sem alteração de código da ferramenta.

## T354 Paridade editor-imagem (auditoria Grok) (2026-11-17 01:50–01:53 America/Sao_Paulo)

Auditoria de paridade de `C:\Users\caion\editor-imagem` contra Paint.NET / GIMP / PhotoScape X. **Só leitura e teste; nenhum código da pasta foi alterado** (Grok é crítico/testador). Harness e artefatos em `C:\Users\caion\fiscal-fabrica\grok_t354\`. **Não usei fotos do Caio** — só imagens geradas em `grok_t354\img\teste_t354.png` (blocos coloridos com o texto "T354 TESTE").

**Scan de caminhos antes do pytest:** `ei_core.py` e `test_ei.py` não usam `Path.home()` / `~/` / AppData. Os 10 testes gravam só em `tempfile.TemporaryDirectory()` e não chamam `save_as` / `QFileDialog`. O único destino em casa está em `editor_imagem.pyw` (`save_as`): se a imagem não tem caminho (ex.: colada), o diálogo sugere `~/imagem.png`. Isso **não escreve sozinho**. `~/imagem.png` não existia antes nem depois. Mesmo assim rodei a suíte com HOME / USERPROFILE / APPDATA / TEMP isolados em `grok_t354\fakehome`. Resultado: **10 passed** em 0,40 s (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `QT_QPA_PLATFORM=offscreen`, `CAIXA_TESTE=1`). Nenhum arquivo novo no fakehome nem em `~/imagem.png`.

Conferência independente (mesma pasta de teste, não as fotos do Caio): recorte (10,10)–(110,70) → 100×60; redimensionar largura 200 → 200×150; girar 90° → 300×400; inverter o bloco vermelho (200,40,40) → (55,215,215); brilho +50 em cinza 100 → 150; texto, retângulo preenchido e composição de camada conferidos; recorte na GUI + Ctrl+Z volta 400×300.

GUI aberta com `CAIXA_TESTE=1` **sem** chamar `main()` (o `main()` fecha em 200 ms). Imagem de teste via `open_path` (sem diálogo de Abrir). PrintWindow da janela "Editor de Imagem Rápido" 1196×799 em `editor_imagem.png` (cópia em `/workspace/grok_t354/`). Fechada por WM_CLOSE no pid **21892**; residual meu = 0. Processos do Caio intocados: IPTV **12428**, Caixa.exe --ponte **12996**, CaixaTela **20516**, pythonw painel **22976**, TV **19528**, carteiro **8112**.

### Itens da vitrine

| Item | Veredito | Evidência |
|------|----------|-----------|
| Cortar, redimensionar, girar | **tinha** | Abas Cortar (proporção + "Cortar seleção"), Tamanho (px/%, manter proporção) e Girar (90°/180°, espelhar, ângulo livre) no screenshot e no código. Core: `crop` / `resize` / `rotate90` / `rotate180` / `rotate_free` / `flip`. Testes oficiais + conferência independente (tamanhos acima). Screenshot: status `teste_t354.png — 400×300px`, aba Cortar visível. |
| Brilho / contraste / filtros | **tinha** | Aba Ajustes: Brilho, Contraste, Saturação, Nitidez, Temperatura, "Otimização Automática (Auto Contraste)". Aba Filtros: P&B, Sépia, Inverter, Desfoque, Vinheta, Vintage, Auto Contraste, Bordas, Relevo (`ei_core.FILTERS`). `test_adjust_filters` passou; inverter (200,40,40)→(55,215,215) e brilho +50 conferidos por fora. |
| Texto e formas | **tinha** | Aba Desenhar: Texto + Pincel, Retângulo, Elipse, Linha, Seta, Marca-texto, Balde de Tinta, Conta-gotas. Core `draw_text` / `draw_shape` / `draw_brush` / `draw_floodfill`. Testes de desenho, texto, pincel, balde e pipeta passaram; retângulo verde e texto "OLA" conferidos em `grok_t354\out`. |
| Camadas simples | **tinha** (com falha no desfazer) | Aba Camadas: Nova, Inserir Foto, Duplicar, Excluir, subir/descer, mesclar, achatar; opacidade e modos de mesclagem. Core `Layer` / `blend_layer` / `composite_layers`. `test_layers_core` e o trecho de camadas em `test_gui` passaram. Composição independente: camada rosa 80×80 em (20,20) → pixel (30,30)=(255,0,170). **Mas o desfazer não cobre a pilha** (abaixo). |
| Desfazer | **tinha** para a imagem; **está ruim** para camadas | Histórico `MAX_UNDO=30`, botões Desfazer/Refazer, atalhos Ctrl+Z / Ctrl+Y / Ctrl+Shift+Z. Recorte 100×60 desfaz de volta para 400×300. `test_floodfill_*` e `test_gui` desfazem pixels com sucesso. Porém: adicionar camada **não entra** no histórico (`ADD_LAYER_UNDO_DELTA=0`); depois de achar 3 camadas, Ctrl+Z restaura os pixels mas deixa **1** camada "Fundo" (`FLATTEN_UNDO_RESTORES_STACK False`). O `test_gui` não confere o número de camadas após esse undo. `do_undo` só reconstrói a lista quando `len(self.layers) <= 1`. |
| Visual pt-BR | **tinha** | Título "Editor de Imagem Rápido"; Abrir, Colar, Desfazer, Refazer, Original, Ajustar, Salvar como, Copiar; abas Cortar, Tamanho, Girar, Ajustes, Filtros (e outras atrás da seta); "Arraste na imagem pra escolher a área", Proporção, Cortar seleção (screenshot). |
| Tema escuro | **tinha** (QSS `#11131a`; print confirma) | |
| Sem travar | **tinha** (nesta abertura) | 10 testes em 0,40 s; conferências independentes ok; janela abriu, PrintWindow ok, fechou pelo pid 21892 sem residual. |

### Prioridade para o construtor (1–2 itens)

1. **Fazer o desfazer cobrir a pilha de camadas:** adicionar/duplicar precisa entrar no histórico; após achatar, Ctrl+Z deve restaurar as camadas (não só os pixels). Hoje `do_undo` só recria "Fundo" quando há no máximo 1 camada. Incluir asserção de `len(w.layers)` no `test_gui` depois do undo do flatten (hoje não confere isso).
2. **Detalhe menor de destino:** em `save_as`, imagem sem caminho sugere `~/imagem.png`. Não chegou a gravar nesta auditoria (só abre o diálogo). Preferir tempfile / última pasta, e não a casa do usuário, como sugestão padrão.

Aviso já visto na T345 (para o construtor, não é desta pasta): `test_gui_smoke_e_abas` em `C:\Users\caion\editor-texto` grava em `~\.caixa_editor_sessao.json`. Isolar o caminho da sessão nesse teste.

Aviso da T349 (também de outro teste, não desta pasta): `test_simulated_*` do gravador-tela ainda pode gravar em `~/Videos`. Às 01:50:03 apareceu um 18º `gravacao_*.mp4` de 2004 bytes (mesmo lixo de teste); não foi esta auditoria T354 e **não apaguei**.

Sem `--pedir` de correção além do encaminhamento ao construtor. Sem git, sem alteração de código da ferramenta.

## T355 Paridade conversor-imagens (auditoria Grok) (2026-11-17 01:54–01:58 America/Sao_Paulo)

Auditoria de paridade de `C:\Users\caion\conversor-imagens` contra conversores / extensões HEIF, WebP e RAW. **Só leitura e teste; nenhum código da pasta foi alterado** (Grok é crítico/testador). Harness e artefatos em `C:\Users\caion\fiscal-fabrica\grok_t355\`. **Não usei fotos do Caio** — só imagens geradas em `grok_t355\img\` (PNG/JPG/HEIC com o texto "T355 TESTE").

**Scan de caminhos antes do pytest:** `test_imgconv.py` grava só em `tempfile.mkdtemp()` e não chama `QFileDialog` / `_default_dir` / `scan_folder` em pasta do usuário. O risco está na GUI: `_default_dir()` abre o diálogo em `~/Pictures` (depois `~/Imagens` ou `~`); se não houver pasta de saída escolhida, `start()` grava em uma subpasta `convertidas` *ao lado do arquivo de origem*. Isso **não dispara sozinho** nos testes. `C:\Users\caion\convertidas` e `Pictures\convertidas` não existiam depois da suíte. Mesmo assim rodei com HOME / USERPROFILE / APPDATA / TEMP isolados em `grok_t355\fakehome`. Resultado: **15 passed** em 0,34 s (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `QT_QPA_PLATFORM=offscreen`, `CAIXA_TESTE=1`). Fakehome sem arquivos novos.

Conferência independente (só imagens geradas): PNG 400×300 → JPG (3729 B), WEBP (1224 B), PNG, BMP, TIFF, todos 400×300; `max_dim=100` → 100×75; 50% → 200×150; JPG q30 (2566 B) < q95 (4535 B); EXIF `Make=T355MAKE` preservado com `keep_metadata=True` e ausente com `False`. **HEIC gerado** (1388 B, `pillow_heif`) convertido para JPG 400×300. Lote de 3 JPGs em `out\lote`. `rawpy` **não está instalado** (`RAWPY=False`; não está em `requirements.txt`). Não abri nenhum RAW do Caio.

GUI aberta com `CAIXA_TESTE=1` **sem** chamar `main()` (o `main()` fecha na hora). Arquivos de teste via `_add` (sem diálogo de Abrir, que começaria em Imagens). Pasta de saída forçada para `grok_t355\out`. PrintWindow da janela "Conversor de Imagens" 867×712 em `conversor_imagens.png` (cópia em `/workspace/grok_t355/`). Fechada por WM_CLOSE no pid **20076**; residual meu = 0. Processos do Caio intocados: IPTV **12428**, Caixa.exe --ponte **12996**, CaixaTela **20516**, pythonw painel **22976**, TV **19528**, carteiro **8112**.

### Nota sobre o 18º `gravacao_*.mp4` (T349, não desta pasta)

`C:\Users\caion\Videos\gravacao_2026-11-17_01-50-03.mp4` (2004 bytes, cabeçalho `RIFF` + zeros — o mesmo lixo do `DummyRecorder` de `test_simulated_*`). **Não apaguei.** O meu teste isolado da T349 gerou *outro* arquivo, às **01:45:58**, só em `grok_t349\fakehome\Videos\`. Depois desse teste e da captura de 2,2 s (01:47:49) a pasta Vídeos real ainda tinha **17** arquivos. Eu não rodei `test_gvt.py` no perfil real depois das 01:45:58. O `--concluir` do painel (01:50:02) não executa testes. Às **01:50:04** (1 s depois desse 18º arquivo) `~\.caixa_editor_sessao.json` foi regravado com o mesmo hash `4fd100b2…eb7f9ae7` do rascunho de teste da T345 — assinatura do `test_gui_smoke_e_abas` sem isolamento. Conclusão: o 18º **não veio do meu harness da T349**; é o mesmo tipo de vazamento, disparado por alguma outra execução dos testes oficiais no perfil do Caio por volta das 01:50:03.

### Itens da vitrine

| Item | Veredito | Evidência |
|------|----------|-----------|
| Lote | **tinha** | Lista com vários arquivos, "Adicionar arquivos/pasta", `ConvTask` em thread, botão Converter. Screenshot: 3 itens na lista, "3 imagem(ns) na lista (3,9 KB)". Lote independente de 3 JPGs em `grok_t355\out\lote`. |
| HEIC, WEBP, RAW, PNG, JPG | **tinha** para HEIC/WEBP/PNG/JPG; **RAW só no código/extensão** | Saídas JPG/PNG/WEBP/BMP/TIFF/ICO/PDF no combo e em `FORMATS`. WEBP e JPG conferidos (1224 B / 3729 B). HEIC: `pillow_heif` ativo; gravei `teste_t355.heic` e converti para JPG 400×300; a GUI listou e pré-visualizou o HEIC. A suíte oficial **só checa a extensão** `.heic`, não converte um HEIC de verdade. RAW: extensões DNG/CR2/CR3/NEF/… no código e `open_image` com `rawpy` + fallback de JPEG embutido, mas **`rawpy` não está instalado** nem no `requirements.txt`. Testes oficiais só fazem `supported("nikon.nef")` / `raw.crw`. Não abri RAW do Caio. |
| Redimensionar e comprimir | **tinha** | Presets (Original, 75/50/25%, 4K, Full HD, HD/WhatsApp, Web/E-mail), "Tamanho máx.", qualidade 1–100, "Limite de peso". Conferência: 100×75, 200×150, q30 < q95. `test_convert_resize`, `test_convert_percent_resize` e `test_target_kb_compression` passaram. |
| Manter EXIF opcional | **tinha** | Checkbox "Manter metadados (EXIF/GPS)" desligado por padrão (screenshot). Padrão do core é `keep_metadata=False`. Independente: `Make=T355MAKE` permanece com keep=True e some com False. `test_keep_metadata` passa, mas só confere que o arquivo existe — não lê a tag. Orientação EXIF 6 é normalizada para 1 (`test_keep_metadata_fixes_orientation`). |
| Visual pt-BR | **tinha** | Título "Conversor de Imagens"; textos "Converte fotos em lote…", Adicionar arquivos/pasta, Remover, Limpar, Formato, Preset, Tamanho máx., Orientação, Qualidade, Limite de peso, Sufixo, Manter metadados, Preto e branco, Sobrescrever, Salvar em, Converter (screenshot). |
| Tema escuro | **tinha** (QSS `#11131a`; print confirma) | |
| Sem travar | **tinha** (nesta abertura) | 15 testes em 0,34 s; conversões independentes ok; janela abriu, PrintWindow ok, fechou pelo pid 20076 sem residual. |

### Prioridade para o construtor (1–2 itens)

1. **Incluir na suíte uma conversão real de HEIC minúsculo gerado em tempfile** (já dá pra gravar com `pillow_heif` e converter para JPG, como em `grok_t355`). Hoje o teste só faz `supported("foto.heic")`.
2. **Decidir o suporte a RAW de verdade:** `rawpy` não está no `requirements.txt` e não importa (`RAWPY=False`). Sem isso, arquivo de câmera só cai no fallback de JPEG embutido. Ou acrescentar `rawpy` e um teste com um RAW *sintético/minúsculo* (nunca fotos do usuário), ou deixar explícito na UI que RAW completo depende dessa lib.

Aviso já visto na T345 (para o construtor, não é desta pasta): `test_gui_smoke_e_abas` em `C:\Users\caion\editor-texto` grava em `~\.caixa_editor_sessao.json`. Isolar. O toque das 01:50:04 nesse arquivo (mesmo hash de teste) reforça o pedido.

Aviso da T349: `test_simulated_*` do gravador-tela ainda pode gravar em `~/Videos`. O 18º `gravacao_*.mp4` de 2004 bytes (01:50:03) é desse teste; **não foi o harness isolado da T349** e **não apaguei**.

Sem `--pedir` de correção além do encaminhamento ao construtor. Sem git, sem alteração de código da ferramenta.

## T356 Paridade cofre-senhas (auditoria Grok) (2026-11-17 02:00–02:04 America/Sao_Paulo)

Auditoria de paridade de `C:\Users\caion\cofre-senhas` contra KeePass / KeePassXC / Bitwarden / 1Password / SafeInCloud. **Só leitura e teste; nenhum código da pasta foi alterado.** Harness em `C:\Users\caion\fiscal-fabrica\grok_t356\`.

**Privacidade:** não abri, não li, não copiei, não desbloqueei, não gerei hash e não alterei o cofre real nem nenhum config do Caio. O caminho no código é só `VAULT_PATH = os.path.join(HERE, "cofre.vault")` → `C:\Users\caion\cofre-senhas\cofre.vault` (ao lado do programa, não no AppData). Esse arquivo **não existia** antes nem depois (mesmo tamanho/mtime: inexistente). Pytest e GUI rodaram com HOME / USERPROFILE / APPDATA / TEMP isolados em `grok_t356\fakehome` (e `tmp`), usando só cofre falso com senha-mestra e entradas falsas (`t356_fake.vault` / `t356_gui.vault`). O print mostra apenas esse cofre falso, com a senha em bullets. Não usei o diálogo de senha-mestra do cofre real nem chamei `main()` sem isolamento (o `main()` sem `CAIXA_TESTE` abriria `VAULT_PATH`). A área de transferência não ficou com valor de teste no fim (limpei depois dos testes oficiais que copiam usuário/TOTP; a GUI visível não copiou nada).

**Scan de caminhos antes do pytest:** `test_cs.py` não menciona `VAULT_PATH` nem `cofre.vault`; os 11 testes usam `tempfile`. Mesmo assim isolei o perfil. Observação: `cryptography` está no user-site (`AppData\Roaming\Python\Python313\site-packages`); isolar `APPDATA` esconde essa lib, então o pytest isolado recebeu só esse `site-packages` no `PYTHONPATH` (não li o cofre). Primeira coleta sem isso falhou com `ModuleNotFoundError: cryptography`; com o path, **11 passed** em 6,04 s (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `QT_QPA_PLATFORM=offscreen`, `CAIXA_TESTE=1`). `cofre.vault` real continuou inexistente.

Conferência independente no cofre falso: gerador 20 caracteres (minúscula+maiúscula+dígito+símbolo), força 129 bits (“excelente”); frase-senha de 4 palavras + número; arquivo do cofre tem `v`, `salt`, `iters=600000` e `data`; a mestra falsa e a senha da entrada **não** aparecem em claro; senha-mestra errada falha (“Senha-mestra incorreta.”); recarregar com a mestra falsa devolve 2 entradas; busca “Exemplo” → 1; exportar/importar JSON recolocou as 2 entradas.

### Itens da vitrine

| Item | Veredito | Evidência |
|------|----------|-----------|
| Gerar senha forte | **tinha** | Aba “Gerador” no screenshot; `vault.generate` e `generate_passphrase` (estilo Diceware). `test_gerador_senhas` / `test_forca_senha` / `test_gerador_passphrase` passaram. Independente: 20 caracteres com as 4 classes, 129 bits, rótulo “excelente”. |
| Cofre criptografado | **tinha** | `Vault` com PBKDF2-HMAC-SHA256 (600.000 iterações + salt) e Fernet. Senha-mestra não é salva. Arquivo falso: chaves `v/salt/iters/data`, iters 600000; mestra e senha da entrada ausentes em claro; load com senha errada falha. GUI: entradas falsas “T356 Site Exemplo” / “T356 Outro Servico”. O cofre real no caminho do código não existia. |
| Copiar com limpeza automática | **tinha** para senha e 2FA (20 s); **está ruim** para usuário | `copy_pw` e `copy_totp` usam `copy_clearing` (`CLIP_CLEAR_MS = 20000`). `copy_user` faz só `clipboard().setText(u)` **sem** timer de limpeza. `test_gui_smoke` confere que o usuário vai para a área de transferência, mas não testa a limpeza da senha. |
| Busca | **tinha** | Campo “Buscar no cofre (nome, usuário, site)…” (screenshot). `Vault.search` + `_refresh`. `test_busca_e_filtro` passou; independente: “Exemplo” → 1, “t356” → 2, “zzzz-nao-existe” → 0. |
| Importar / exportar | **tinha** | Botões “Importar (JSON/CSV)” e “Exportar (JSON/CSV)” no print. `export_json` / `import_json` / `export_csv` / `import_csv`. Testes oficiais e export+reimport independente em `grok_t356\out` (2 entradas). Não abri diálogo apontando para pasta do Caio. |
| Visual pt-BR | **tinha** | Título “Cofre de Senhas”; abas Cofre e Gerador; buscar, Nova, Editar, Excluir, Copiar senha/usuário/2FA, Mostrar, Auditoria do Cofre, Alterar Mestra, Bloquear, Importar, Exportar (screenshot). |
| Tema escuro | **tinha** (QSS `#11131a`; print confirma) | |
| Sem travar | **tinha** (nesta abertura) | 11 testes em 6,04 s (o tempo cabe nas 600k iterações); janela abriu, PrintWindow ok, fechou pelo pid **28776** sem residual. |

### Prioridade para o construtor (1–2 itens)

1. **`copy_user` deve usar a mesma limpeza automática da senha** (`copy_clearing`, 20 s). Hoje o usuário (e-mail) fica na área de transferência até outra coisa sobrescrever.
2. **Cobrir a limpeza no teste oficial:** além de copiar, conferir que a senha some depois do timer (e que o usuário também some, depois do item 1). Não usar o cofre real nesses testes.

Aviso de caminho (para qualquer agente): o cofre real, se for criado, fica em `C:\Users\caion\cofre-senhas\cofre.vault`. Isolar só HOME/APPDATA **não** protege esse arquivo. Nunca chamar `main()` sem `CAIXA_TESTE=1` e sem um `Vault` apontando para pasta de teste. Nesta auditoria o arquivo não chegou a existir.

Avisos já vistos (outras pastas): T345 — `test_gui_smoke_e_abas` do editor-texto grava em `~\.caixa_editor_sessao.json`; T349 — `test_simulated_*` do gravador pode gravar em `~/Videos`.

Sem `--pedir` de correção além do encaminhamento ao construtor. Sem git, sem alteração de código da ferramenta.

## T357 Paridade busca-arquivos (auditoria Grok) (2026-11-17 02:05–02:08 America/Sao_Paulo)

Auditoria de paridade de `C:\Users\caion\busca-arquivos` contra Everything. **Só leitura e teste; nenhum código da pasta foi alterado.** Harness em `C:\Users\caion\fiscal-fabrica\grok_t357\`.

**Sem varredura do disco do Caio.** Não abri a GUI no modo padrão (`auto_index=True`), não apertei F5/Reindexar e não chamei `Index.build()` com `finder.fixed_drives()`. O `start_index()` da GUI indexa **todas as unidades fixas** (`GetLogicalDrives` + `DRIVE_FIXED`, aqui seria `C:\` e `G:\` — listei as letras, **não indexei**). Não usa MFT/USN: a varredura é `os.scandir` em memória. Indexei e busquei **somente** a árvore gerada `grok_t357\tree\` (8 itens). O `main()` com `CAIXA_TESTE=1` já abre com `auto_index=False`, mas mesmo nesse modo a janela **dispara um timer de 10 min** que chamaria `start_index()` (disco inteiro) e o `QFileSystemWatcher` olharia Desktop/Downloads/Documents/Pictures de `~`. Por isso a GUI visível rodou com perfil isolado, `Busca(auto_index=False)`, timer de reindexação parado, índice só da pasta de teste, e foi fechada em seguida. Nenhum indexador/serviço ficou rodando.

**Scan de caminhos antes do pytest:** os testes oficiais usam `tempfile` e `Busca(auto_index=False)`; não chamam `fixed_drives()` / `start_index()`. O histórico padrão seria `%APPDATA%\CaixaFerramentas\busca-arquivos-historico.json` — com `CAIXA_TESTE=1` a GUI não carrega nem grava esse arquivo, salvo se o teste apontar outro caminho (eles usam tempfile). O arquivo real **não existia** antes nem depois. `test_lixeira_real` foi **desmarcado** de propósito (mandaria um arquivo de tempfile para a Lixeira do Windows). Suite isolada (HOME/USERPROFILE/APPDATA/TEMP em `grok_t357\fakehome`): **23 passed, 1 deselected** em 0,44 s.

Conferência independente só na árvore de teste: `Index.build([tree])` → 8 itens em 0,27 ms, todos dentro de `grok_t357\tree`. Busca `t357` → 5 arquivos em 0,14 ms. Filtro imagens → `foto_t357.png`; “últimos 30 dias” exclui `arquivo_velho_t357.txt` (mtime ~40 dias); tamanho “pequeno” não inclui `notas_t357.log` (~150 KB); `content:"relatorio"` acha `relatorio_t357.txt`.

### Itens da vitrine

| Item | Veredito | Evidência |
|------|----------|-----------|
| Resultado instantâneo enquanto digita | **tinha** (depois do índice em memória) | Campo de busca com debounce de 150 ms (`_timer`) e `finder.search` no índice. Screenshot: busca `t357`, “5 resultado(s) em 0 ms”, só arquivos da pasta de teste. Independente: 5 hits em 0,14 ms. Sem o índice, a busca não percorre o disco (lista vazia). |
| Filtros tipo / tamanho / data | **tinha** | Combos Tipo, Tamanho e Modificado no print (`Todos`, `Qualquer tamanho`, `Qualquer data`). Core e testes oficiais (`test_filtros_tipo_tamanho_data`, `test_presets_tamanho_e_data`) passaram. Independente: imagens=1, últimos 30 dias=4 (cai o arquivo velho), pequeno não inclui o log de 150 KB. Também há filtros no estilo Everything (`ext:`, `size:`, `dm:`, `path:`, `content:`). |
| Abrir pasta do arquivo | **tinha** (código/UI; não cliquei) | Botão “Abrir Pasta”, tooltip Ctrl+Enter, menu “Abrir pasta no Explorer”, `_abrir_pasta_entry` usa `explorer.exe /select,` no arquivo. Não executei isso nesta auditoria (não abri o Explorer). |
| Índice que atualiza sozinho | **parcial / está incompleto** frente ao Everything | Não há MFT/USN; o índice **não é gravado em disco** (só memória). Atualização “sozinha”: `QFileSystemWatcher` em apenas 4 pastas do perfil (Desktop, Downloads, Documents, Pictures) via `update_directory`, e um timer de **10 minutos que reindexa o disco inteiro**. Isso vale mesmo com `auto_index=False`. Não é o monitoramento incremental do NTFS do Everything. |
| Visual pt-BR | **tinha** | Título “Busca Instantânea de Arquivos”; Abrir, Abrir Pasta, Copiar, Lixeira, Prévia, Exportar, Reindexar; “Buscar no conteúdo”; Tipo, Tamanho, Modificado; “Só pastas” (screenshot). |
| Tema escuro | **tinha** (QSS `#11131a`; print confirma) | |
| Sem travar | **tinha** (nesta abertura, só árvore de teste) | 23 testes em 0,44 s; índice de 8 itens instantâneo; janela abriu, PrintWindow ok, fechou pelo pid **25780** sem residual. Não medi uma indexação de disco inteiro (de propósito). |

### Prioridade para o construtor (1–2 itens)

1. **Não reindexar o disco inteiro no modo de teste, nem no timer de 10 min quando `auto_index=False`.** Hoje F5/Reindexar e o timer chamam `fixed_drives()` (nesta máquina, `C:\` e `G:\`). Com `CAIXA_TESTE=1` o `main()` não autoindexa, mas o timer continua armado. Parar o timer no modo de teste e permitir indexar só uma pasta escolhida (como fiz na auditoria).
2. **Deixar o “atualiza sozinho” mais perto do Everything, ou ser explícito na UI:** o índice some ao fechar; o watcher cobre só 4 pastas da casa; o “auto” de 10 min é varredura completa das unidades, não USN/MFT.

Aviso de histórico (não disparou aqui): `caminho_historico()` grava em `%APPDATA%\CaixaFerramentas\busca-arquivos-historico.json`. Isolar APPDATA ou manter `CAIXA_TESTE=1`. O arquivo real não existia antes nem depois.

Avisos já vistos (outras pastas): T345 (sessão do editor-texto), T349 (`~/Videos` no teste do gravador), T356 (o cofre real ficaria ao lado do programa, não no AppData).

Sem `--pedir` de correção além do encaminhamento ao construtor. Sem git, sem alteração de código da ferramenta.

## T358 Paridade renomeador (auditoria Grok) (2026-11-17 02:10–02:16 America/Sao_Paulo)

Auditoria de paridade de `C:\Users\caion\renomeador` contra PowerToys PowerRename, conferindo de forma independente as afirmações da T327 (Cursor, 16/11 19:01). **Só leitura e teste; nenhum código da pasta foi alterado.** Harness em `C:\Users\caion\fiscal-fabrica\grok_t358\`.

**Só a árvore de teste.** Não abri os diálogos “Adicionar arquivos/pasta” (o `QFileDialog` não fixa a pasta inicial e no Windows pode abrir a última usada). Os 11 arquivos da prévia foram colocados na janela por `_add()` e todos estavam em `grok_t358\tree`. Apply/undo reais rodaram só em `grok_t358\work` (cópias). A árvore original ficou intacta. O histórico de desfazer é só memória (`self.history`); não há `QSettings` / `Path.home` / APPDATA. Depois da sessão, não existia config do renomeador no perfil real.

**Scan de caminhos antes do pytest:** os 8 testes oficiais usam `tempfile.TemporaryDirectory()` ou só `compute()` com caminhos fictícios. Suite isolada (HOME/USERPROFILE/APPDATA/TEMP em `grok_t358\fakehome`, `CAIXA_TESTE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`): **8 passed** em 0,11 s. Nada além das pastas vazias que eu criei apareceu no fakehome.

### Itens da vitrine e das afirmações da T327

| Item | Veredito | Evidência |
|------|----------|-----------|
| Prévia interativa antes de aplicar | **tinha** | Tabela Nome atual / Novo nome; recálculo com debounce de 120 ms. Print: `snake_case` + “Sem acentos”, “4 arquivo(s) serão renomeados (11 selecionados de 11)”, nomes novos em verde. Não apertei Aplicar na GUI. |
| Regex (grupos `$1`) | **tinha** | Independente: `IMG_(\d+)` → `Foto_$1` virou `Foto_001.jpg` / `Foto_002.jpg`. Teste oficial `test_regex_capture_groups_dates` passou. Checkbox “regex” na GUI. |
| Numeração sequencial + passo | **tinha** | Independente: modelo `item_<001>`, início 10, passo 5 → `item_010.txt`, `item_015.txt`, `item_020.txt`. Controles “Nº inicial”, “passo”, “dígitos” no print. |
| Proteção em duas fases (troca sem perda) | **tinha** | `apply()` renomeia para `.ren_tmp_{pid}_…` e depois para o nome final. Swap real em `work\swap`: `alpha.txt` (ALPHA) ⇄ `beta.txt` (BETA); depois `alpha.txt` tinha BETA e `beta.txt` tinha ALPHA; nenhum temporário ficou. |
| Desfazer (Ctrl+Z) | **tinha** (só nesta sessão, em memória) | Depois do swap, `R.undo(hist)` restaurou ALPHA/BETA. Depois de snake+acentos em cópias, o undo devolveu `Relatório de Férias 2026.txt` e `Ação Comercial & Vendas.txt`. Botão “Desfazer (Ctrl+Z)” no print (desabilitado porque a GUI não aplicou). |
| snake_case / kebab-case / camelCase | **tinham** | Independente, iguais aos testes oficiais: `relatório_de_férias_2026.txt`, `relatório-de-férias-2026.txt`, `relatórioDeFérias2026.txt`. Combo “Formato / Caixa” no print em snake_case. |
| Sem acentos (NFKD) | **tinha** | Isolado: `Relatorio de Ferias 2026.txt`. Com snake: `relatorio_de_ferias_2026.txt`. Print mostra a mesma prévia. |
| Filtros da prévia (Todos / Alterados / Conflito) | **tinham** | Com Localizar `vai_conflitar` → `destino_ocupado`: Todos=11, Alterados=0 (os que mudariam eram conflito), Erros=2 (`destino_ocupado.txt`, `vai_conflitar.txt`, marca “nome repetido”). Com snake+acentos: Alterados=4 (`Ação…`, `IMG_001.jpg`, `IMG_002.jpg`, `Relatório…`), Erros=0. “já existe um arquivo com esse nome” também foi confirmado (`igual.txt` → `destino_ocupado.txt`, alvo fora da seleção). |
| Data EXIF | **tinha** | JPEG gerado com DateTime `2024:12:25 10:11:12`; `{data}_{nome}` + `use_exif=True` → `2024-12-25_foto_exif_t358.jpg`. Checkbox “{data} da foto (EXIF)” na GUI (não marcado no print). |
| Arrastar pasta | **tinha** no código (`dropEvent` + `scan_dir`, com “Subpastas”). Não arrastei nada nesta auditoria. |
| Visual pt-BR | **tinha** | Título “Renomeador em Lote”; Localizar, Trocar por, Modelo, Prefixo, Sufixo, Aplicar a, Exibição da prévia, Desfazer, Aplicar (screenshot). |
| Tema escuro | **tinha** (QSS `#11131a`; print confirma). |
| Sem travar | **tinha** nesta abertura | 8 testes em 0,11 s; janela 1355×779; fechada no próprio processo (pid **24292**), residual 0. Uma primeira tentativa de PrintWindow em *outro* processo travou (a GUI não processava eventos) e eu encerrei só esses dois PIDs meus (16348 e 5584); a captura boa foi no mesmo processo, com o loop de eventos ligado. |

### Sobre a T327

As afirmações da T327 (cobertura dos essenciais do PowerRename, inclusive snake/kebab/camel, remoção de acentos, passo da numeração e filtros da prévia) **conferem** nesta auditoria independente. Não pedi correção ao construtor.

Sem git, sem alteração de código da ferramenta.

## T360 — Paridade [extrator-texto] vs PowerToys Text Extractor (2026-11-17)
- **Alvo:** `C:\Users\caion\extrator-texto`
- **Essenciais vitrine:** selecionar área · OCR pt-BR · copiar direto · abrir imagem existente — todos **já tinham** (T329).
- **Tinha:** Overlay congelado + F9, OCR `winocr` pt-BR, auto-invert/upscale, cópia automática, arquivo/DnD/Ctrl+V, modo tabela TSV, acumular, des-hífen, filtros URL/e-mail/número, thumbnail.
- **Fiz agora (gaps reais vs PowerToys):**
  1. *Shift move a área* no overlay (docs PowerToys: “holding Shift… moving the capture region”) + rótulo `L × A px` e dica no overlay.
  2. *Atalho global Win+Shift+T* (padrão PowerToys) via `RegisterHotKey`, com fallbacks Ctrl+Shift+T / Ctrl+Alt+T; badge na UI; desligado em `CAIXA_TESTE`/offscreen.
- **Falta:** nada dos 4 essenciais da vitrine; overlay com toggles Table/Single-line *durante* a captura (Text Extractor 2.0) ainda não — dá pra próxima se sobrar.
- **Testes:** 13 em `test_ocr.py` OK (novos: `clamp_move_rect`, tamanho da seleção, Shift no Overlay, badge de atalho); offscreen `CAIXA_TESTE=1` exit 0.

## T376 — Paridade [kit-pdf] vs PDF24 / Foxit / Sumatra (2026-11-17)
- **Alvo:** `C:\Users\caion\kit-pdf`
- **Essenciais:** ler · juntar/separar/girar/comprimir · imagens↔PDF · texto · senha — todos **já tinham** (+ marca d'água/números).
- **Fiz agora:**
  1. *Inverter ordem* (`reverse_pages`) + ferramenta na grade.
  2. *Frente e verso ADF* (`intercalar_frente_verso` / `reorder_pages`) — monta duplex após digitalizar.
- **Falta:** nada dos 5 essenciais; OCR embutido no kit fica pra depois (já no extrator/scanner).
- **Testes:** `test_reorder_reverse_e_duplex` OK.

## T375 — Paridade [compactador] vs 7-Zip / WinRAR (2026-11-17)
- **Alvo:** `C:\Users\caion\compactador`
- **Essenciais:** ZIP/7z/RAR · senha · arrastar · progresso — todos **já tinham**.
- **Fiz agora:**
  1. *Excluir temporários na compactação* (`EXCLUDE_TEMP_MASKS` / `collect_files` + checkbox).
  2. *CRC-32 de arquivo* (`crc32_arquivo`) estilo coluna CRC do 7-Zip.
- **Falta:** nada dos 4 essenciais; volumes divididos / SFX ficam pra depois.
- **Testes:** `ExcludeAndCrc` + suite OK.

## T373 — Paridade [editor-texto] vs Notepad++ (2026-11-17)
- **Alvo:** `C:\Users\caion\editor-texto`
- **Essenciais:** abas · sintaxe · localizar/substituir regex · UTF-8/ANSI · não perde ao fechar — todos **já tinham**.
- **Fiz agora:**
  1. *Comentar/descomentar linhas* (`comentar_descomentar_linhas` + Ctrl+Q) por linguagem (#, //, --, <!--, /*).
  2. *Ordenar linhas* A→Z / Z→A (`ordenar_linhas`) no menu Editar.
- **Falta:** nada dos 5 essenciais; bookmarks F2 / coluna multi-seleção ficam pra depois.
- **Testes:** `test_npp.py` OK (comentar+ordenar + smoke).

## T372 — Paridade [player-video] vs VLC / K-Lite (2026-11-17)
- **Alvo:** `C:\Users\caion\player-video`
- **Essenciais:** qualquer formato · legenda .srt · velocidade/atalhos · playlist — todos **já tinham**.
- **Fiz agora:**
  1. *Proporção da tela* (`aspect_ratio_value` / `letterbox_size` + combo Automático/16:9/4:3/1:1/2.35:1/Esticar).
  2. *Recentes* (JSON em AppData + menu 🕓) e *quadro a quadro* (`frame_step_ms` + tecla E).
- **Falta:** nada dos 4 essenciais; faixas de áudio múltiplas / ASS ficam pra depois.
- **Testes:** `test_vpl.py` 10 OK.

## T371 — Paridade [copiador-rapido] vs TeraCopy (2026-11-17)
- **Alvo:** `C:\Users\caion\copiador-rapido`
- **Essenciais:** fila grande · pausar/retomar · verificar hash · pular erro — todos **já tinham**.
- **Fiz agora:**
  1. *Limite de velocidade* (`speed_limit_mbps` no motor + spin “Limite MB/s” / Sem limite) estilo TeraCopy.
  2. *Relatório TXT* (`format_job_report` + botão Relatório TXT) além do CSV já existente.
- **Falta:** nada dos 4 essenciais; integração shell Explorer fica pra depois.
- **Testes:** `test_cpr.py` 8 OK + `test_cpr_edicao.py` 5 OK.

## T369 — Paridade [scanner-documentos] vs Scanner do Windows (2026-11-17)
- **Alvo:** `C:\Users\caion\scanner-documentos`
- **Essenciais:** digitalizar da impressora · virar PDF · cortar/endireitar — todos **já tinham** (WIA, PDF multipágina, deskew, crop).
- **Fiz agora:**
  1. *Modo de cor estilo Scanner* (`aplicar_modo_cor`: Cor / Tons de Cinza / Preto e Branco) + combo na barra da prévia.
  2. *Dividir folha dupla* (`dividir_folha_dupla`) — livro/duas páginas lado a lado vira 2 páginas na fila do PDF.
- **Falta:** nada dos 3 essenciais; ADF duplex nativo via WIA avançado fica pra depois.
- **Testes:** `test_scn.py` + `test_scn_edicao.py` OK (modo cor + folha dupla).

## T368 — Paridade [comparar-pastas] vs WinMerge (2026-11-17)
- **Alvo:** `C:\Users\caion\comparar-pastas`
- **Essenciais:** comparar pastas · texto lado a lado · copiar diferenças — todos **já tinham**.
- **Fiz agora:** diff por caractere (`inline_char_diff` / `format_inline_char_diff`) na linha selecionada; detecção de fim de linha CRLF/LF/CR/mixed; Copiar Diffs pro clipboard (`copy_diff_text`).
- **Falta:** nada dos 3 essenciais; 3-way merge fica pra depois.
- **Testes:** `test_cpz.py` OK (inline+EOL+smoke GUI).

## T366 — Paridade [notas-md] vs Evernote (2026-11-17)
- **Alvo:** `C:\Users\caion\notas-md`
- **Essenciais vitrine:** notas com busca · pastas/etiquetas · imagens · exportar — todos **já tinham**.
- **Tinha:** pastas, tags `#`, busca com operadores, imagens `_imagens/`, export MD/HTML/PDF/ZIP, pin, templates, histórico, duplicar.
- **Fiz agora:**
  1. *Links internos `[[Nota]]`* (extract/resolve/format/suggest) + botão `[[ ]]` / Ctrl+Shift+L.
  2. *Mesclar notas* (`merge_notes`) estilo Evernote Merge + seleção múltipla na lista + botão 🧬 Mesclar.
- **Falta:** nada dos 4 essenciais; lembretes com data/hora e sync na nuvem ficam fora (Evernote cloud).
- **Testes:** `test_nm.py` OK (wiki+merge + smoke ExtendedSelection).

## T365 — Paridade [laboratorio-audio] vs Audacity (2026-11-17)
- **Alvo:** `C:\Users\caion\laboratorio-audio`
- **Essenciais vitrine:** gravar · cortar/juntar · normalizar+remover ruído · exportar MP3/WAV — todos **já tinham**.
- **Tinha:** gravação MCI, waveform com seleção, trim/cut/paste/delete, normalize pico/RMS, noise profile+spectral, export WAV/MP3 via FFmpeg, undo/redo, fades, etc.
- **Fiz agora:**
  1. *Compressor dinâmico* (`compress_dynamic_range`, Effect › Compressor do Audacity) vetorizado + botão na GUI (seleção ou faixa).
  2. *Mono ↔ Estéreo* na barra + *bitrate MP3* 128/192/256/320k no export (faixa e seleção).
- **Falta:** nada dos 4 essenciais; equalizador multibanda / pitch sem mudar tempo ficam pra depois.
- **Testes:** `test_syn.py` 13 OK (novo compressor+canais; smoke bitrate/mono/compress); `test_syn_edicao.py` ok.

## T363 — Paridade [rede] vs Speedtest / Advanced IP Scanner (2026-11-17)
- **Alvo:** `C:\Users\caion\rede`
- **Essenciais vitrine:** teste de velocidade · quem está na rede (IP/fabricante) · ping/diagnóstico — todos **já tinham** (T332).
- **Tinha:** speedtest Cloudflare com picos/presets/veredito, varredura ARP+OUI+WoL+classificação+faixa IP, ping/tracert/DNS/info.
- **Fiz agora:**
  1. *Histórico persistente de speedtest* (JSON em `%APPDATA%\CaixaFerramentas`) com médias, melhor Down, Δ vs anterior e limpar de verdade — gap vs Ookla (antes só sessão).
  2. *Filtro por categoria* na lista de dispositivos (Roteador/Impressora/NAS/TV/Móvel/IoT/PC) + `filter_devices` no core — estilo Advanced IP Scanner.
- **Falta:** nada dos 3 essenciais; escolha de servidor Ookla oficial (API proprietária) de propósito fora.
- **Testes:** 21 em `test_rd.py` OK (novos: histórico/delta, filter por categoria; smoke GUI cobre combo + Δ).

## T361 Paridade faxina-disco (auditoria Grok) (2026-11-17 02:18–02:22 America/Sao_Paulo)

Auditoria de paridade de `C:\Users\caion\faxina-disco` contra WinDirStat / WizTree / CCleaner. **Só leitura e teste; nenhum código da pasta foi alterado.** Harness em `C:\Users\caion\fiscal-fabrica\grok_t361\`.

**Sem varredura do disco do Caio e sem limpeza real.** `iniciar_varredura_ao_abrir()` hoje **sempre devolve False** (o `main()` não auto-varre ao abrir; o construtor também não chama `start_scan()`). Sem `--pasta`, porém, a pasta padrão é `os.path.expanduser("~")`. A GUI foi aberta só com `Faxina(pasta_inicial=grok_t361\tree)`. Não troquei a unidade no combo (isso apontaria `C:\` ou `G:\`), não cliquei em “Escolher pasta”, “Analisar Cache & Temporários”, “Limpar selecionados”, “Mandar pra Lixeira” nem “Abrir local”. A varredura de tamanho (`start_scan` / `scanner.scan`) rodou **somente** na árvore de teste (9 arquivos, 272,0 KB). O cabeçalho mostra espaço livre do volume C: via `shutil.disk_usage` — isso é metadado do volume, não caminhada de arquivos.

**Limpeza:** `analyze_cleanup()` sem `custom_roots` usa `_default_cleanup_roots()` e varre `%TEMP%`, thumbcache, CrashDumps, cache do Edge/Chrome, WER, cache do Windows Update (`SoftwareDistribution\Download`), instaladores em `~/Downloads`, e consulta a Lixeira real (`SHQueryRecycleBinW`). `run_cleanup()` chama `clean_category_files(..., allow_system_recycle=True)`, que **apaga com `os.unlink`** (não manda pra Lixeira) e pode **esvaziar a Lixeira do Windows** (`SHEmptyRecycleBinW`); depois chama de novo `analyze_cleanup()` **sem** `custom_roots`. Nesta auditoria a limpeza real só rodou em `grok_t361\clean_sandbox`, com `custom_roots` explícitos e `allow_system_recycle=False`. Não usei `move_to_trash`.

**Scan de caminhos antes do pytest:** pulei de propósito `test_move_to_trash` e `test_gui_drive_combo_and_export_csv_and_trash_duplicates` (mandam arquivo para a Lixeira do usuário; o segundo ainda grava `test_export_faxina.csv` em `tempfile.gettempdir()` no modo offscreen). Suite isolada (HOME/USERPROFILE/APPDATA/TEMP em `grok_t361\fakehome`): **20 passed, 2 deselected** em 0,21 s.

### Itens da vitrine

| Item | Veredito | Evidência |
|------|----------|-----------|
| O que ocupa o disco em gráfico | **tinha** (na pasta varrida) | Aba “Tipos & Gráfico”: barra por extensão, tabela e treemap (estilo WinDirStat). Print da árvore de teste: `.mp4` 2 arquivos, 250,0 KB, 91,9%; `.bin` 16,0 KB; `.jpg` 6,0 KB. Treemap mostra `filme_grande_t361.mp4`, `clip_t361.mp4`, `copia_a/b_t361.bin`, `foto1_t361` — só a pasta de teste. Independente: `.mp4` = 256000 B, 2 arquivos. |
| Maiores arquivos | **tinha** | Aba “Maiores arquivos” com filtro. Independente: o maior é `filme_grande_t361.mp4` (204800 B), depois `clip_t361.mp4` (51200 B). |
| Duplicados | **tinha** | Aba “Duplicados”, presets e “Procurar duplicados”. Independente: um grupo de 8192 B com `copia_a_t361.bin` e `copia_b_t361.bin`. Não enviei cópias à Lixeira. |
| Limpar temporários com segurança | **está ruim / perigoso no modo padrão** | Com `custom_roots` na sandbox, a prévia e a limpeza seletiva funcionaram (thumbs+dumps: 2 arquivos / 5120 B removidos; `documento.txt`, `app.dll`, `sessao.tmp` e `keep\` ficaram). No clique da GUI, a análise e a limpeza usam as pastas reais do sistema (TEMP, caches, Downloads, Update) e **apagos diretos**. |
| Mandar pra Lixeira (nunca apagar direto) | **parcial / está ruim na Limpeza Rápida** | “Mandar pra Lixeira” nos arquivos da varredura usa `move_to_trash` (send2trash / SHFileOperation). Já a Limpeza Rápida faz `os.unlink` e pode esvaziar a Lixeira real. Não testeí o envio à Lixeira nesta auditoria. |
| Visual pt-BR | **tinha** | Título “Faxina de disco”; Escolher pasta, Varrer, Parar; abas Pastas, Tipos & Gráfico, Maiores arquivos, Duplicados, Limpeza Rápida; Exportar CSV, Abrir local, Mandar pra Lixeira (screenshot). |
| Tema escuro | **tinha** (print confirma). |
| Sem travar | **tinha** nesta abertura (só árvore de teste) | 20 testes em 0,21 s; varredura de 9 arquivos instantânea; PrintWindow pid **18268**, 1116×799, residual 0. |

### Prioridade para o construtor (1–2 itens)

1. **Não varrer pastas reais no modo de teste nem no “Analisar” sem alvo explícito.** Em `CAIXA_TESTE=1`, não usar `_default_cleanup_roots()`; exigir `custom_roots`. Depois de `run_cleanup()`, não chamar `analyze_cleanup()` sem os mesmos roots. O combo de unidades + “Varrer” ainda pode caminhar `C:\` / `G:\`.
2. **A Limpeza Rápida deve ir pra Lixeira (nunca `os.unlink`), e nunca esvaziar a Lixeira do sistema com `allow_system_recycle=True` no padrão.** Isolar ou pular `test_move_to_trash` e `test_gui_drive_combo_and_export_csv_and_trash_duplicates` (hoje usam a Lixeira do usuário).

Sem git, sem alteração de código da ferramenta.
