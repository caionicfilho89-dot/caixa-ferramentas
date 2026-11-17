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



